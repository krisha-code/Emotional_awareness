"""
app/routes/predict.py — Individual modality prediction Blueprint.

Provides per-modality prediction endpoints so the frontend or clients can
test each inference pipeline independently. All routes are JWT-protected.

Routes:
    POST /api/predict/face         — face emotion from base64 image
    POST /api/predict/text         — text emotion from plain text
    POST /api/predict/speech       — speech emotion from uploaded audio file
    POST /api/predict/physiological — mock wearable sensor analysis
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

logger = logging.getLogger(__name__)

predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")


def _error(message: str, status: int = 400) -> tuple[Any, int]:
    return jsonify({"error": message}), status


# --------------------------------------------------------------------------- #
# Lazy inference loader helpers                                                #
# --------------------------------------------------------------------------- #

def _get_face_inferer():
    """Return singleton FaceEmotionInferer, initialised on first call."""
    from ml.face.inference import FaceEmotionInferer
    if not hasattr(_get_face_inferer, "_instance"):
        _get_face_inferer._instance = FaceEmotionInferer()
    return _get_face_inferer._instance


def _get_text_inferer():
    """Return singleton TextEmotionInferer, initialised on first call."""
    from ml.text.inference import TextEmotionInferer
    if not hasattr(_get_text_inferer, "_instance"):
        _get_text_inferer._instance = TextEmotionInferer()
    return _get_text_inferer._instance


def _get_speech_inferer():
    """Return singleton SpeechEmotionInferer, initialised on first call."""
    from ml.speech.inference import SpeechEmotionInferer
    if not hasattr(_get_speech_inferer, "_instance"):
        _get_speech_inferer._instance = SpeechEmotionInferer()
    return _get_speech_inferer._instance


def _get_physio_inferer():
    """Return singleton MockWearableInferer, initialised on first call."""
    from ml.physiological.mock_wearable import MockWearableInferer
    if not hasattr(_get_physio_inferer, "_instance"):
        _get_physio_inferer._instance = MockWearableInferer()
    return _get_physio_inferer._instance


# --------------------------------------------------------------------------- #
# POST /api/predict/face                                                       #
# --------------------------------------------------------------------------- #

@predict_bp.route("/face", methods=["POST"])
@jwt_required()
def predict_face():
    """
    Predict emotion from a base64-encoded image.

    Expected JSON body:
        {image_base64: str}  — base64-encoded JPEG/PNG image.

    Returns:
        200 with face inference result dict.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return _error("Request body must be JSON.", 400)

    image_b64: str = data.get("image_base64", "").strip()
    if not image_b64:
        return _error("'image_base64' is required.", 400)

    # Validate that the string is decodable base64
    try:
        raw = base64.b64decode(image_b64, validate=True)
        if len(raw) < 100:
            return _error("Provided image is too small or invalid.", 400)
    except Exception:
        return _error("'image_base64' is not valid base64-encoded data.", 400)

    try:
        inferer = _get_face_inferer()
        result = inferer.predict(image_b64)
        logger.debug("Face prediction for user %s: %s", user_id, result.get("label"))
        return jsonify({"result": result})
    except Exception as exc:
        logger.exception("Face inference error for user %s: %s", user_id, exc)
        return _error("Face inference failed. Please try again.", 500)


# --------------------------------------------------------------------------- #
# POST /api/predict/text                                                       #
# --------------------------------------------------------------------------- #

