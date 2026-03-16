"""Output guardrails for AI responses."""

from __future__ import annotations

import re


BLOCK_PATTERNS = {
    "system prompts": [
        r"system prompt",
        r"internal instructions",
        r"hidden instructions",
    ],
    "API keys or tokens": [
        r"api[_\s-]?key",
        r"secret[_\s-]?token",
        r"sk-[a-z0-9]{12,}",
    ],
    "internal privileged data": [
        r"internal privileged data",
        r"confidential backend",
        r"private credentials",
    ],
}


def scan_output(response_text: str) -> dict:
    """Scan response text for sensitive content leaks."""

    for category, patterns in BLOCK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                return {
                    "safe": False,
                    "blocked_reason": category,
                    "clean_output": "Response blocked by output guardrails.",
                }

    return {
        "safe": True,
        "blocked_reason": None,
        "clean_output": response_text,
    }
