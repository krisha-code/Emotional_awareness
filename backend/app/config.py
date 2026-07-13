"""
app/config.py — Application configuration classes.

Provides a base Config and environment-specific subclasses (Development,
Production, Testing). All sensitive values are read from environment
variables to avoid hard-coding secrets.
"""

from __future__ import annotations

import os
from datetime import timedelta


class Config:
    """Base configuration shared across all environments."""

    # ------------------------------------------------------------------ #
    # Flask core                                                           #
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB

    # ------------------------------------------------------------------ #
    # SQLAlchemy                                                           #
    # ------------------------------------------------------------------ #
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "postgresql://emotion_user:emotion_pass@localhost:5432/emotion_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ------------------------------------------------------------------ #
    # Flask-JWT-Extended                                                   #
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-jwt-key-in-production")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)
    JWT_TOKEN_LOCATION: list[str] = ["headers"]
    JWT_HEADER_NAME: str = "Authorization"
    JWT_HEADER_TYPE: str = "Bearer"

    # ------------------------------------------------------------------ #
    # Redis / Celery                                                       #
    # ------------------------------------------------------------------ #
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ------------------------------------------------------------------ #
    # CORS                                                                 #
    # ------------------------------------------------------------------ #
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ------------------------------------------------------------------ #
    # ML model paths                                                       #
    # ------------------------------------------------------------------ #
    FACE_MODEL_PATH: str = os.getenv("FACE_MODEL_PATH", "ml/face/models/fer2013_mobilenetv2.h5")
    TEXT_MODEL_PATH: str = os.getenv("TEXT_MODEL_PATH", "ml/text/models/distilbert_emotion")
    SPEECH_MODEL_PATH: str = os.getenv("SPEECH_MODEL_PATH", "ml/speech/models/speech_emotion_cnn_lstm.h5")

    # ------------------------------------------------------------------ #
    # Encryption                                                           #
    # ------------------------------------------------------------------ #
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "your-32-byte-encryption-key-here")

    # ------------------------------------------------------------------ #
    # Pagination defaults                                                  #
    # ------------------------------------------------------------------ #
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


class DevelopmentConfig(Config):
    """Development-specific configuration — verbose logging, no SSL."""

    DEBUG: bool = True
    TESTING: bool = False
    SQLALCHEMY_ECHO: bool = True  # Log all SQL queries
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=8)  # Longer for dev convenience


class ProductionConfig(Config):
    """Production configuration — strict security settings."""

    DEBUG: bool = False
    TESTING: bool = False
    # In production always force SSL on DB connections
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        "connect_args": {"sslmode": "require"},
    }
    # Shorter lived access tokens in production
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=7)
    # Strict CORS in production — override CORS_ORIGINS via env
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]


class TestingConfig(Config):
    """Testing configuration — uses in-memory SQLite to avoid needing Postgres."""

    DEBUG: bool = True
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    SQLALCHEMY_ECHO: bool = False
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=5)
    WTF_CSRF_ENABLED: bool = False
    BCRYPT_LOG_ROUNDS: int = 4  # Faster hashing in tests


# Convenience mapping used by the app factory.
config_map: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    # Alias so FLASK_ENV=dev also works
    "dev": DevelopmentConfig,
    "prod": ProductionConfig,
    "test": TestingConfig,
}
