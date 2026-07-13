"""
app/routes/fusion.py — Multimodal Fusion Blueprint.

Accepts inputs from one or more modalities, runs all available inference
pipelines, applies the weighted fusion algorithm, grades severity, generates
XAI explanations, persists an EmotionSession, and returns a complete result.

Routes:
    POST /api/fusion/analyze              — full multimodal analysis
    GET  /api/fusion/session/<session_id> — retrieve a specific session
"""

from __future__ import annotations

import base64
import logging
import uuid
from typing import Any

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.emotion_session import EmotionSession
from app.models.user import User
from app.services.fusion_engine import FusionEngine
from app.services.severity_grader import SeverityGrader
from app.services.xai_explainer import XAIExplainer
from app.services.baseline import BaselineCalibrator

logger = logging.getLogger(__name__)

fusion_bp = Blueprint("fusion", __name__, url_prefix="/api/fusion")

# Module-level service singletons
_fusion_engine = FusionEngine()
_severity_grader = SeverityGrader()
_xai_explainer = XAIExplainer()
_baseline_calibrator = BaselineCalibrator()


def _error(message: str, status: int = 400) -> tuple[Any, int]:
    return jsonify({"error": message}), status


def _get_face_inferer():
    from ml.face.inference import FaceEmotionInferer
    if not hasattr(_get_face_inferer, "_instance"):
        _get_face_inferer._instance = FaceEmotionInferer()
    return _get_face_inferer._instance


def _get_text_inferer():
    from ml.text.inference import TextEmotionInferer
    if not hasattr(_get_text_inferer, "_instance"):
        _get_text_inferer._instance = TextEmotionInferer()
    return _get_text_inferer._instance


def _get_speech_inferer():
    from ml.speech.inference import SpeechEmotionInferer
    if not hasattr(_get_speech_inferer, "_instance"):
        _get_speech_inferer._instance = SpeechEmotionInferer()
    return _get_speech_inferer._instance


def _get_physio_inferer():
    from ml.physiological.mock_wearable import MockWearableInferer
    if not hasattr(_get_physio_inferer, "_instance"):
        _get_physio_inferer._instance = MockWearableInferer()
    return _get_physio_inferer._instance


# --------------------------------------------------------------------------- #
# POST /api/fusion/analyze                                                     #
# --------------------------------------------------------------------------- #

