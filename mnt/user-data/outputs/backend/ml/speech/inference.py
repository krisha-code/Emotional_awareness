"""
backend/ml/speech/inference.py

Entry point the Flask route (`/api/predict/speech`) and fusion engine call.

Loads the trained SpeechEmotionCNNLSTM checkpoint if present; otherwise
falls back to a deterministic mock distribution driven off the *actual*
extracted pitch/energy features when audio is available (so mock mode
still responds sensibly to loud/fast vs. quiet/slow speech), or a stable
hash-based mock if feature extraction itself fails.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

from .feature_extraction import extract_features
from .model import EMOTION_LABELS, NUM_CLASSES

logger = logging.getLogger(__name__)

DEFAULT_CHECKPOINT = os.environ.get(
    "SPEECH_MODEL_PATH", "ml/speech/models/speech_emotion_cnn_lstm.pt"
)


@dataclass
class ModalityResult:
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


class SpeechEmotionInference:
    def __init__(self, checkpoint_path: str = DEFAULT_CHECKPOINT):
        self.checkpoint_path = checkpoint_path
        self._model = None
        self._device = None
        self._load_attempted = False

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        if self._load_attempted:
            return False
        self._load_attempted = True

        if not os.path.exists(self.checkpoint_path):
            logger.warning(
                "Speech checkpoint not found at %s; using mock mode. "
                "Run ml/speech/train_speech.py to produce a real checkpoint.",
                self.checkpoint_path,
            )
            return False

        try:
            import torch

            from .model import SpeechEmotionCNNLSTM

            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = SpeechEmotionCNNLSTM()
            model.load_state_dict(torch.load(self.checkpoint_path, map_location=self._device))
            model.eval()
            model.to(self._device)
            self._model = model
            logger.info("Loaded speech emotion checkpoint from %s", self.checkpoint_path)
            return True
        except Exception as exc:
            logger.warning("Failed to load speech checkpoint (%s); using mock mode.", exc)
            return False

    def predict(self, audio_path: str) -> ModalityResult:
        features = extract_features(audio_path)

        if self._ensure_loaded() and features.valid:
            try:
                return self._predict_real(features)
            except Exception as exc:
                logger.warning("Speech model inference failed, using mock: %s", exc)

        return self._predict_mock(audio_path, features)

    def _predict_real(self, features) -> ModalityResult:
        import torch
        import torch.nn.functional as F

        mfcc_tensor = torch.tensor(features.mfcc, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        mfcc_tensor = mfcc_tensor.to(self._device)
        with torch.no_grad():
            logits = self._model(mfcc_tensor)
            probs_tensor = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        probs = {lbl: float(p) for lbl, p in zip(EMOTION_LABELS, probs_tensor)}
        top_label = max(probs, key=probs.get)
        return ModalityResult(label=top_label, confidence=probs[top_label], probabilities=probs, mock=False)

    def _predict_mock(self, audio_path: str, features) -> ModalityResult:
        """
        Feature-informed mock: if we at least extracted valid pitch/energy,
        use simple arousal heuristics (high energy + high pitch variance ->
        anger/fear leaning; low energy + low pitch -> sadness leaning) so
        demos react plausibly to real audio even with no trained checkpoint.
        Otherwise fall back to a hash-seeded distribution.
        """
        if features.valid and (features.energy_mean > 0 or features.pitch_mean > 0):
            weights = _arousal_heuristic_weights(features)
        else:
            seed = int(hashlib.sha256(audio_path.encode("utf-8")).hexdigest(), 16) % (2**32)
            weights = _deterministic_weights(seed, NUM_CLASSES)

        probs = dict(zip(EMOTION_LABELS, weights))
        top_label = max(probs, key=probs.get)
        return ModalityResult(label=top_label, confidence=probs[top_label], probabilities=probs, mock=True)


def _arousal_heuristic_weights(features) -> list:
    # Normalize crude proxies into [0, 1]-ish ranges; thresholds are rough
    # and meant only to make mock mode *react* to audio, not to be accurate.
    energy_score = min(features.energy_mean * 20, 1.0)
    pitch_var_score = min(features.pitch_std / 50.0, 1.0) if features.pitch_std else 0.0
    arousal = 0.6 * energy_score + 0.4 * pitch_var_score

    base = {
        "joy": 0.10, "sadness": 0.10, "anger": 0.10, "fear": 0.10,
        "disgust": 0.10, "surprise": 0.10, "neutral": 0.40,
    }
    if arousal > 0.6:
        base["anger"] += 0.35
        base["fear"] += 0.15
        base["neutral"] -= 0.30
    elif arousal < 0.25:
        base["sadness"] += 0.35
        base["neutral"] -= 0.15
    total = sum(base.values())
    return [base[lbl] / total for lbl in EMOTION_LABELS]


def _deterministic_weights(seed: int, n: int) -> list:
    import random

    rnd = random.Random(seed)
    raw = [rnd.random() ** 2 for _ in range(n)]
    total = sum(raw)
    return [r / total for r in raw]


_default_inference: Optional[SpeechEmotionInference] = None


def get_inference() -> SpeechEmotionInference:
    global _default_inference
    if _default_inference is None:
        _default_inference = SpeechEmotionInference()
    return _default_inference