@predict_bp.route("/text", methods=["POST"])
@jwt_required()
def predict_text():
    """
    Predict emotion from a text string.

    Expected JSON body:
        {text: str}  — plaintext input from the user.

    Returns:
        200 with text inference result dict.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return _error("Request body must be JSON.", 400)

    text: str = (data.get("text") or "").strip()
    if not text:
        return _error("'text' is required and must not be empty.", 400)

    if len(text) > 5000:
        return _error("Text input exceeds maximum length of 5000 characters.", 400)

    try:
        inferer = _get_text_inferer()
        result = inferer.predict(text)
        logger.debug("Text prediction for user %s: %s", user_id, result.get("label"))
        return jsonify({"result": result})
    except Exception as exc:
        logger.exception("Text inference error for user %s: %s", user_id, exc)
        return _error("Text inference failed. Please try again.", 500)


# --------------------------------------------------------------------------- #
# POST /api/predict/speech                                                     #
# --------------------------------------------------------------------------- #

@predict_bp.route("/speech", methods=["POST"])
@jwt_required()
def predict_speech():
    """
    Predict emotion from an uploaded audio file.

    Accepts multipart/form-data with field name 'audio'.
    Supports WAV, MP3, OGG, FLAC file types.
    Max file size is governed by MAX_CONTENT_LENGTH.

    Returns:
        200 with speech inference result dict.
    """
    user_id = get_jwt_identity()

    if "audio" not in request.files:
        return _error("An audio file is required under the 'audio' field.", 400)

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return _error("No audio file selected.", 400)

    allowed_extensions = {"wav", "mp3", "ogg", "flac", "m4a"}
    filename: str = audio_file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in allowed_extensions:
        return _error(
            f"Unsupported audio format '{extension}'. "
            f"Allowed: {', '.join(sorted(allowed_extensions))}.",
            400,
        )

    try:
        audio_bytes: bytes = audio_file.read()
        if len(audio_bytes) < 1000:
            return _error("Audio file is too small or empty.", 400)

        inferer = _get_speech_inferer()
        result = inferer.predict(audio_bytes)
        logger.debug("Speech prediction for user %s: %s", user_id, result.get("label"))
        return jsonify({"result": result})
    except Exception as exc:
        logger.exception("Speech inference error for user %s: %s", user_id, exc)
        return _error("Speech inference failed. Please try again.", 500)


# --------------------------------------------------------------------------- #
# POST /api/predict/physiological                                              #
# --------------------------------------------------------------------------- #

@predict_bp.route("/physiological", methods=["POST"])
@jwt_required()
def predict_physiological():
    """
    Analyse physiological (wearable sensor) data for stress/arousal indicators.

    Expected JSON body:
        {
          heart_rate: float,   — BPM (e.g. 72.0)
          hrv: float,          — heart rate variability in ms (e.g. 45.0)
          eda: float,          — electrodermal activity in μS (e.g. 2.5)
          skin_temp: float     — skin temperature in °C (e.g. 33.1)
        }

    Returns:
        200 with physiological analysis result dict.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return _error("Request body must be JSON.", 400)

    required_fields = ["heart_rate", "hrv", "eda", "skin_temp"]
    missing = [f for f in required_fields if data.get(f) is None]
    if missing:
        return _error(f"Missing required fields: {', '.join(missing)}.", 400)

    try:
        heart_rate = float(data["heart_rate"])
        hrv = float(data["hrv"])
        eda = float(data["eda"])
        skin_temp = float(data["skin_temp"])
    except (TypeError, ValueError):
        return _error("All physiological fields must be numeric.", 400)

    # Basic range sanity checks
    if not (30 <= heart_rate <= 220):
        return _error("heart_rate must be between 30 and 220 BPM.", 400)
    if not (0 <= hrv <= 300):
        return _error("hrv must be between 0 and 300 ms.", 400)
    if not (0 <= eda <= 100):
        return _error("eda must be between 0 and 100 μS.", 400)
    if not (25 <= skin_temp <= 42):
        return _error("skin_temp must be between 25 and 42 °C.", 400)

    try:
        inferer = _get_physio_inferer()
        result = inferer.analyze(heart_rate, hrv, eda, skin_temp)
        logger.debug("Physiological analysis for user %s: %s", user_id, result.get("label"))
        return jsonify({"result": result})
    except Exception as exc:
        logger.exception("Physiological inference error for user %s: %s", user_id, exc)
        return _error("Physiological analysis failed. Please try again.", 500)
