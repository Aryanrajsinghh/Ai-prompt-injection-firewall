"""Client for the external AI detection service."""

from __future__ import annotations

from typing import Any, Dict

import httpx

from backend.config import settings


DEFAULT_AI_DETECTION_RESULT = {
    "attack_type": "unknown",
    "risk_score": 0.5,
}


async def get_ai_detection(prompt: str) -> Dict[str, Any]:
    """Fetch attack classification from the external AI detection API."""

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.ai_detection_api_url,
                json={"prompt": prompt},
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError):
        return DEFAULT_AI_DETECTION_RESULT.copy()

    attack_type = str(payload.get("attack_type", DEFAULT_AI_DETECTION_RESULT["attack_type"]))
    risk_score_raw = payload.get("risk_score", DEFAULT_AI_DETECTION_RESULT["risk_score"])
    try:
        risk_score = float(risk_score_raw)
    except (TypeError, ValueError):
        risk_score = DEFAULT_AI_DETECTION_RESULT["risk_score"]

    return {
        "attack_type": attack_type,
        "risk_score": max(0.0, min(risk_score, 1.0)),
    }
