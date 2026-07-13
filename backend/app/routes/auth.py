"""
app/routes/auth.py — Authentication Blueprint.

Provides user registration, login, token refresh/revocation, profile
retrieval, consent management, and account deletion endpoints.
All passwords are hashed with bcrypt; JWTs are issued via Flask-JWT-Extended.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN_LENGTH = 8


def _validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def _validate_password(password: str) -> tuple[bool, str]:
    """Return (valid, error_message)."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    return True, ""


def _encrypt_email(email: str) -> str:
    """
    Encrypt the user's email using the application-level encryption key.

    For the scaffold, a simple reversible base64 placeholder is used.
    Replace with real Fernet/AES-256 encryption in production.
    """
    import base64
    return base64.urlsafe_b64encode(email.lower().encode()).decode()


def _decrypt_email(encrypted: str) -> str:
    """Reverse of _encrypt_email."""
    import base64
    return base64.urlsafe_b64decode(encrypted.encode()).decode()


def _error(message: str, status: int = 400) -> tuple[Any, int]:
    return jsonify({"error": message}), status


# --------------------------------------------------------------------------- #
# POST /api/auth/register                                                      #
# --------------------------------------------------------------------------- #

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user account.

    Expected JSON body:
        {email, username, password}

    Returns:
        201 with {user, access_token, refresh_token} on success.
    """
    data = request.get_json(silent=True)
    if not data:
        return _error("Request body must be JSON.", 400)

    email: str = (data.get("email") or "").strip().lower()
    username: str = (data.get("username") or "").strip()
    password: str = data.get("password") or ""

    # ---- Validation ----
    if not email or not username or not password:
        return _error("email, username, and password are required.", 400)

    if not _validate_email(email):
        return _error("Invalid email address.", 400)

    valid_pw, pw_error = _validate_password(password)
    if not valid_pw:
        return _error(pw_error, 400)

    if len(username) < 3 or len(username) > 64:
        return _error("Username must be between 3 and 64 characters.", 400)

    encrypted_email = _encrypt_email(email)

    # ---- Uniqueness checks ----
    if User.query.filter_by(email=encrypted_email).first():
        return _error("An account with this email already exists.", 409)

    if User.query.filter_by(username=username).first():
        return _error("Username is already taken.", 409)

    # ---- Create user ----
    user = User(email=encrypted_email, username=username)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    logger.info("New user registered: %s", user.username)

    return (
        jsonify(
            {
                "message": "Account created successfully.",
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        ),
        201,
    )


# --------------------------------------------------------------------------- #
# POST /api/auth/login                                                         #
# --------------------------------------------------------------------------- #

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and issue JWT tokens.

    Expected JSON body:
        {email, password}

    Returns:
        200 with {user, access_token, refresh_token} on success.
    """
    data = request.get_json(silent=True)
    if not data:
        return _error("Request body must be JSON.", 400)

    email: str = (data.get("email") or "").strip().lower()
    password: str = data.get("password") or ""

    if not email or not password:
        return _error("email and password are required.", 400)

    encrypted_email = _encrypt_email(email)
    user: User | None = User.query.filter_by(email=encrypted_email, is_active=True).first()

    if user is None or not user.check_password(password):
        # Generic message prevents user enumeration
        return _error("Invalid email or password.", 401)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    logger.info("User logged in: %s", user.username)

    return jsonify(
        {
            "message": "Login successful.",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )


# --------------------------------------------------------------------------- #
# POST /api/auth/refresh                                                       #
# --------------------------------------------------------------------------- #

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Issue a new access token using a valid refresh token.

    Requires:  Authorization: Bearer <refresh_token>

    Returns:
        200 with {access_token}
    """
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    logger.debug("Token refreshed for user id=%s", identity)
    return jsonify({"access_token": new_access_token})


# --------------------------------------------------------------------------- #
# POST /api/auth/logout                                                        #
# --------------------------------------------------------------------------- #

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Revoke the current access token by adding its JTI to the blocklist.

    Requires:  Authorization: Bearer <access_token>

    Returns:
        200 with {message}
    """
    jti: str = get_jwt()["jti"]
    blocklist: set[str] = current_app.config["TOKEN_BLOCKLIST"]
    blocklist.add(jti)
    logger.debug("Token revoked: jti=%s", jti)
    return jsonify({"message": "Logged out successfully."})


# --------------------------------------------------------------------------- #
# GET /api/auth/me                                                             #
# --------------------------------------------------------------------------- #

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Return the current authenticated user's profile.

    Requires:  Authorization: Bearer <access_token>

    Returns:
        200 with {user}
    """
    user_id = get_jwt_identity()
    user: User | None = db.session.get(User, user_id)

    if user is None or not user.is_active:
        return _error("User not found.", 404)

    # Decrypt email for the profile response
    try:
        plain_email = _decrypt_email(user.email)
    except Exception:
        plain_email = None

    profile = user.to_dict(include_baseline=True)
    profile["email"] = plain_email  # expose plaintext only to the owner

    return jsonify({"user": profile})


# --------------------------------------------------------------------------- #
# PUT /api/auth/consent                                                        #
# --------------------------------------------------------------------------- #

@auth_bp.route("/consent", methods=["PUT"])
@jwt_required()
def update_consent():
    """
    Update the authenticated user's data-collection consent flags.

    Expected JSON body (all optional, only provided keys are updated):
        {
          consent_camera: bool,
          consent_microphone: bool,
          consent_wearable: bool,
          consent_emergency: bool,
          emergency_contact_email: str | null
        }

    Returns:
        200 with updated consent object.
    """
    user_id = get_jwt_identity()
    user: User | None = db.session.get(User, user_id)

    if user is None or not user.is_active:
        return _error("User not found.", 404)

    data = request.get_json(silent=True) or {}

    bool_fields = [
        "consent_camera",
        "consent_microphone",
        "consent_wearable",
        "consent_emergency",
    ]
    for field in bool_fields:
        if field in data:
            value = data[field]
            if not isinstance(value, bool):
                return _error(f"'{field}' must be a boolean.", 400)
            setattr(user, field, value)

    if "emergency_contact_email" in data:
        ec_email: str | None = data["emergency_contact_email"]
        if ec_email is not None:
            ec_email = ec_email.strip().lower()
            if not _validate_email(ec_email):
                return _error("Invalid emergency contact email address.", 400)
            user.emergency_contact_email = _encrypt_email(ec_email)
        else:
            user.emergency_contact_email = None

    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Consent updated for user: %s", user.username)

    return jsonify(
        {
            "message": "Consent preferences updated.",
            "consent": {
                "camera": user.consent_camera,
                "microphone": user.consent_microphone,
                "wearable": user.consent_wearable,
                "emergency": user.consent_emergency,
                "has_emergency_contact": user.emergency_contact_email is not None,
            },
        }
    )


# --------------------------------------------------------------------------- #
# DELETE /api/auth/account                                                     #
# --------------------------------------------------------------------------- #

@auth_bp.route("/account", methods=["DELETE"])
@jwt_required()
def delete_account():
    """
    Soft-delete (deactivate) the authenticated user's account.

    The user record is marked inactive rather than physically deleted so
    that foreign-key references from EmotionSession / MoodJournal entries
    remain intact for audit purposes. A separate GDPR purge job can
    hard-delete after the retention window.

    Requires:  Authorization: Bearer <access_token>

    Returns:
        200 with {message}
    """
    user_id = get_jwt_identity()
    user: User | None = db.session.get(User, user_id)

    if user is None or not user.is_active:
        return _error("User not found.", 404)

    # Verify password before deletion for extra security
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not password or not user.check_password(password):
        return _error("Password confirmation is required to delete the account.", 403)

    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    # Revoke current token
    jti: str = get_jwt()["jti"]
    blocklist: set[str] = current_app.config["TOKEN_BLOCKLIST"]
    blocklist.add(jti)

    logger.info("Account deactivated for user: %s", user.username)

    return jsonify({"message": "Account has been deactivated. We're sorry to see you go."})
