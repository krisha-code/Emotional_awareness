"""
app/models/mood_journal.py — MoodJournalEntry SQLAlchemy model.

Represents a user's written mood journal entry. Content is stored encrypted
at the application layer. Each entry can optionally be linked to a specific
EmotionSession for contextual correlation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class MoodJournalEntry(db.Model):
    """
    A single mood journal entry authored by a user.

    The `content` field holds encrypted text. The `tags` field stores a
    JSON array of free-form string tags for search and filtering.
    """

    __tablename__ = "mood_journal_entries"

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
    # Timestamps                                                           #
    # ------------------------------------------------------------------ #
    created_at = db.Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = db.Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # Content                                                              #
    # ------------------------------------------------------------------ #
    # Stored as AES-256 encrypted ciphertext (base64 encoded).
    content = db.Column(Text, nullable=False)

    # Short mood label chosen by the user or inferred from the linked session.
    mood_tag = db.Column(String(64), nullable=True, index=True)

    # ------------------------------------------------------------------ #
    # Optional link to an analysis session                                 #
    # ------------------------------------------------------------------ #
    emotion_session_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("emotion_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Tags                                                                 #
    # JSON array of strings, e.g. ["work", "anxiety", "morning"]          #
    # ------------------------------------------------------------------ #
    tags = db.Column(JSON, nullable=True, default=list)

    # ------------------------------------------------------------------ #
    # Relationships                                                        #
    # ------------------------------------------------------------------ #
    user = db.relationship("User", back_populates="mood_journal_entries")
    emotion_session = db.relationship(
        "EmotionSession",
        back_populates="mood_journal_entries",
    )

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #
    def to_dict(self, decrypt_content: bool = False, decrypted_text: str | None = None) -> dict[str, Any]:
        """
        Serialise the journal entry to a dictionary suitable for JSON responses.

        Args:
            decrypt_content: Whether to include decrypted content in output.
            decrypted_text: Pre-decrypted text to embed (caller is responsible
                            for decryption to avoid coupling this model to the
                            encryption helper).

        Returns:
            Dictionary representation of the mood journal entry.
        """
        data: dict[str, Any] = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "mood_tag": self.mood_tag,
            "tags": self.tags or [],
            "emotion_session_id": (
                str(self.emotion_session_id) if self.emotion_session_id else None
            ),
        }
        if decrypt_content and decrypted_text is not None:
            data["content"] = decrypted_text
        else:
            # Return content as-is (encrypted) — routes should decrypt before
            # calling to_dict if they need the plaintext.
            data["content"] = self.content
        return data

    def __repr__(self) -> str:
        return (
            f"<MoodJournalEntry id={self.id} user_id={self.user_id} "
            f"mood_tag={self.mood_tag!r}>"
        )
