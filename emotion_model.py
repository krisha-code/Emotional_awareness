"""
backend/ml/text/emotion_model.py

Text emotion classifier for MindSense.

Matches the 7-class taxonomy used by the facial model:
    joy, sadness, anger, fear, disgust, surprise, neutral

Model: bhadresh-savani/distilbert-base-uncased-emotion (HuggingFace, auto-downloaded)
Falls back to a deterministic "mock" distribution if the model/weights are not
available, so the rest of the team can develop against this module without a
GPU or network access to HuggingFace Hub.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Canonical 7-class taxonomy shared with backend/ml/face/train_fer2013.py
EMOTION_LABELS = ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"]

# Maps the HF model's native label set onto our shared taxonomy.
# bhadresh-savani/distilbert-base-uncased-emotion uses: sadness, joy, love, anger, fear, surprise
_HF_LABEL_MAP = {
    "sadness": "sadness",
    "joy": "joy",
    "love": "joy",  # collapsed into joy; no "love" class in shared schema
    "anger": "anger",
    "fear": "fear",
    "surprise": "surprise",
}

DEFAULT_MODEL_NAME = os.environ.get(
    "TEXT_EMOTION_MODEL", "bhadresh-savani/distilbert-base-uncased-emotion"
)


@dataclass
class ModalityResult:
    """Matches the shared "Modality Result" schema in README.md."""

    label: str
    confidence: float
    probabilities: Dict[str, float]
    mock: bool = False

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in self.probabilities.items()},
            "mock": self.mock,
        }


class TextEmotionModel:
    """
    Thin wrapper around a HuggingFace text-classification pipeline.

    Usage:
        model = TextEmotionModel()
        result = model.predict("I can't stop smiling today!")
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: int = -1):
        self.model_name = model_name
        self.device = device
        self._pipeline = None
        self._load_attempted = False

    # ------------------------------------------------------------------
    # Lazy loading — avoids importing torch/transformers (and downloading
    # weights) until the first real prediction is requested. This keeps
    # `flask run` fast and lets the app boot even with no internet access.
    # ------------------------------------------------------------------
    def _ensure_loaded(self) -> bool:
        if self._pipeline is not None:
            return True
        if self._load_attempted:
            return False
        self._load_attempted = True

        try:
            from transformers import pipeline  # noqa: WPS433 (lazy import)

            self._pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,
                device=self.device,
            )
            logger.info("Loaded text emotion model '%s'", self.model_name)
            return True
        except Exception as exc:  # broad: any import/download/runtime failure
            logger.warning(
                "Falling back to MOCK text emotion model (%s could not be "
                "loaded: %s). Real inference will resume once the model "
                "is reachable.",
                self.model_name,
                exc,
            )
            return False

    def predict(self, text: str) -> ModalityResult:
        text = (text or "").strip()
        if not text:
            return ModalityResult(
                label="neutral",
                confidence=1.0,
                probabilities={lbl: (1.0 if lbl == "neutral" else 0.0) for lbl in EMOTION_LABELS},
                mock=True,
            )

        if self._ensure_loaded():
            try:
                return self._predict_real(text)
            except Exception as exc:  # inference-time failure -> mock
                logger.warning("Text model inference failed, using mock: %s", exc)

        return self._predict_mock(text)

    # ------------------------------------------------------------------
    def _predict_real(self, text: str) -> ModalityResult:
        raw = self._pipeline(text)[0]  # list[{"label": str, "score": float}]
        probs = {lbl: 0.0 for lbl in EMOTION_LABELS}
        for entry in raw:
            mapped = _HF_LABEL_MAP.get(entry["label"].lower())
            if mapped:
                probs[mapped] += float(entry["score"])

        total = sum(probs.values()) or 1.0
        probs = {k: v / total for k, v in probs.items()}
        top_label = max(probs, key=probs.get)
        return ModalityResult(label=top_label, confidence=probs[top_label], probabilities=probs, mock=False)

    def _predict_mock(self, text: str) -> ModalityResult:
        """
        Deterministic pseudo-random distribution seeded on the text hash, so
        demos are stable across reloads (same input -> same output) without
        requiring a real model. NOT used for any clinical inference.
        """
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng_weights = _deterministic_weights(seed, len(EMOTION_LABELS))
        probs = dict(zip(EMOTION_LABELS, rng_weights))
        top_label = max(probs, key=probs.get)
        return ModalityResult(label=top_label, confidence=probs[top_label], probabilities=probs, mock=True)


def _deterministic_weights(seed: int, n: int) -> list:
    import random

    rnd = random.Random(seed)
    raw = [rnd.random() ** 2 for _ in range(n)]  # skew toward one dominant class
    total = sum(raw)
    return [r / total for r in raw]


# Module-level singleton so the Flask app / Celery worker only loads the
# model once per process.
_default_model: Optional[TextEmotionModel] = None


def get_model() -> TextEmotionModel:
    global _default_model
    if _default_model is None:
        _default_model = TextEmotionModel()
    return _default_model
