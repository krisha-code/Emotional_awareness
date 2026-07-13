"""
app/models/__init__.py — Models package.

Imports and re-exports all SQLAlchemy models so that Flask-Migrate can
discover them when generating migration scripts, and so that other modules
can import models from a single canonical location.
"""

from app.models.user import User
from app.models.emotion_session import EmotionSession
from app.models.mood_journal import MoodJournalEntry

__all__ = [
    "User",
    "EmotionSession",
    "MoodJournalEntry",
]
