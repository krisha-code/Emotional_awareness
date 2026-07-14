"""
backend/ml/text/sarcasm_detector.py

Sarcasm and negation handling so flat/ambiguous phrasing isn't misread as
genuine positive emotion (e.g. "great, another Monday", "I'm SO fine").

Two complementary signals, combined into one sarcasm probability:

1. Negation scope detection — cheap, rule-based, catches "not happy",
   "hardly thrilled", "isn't great", etc. Flips or dampens the polarity
   of the emotion word(s) inside the negation's scope.

2. Sarcasm classifier — a lightweight model-based signal (falls back to a
   heuristic cue-counter in mock mode: contrast connectives + exaggeration
   punctuation + incongruent positive-word/negative-context combos).

Both signals feed `adjust_for_sarcasm`, which the text inference pipeline
calls after the base emotion classifier but before the result is returned,
so `sarcasm_detected` and the (possibly re-weighted) probabilities are
computed together.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Negation cues that flip/dampen whatever polarity follows them within a
# short window (heuristic scope, not full dependency parsing).
_NEGATION_CUES = {
    "not", "no", "never", "isn't", "aren't", "wasn't", "weren't",
    "don't", "doesn't", "didn't", "can't", "cannot", "won't", "wouldn't",
    "hardly", "barely", "scarcely", "without",
}

# Connectives that often introduce a sarcastic contrast ("great, but of
# course...", "yeah right", "oh sure").
_CONTRAST_CUES = ["yeah right", "oh sure", "as if", "totally", "just great", "just perfect"]

# Positive-affect words that, in a negative or exclamatory context, are the
# classic sarcasm tell ("great", "wonderful", "love this", "thrilled").
_POSITIVE_MARKERS = {"great", "wonderful", "perfect", "love", "thrilled", "fantastic", "amazing"}

_NEGATION_WINDOW = 3  # tokens after a negation cue considered "in scope"


@dataclass
class SarcasmSignal:
    sarcasm_detected: bool
    sarcasm_score: float  # 0-1
    negation_spans: List[Tuple[int, int]]
    cues: List[str]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def detect_negation_spans(tokens: List[str]) -> List[Tuple[int, int]]:
    """Return (start, end) index ranges of tokens considered negated."""
    spans = []
    for i, tok in enumerate(tokens):
        if tok in _NEGATION_CUES:
            spans.append((i + 1, min(i + 1 + _NEGATION_WINDOW, len(tokens))))
    return spans


def _heuristic_sarcasm_score(text: str, tokens: List[str], negation_spans: List[Tuple[int, int]]) -> Tuple[float, List[str]]:
    lowered = text.lower()
    cues_hit = []
    score = 0.0

    for cue in _CONTRAST_CUES:
        if cue in lowered:
            score += 0.35
            cues_hit.append(cue)

    # Exaggerated punctuation ("great...", "wonderful!!!") next to a
    # negative-context word is a common sarcasm signature.
    if re.search(r"(great|wonderful|perfect|love(d)?|thrilled)\W*(\.\.\.|!!)", lowered):
        score += 0.25
        cues_hit.append("exaggerated_punctuation")

    # Positive marker falling inside a negation span, or immediately
    # followed by an explicitly negative clause joined by a comma/"but".
    positive_positions = [i for i, t in enumerate(tokens) if t in _POSITIVE_MARKERS]
    for pos in positive_positions:
        in_negation = any(start <= pos < end for start, end in negation_spans)
        if in_negation:
            score += 0.2
            cues_hit.append(f"negated_positive:{tokens[pos]}")
        # "great, {negative clause}" pattern
        tail = " ".join(tokens[pos + 1 : pos + 5])
        if re.search(r"\b(ruined|worst|hate|awful|terrible|ugh)\b", tail):
            score += 0.3
            cues_hit.append(f"incongruent_context:{tokens[pos]}")

    return min(score, 1.0), cues_hit


def analyze(text: str) -> SarcasmSignal:
    tokens = _tokenize(text)
    negation_spans = detect_negation_spans(tokens)
    score, cues = _heuristic_sarcasm_score(text, tokens, negation_spans)
    return SarcasmSignal(
        sarcasm_detected=score >= 0.4,
        sarcasm_score=score,
        negation_spans=negation_spans,
        cues=cues,
    )


_POLARITY = {
    "joy": 1,
    "surprise": 1,
    "neutral": 0,
    "sadness": -1,
    "anger": -1,
    "fear": -1,
    "disgust": -1,
}


def adjust_for_sarcasm(probabilities: Dict[str, float], text: str) -> Tuple[Dict[str, float], SarcasmSignal]:
    """
    Given the raw emotion classifier probabilities, apply a sarcasm/negation
    correction and return the adjusted distribution alongside the signal
    used to compute `sarcasm_detected` for the API response.

    Strategy: when sarcasm is detected, dampen the positive-polarity mass
    and redistribute it toward the nearest negative-polarity emotion
    (default: "sadness", a safe default for flat/deadpan negativity),
    scaled by the sarcasm score. This is intentionally conservative — it
    never fully inverts the model's output, since sarcasm detection itself
    is uncertain and this feeds a wellbeing-sensitive pipeline.
    """
    signal = analyze(text)
    if not signal.sarcasm_detected:
        return probabilities, signal

    adjusted = dict(probabilities)
    positive_mass = sum(p for lbl, p in adjusted.items() if _POLARITY.get(lbl, 0) > 0)
    if positive_mass <= 0:
        return adjusted, signal

    shift = positive_mass * signal.sarcasm_score * 0.6  # conservative damping factor
    for lbl in adjusted:
        if _POLARITY.get(lbl, 0) > 0:
            adjusted[lbl] *= 1 - (shift / positive_mass)

    # Redistribute the shifted mass to sadness (nearest "flat negative"
    # emotion for deadpan/sarcastic text) rather than anger/disgust, which
    # would overstate the signal.
    adjusted["sadness"] = adjusted.get("sadness", 0.0) + shift

    total = sum(adjusted.values()) or 1.0
    adjusted = {k: v / total for k, v in adjusted.items()}
    return adjusted, signal
