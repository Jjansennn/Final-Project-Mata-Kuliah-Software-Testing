"""Unit tests for app.models — uses SQLite in-memory DB via tmp_path fixture."""
import sqlite3
from datetime import datetime

import pytest

import app.models as models


NOW = "2024-01-15 10:00:00"


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
# User helpers
# ---------------------------------------------------------------------------

def _make_user(email="user@example.com", password_hash="hashed", created_at=NOW):
    return models.insert_user(email, password_hash, created_at)


# ---------------------------------------------------------------------------
# insert_user
# ---------------------------------------------------------------------------

def test_insert_user_returns_id():
    user_id = _make_user()
    assert isinstance(user_id, int)
    assert user_id > 0


def test_insert_user_stores_data():
    user_id = _make_user(email="alice@example.com", password_hash="abc123")
    user = models.fetch_user_by_id(user_id)
    assert user["email"] == "alice@example.com"
    assert user["password_hash"] == "abc123"
    assert user["created_at"] == NOW


# ---------------------------------------------------------------------------
# fetch_user_by_email
# ---------------------------------------------------------------------------

def test_fetch_user_by_email_returns_user():
    user_id = _make_user(email="bob@example.com")
    user = models.fetch_user_by_email("bob@example.com")
    assert user is not None
    assert user["id"] == user_id
    assert user["email"] == "bob@example.com"


def test_fetch_user_by_email_not_found_returns_none():
    result = models.fetch_user_by_email("nobody@example.com")
    assert result is None


# ---------------------------------------------------------------------------
# fetch_user_by_id
# ---------------------------------------------------------------------------

def test_fetch_user_by_id_returns_user():
    user_id = _make_user(email="carol@example.com")
    user = models.fetch_user_by_id(user_id)
    assert user is not None
    assert user["id"] == user_id
    assert user["email"] == "carol@example.com"


def test_fetch_user_by_id_not_found_returns_none():
    result = models.fetch_user_by_id(99999)
    assert result is None


# ---------------------------------------------------------------------------
# duplicate email
# ---------------------------------------------------------------------------

def test_insert_user_duplicate_email_raises():
    _make_user(email="dup@example.com")
    with pytest.raises(sqlite3.IntegrityError):
        _make_user(email="dup@example.com")


# ---------------------------------------------------------------------------
# fetch_all_tasks
# ---------------------------------------------------------------------------

def _make_task(user_id, title="Task", deadline=None):
    return models.insert_task(
        title=title,
        description="desc",
        status="pending",
        deadline=deadline,
        user_id=user_id,
        created_at=NOW,
        updated_at=NOW,
    )


def test_fetch_all_tasks_filters_by_user_id():
    user_a = _make_user(email="a@example.com")
    user_b = _make_user(email="b@example.com")
    _make_task(user_a, title="Task A1")
    _make_task(user_a, title="Task A2")
    _make_task(user_b, title="Task B1")

    tasks_a = models.fetch_all_tasks(user_a)
    assert len(tasks_a) == 2
    assert all(t["user_id"] == user_a for t in tasks_a)


def test_fetch_all_tasks_empty_for_other_user():
    user_a = _make_user(email="a@example.com")
    user_b = _make_user(email="b@example.com")
    _make_task(user_a, title="Task A1")

    tasks_b = models.fetch_all_tasks(user_b)
    assert tasks_b == []


# ---------------------------------------------------------------------------
# insert_task with/without deadline
# ---------------------------------------------------------------------------

def test_insert_task_with_deadline():
    user_id = _make_user()
    deadline = "2024-12-31 23:59:59"
    task_id = _make_task(user_id, title="Deadline Task", deadline=deadline)
    task = models.fetch_task_by_id(task_id)
    assert task is not None
    assert task["deadline"] == deadline


def test_insert_task_without_deadline():
    user_id = _make_user()
    task_id = _make_task(user_id, title="No Deadline Task", deadline=None)
    task = models.fetch_task_by_id(task_id)
    assert task is not None
    assert task["deadline"] is None


# ---------------------------------------------------------------------------
# fetch_all_tasks without user_id (else branch — returns all tasks)
# ---------------------------------------------------------------------------

def test_fetch_all_tasks_without_user_id_returns_all():
    user_a = _make_user(email="a2@example.com")
    user_b = _make_user(email="b2@example.com")
    _make_task(user_a, title="Task A")
    _make_task(user_b, title="Task B")

    all_tasks = models.fetch_all_tasks()
    assert len(all_tasks) == 2
