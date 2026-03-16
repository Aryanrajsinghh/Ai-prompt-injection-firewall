"""Prompt fingerprinting engine."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import List


SUSPICIOUS_KEYWORDS = {
    "ignore",
    "bypass",
    "reveal",
    "system",
    "prompt",
    "hidden",
    "developer",
    "api",
    "key",
    "override",
    "jailbreak",
    "token",
}

STRUCTURAL_COMMAND_MARKERS = {
    "ignore previous",
    "act as",
    "system:",
    "developer mode",
    "reveal",
    "print",
    "show",
    "bypass",
}


def generate_fingerprint(prompt: str) -> dict:
    """Generate simple statistical features to fingerprint prompts."""

    tokens = _tokenize(prompt)
    token_count = len(tokens) or 1
    token_frequency = Counter(tokens)
    suspicious_count = sum(1 for token in tokens if token in SUSPICIOUS_KEYWORDS)
    override_pattern_count = sum(
        1 for marker in STRUCTURAL_COMMAND_MARKERS if marker in prompt.lower()
    )

    structural_command_score = min(
        1.0,
        (
            override_pattern_count * 0.18
            + prompt.count(":") * 0.04
            + prompt.count("\n") * 0.03
            + _imperative_verb_score(tokens) * 0.2
        ),
    )

    suspicious_keyword_density = suspicious_count / token_count
    prompt_length = len(prompt)

    anomaly_score = min(
        1.0,
        (
            suspicious_keyword_density * 0.45
            + min(override_pattern_count / 5, 1.0) * 0.3
            + structural_command_score * 0.2
            + _entropy_score(token_frequency, token_count) * 0.05
        ),
    )

    return {
        "fingerprint": {
            "prompt_length": prompt_length,
            "suspicious_keyword_density": round(suspicious_keyword_density, 4),
            "override_pattern_count": override_pattern_count,
            "token_frequency": dict(token_frequency.most_common(20)),
            "structural_command_score": round(structural_command_score, 4),
        },
        "anomaly_score": round(anomaly_score, 4),
    }


def _tokenize(prompt: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", prompt.lower())


def _imperative_verb_score(tokens: List[str]) -> float:
    verbs = {"ignore", "reveal", "print", "show", "bypass", "dump", "output"}
    imperative_hits = sum(1 for token in tokens if token in verbs)
    return min(imperative_hits / max(len(tokens), 1), 1.0)


def _entropy_score(token_frequency: Counter[str], token_count: int) -> float:
    entropy = 0.0
    for count in token_frequency.values():
        probability = count / token_count
        entropy -= probability * math.log2(probability)
    return min(entropy / 6, 1.0)
