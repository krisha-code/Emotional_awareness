"""
app/__init__.py — Flask application factory.

Creates and configures the Flask application instance, registers all
blueprints, initialises extensions, and attaches global error handlers.
"""

from __future__ import annotations

import logging
from flask import Flask, jsonify

from app.config import config_map
from app.extensions import db, jwt, cors, bcrypt, migrate

logger = logging.getLogger(__name__)


def create_app(env: str = "development") -> Flask:
    """
    Application factory function.

    Args:
        env: Configuration environment name ('development', 'production',
             'testing'). Defaults to 'development'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # ------------------------------------------------------------------ #
    # Configuration                                                        #
    # ------------------------------------------------------------------ #
    cfg = config_map.get(env, config_map["development"])
    app.config.from_object(cfg)

    # ------------------------------------------------------------------ #
    # Extensions initialisation                                            #
    # ------------------------------------------------------------------ #
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["http://localhost:5173"])}},
        supports_credentials=True,
    )

    # ------------------------------------------------------------------ #
    # JWT token blocklist (simple in-memory set for scaffold)             #
    # ------------------------------------------------------------------ #
    token_blocklist: set[str] = set()
    app.config["TOKEN_BLOCKLIST"] = token_blocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header: dict, jwt_payload: dict) -> bool:
        jti = jwt_payload.get("jti", "")
        return jti in token_blocklist

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header: dict, jwt_payload: dict):  # type: ignore[return]
        return jsonify({"error": "Token has been revoked", "code": "token_revoked"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header: dict, _jwt_payload: dict):  # type: ignore[return]
        return jsonify({"error": "Token has expired", "code": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason: str):  # type: ignore[return]
        return jsonify({"error": f"Invalid token: {reason}", "code": "invalid_token"}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(reason: str):  # type: ignore[return]
        return jsonify({"error": f"Authorization required: {reason}", "code": "unauthorized"}), 401

    # ------------------------------------------------------------------ #
    # Blueprint registration                                               #
    # ------------------------------------------------------------------ #
    _register_blueprints(app)

    # ------------------------------------------------------------------ #
    # Error handlers                                                       #
    # ------------------------------------------------------------------ #
    _register_error_handlers(app)

    # ------------------------------------------------------------------ #
    # Logging                                                              #
    # ------------------------------------------------------------------ #
    logging.basicConfig(
        level=logging.DEBUG if env == "development" else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Flask app created in %s mode.", env)

    return app


# --------------------------------------------------------------------------- #
# Private helpers                                                              #
# --------------------------------------------------------------------------- #

def _register_blueprints(app: Flask) -> None:
    """Import and register all route blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.predict import predict_bp
    from app.routes.fusion import fusion_bp
    from app.routes.history import history_bp
    from app.routes.export import export_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(fusion_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(export_bp)

    logger.debug(
        "Registered blueprints: %s",
        [auth_bp.name, predict_bp.name, fusion_bp.name, history_bp.name, export_bp.name],
    )


def _register_error_handlers(app: Flask) -> None:
    """Attach JSON error responses for common HTTP status codes."""

    @app.errorhandler(400)
    def bad_request(exc):  # type: ignore[return]
        logger.warning("400 Bad Request: %s", exc)
        return jsonify({"error": "Bad request", "details": str(exc)}), 400

    @app.errorhandler(401)
    def unauthorized(exc):  # type: ignore[return]
        logger.warning("401 Unauthorized: %s", exc)
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(exc):  # type: ignore[return]
        logger.warning("403 Forbidden: %s", exc)
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(exc):  # type: ignore[return]
        logger.warning("404 Not Found: %s", exc)
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(422)
    def unprocessable(exc):  # type: ignore[return]
        logger.warning("422 Unprocessable Entity: %s", exc)
        return jsonify({"error": "Unprocessable entity", "details": str(exc)}), 422

    @app.errorhandler(500)
    def internal_server_error(exc):  # type: ignore[return]
        logger.exception("500 Internal Server Error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500
