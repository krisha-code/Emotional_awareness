"""
app/models/emotion_session.py — EmotionSession SQLAlchemy model.

Records one complete multimodal emotion analysis event for a user,
capturing per-modality predictions, the fusion result, severity grading,
conflict detection metrics, and XAI explanation data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db

# Valid severity tier literals
SEVERITY_TIERS = ("low", "moderate", "high", "critical")


class EmotionSession(db.Model):
    """
    Represents a single multimodal emotion analysis session.

    One session captures the outputs from one or more inference modalities
    (face, text, speech, physiological), the weighted fusion result,
    conflict detection score, severity tier, and XAI data.
    """

    __tablename__ = "emotion_sessions"

    # ------------------------------------------------------------------ #
    # Primary key                                                          #
    # ------------------------------------------------------------------ #
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # Ownership                                                            #
    # ------------------------------------------------------------------ #
    user_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Timestamp                                                            #
    # ------------------------------------------------------------------ #
    created_at = db.Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Face modality                                                        #
    # ------------------------------------------------------------------ #
    face_label = db.Column(String(32), nullable=True)
    face_confidence = db.Column(Float, nullable=True)
    # {label: probability_float, ...}
    face_probabilities = db.Column(JSON, nullable=True)

    # ------------------------------------------------------------------ #
    # Text modality                                                        #
    # ------------------------------------------------------------------ #
    text_label = db.Column(String(32), nullable=True)
    text_confidence = db.Column(Float, nullable=True)
    # {label: probability_float, ...}
    text_probabilities = db.Column(JSON, nullable=True)
    # User's raw text input — stored encrypted at the application layer
    text_input = db.Column(String(4096), nullable=True)

    # ------------------------------------------------------------------ #
    # Speech modality                                                      #
    # ------------------------------------------------------------------ #
    speech_label = db.Column(String(32), nullable=True)
    speech_confidence = db.Column(Float, nullable=True)

    # ------------------------------------------------------------------ #
    # Physiological modality (optional wearable data)                     #
    # ------------------------------------------------------------------ #
    # {heart_rate, hrv, eda, skin_temp, arousal_level, stress_indicator}
    physiological_data = db.Column(JSON, nullable=True)

    # ------------------------------------------------------------------ #
    # Fusion result                                                        #
    # ------------------------------------------------------------------ #
    fused_label = db.Column(String(32), nullable=True)
    fused_confidence = db.Column(Float, nullable=True)

    # ------------------------------------------------------------------ #
    # Conflict detection                                                   #
    # ------------------------------------------------------------------ #
    conflict_detected = db.Column(Boolean, default=False, nullable=False)
    conflict_score = db.Column(Float, default=0.0, nullable=False)

    # ------------------------------------------------------------------ #
    # Severity grading                                                     #
    # ------------------------------------------------------------------ #
    severity_tier = db.Column(
        String(16),
        nullable=True,
        comment="One of: low, moderate, high, critical",
    )
    severity_action = db.Column(String(512), nullable=True)

    # ------------------------------------------------------------------ #
    # XAI / Explainability data                                           #
    # ------------------------------------------------------------------ #
    # {
    #   gradcam: {region, intensity, description},
    #   token_attributions: [{token, score}],
    #   speech_explanation: {dominant_frequency_band, energy_profile},
    #   reasoning: "human-readable string",
    # }
    xai_data = db.Column(JSON, nullable=True)

    # ------------------------------------------------------------------ #
    # Free-form session notes                                              #
    # ------------------------------------------------------------------ #
    session_notes = db.Column(Text, nullable=True)

    # ------------------------------------------------------------------ #
    # Relationships                                                        #
    # ------------------------------------------------------------------ #
    user = db.relationship("User", back_populates="emotion_sessions")
    mood_journal_entries = db.relationship(
        "MoodJournalEntry",
        back_populates="emotion_session",
        lazy="dynamic",
    )

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #
    def to_dict(self, include_xai: bool = True) -> dict[str, Any]:
        """
        Serialise the session to a dictionary suitable for JSON responses.

        Args:
            include_xai: Whether to embed full XAI data. Set to False for
                         lightweight list views.

        Returns:
            Dictionary representation of the emotion session.
        """
        data: dict[str, Any] = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "face": {
                "label": self.face_label,
                "confidence": self.face_confidence,
                "probabilities": self.face_probabilities,
            },
            "text": {
                "label": self.text_label,
                "confidence": self.text_confidence,
                "probabilities": self.text_probabilities,
                # text_input is omitted from API responses for privacy
            },
            "speech": {
                "label": self.speech_label,
                "confidence": self.speech_confidence,
            },
            "physiological": self.physiological_data,
            "fusion": {
                "fused_label": self.fused_label,
                "fused_confidence": self.fused_confidence,
                "conflict_detected": self.conflict_detected,
                "conflict_score": self.conflict_score,
            },
            "severity": {
                "tier": self.severity_tier,
                "action": self.severity_action,
            },
            "session_notes": self.session_notes,
        }
        if include_xai:
            data["xai"] = self.xai_data
        return data

    def __repr__(self) -> str:
        return (
            f"<EmotionSession id={self.id} user_id={self.user_id} "
            f"fused={self.fused_label!r} severity={self.severity_tier!r}>"
        )
