"""Rule-based prompt firewall."""

from __future__ import annotations

from typing import Dict, List


PATTERN_CLASSIFICATIONS: Dict[str, str] = {
    "ignore previous instructions": "instruction_override",
    "reveal system prompt": "data_exfiltration",
    "print api key": "data_exfiltration",
    "developer mode": "privilege_escalation",
    "bypass safety restrictions": "jailbreak_attempt",
    "show hidden instructions": "data_exfiltration",
}


def scan_prompt_rules(prompt: str) -> dict:
    """Match well-known prompt injection patterns."""

    normalized_prompt = prompt.lower()
    matched_patterns: List[str] = [
        pattern for pattern in PATTERN_CLASSIFICATIONS if pattern in normalized_prompt
    ]

    if not matched_patterns:
        return {
            "matched": False,
            "attack_type": "benign",
            "matched_patterns": [],
        }

    attack_type = _select_primary_attack_type(matched_patterns)
    return {
        "matched": True,
        "attack_type": attack_type,
        "matched_patterns": matched_patterns,
    }


def _select_primary_attack_type(matched_patterns: List[str]) -> str:
    """Choose the dominant attack type across matched patterns."""

    priority = {
        "data_exfiltration": 4,
        "privilege_escalation": 3,
        "instruction_override": 2,
        "jailbreak_attempt": 1,
    }
    attack_types = [PATTERN_CLASSIFICATIONS[pattern] for pattern in matched_patterns]
    return max(attack_types, key=lambda attack_type: priority.get(attack_type, 0))
