"""Prompt sandbox analyzer."""

from __future__ import annotations

from typing import Dict, List


BEHAVIOR_PATTERNS: Dict[str, List[str]] = {
    "override_system_instructions": [
        "ignore previous instructions",
        "forget prior rules",
        "disregard system prompt",
        "override",
    ],
    "reveal_hidden_system_prompts": [
        "reveal system prompt",
        "show hidden instructions",
        "display internal prompt",
    ],
    "manipulate_ai_roles": [
        "you are now",
        "act as",
        "developer mode",
        "pretend to be",
    ],
    "access_restricted_internal_data": [
        "print api key",
        "dump secrets",
        "internal data",
        "access token",
    ],
}

# Total number of behavior categories — used to normalize the behavior score
_MAX_BEHAVIORS = len(BEHAVIOR_PATTERNS)


def analyze_in_sandbox(prompt: str) -> dict:
    """Perform behavioral analysis on prompt contents."""

    normalized_prompt = prompt.lower()
    behaviors_detected = [
        behavior
        for behavior, patterns in BEHAVIOR_PATTERNS.items()
        if any(pattern in normalized_prompt for pattern in patterns)
    ]

    # Normalize behavior count to [0.0, 1.0] range before applying weight
    behavior_score = len(behaviors_detected) / _MAX_BEHAVIORS

    # Bonus signals for high-severity indicators
    system_bonus  = 0.12 if "system" in normalized_prompt else 0.0
    secret_bonus  = 0.18 if "api key" in normalized_prompt or "token" in normalized_prompt else 0.0
    repeat_bonus  = 0.08 if normalized_prompt.count("ignore") > 1 else 0.0

    sandbox_risk = min(
        1.0,
        behavior_score * 0.62 + system_bonus + secret_bonus + repeat_bonus,
    )

    return {
        "suspicious": bool(behaviors_detected),
        "behaviors_detected": behaviors_detected,
        "sandbox_risk": round(sandbox_risk, 4),
    }
