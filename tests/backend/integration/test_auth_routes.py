"""Integration tests for /auth/register and /auth/login endpoints."""
import json
import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

import app.models as models


def create_app_with_auth():
    """Create a Flask test app that includes both tasks_bp and auth_bp."""
    from flask import Flask
    from app.routes import tasks_bp
    from app.auth_routes import auth_bp

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.register_blueprint(tasks_bp)
    flask_app.register_blueprint(auth_bp)
    return flask_app


@pytest.fixture
def client(tmp_path):
    """Flask test client with a fresh in-memory SQLite database."""
    db_path = str(tmp_path / "test_auth.db")
    original_db = models.DATABASE
    models.DATABASE = db_path

    flask_app = create_app_with_auth()
    models.init_db()

    with flask_app.test_client() as test_client:
        yield test_client

    models.DATABASE = original_db


def _register(client, email="user@example.com", password="password123"):
    return client.post(
        "/auth/register",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )


def _login(client, email="user@example.com", password="password123"):
    return client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_success_returns_201(self, client):
        assert _register(client).status_code == 201

    def test_register_success_returns_user_fields(self, client):
        data = _register(client).get_json()
        assert all(k in data for k in ("id", "email", "created_at"))

    def test_register_success_no_password_in_response(self, client):
        data = _register(client).get_json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_success_email_matches(self, client):
        data = _register(client, email="test@example.com").get_json()
        assert data["email"] == "test@example.com"

    def test_register_duplicate_email_returns_409(self, client):
        _register(client)
        assert _register(client).status_code == 409

    def test_register_duplicate_email_has_error(self, client):
        _register(client)
        data = _register(client).get_json()
        assert "error" in data

    def test_register_invalid_email_returns_400(self, client):
        assert _register(client, email="not-an-email").status_code == 400

    def test_register_email_missing_at_returns_400(self, client):
        assert _register(client, email="nodomain").status_code == 400

    def test_register_email_missing_domain_returns_400(self, client):
        assert _register(client, email="user@").status_code == 400

    def test_register_empty_email_returns_400(self, client):
        assert _register(client, email="").status_code == 400

    def test_register_short_password_returns_400(self, client):
        assert _register(client, password="short").status_code == 400

    def test_register_password_7_chars_returns_400(self, client):
        assert _register(client, password="1234567").status_code == 400

    def test_register_password_8_chars_returns_201(self, client):
        assert _register(client, password="12345678").status_code == 201

    def test_register_empty_password_returns_400(self, client):
        assert _register(client, password="").status_code == 400

    def test_register_invalid_json_returns_400(self, client):
        resp = client.post("/auth/register", data=b"not-json", content_type="application/json")
        assert resp.status_code == 400

    def test_register_missing_email_field_returns_400(self, client):
        resp = client.post(
            "/auth/register",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_register_missing_password_field_returns_400(self, client):
        resp = client.post(
            "/auth/register",
            data=json.dumps({"email": "user@example.com"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_register_empty_body_returns_400(self, client):
        resp = client.post(
            "/auth/register",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success_returns_200(self, client):
        _register(client)
        assert _login(client).status_code == 200

    def test_login_success_returns_token(self, client):
        _register(client)
        data = _login(client).get_json()
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0

    def test_login_unknown_email_returns_401(self, client):
        assert _login(client, email="unknown@example.com").status_code == 401

    def test_login_wrong_password_returns_401(self, client):
        _register(client)
        assert _login(client, password="wrongpassword").status_code == 401

    def test_login_wrong_password_has_error(self, client):
        _register(client)
        data = _login(client, password="wrongpassword").get_json()
        assert "error" in data

    def test_login_invalid_json_returns_400(self, client):
        resp = client.post("/auth/login", data=b"not-json", content_type="application/json")
        assert resp.status_code == 400

    def test_login_missing_email_returns_401(self, client):
        resp = client.post(
            "/auth/login",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_missing_password_returns_401(self, client):
        resp = client.post(
            "/auth/login",
            data=json.dumps({"email": "user@example.com"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_empty_body_returns_401(self, client):
        resp = client.post(
            "/auth/login",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------

valid_email_st = st.emails()
valid_password_st = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=8,
    max_size=64,
).filter(lambda p: 8 <= len(p.encode("utf-8")) <= 72)


class TestPropertyRegisterNoPassword:
    """Property 1: Registrasi menghasilkan user tanpa password."""

    @given(email=valid_email_st, password=valid_password_st)
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_1_register_response_has_no_password(self, client, email, password):
        # Feature: task-auth-deadline-calendar, Property 1: Registrasi menghasilkan user tanpa password
        resp = _register(client, email=email, password=password)
        # May be 201 (success) or 409 (duplicate from hypothesis reuse) — both are valid
        assert resp.status_code in (201, 409)
        if resp.status_code == 201:
            data = resp.get_json()
            assert "id" in data
            assert "email" in data
            assert "created_at" in data
            assert "password" not in data
            assert "password_hash" not in data


class TestPropertyDuplicateEmail409:
    """Property 2: Email duplikat ditolak dengan 409."""

    @given(
        email=valid_email_st,
        password1=valid_password_st,
        password2=valid_password_st,
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_2_duplicate_email_returns_409(self, client, email, password1, password2):
        # Feature: task-auth-deadline-calendar, Property 2: Email duplikat ditolak dengan 409
        first = _register(client, email=email, password=password1)
        if first.status_code != 201:
            # Email already used in a prior hypothesis example — skip
            return
        second = _register(client, email=email, password=password2)
        assert second.status_code == 409
        assert "error" in second.get_json()


# ---------------------------------------------------------------------------
# 500 error handlers
# ---------------------------------------------------------------------------

class TestAuthRoutes500:
    """Cover the generic Exception handlers in register and login routes."""

    def test_register_500_on_unexpected_error(self, client):
        from unittest.mock import patch
        with patch("app.auth_routes.register_user", side_effect=RuntimeError("boom")):
            resp = client.post(
                "/auth/register",
                data=json.dumps({"email": "x@example.com", "password": "password123"}),
                content_type="application/json",
            )
        assert resp.status_code == 500
        assert "error" in resp.get_json()

    def test_login_500_on_unexpected_error(self, client):
        from unittest.mock import patch
        _register(client)
        with patch("app.auth_routes.login_user", side_effect=Exception("unexpected")):
            resp = client.post(
                "/auth/login",
                data=json.dumps({"email": "user@example.com", "password": "password123"}),
                content_type="application/json",
            )
        assert resp.status_code == 500
        assert "error" in resp.get_json()

    def test_login_valueerror_returns_400(self, client):
        from unittest.mock import patch
        _register(client)
        with patch("app.auth_routes.login_user", side_effect=ValueError("bad input")):
            resp = client.post(
                "/auth/login",
                data=json.dumps({"email": "user@example.com", "password": "password123"}),
                content_type="application/json",
            )
        assert resp.status_code == 400
        assert "error" in resp.get_json()
