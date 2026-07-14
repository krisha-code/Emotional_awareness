"""
backend/app/services/severity_grader.py

Maps a fusion result (+ the independent crisis flag from the text
modality) onto a severity tier with a matching app-facing action and
resource list, per the README schema:

    { "tier": ..., "action": ..., "resources": [...] }

This module makes NO diagnostic claims — tiers describe recommended
*app behavior* (e.g. "surface a check-in prompt"), not a clinical
assessment of the person. Per the project's ethical safeguards, every
tier at or above "high" should route to a human-reviewable flag in
addition to whatever the UI shows the user in the moment.

IMPORTANT: `crisis_detected=True` is a hard floor on severity regardless
of conflict_score or fused_confidence — a calm-sounding voice with
crisis-flagged text is exactly the "single modality would miss this"
case this whole system exists to catch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .fusion_engine import FusionResult

# NOTE: verify these are current and correct for your deployment region/
# locale before shipping — helpline numbers and names change. These are
# the two India-based lines already referenced in this project's README.
DEFAULT_RESOURCES = [
    "iCall (India): 9152987821",
    "Vandrevala Foundation (India): 1860-2662-345",
]

TIERS = ("low", "moderate", "high", "critical")


@dataclass
class SeverityResult:
    tier: str
    action: str
    resources: List[str]
    crisis_forced: bool


def grade(
    fusion_result: FusionResult,
    crisis_risk_level: str = "none",
    baseline_deviation_significant: bool = False,
) -> SeverityResult:
    """
    fusion_result: output of fusion_engine.fuse()
    crisis_risk_level: "none" | "moderate" | "high" (from crisis_detector.py)
    baseline_deviation_significant: from baseline.py — a significant
        departure from the person's own calibrated baseline nudges
        severity up even when the raw label looks mild, to catch e.g.
        someone whose "neutral" is actually a big drop for them.
    """
    crisis_forced = False

    if crisis_risk_level == "high":
        tier = "critical"
        crisis_forced = True
    elif crisis_risk_level == "moderate":
        tier = "high"
        crisis_forced = True
    else:
        tier = _tier_from_signals(fusion_result, baseline_deviation_significant)

    action = _action_for_tier(tier, fusion_result.conflict_detected)
    resources = list(DEFAULT_RESOURCES) if tier in ("high", "critical") else []

    return SeverityResult(tier=tier, action=action, resources=resources, crisis_forced=crisis_forced)


def _tier_from_signals(fusion_result: FusionResult, baseline_deviation_significant: bool) -> str:
    negative_labels = {"sadness", "anger", "fear", "disgust"}
    is_negative = fusion_result.fused_label in negative_labels

    score = 0.0
    if is_negative:
        score += fusion_result.fused_confidence
    if fusion_result.conflict_detected:
        score += fusion_result.conflict_score  # unresolved cross-modal disagreement raises concern
    if baseline_deviation_significant:
        score += 0.3

    if score >= 0.9:
        return "high"
    if score >= 0.5:
        return "moderate"
    return "low"


def _action_for_tier(tier: str, conflict_detected: bool) -> str:
    if tier == "critical":
        return (
            "Immediate crisis-resource surface + persistent Crisis Help button; "
            "flag session for urgent human review."
        )
    if tier == "high":
        base = "Direct follow-up question, surface self-help and professional resources"
        if conflict_detected:
            base += "; note the cross-modal conflict in the check-in prompt"
        return base
    if tier == "moderate":
        return "Gentle check-in prompt; log for longitudinal trend review"
    return "No action; log for baseline calibration"
