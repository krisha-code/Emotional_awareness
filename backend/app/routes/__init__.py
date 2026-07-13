"""
app/routes/__init__.py — Routes package.

Imports and exposes all Flask Blueprint objects so they can be conveniently
imported from a single location by the application factory.
"""

from app.routes.auth import auth_bp
from app.routes.predict import predict_bp
from app.routes.fusion import fusion_bp
from app.routes.history import history_bp
from app.routes.export import export_bp

__all__ = [
    "auth_bp",
    "predict_bp",
    "fusion_bp",
    "history_bp",
    "export_bp",
]
