"""
app/models/user.py — User SQLAlchemy model.

Stores account credentials, privacy-consent flags, and per-user emotion
baseline data. Sensitive fields (email) are encrypted at the application
layer before being persisted.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db, bcrypt


class User(db.Model):
    """
    Represents a registered user of the Emotion-Aware System.

    Email is stored in encrypted form using the application-level
    encryption helper. The raw email is never persisted.
    """

    __tablename__ = "users"

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
    # Identity fields                                                      #
    # ------------------------------------------------------------------ #
    # Stored as encrypted ciphertext; max 512 chars covers long emails
    # after base64-encoded AES-256 encryption.
    email = db.Column(String(512), unique=True, nullable=False, index=True)
    username = db.Column(String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(256), nullable=False)

    # ------------------------------------------------------------------ #
    # Timestamps                                                           #
    # ------------------------------------------------------------------ #
    created_at = db.Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # Privacy consent flags (GDPR / ethical AI compliance)                #
    # ------------------------------------------------------------------ #
    consent_camera = db.Column(Boolean, default=False, nullable=False)
    consent_microphone = db.Column(Boolean, default=False, nullable=False)
    consent_wearable = db.Column(Boolean, default=False, nullable=False)
    consent_emergency = db.Column(Boolean, default=False, nullable=False)

    # ------------------------------------------------------------------ #
    # Emergency & safety                                                   #
    # ------------------------------------------------------------------ #
    emergency_contact_email = db.Column(String(512), nullable=True)

    # ------------------------------------------------------------------ #
    # Account state                                                        #
    # ------------------------------------------------------------------ #
    is_active = db.Column(Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------ #
    # Per-user emotion baseline (JSON blob)                                #
    # Schema: {                                                            #
    #   face:   {label_counts: {}, avg_confidence: float},                #
    #   text:   {label_counts: {}, avg_confidence: float},                #
    #   speech: {label_counts: {}, avg_confidence: float},                #
    #   sessions_count: int                                                #
    # }                                                                    #
    # ------------------------------------------------------------------ #
    baseline_data = db.Column(JSON, nullable=True)

    # ------------------------------------------------------------------ #
    # Relationships                                                        #
    # ------------------------------------------------------------------ #
    emotion_sessions = db.relationship(
        "EmotionSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    mood_journal_entries = db.relationship(
        "MoodJournalEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # ------------------------------------------------------------------ #
    # Password helpers                                                     #
    # ------------------------------------------------------------------ #
    def set_password(self, raw_password: str) -> None:
        """Hash and store the plaintext password using bcrypt."""
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        """Return True if *raw_password* matches the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #
    def to_dict(self, include_baseline: bool = False) -> dict[str, Any]:
        """
        Serialise the user to a plain dictionary suitable for JSON responses.

        The email field is returned in its *encrypted* form here; routes
        that need the plaintext should decrypt it themselves using the
        application encryption helper.

        Args:
            include_baseline: Whether to include baseline_data in the output.

        Returns:
            Dictionary representation of the user.
        """
        data: dict[str, Any] = {
            "id": str(self.id),
            "username": self.username,
            # email is stored encrypted; callers decrypt if needed
            "email_encrypted": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "consent": {
                "camera": self.consent_camera,
                "microphone": self.consent_microphone,
                "wearable": self.consent_wearable,
                "emergency": self.consent_emergency,
            },
            "has_emergency_contact": self.emergency_contact_email is not None,
        }
        if include_baseline:
            data["baseline_data"] = self.baseline_data
        return data

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
