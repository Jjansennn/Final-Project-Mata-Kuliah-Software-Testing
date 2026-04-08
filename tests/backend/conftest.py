"""Shared fixtures for backend tests."""
import json
import os
import pytest

import app.models as models


def create_app():
    """Create a minimal Flask app for testing (includes both blueprints)."""
    from flask import Flask, jsonify
    from werkzeug.exceptions import HTTPException
    from app.routes import tasks_bp
    from app.auth_routes import auth_bp

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.register_blueprint(tasks_bp)
    flask_app.register_blueprint(auth_bp)

    @flask_app.errorhandler(Exception)
    def handle_error(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500

    return flask_app


@pytest.fixture
def client(tmp_path):
    """Flask test client backed by a fresh temporary SQLite database."""
    db_path = str(tmp_path / "test.db")
    original_db = models.DATABASE
    models.DATABASE = db_path

    flask_app = create_app()
    flask_app.config["TEST_DB_PATH"] = db_path  # RC1 fix: expose db_path for Hypothesis tests
    models.init_db()

    with flask_app.test_client() as test_client:
        yield test_client

    models.DATABASE = original_db


def register_and_login(client, email="test@example.com", password="password123"):
    """Helper: register a user and return their JWT token."""
    client.post(
        "/auth/register",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )
    resp = client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )
    return resp.get_json()["token"]


def auth_headers(token):
    """Return Authorization header dict for a given token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def real_app_client(tmp_path):
    """Flask test client using the real app from app/__init__.py (includes global error handler)."""
    import app as app_module

    db_path = str(tmp_path / "real_test.db")
    original_db = models.DATABASE
    models.DATABASE = db_path
    models.init_db()

    if '/_test_error' not in [r.rule for r in app_module.app.url_map.iter_rules()]:
        @app_module.app.route("/_test_error")
        def _trigger_error():
            raise RuntimeError("global handler test")

    app_module.app.config["TESTING"] = False
    with app_module.app.test_client() as test_client:
        yield test_client
    app_module.app.config["TESTING"] = True

    models.DATABASE = original_db
