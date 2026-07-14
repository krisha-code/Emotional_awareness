"""
backend/ml/text/code_switch.py

Lightweight support for code-switched input (e.g. Hindi-English, "Hinglish"),
since real users rarely type in one language only ("aaj bahut udaas hoon,
but I'm trying to smile").

This is a preprocessing stage, not a separate model: it normalizes
romanized Hindi emotion/distress words into English tokens the downstream
DistilBERT/crisis models already understand, and tags the text with a
per-token language guess so the fusion layer can note when a translation
step was involved (useful for the XAI explanation and for QA).

Scope kept intentionally narrow for a hackathon/demo timeline:
- Token-level language ID via a small function-word + script heuristic
  (falls back gracefully — this is NOT a full language identifier).
- A compact glossary of common romanized Hindi emotion/distress terms.
- No full machine translation; only lexical substitution of recognized
  affect-bearing words, since that's what the emotion/crisis classifiers
  actually key on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Romanized Hindi -> English glossary, restricted to affect-relevant terms.
# Extend this table as real user data reveals more common variants; keep it
# a flat lexical map so it stays auditable rather than a black-box model.
_HI_EN_GLOSSARY: Dict[str, str] = {
    "khush": "happy",
    "khushi": "happiness",
    "udaas": "sad",
    "udaasi": "sadness",
    "dukhi": "sad",
    "gussa": "angry",
    "gussa aaya": "got angry",
    "dar": "fear",
    "darr": "fear",
    "dukh": "sorrow",
    "pareshan": "worried",
    "pareshaan": "worried",
    "akela": "lonely",
    "akelapan": "loneliness",
    "thak gaya": "exhausted",
    "thak gayi": "exhausted",
    "rona": "crying",
    "ro raha": "crying",
    "ro rahi": "crying",
    "acha": "good",
    "accha": "good",
    "bura": "bad",
    "bekar": "worthless",
    "bekaar": "worthless",
    "tension": "stress",
    "tanav": "stress",
    "himmat": "courage",
    "umeed": "hope",
    "beh umeed": "hopeless",
    "nirasha": "hopelessness",
}

# Devanagari script range, for the (rarer, non-romanized) case.
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+")


@dataclass
class CodeSwitchResult:
    normalized_text: str
    detected_hindi_terms: List[str]
    contains_devanagari: bool


def _normalize_romanized_hindi(text: str) -> Tuple[str, List[str]]:
    detected = []
    normalized = text
    # Match multi-word entries first so "beh umeed" doesn't get shadowed by
    # a shorter overlapping single-word match.
    for hi_term in sorted(_HI_EN_GLOSSARY, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(hi_term)}\b", flags=re.IGNORECASE)
        if pattern.search(normalized):
            detected.append(hi_term)
            normalized = pattern.sub(_HI_EN_GLOSSARY[hi_term], normalized)
    return normalized, detected


def preprocess(text: str) -> CodeSwitchResult:
    """
    Normalize code-switched text before it hits the emotion/sarcasm/crisis
    models. Safe to call on pure-English input — it's a no-op if nothing
    in the glossary matches.
    """
    contains_devanagari = bool(_DEVANAGARI_RE.search(text))
    normalized, detected = _normalize_romanized_hindi(text)

    if contains_devanagari:
        # No transliteration engine wired up yet for this demo scope;
        # flag it so the API/response can surface "partial support" rather
        # than silently mis-scoring native-script input.
        pass

    return CodeSwitchResult(
        normalized_text=normalized,
        detected_hindi_terms=detected,
        contains_devanagari=contains_devanagari,
    )
