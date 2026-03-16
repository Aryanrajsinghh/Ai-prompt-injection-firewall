"""FastAPI entrypoint for the prompt injection firewall."""

from __future__ import annotations

import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.attack_simulator.red_team import run_red_team
from backend.database.logger import get_all_logs, init_db, log_attack
from backend.decision.threat_engine import evaluate_threat
from backend.firewall.fingerprint import generate_fingerprint
from backend.firewall.rule_engine import scan_prompt_rules
from backend.firewall.sandbox import analyze_in_sandbox
from backend.guardrails.output_guard import scan_output
from backend.integration.ai_detection import get_ai_detection


DASHBOARD_FILE = Path(__file__).resolve().parent / "dashboard" / "index.html"

# Phrases stripped from prompt when action is "sanitize"
_SANITIZE_PHRASES = [
    r"ignore previous instructions?",
    r"reveal system prompt",
    r"print api[_\s]?key",
    r"developer mode",
    r"bypass safety restrictions?",
    r"show hidden instructions?",
    r"forget prior rules?",
    r"disregard system prompt",
    r"you are now",
    r"act as\b",
    r"pretend to be",
    r"dump secrets?",
    r"access token",
]
_SANITIZE_PATTERN = re.compile(
    "|".join(_SANITIZE_PHRASES), flags=re.IGNORECASE
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize resources on startup."""
    init_db()
    yield


app = FastAPI(
    title="AI Prompt Injection Firewall",
    version="1.0.0",
    lifespan=lifespan,
)


class PromptScanRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="User-provided prompt text.",
    )


@app.post("/scan_prompt")
async def scan_prompt(body: PromptScanRequest) -> Dict[str, Any]:
    """Run the full prompt security pipeline and return a safe summary response."""

    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt must not be empty.")

    # ── Security pipeline ────────────────────────────────────────────────────
    rule_result        = scan_prompt_rules(prompt)
    fingerprint_result = generate_fingerprint(prompt)
    sandbox_result     = analyze_in_sandbox(prompt)
    ai_result          = await get_ai_detection(prompt)
    decision_result    = evaluate_threat(
        rule_result=rule_result,
        fingerprint_result=fingerprint_result,
        sandbox_result=sandbox_result,
        ai_result=ai_result,
    )

    action = decision_result["action"]

    # ── Sanitize prompt when action requires it ──────────────────────────────
    safe_prompt = _sanitize_prompt(prompt) if action == "sanitize" else prompt

    # ── Build placeholder AI response then apply output guardrails ───────────
    raw_response       = _build_ai_response(safe_prompt, action)
    output_guard_result = scan_output(raw_response)
    final_response     = output_guard_result["clean_output"]

    # ── Persist event ────────────────────────────────────────────────────────
    attack_type = _resolve_attack_type(rule_result, ai_result)
    log_attack(
        prompt=prompt,
        attack_type=attack_type,
        risk_score=decision_result["final_risk_score"],
        decision=action,
    )

    # ── Return summary only (internals never exposed to caller) ─────────────
    return {
        "action": action,
        "risk_score": decision_result["final_risk_score"],
        "attack_type": attack_type,
        "reasons": decision_result["reasons"],
        "response_blocked": not output_guard_result["safe"],
        "final_response": final_response,
    }


@app.get("/logs")
async def list_logs() -> List[Dict[str, Any]]:
    """Return all logged prompt events."""
    return get_all_logs()


@app.get("/dashboard_data")
async def dashboard_data() -> Dict[str, Any]:
    """Return aggregated statistics for the dashboard (no red-team execution)."""

    logs = get_all_logs()
    attacks_by_category: Dict[str, int] = {}
    decisions: Dict[str, int] = {}
    for log in logs:
        attacks_by_category[log["attack_type"]] = (
            attacks_by_category.get(log["attack_type"], 0) + 1
        )
        decisions[log["decision"]] = decisions.get(log["decision"], 0) + 1

    return {
        "attacks_by_category": attacks_by_category,
        "decision_distribution": decisions,
        "recent_logs": logs[:10],
    }


@app.post("/run_red_team")
async def trigger_red_team(request: Request) -> Dict[str, Any]:
    """Manually trigger the red-team simulator. Do NOT call from dashboards on a timer."""
    try:
        return await run_red_team(base_url=str(request.base_url).rstrip("/"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    """Serve the security dashboard."""
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return HTMLResponse(DASHBOARD_FILE.read_text(encoding="utf-8"))


# ── Private helpers ──────────────────────────────────────────────────────────

def _sanitize_prompt(prompt: str) -> str:
    """Strip known malicious phrases from a prompt flagged for sanitization."""
    return _SANITIZE_PATTERN.sub("[REMOVED]", prompt).strip()


def _build_ai_response(prompt: str, action: str) -> str:
    """Build a placeholder response that exercises the output guardrails."""
    if action == "block":
        return "Request blocked due to detected prompt injection risk."
    if action == "sanitize":
        return f"Sanitized response generated for: {prompt[:120]}"
    return "Request processed safely by the protected AI system."


def _resolve_attack_type(
    rule_result: Dict[str, Any], ai_result: Dict[str, Any]
) -> str:
    if rule_result.get("matched"):
        return str(rule_result.get("attack_type", "unknown"))
    return str(ai_result.get("attack_type", "unknown"))
