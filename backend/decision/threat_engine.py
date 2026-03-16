"""Threat decision engine."""

from __future__ import annotations

from typing import Any, Dict, List


def evaluate_threat(
    rule_result: Dict[str, Any],
    fingerprint_result: Dict[str, Any],
    sandbox_result: Dict[str, Any],
    ai_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Combine pipeline signals into a final decision."""

    reasons: List[str] = []
    weighted_risk = (
        _rule_risk(rule_result) * 0.3
        + float(fingerprint_result.get("anomaly_score", 0.0)) * 0.2
        + float(sandbox_result.get("sandbox_risk", 0.0)) * 0.2
        + float(ai_result.get("risk_score", 0.5)) * 0.3
    )
    final_risk_score = round(max(0.0, min(weighted_risk, 1.0)), 4)

    if rule_result.get("matched"):
        reasons.append(
            f"Rule engine matched: {', '.join(rule_result.get('matched_patterns', []))}"
        )
    if fingerprint_result.get("anomaly_score", 0.0) >= 0.35:
        reasons.append(
            f"Fingerprint anomaly score elevated: {fingerprint_result['anomaly_score']}"
        )
    if sandbox_result.get("suspicious"):
        reasons.append(
            "Sandbox detected behaviors: "
            + ", ".join(sandbox_result.get("behaviors_detected", []))
        )
    if float(ai_result.get("risk_score", 0.5)) >= 0.3:
        reasons.append(
            f"AI detection flagged {ai_result.get('attack_type', 'unknown')} with risk {ai_result.get('risk_score')}"
        )

    action = _risk_to_action(final_risk_score)

    return {
        "action": action,
        "final_risk_score": final_risk_score,
        "reasons": reasons or ["No significant risk indicators detected."],
    }


def _rule_risk(rule_result: Dict[str, Any]) -> float:
    if not rule_result.get("matched"):
        return 0.0

    attack_type = rule_result.get("attack_type", "benign")
    risk_by_type = {
        "instruction_override": 0.65,
        "jailbreak_attempt": 0.7,
        "data_exfiltration": 0.9,
        "privilege_escalation": 0.8,
    }
    return risk_by_type.get(attack_type, 0.5)


def _risk_to_action(risk_score: float) -> str:
    if risk_score < 0.3:
        return "allow"
    if risk_score <= 0.7:
        return "sanitize"
    return "block"
