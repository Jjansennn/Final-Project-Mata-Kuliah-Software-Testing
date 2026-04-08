"""Flask application factory and global configuration."""
import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

app = Flask(__name__)
CORS(app)

# Allow DATABASE path to be overridden via environment variable
app.config["DATABASE"] = os.environ.get("DATABASE", "database.db")

from app.routes import tasks_bp        # noqa: E402 (import after app creation)
from app.auth_routes import auth_bp    # noqa: E402
from app.models import init_db         # noqa: E402

app.register_blueprint(tasks_bp)
app.register_blueprint(auth_bp)


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    # Biarkan HTTPException (404, 405, dll) ditangani Flask secara normal
    if isinstance(e, HTTPException):
        return jsonify({"error": e.description}), e.code
    logging.getLogger(__name__).error("Unhandled exception: %s", e, exc_info=True)
    return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500


init_db()