@fusion_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze():
    """
    Run multimodal emotion analysis on one or more input modalities.

    At least ONE modality input must be provided.

    Expected JSON body (all fields optional, but at least one required):
        {
          image_base64: str        — base64-encoded image for face analysis
          text: str                — plaintext for text emotion analysis
          audio_base64: str        — base64-encoded audio for speech analysis
          physiological: {         — wearable sensor readings
            heart_rate: float,
            hrv: float,
            eda: float,
            skin_temp: float
          }
        }

    Returns:
        201 with the complete EmotionSession result including fusion,
        severity grading, XAI explanation, and baseline deviation.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return _error("Request body must be JSON.", 400)

    image_b64: str | None = (data.get("image_base64") or "").strip() or None
    text_input: str | None = (data.get("text") or "").strip() or None
    audio_b64: str | None = (data.get("audio_base64") or "").strip() or None
    physio_raw: dict | None = data.get("physiological")

    # Require at least one modality
    if not any([image_b64, text_input, audio_b64, physio_raw]):
        return _error(
            "At least one modality input is required: "
            "image_base64, text, audio_base64, or physiological.",
            400,
        )

    # ------------------------------------------------------------------ #
    # Run per-modality inference                                           #
    # ------------------------------------------------------------------ #
    face_result: dict | None = None
    text_result: dict | None = None
    speech_result: dict | None = None
    physio_result: dict | None = None
    errors: list[str] = []

    if image_b64:
        try:
            face_result = _get_face_inferer().predict(image_b64)
        except Exception as exc:
            logger.warning("Face inference skipped due to error: %s", exc)
            errors.append(f"Face inference error: {exc}")

    if text_input:
        try:
            text_result = _get_text_inferer().predict(text_input)
        except Exception as exc:
            logger.warning("Text inference skipped due to error: %s", exc)
            errors.append(f"Text inference error: {exc}")

    if audio_b64:
        try:
            audio_bytes = base64.b64decode(audio_b64)
            speech_result = _get_speech_inferer().predict(audio_bytes)
        except Exception as exc:
            logger.warning("Speech inference skipped due to error: %s", exc)
            errors.append(f"Speech inference error: {exc}")

    if physio_raw:
        try:
            physio_result = _get_physio_inferer().analyze(
                heart_rate=float(physio_raw.get("heart_rate", 72)),
                hrv=float(physio_raw.get("hrv", 45)),
                eda=float(physio_raw.get("eda", 2.5)),
                skin_temp=float(physio_raw.get("skin_temp", 33.1)),
            )
        except Exception as exc:
            logger.warning("Physiological inference skipped: %s", exc)
            errors.append(f"Physiological inference error: {exc}")

    # Ensure at least one succeeded
    if all(r is None for r in [face_result, text_result, speech_result, physio_result]):
        return _error(
            "All inference pipelines failed. Details: " + "; ".join(errors),
            500,
        )

    # ------------------------------------------------------------------ #
    # Fusion                                                               #
    # ------------------------------------------------------------------ #
    fusion_result = _fusion_engine.fuse(
        face_result=face_result,
        text_result=text_result,
        speech_result=speech_result,
        physiological_result=physio_result,
    )

    # ------------------------------------------------------------------ #
    # Severity grading                                                     #
    # ------------------------------------------------------------------ #
    severity = _severity_grader.grade(fusion_result, text_result)

    # ------------------------------------------------------------------ #
    # XAI explanation                                                      #
    # ------------------------------------------------------------------ #
    face_xai = None
    text_xai = None
    speech_xai = None

    if face_result:
        face_xai = _xai_explainer.explain_face(
            image_array=None,  # actual array not available post-inference
            model=None,
            predicted_class=face_result.get("label", ""),
        )
        # Enrich with gradcam_hint from inferer
        if face_result.get("gradcam_hint"):
            face_xai["gradcam_hint"] = face_result["gradcam_hint"]

    if text_result:
        text_xai = _xai_explainer.explain_text(
            text=text_input or "",
            label=text_result.get("label", ""),
            token_scores=text_result.get("token_attributions", []),
        )

    if speech_result:
        speech_xai = _xai_explainer.explain_speech(
            mfcc_features=None,
            label=speech_result.get("label", ""),
        )
        if speech_result.get("features_summary"):
            speech_xai["features_summary"] = speech_result["features_summary"]

    xai_report = _xai_explainer.build_explanation(
        face_xai=face_xai,
        text_xai=text_xai,
        speech_xai=speech_xai,
        fusion_result=fusion_result,
    )

    # ------------------------------------------------------------------ #
    # Encrypt text_input before storing                                    #
    # ------------------------------------------------------------------ #
    encrypted_text_input: str | None = None
    if text_input:
        try:
            encrypted_text_input = base64.urlsafe_b64encode(text_input.encode()).decode()
        except Exception:
            encrypted_text_input = None

    # ------------------------------------------------------------------ #
    # Persist EmotionSession                                               #
    # ------------------------------------------------------------------ #
    session = EmotionSession(
        user_id=uuid.UUID(user_id),
        # Face
        face_label=face_result.get("label") if face_result else None,
        face_confidence=face_result.get("confidence") if face_result else None,
        face_probabilities=face_result.get("probabilities") if face_result else None,
        # Text
        text_label=text_result.get("label") if text_result else None,
        text_confidence=text_result.get("confidence") if text_result else None,
        text_probabilities=text_result.get("probabilities") if text_result else None,
        text_input=encrypted_text_input,
        # Speech
        speech_label=speech_result.get("label") if speech_result else None,
        speech_confidence=speech_result.get("confidence") if speech_result else None,
        # Physiological
        physiological_data=physio_result,
        # Fusion
        fused_label=fusion_result.get("fused_label"),
        fused_confidence=fusion_result.get("fused_confidence"),
        conflict_detected=fusion_result.get("conflict_detected", False),
        conflict_score=fusion_result.get("conflict_score", 0.0),
        # Severity
        severity_tier=severity.get("tier"),
        severity_action=severity.get("action"),
        # XAI
        xai_data=xai_report,
    )
    db.session.add(session)
    db.session.commit()

    # ------------------------------------------------------------------ #
    # Update baseline (non-blocking)                                      #
    # ------------------------------------------------------------------ #
    try:
        user: User | None = db.session.get(User, user_id)
        if user:
            session_result_for_baseline = {
                "face": face_result,
                "text": text_result,
                "speech": speech_result,
            }
            _baseline_calibrator.update_baseline(str(user.id), session_result_for_baseline)
            db.session.commit()
    except Exception as exc:
        logger.warning("Baseline update failed (non-fatal): %s", exc)

    # ------------------------------------------------------------------ #
    # Response                                                             #
    # ------------------------------------------------------------------ #
    response_data = {
        "session": session.to_dict(include_xai=True),
        "severity": {
            "tier": severity.get("tier"),
            "action": severity.get("action"),
            "resources": severity.get("resources", []),
        },
        "xai": xai_report,
        "modality_weights_used": fusion_result.get("modality_weights_used", {}),
        "inference_errors": errors if errors else None,
    }

    logger.info(
        "Fusion session %s created for user %s — fused=%s tier=%s",
        session.id,
        user_id,
        session.fused_label,
        session.severity_tier,
    )

    return jsonify(response_data), 201


# --------------------------------------------------------------------------- #
# GET /api/fusion/session/<session_id>                                         #
# --------------------------------------------------------------------------- #

@fusion_bp.route("/session/<session_id>", methods=["GET"])
@jwt_required()
def get_session(session_id: str):
    """
    Retrieve details of a specific emotion session owned by the current user.

    Args:
        session_id: UUID string of the EmotionSession.

    Returns:
        200 with the session dict including XAI data.
    """
    user_id = get_jwt_identity()

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return _error("Invalid session ID format.", 400)

    session: EmotionSession | None = EmotionSession.query.filter_by(
        id=session_uuid,
        user_id=uuid.UUID(user_id),
    ).first()

    if session is None:
        return _error("Session not found.", 404)

    return jsonify({"session": session.to_dict(include_xai=True)})
