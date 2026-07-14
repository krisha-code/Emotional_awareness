"""
backend/ml/text/crisis_detector.py

Dedicated high-priority "distress / crisis" detector.

This is intentionally NOT folded into the 7-way emotion softmax: crisis
language (hopelessness, suicidal ideation, self-harm intent) needs its own
gate because (a) it must never be diluted by averaging against other
classes, and (b) the fusion engine treats it as an override signal rather
than "just another emotion."

Design:
- Primary signal: a small text-classification model fine-tuned for
  suicide/self-harm risk language (e.g. a HF model trained on the
  Reddit-based SDCNL / C-SSRS-aligned corpora). Loaded lazily; falls back
  to a lightweight lexical+syntactic heuristic in mock mode.
- The heuristic is a coarse, low-precision safety net only — it flags a
  SMALL set of unambiguous first-person distress patterns (not an
  exhaustive phrase library) and is designed to over-trigger rather than
  under-trigger, since a false positive here costs a follow-up question
  while a false negative could miss someone who needs help.
- Every positive is routed to `severity_grader` for human-facing next
  steps (resources, follow-up prompts) — this module NEVER auto-diagnoses
  or auto-messages a person; it only raises a flag for the app layer.

IMPORTANT: crisis_detected=True should always be treated as a hard floor
on severity (see severity_grader.py), regardless of what the 7-class
emotion model or other modalities report.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_CRISIS_MODEL = "sentinet/suicidality"  # placeholder; swap for team's vetted model

# Small, illustrative set of unambiguous first-person distress markers.
# This is a coarse safety net, NOT an exhaustive clinical lexicon — the
# model above is the primary signal. Keep this list short; expanding it
# indefinitely trades precision for false confidence.
_HIGH_RISK_PATTERNS = [
    r"\bi (want|wish) to (die|end it)\b",
    r"\bi('m| am) going to (kill|hurt) myself\b",
    r"\bi don'?t want to (be here|live) anymore\b",
    r"\bno reason to (live|go on)\b",
    r"\bi can'?t (go on|do this) anymore\b",
    r"\bi feel hopeless\b",
]

_MODERATE_RISK_PATTERNS = [
    r"\beveryone would be better off without me\b",
    r"\bi'?m a burden\b",
    r"\bnothing matters anymore\b",
]


@dataclass
class CrisisSignal:
    crisis_detected: bool
    risk_level: str  # "none" | "moderate" | "high"
    confidence: float
    matched_pattern_count: int
    mock: bool = False


class CrisisDetector:
    def __init__(self, model_name: str = DEFAULT_CRISIS_MODEL):
        self.model_name = model_name
        self._pipeline = None
        self._load_attempted = False

    def _ensure_loaded(self) -> bool:
        if self._pipeline is not None:
            return True
        if self._load_attempted:
            return False
        self._load_attempted = True
        try:
            from transformers import pipeline  # noqa: WPS433

            self._pipeline = pipeline("text-classification", model=self.model_name)
            logger.info("Loaded crisis detection model '%s'", self.model_name)
            return True
        except Exception as exc:
            logger.warning(
                "Crisis model unavailable (%s); using heuristic fallback. "
                "Heuristic fallback is intentionally conservative (favors "
                "over-flagging) and should not be treated as clinically "
                "validated.",
                exc,
            )
            return False

    def detect(self, text: str) -> CrisisSignal:
        text = (text or "").strip()
        if not text:
            return CrisisSignal(False, "none", 1.0, 0, mock=True)

        if self._ensure_loaded():
            try:
                return self._detect_real(text)
            except Exception as exc:
                logger.warning("Crisis model inference failed, using heuristic: %s", exc)

        return self._detect_heuristic(text)

    def _detect_real(self, text: str) -> CrisisSignal:
        raw = self._pipeline(text)[0]
        label = raw["label"].lower()
        score = float(raw["score"])
        is_positive = label in {"suicidal", "risk", "positive", "1", "label_1"}
        if is_positive and score >= 0.75:
            level = "high"
        elif is_positive and score >= 0.5:
            level = "moderate"
        else:
            level = "none"
        return CrisisSignal(level != "none", level, score, matched_pattern_count=0, mock=False)

    def _detect_heuristic(self, text: str) -> CrisisSignal:
        lowered = text.lower()
        high_hits = sum(1 for pat in _HIGH_RISK_PATTERNS if re.search(pat, lowered))
        mod_hits = sum(1 for pat in _MODERATE_RISK_PATTERNS if re.search(pat, lowered))

        if high_hits > 0:
            return CrisisSignal(True, "high", min(0.6 + 0.15 * high_hits, 0.95), high_hits, mock=True)
        if mod_hits > 0:
            return CrisisSignal(True, "moderate", min(0.4 + 0.1 * mod_hits, 0.7), mod_hits, mock=True)
        return CrisisSignal(False, "none", 0.9, 0, mock=True)


_default_detector: Optional[CrisisDetector] = None


def get_detector() -> CrisisDetector:
    global _default_detector
    if _default_detector is None:
        _default_detector = CrisisDetector()
    return _default_detector
