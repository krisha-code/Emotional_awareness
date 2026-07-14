"""
backend/app/services/fusion_engine.py

Combines face / text / speech / physiological modality results into one
fused emotion estimate, with cross-modal conflict scoring.

Base modality weights (see docs/FUSION_WEIGHTING_DESIGN_NOTE.md for the
full rationale, co-designed with the frontend/integration owner):

    face: 0.30   text: 0.45   speech: 0.20   physiological: 0.05

Text is weighted highest because it's the most direct, low-ambiguity
channel for self-reported affect and the only channel carrying the crisis
signal. Weights are NOT static, though — they shift per-request based on:

    1. Confidence re-weighting: a modality's weight is scaled by its own
       prediction confidence (low-confidence face reads shouldn't drag
       down a highly-confident text signal).
    2. Sarcasm dampening: if `sarcasm_detected` is true for text, text's
       *relative* weight is reduced and speech is allowed to break the
       tie, since prosody is a stronger sarcasm/deadpan signal than the
       words themselves (see design note, Section 3).
    3. Crisis override: if `crisis_detected` is true, fusion still runs
       normally for the reported `fused_label`/`fused_confidence`, but the
       function also returns `crisis_override=True` so the route layer
       can force severity to at least "high" regardless of what the
       fused label/conflict score would otherwise imply. This module
       never silently hides a crisis flag inside an averaged score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

BASE_WEIGHTS = {
    "face": 0.30,
    "text": 0.45,
    "speech": 0.20,
    "physiological": 0.05,
}

EMOTION_LABELS = ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"]

# How much to shrink text's relative weight when sarcasm is flagged, and
# how much of that gets reallocated to speech specifically (rather than
# split evenly) — speech tone is the tie-breaker for ambiguous/deadpan text.
SARCASM_TEXT_DAMPING = 0.35
SARCASM_SPEECH_BOOST_SHARE = 0.7  # fraction of the damped weight given to speech


@dataclass
class FusionResult:
    fused_label: str
    fused_confidence: float
    conflict_detected: bool
    conflict_score: float
    modality_weights: Dict[str, float]
    crisis_override: bool


def _effective_weights(
    modality_confidences: Dict[str, float],
    present_modalities: list,
    sarcasm_detected: bool,
) -> Dict[str, float]:
    weights = {m: BASE_WEIGHTS[m] for m in present_modalities}

    # Confidence re-weighting: multiply, then renormalize.
    for m in weights:
        conf = modality_confidences.get(m, 1.0)
        weights[m] *= max(conf, 0.05)  # floor so a near-zero confidence doesn't zero out entirely

    # Sarcasm dampening — only meaningful if both text and speech present.
    if sarcasm_detected and "text" in weights and "speech" in weights:
        shift = weights["text"] * SARCASM_TEXT_DAMPING
        weights["text"] -= shift
        weights["speech"] += shift * SARCASM_SPEECH_BOOST_SHARE
        # remainder of the shift is redistributed proportionally to everyone else
        remainder = shift * (1 - SARCASM_SPEECH_BOOST_SHARE)
        others = [m for m in weights if m not in ("text",)]
        if others:
            for m in others:
                weights[m] += remainder / len(others)

    total = sum(weights.values()) or 1.0
    return {m: w / total for m, w in weights.items()}


def _conflict_score(modality_probs: Dict[str, Dict[str, float]], weights: Dict[str, float]) -> float:
    """
    Measures how much modalities disagree, independent of which label
    "wins". Computed as the weighted average pairwise distance between
    each modality's per-emotion probability vector (L1 distance / 2, so
    the result is naturally bounded to [0, 1]).
    """
    modalities = list(modality_probs.keys())
    if len(modalities) < 2:
        return 0.0

    total_weight = 0.0
    weighted_disagreement = 0.0
    for i in range(len(modalities)):
        for j in range(i + 1, len(modalities)):
            m1, m2 = modalities[i], modalities[j]
            p1, p2 = modality_probs[m1], modality_probs[m2]
            l1_dist = sum(abs(p1.get(lbl, 0.0) - p2.get(lbl, 0.0)) for lbl in EMOTION_LABELS) / 2
            pair_weight = weights.get(m1, 0.0) * weights.get(m2, 0.0)
            weighted_disagreement += l1_dist * pair_weight
            total_weight += pair_weight

    return weighted_disagreement / total_weight if total_weight else 0.0


def fuse(
    modality_probs: Dict[str, Dict[str, float]],
    modality_confidences: Dict[str, float],
    sarcasm_detected: bool = False,
    crisis_detected: bool = False,
    conflict_threshold: float = 0.35,
) -> FusionResult:
    """
    modality_probs: e.g. {"face": {...7 probs...}, "text": {...}, "speech": {...}}
    modality_confidences: e.g. {"face": 0.81, "text": 0.76, "speech": 0.62}
    """
    present = list(modality_probs.keys())
    weights = _effective_weights(modality_confidences, present, sarcasm_detected)

    fused_probs = {lbl: 0.0 for lbl in EMOTION_LABELS}
    for modality, probs in modality_probs.items():
        w = weights.get(modality, 0.0)
        for lbl in EMOTION_LABELS:
            fused_probs[lbl] += w * probs.get(lbl, 0.0)

    fused_label = max(fused_probs, key=fused_probs.get)
    fused_confidence = fused_probs[fused_label]

    conflict_score = _conflict_score(modality_probs, weights)
    conflict_detected = conflict_score >= conflict_threshold

    return FusionResult(
        fused_label=fused_label,
        fused_confidence=round(fused_confidence, 4),
        conflict_detected=conflict_detected,
        conflict_score=round(conflict_score, 4),
        modality_weights={m: round(w, 4) for m, w in weights.items()},
        crisis_override=crisis_detected,
    )
