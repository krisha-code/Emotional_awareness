"""
backend/ml/text/inference.py

Single entry point the Flask route (`/api/predict/text`) and the fusion
engine should call. Wires together:

    code_switch.preprocess()   -> normalize Hinglish input
    emotion_model.predict()    -> base 7-class distribution
    sarcasm_detector.adjust()  -> dampen/redirect probabilities if sarcastic
    crisis_detector.detect()   -> independent high-priority flag

Returns a dict matching the "Modality Result" schema in README.md, extended
with the `sarcasm_detected`, `crisis_detected`, and `token_attributions`
fields already documented there for the text modality.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from . import code_switch, crisis_detector, sarcasm_detector
from .emotion_model import get_model

logger = logging.getLogger(__name__)


def _token_attributions(text: str, top_label: str) -> List[Dict[str, Any]]:
    """
    Crude keyword-attribution fallback for the XAI layer when a real
    gradient/attention-based attribution isn't wired up. Highlights words
    that plausibly drove the prediction, ranked by a simple heuristic
    (affect-lexicon overlap), so `xai_explainer.py` always has *something*
    to show even in mock mode.
    """
    import re

    affect_words = {
        "sadness": {"sad", "sadness", "cry", "crying", "hopeless", "lonely", "loneliness", "down"},
        "joy": {"happy", "happiness", "great", "excited", "glad", "joy"},
        "anger": {"angry", "furious", "mad", "annoyed", "frustrated"},
        "fear": {"afraid", "scared", "anxious", "worried", "fear"},
        "disgust": {"disgusted", "gross", "sick"},
        "surprise": {"surprised", "shocked", "unexpected"},
        "neutral": set(),
    }
    words = re.findall(r"[a-zA-Z']+", text.lower())
    lexicon = affect_words.get(top_label, set())
    hits = [w for w in words if w in lexicon]
    return [{"token": w, "score": 0.85} for w in dict.fromkeys(hits)][:5]


def analyze_text(raw_text: str) -> Dict[str, Any]:
    """
    Full text-modality analysis. Returns a JSON-serializable dict ready to
    be embedded under `modalities.text` in the fusion response.
    """
    cs_result = code_switch.preprocess(raw_text or "")
    working_text = cs_result.normalized_text

    base_result = get_model().predict(working_text)
    adjusted_probs, sarcasm_signal = sarcasm_detector.adjust_for_sarcasm(
        base_result.probabilities, working_text
    )
    top_label = max(adjusted_probs, key=adjusted_probs.get)

    crisis_signal = crisis_detector.get_detector().detect(working_text)

    payload: Dict[str, Any] = {
        "label": top_label,
        "confidence": round(adjusted_probs[top_label], 4),
        "probabilities": {k: round(v, 4) for k, v in adjusted_probs.items()},
        "mock": base_result.mock,
        "sarcasm_detected": sarcasm_signal.sarcasm_detected,
        "sarcasm_score": round(sarcasm_signal.sarcasm_score, 4),
        "crisis_detected": crisis_signal.crisis_detected,
        "crisis_risk_level": crisis_signal.risk_level,
        "crisis_confidence": round(crisis_signal.confidence, 4),
        "token_attributions": _token_attributions(working_text, top_label),
    }

    if cs_result.detected_hindi_terms or cs_result.contains_devanagari:
        payload["code_switch"] = {
            "detected_hindi_terms": cs_result.detected_hindi_terms,
            "contains_devanagari": cs_result.contains_devanagari,
            "normalized_text": working_text if working_text != raw_text else None,
        }

    return payload
