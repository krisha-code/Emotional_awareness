"""
backend/ml/speech/feature_extraction.py

Audio feature extraction for speech emotion recognition, using librosa.

Primary features: MFCCs (matches README tech stack: "CNN-LSTM + MFCC").
Secondary features (used if available): pitch (F0) and short-time energy,
which meaningfully improve emotion separability (especially arousal:
anger/fear vs. sadness/neutral) beyond MFCCs alone.

All extraction is wrapped so a missing/corrupt audio file degrades to a
zero-vector rather than crashing the request — the caller (inference.py)
is responsible for falling back to mock mode when that happens.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
N_MFCC = 40
MAX_PAD_LEN = 174  # ~4s of audio at the hop length below; matches RAVDESS clip length
HOP_LENGTH = 512


@dataclass
class SpeechFeatures:
    mfcc: np.ndarray  # shape: (N_MFCC, MAX_PAD_LEN)
    pitch_mean: float
    pitch_std: float
    energy_mean: float
    energy_std: float
    valid: bool


def _pad_or_truncate(feat: np.ndarray, max_len: int) -> np.ndarray:
    if feat.shape[1] > max_len:
        return feat[:, :max_len]
    pad_width = max_len - feat.shape[1]
    return np.pad(feat, pad_width=((0, 0), (0, pad_width)), mode="constant")


def extract_features(file_path: str) -> SpeechFeatures:
    """
    Load an audio file and extract MFCC + pitch + energy features.
    Returns SpeechFeatures(valid=False) on any failure so the caller can
    cleanly fall back to mock inference instead of raising mid-request.
    """
    try:
        import librosa
    except ImportError:
        logger.warning("librosa not installed; returning invalid features (mock mode expected).")
        return _empty_features()

    try:
        y, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
        if y.size == 0:
            raise ValueError("empty audio signal")

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC, hop_length=HOP_LENGTH)
        mfcc = _pad_or_truncate(mfcc, MAX_PAD_LEN)

        # Pitch (F0) via the pYIN tracker; robust to silence/unvoiced frames.
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr
        )
        voiced_f0 = f0[voiced_flag] if voiced_flag is not None else np.array([])
        pitch_mean = float(np.nanmean(voiced_f0)) if voiced_f0.size else 0.0
        pitch_std = float(np.nanstd(voiced_f0)) if voiced_f0.size else 0.0

        # Short-time energy (RMS).
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        energy_mean = float(np.mean(rms))
        energy_std = float(np.std(rms))

        return SpeechFeatures(
            mfcc=mfcc,
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            energy_mean=energy_mean,
            energy_std=energy_std,
            valid=True,
        )
    except Exception as exc:
        logger.warning("Feature extraction failed for %s: %s", file_path, exc)
        return _empty_features()


def _empty_features() -> SpeechFeatures:
    return SpeechFeatures(
        mfcc=np.zeros((N_MFCC, MAX_PAD_LEN), dtype=np.float32),
        pitch_mean=0.0,
        pitch_std=0.0,
        energy_mean=0.0,
        energy_std=0.0,
        valid=False,
    )
