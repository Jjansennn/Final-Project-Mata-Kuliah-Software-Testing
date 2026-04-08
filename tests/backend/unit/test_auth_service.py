"""Unit tests and property-based tests for app.auth_service."""
import pytest
import jwt

import app.models as models
from app.auth_service import (
    register_user,
    login_user,
    ConflictError,
    AuthError,
    JWT_SECRET_KEY,
)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Point models.DATABASE at a fresh SQLite file for each test."""
    db_path = str(tmp_path / "test.db")
    original = models.DATABASE
    models.DATABASE = db_path
    models.init_db()
    yield
    models.DATABASE = original


# ---------------------------------------------------------------------------
# Unit tests — register_user
# ---------------------------------------------------------------------------

def test_register_user_returns_id_email_created_at():
    result = register_user("alice@example.com", "password123")
    assert "id" in result
    assert result["email"] == "alice@example.com"
    assert "created_at" in result


def test_register_user_no_password_in_response():
    result = register_user("bob@example.com", "securepass")
    assert "password" not in result
    assert "password_hash" not in result


def test_register_user_stores_hashed_password():
    register_user("carol@example.com", "mypassword")
    user = models.fetch_user_by_email("carol@example.com")
    assert user is not None
    assert user["password_hash"] != "mypassword"


def test_register_user_duplicate_email_raises_conflict():
    register_user("dup@example.com", "password1")
    with pytest.raises(ConflictError):
        register_user("dup@example.com", "password2")


def test_register_user_invalid_email_raises_value_error():
    with pytest.raises(ValueError):
        register_user("not-an-email", "password123")


def test_register_user_short_password_raises_value_error():
    with pytest.raises(ValueError):
        register_user("user@example.com", "short")


def test_register_user_password_exactly_8_chars_succeeds():
    result = register_user("user@example.com", "exactly8")
    assert result["email"] == "user@example.com"


# ---------------------------------------------------------------------------
# Unit tests — login_user
# ---------------------------------------------------------------------------

def test_login_user_returns_jwt_string():
    register_user("login@example.com", "password123")
    token = login_user("login@example.com", "password123")
    assert isinstance(token, str)
    assert len(token) > 0


def test_login_user_wrong_password_raises_auth_error():
    register_user("user@example.com", "correctpass")
    with pytest.raises(AuthError):
        login_user("user@example.com", "wrongpass!")


def test_login_user_unknown_email_raises_auth_error():
    with pytest.raises(AuthError):
        login_user("nobody@example.com", "password123")


def test_login_user_jwt_contains_user_id_and_email():
    register_user("payload@example.com", "password123")
    token = login_user("payload@example.com", "password123")
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    assert "user_id" in payload
    assert payload["email"] == "payload@example.com"


def test_login_user_jwt_expiry_is_24_hours():
    register_user("expiry@example.com", "password123")
    token = login_user("expiry@example.com", "password123")
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    assert payload["exp"] - payload["iat"] == 86400


# ---------------------------------------------------------------------------
# Property-based tests — Hypothesis
# ---------------------------------------------------------------------------

import itertools
from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

# Strategy for valid passwords (≥8 ASCII alphanumeric chars)
_valid_password_st = st.text(
    min_size=8, max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
)

# Each property test uses its own counter so emails are unique within a single
# test run (all Hypothesis examples share the same DB instance per test function).
_counter_p5 = itertools.count()
_counter_p6 = itertools.count()
_counter_p7 = itertools.count()


# Feature: task-auth-deadline-calendar, Property 5: Password disimpan sebagai hash, bukan plaintext
@given(password=_valid_password_st)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_5_password_stored_as_hash_not_plaintext(fresh_db, password):
    """Validates: Requirements 1.5"""
    email = f"user{next(_counter_p5)}@example.com"
    register_user(email, password)
    user = models.fetch_user_by_email(email)
    assert user is not None
    assert user["password_hash"] != password


# Feature: task-auth-deadline-calendar, Property 6: Login sukses menghasilkan JWT dengan payload dan expiry yang benar
@given(password=_valid_password_st)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_6_login_returns_jwt_with_correct_payload_and_expiry(fresh_db, password):
    """Validates: Requirements 2.1, 2.4, 2.5"""
    email = f"user{next(_counter_p6)}@example.com"
    register_user(email, password)
    token = login_user(email, password)
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    assert "user_id" in payload
    assert payload["email"] == email
    assert payload["exp"] - payload["iat"] == 86400


# Feature: task-auth-deadline-calendar, Property 7: Kredensial salah selalu menghasilkan AuthError
@given(
    password=_valid_password_st,
    wrong_password=_valid_password_st,
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_7_wrong_credentials_always_raise_auth_error(fresh_db, password, wrong_password):
    """Validates: Requirements 2.2, 2.3"""
    idx = next(_counter_p7)
    email = f"user{idx}@example.com"

    # Case 1: unregistered email — should always raise AuthError
    with pytest.raises(AuthError):
        login_user(f"unregistered{idx}@example.com", password)

    # Case 2: registered user with wrong password (only when passwords differ)
    register_user(email, password)
    assume(wrong_password != password)
    with pytest.raises(AuthError):
        login_user(email, wrong_password)
