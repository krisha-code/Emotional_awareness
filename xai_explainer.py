"""
backend/app/services/xai_explainer.py

Builds the `xai` block of the fusion response (see README schema):

    {
      "face": {"region": ..., "intensity": ..., "description": ...},
      "text": {"top_tokens": [...], "reasoning": ...},
      "speech": {"dominant_band": ..., "energy": ..., "description": ...},
      "human_readable": "..."
    }

Design: each modality contributes whatever native explanation signal it
has (Grad-CAM regions for face, token attributions for text, spectral/
energy summary for speech), and this module's job is only to normalize
those into the shared shape and compose the cross-modal narrative — it
does not re-derive explanations from raw probabilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _text_explanation(text_result: Dict[str, Any]) -> Dict[str, Any]:
    top_tokens = text_result.get("token_attributions", [])
    label = text_result.get("label", "neutral")

    if text_result.get("crisis_detected"):
        reasoning = (
            f"Language patterns matched the high-priority distress category "
            f"(risk level: {text_result.get('crisis_risk_level', 'unknown')})."
        )
    elif text_result.get("sarcasm_detected"):
        reasoning = (
            f"Surface wording leaned positive, but sarcasm/negation cues shifted "
            f"the reading toward '{label}'."
        )
    elif top_tokens:
        token_list = ", ".join(f"'{t['token']}'" for t in top_tokens[:3])
        reasoning = f"Word(s) {token_list} strongly indicate {label}."
    else:
        reasoning = f"No strong affect-bearing keywords found; classified as {label} by overall phrasing."

    return {"top_tokens": top_tokens, "reasoning": reasoning}


def _speech_explanation(speech_result: Dict[str, Any], speech_features: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    label = speech_result.get("label", "neutral")
    energy_level = "unavailable"
    dominant_band = "unavailable"

    if speech_features:
        energy_mean = speech_features.get("energy_mean", 0.0)
        pitch_std = speech_features.get("pitch_std", 0.0)
        energy_level = "high" if energy_mean > 0.05 else "subdued"
        dominant_band = "high_frequency" if pitch_std > 40 else "low_frequency"

    descriptions = {
        "anger": "Sharp, high-energy vocal bursts",
        "fear": "Elevated pitch variance with tense, uneven pacing",
        "joy": "Bright tone with upward pitch inflection",
        "sadness": "Low energy, slow tempo",
        "disgust": "Clipped, low-energy delivery",
        "surprise": "Sudden pitch spike",
        "neutral": "Even tone, stable pitch and energy",
    }

    return {
        "dominant_band": dominant_band,
        "energy": energy_level,
        "description": descriptions.get(label, "No dominant vocal pattern detected"),
    }


def _human_readable_summary(
    text_result: Optional[Dict[str, Any]],
    face_xai: Optional[Dict[str, Any]],
    speech_xai: Optional[Dict[str, Any]],
    fused_label: str,
    conflict_detected: bool,
    confidence_tier: str,
) -> str:
    parts: List[str] = []

    if text_result:
        top_tokens = text_result.get("token_attributions", [])
        if top_tokens:
            token, score = top_tokens[0]["token"], top_tokens[0]["score"]
            parts.append(
                f"Text signals {'significant distress' if text_result.get('crisis_detected') else text_result.get('label')} "
                f"(word '{token}' — score {score})"
            )
        else:
            parts.append(f"Text suggests {text_result.get('label', 'neutral')}")

    if face_xai:
        parts.append(f"face shows {fused_label} markers ({face_xai.get('description', 'no notable region')})")

    if speech_xai:
        parts.append(f"speech corroborates with {speech_xai.get('energy', 'unclear')} energy")

    if conflict_detected:
        parts.append("modalities show notable disagreement — treat the fused label with caution")

    narrative = "; ".join(parts) if parts else "Insufficient modality data for a detailed explanation."
    return f"{narrative}. Combined confidence: {confidence_tier.upper()}."


def build_xai(
    face_result: Optional[Dict[str, Any]] = None,
    text_result: Optional[Dict[str, Any]] = None,
    speech_result: Optional[Dict[str, Any]] = None,
    speech_features: Optional[Dict[str, Any]] = None,
    fused_label: str = "neutral",
    fused_confidence: float = 0.0,
    conflict_detected: bool = False,
) -> Dict[str, Any]:
    xai: Dict[str, Any] = {}

    if face_result:
        # Face's own Grad-CAM output is expected to already populate
        # region/intensity/description upstream (owned by the face model
        # module); this function just passes it through if present.
        xai["face"] = face_result.get("xai", {
            "region": "unknown",
            "intensity": face_result.get("confidence", 0.0),
            "description": "No region-level explanation available.",
        })

    if text_result:
        xai["text"] = _text_explanation(text_result)

    if speech_result:
        xai["speech"] = _speech_explanation(speech_result, speech_features)

    confidence_tier = "high" if fused_confidence >= 0.7 else "moderate" if fused_confidence >= 0.4 else "low"
    xai["human_readable"] = _human_readable_summary(
        text_result, xai.get("face"), xai.get("speech"), fused_label, conflict_detected, confidence_tier
    )

    return xai
