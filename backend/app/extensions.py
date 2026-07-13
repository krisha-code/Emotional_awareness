"""
app/extensions.py — Extension singletons.

All Flask extensions are instantiated here WITHOUT being bound to an app.
The app factory in app/__init__.py calls each extension's init_app() method
to bind them to the concrete application instance at runtime.

This pattern avoids circular imports and supports the application factory
pattern correctly.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# SQLAlchemy ORM instance — used for all database interactions.
db: SQLAlchemy = SQLAlchemy()

# Flask-Migrate — Alembic-based schema migration management.
migrate: Migrate = Migrate()

# Flask-JWT-Extended — JWT authentication and token management.
jwt: JWTManager = JWTManager()

# Flask-Bcrypt — secure password hashing using bcrypt.
bcrypt: Bcrypt = Bcrypt()

# Flask-CORS — Cross-Origin Resource Sharing middleware.
cors: CORS = CORS()
