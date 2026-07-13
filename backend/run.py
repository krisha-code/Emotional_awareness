"""
run.py — Application entry point.

Loads environment variables from .env, creates the Flask app via the
factory function, and starts the development server when executed directly.
"""

import os
from dotenv import load_dotenv

# Load .env before importing app so that os.getenv calls inside config work.
load_dotenv()

from app import create_app  # noqa: E402 — must come after load_dotenv

flask_app = create_app(os.getenv("FLASK_ENV", "development"))

with flask_app.app_context():
    from app.extensions import db
    import app.models  # Ensure models are imported
    db.create_all()

if __name__ == "__main__":
    flask_app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=(os.getenv("FLASK_ENV") == "development"),
    )
