"""Integration tests for Flask API routes (HTTP → SQLite end-to-end)."""
import json
import pytest
from unittest.mock import patch
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

from conftest import register_and_login, auth_headers

VALID_DEADLINE = "2099-12-31T23:59:59"
INVALID_DEADLINES = ["not-a-date", "2024-13-01", "31-12-2024", "yesterday", ""]


def _create_task(client, token, title="Test Task", description="A description", deadline=None):
    payload = {"title": title, "description": description}
    if deadline is not None:
        payload["deadline"] = deadline
    return client.post(
        "/tasks",
        data=json.dumps(payload),
        content_type="application/json",
        headers=auth_headers(token),
    )


# ---------------------------------------------------------------------------
# POST /tasks
# ---------------------------------------------------------------------------

class TestPostTasks:
    def test_post_tasks_valid_returns_201(self, client):
        token = register_and_login(client)
        assert _create_task(client, token).status_code == 201

    def test_post_tasks_valid_has_required_fields(self, client):
        token = register_and_login(client)
        data = _create_task(client, token).get_json()
        assert all(k in data for k in ("id", "status", "created_at", "updated_at", "deadline", "is_overdue"))

    def test_post_tasks_status_is_pending(self, client):
        token = register_and_login(client)
        assert _create_task(client, token).get_json()["status"] == "pending"

    def test_post_tasks_missing_title_returns_400(self, client):
        token = register_and_login(client)
        resp = client.post("/tasks", data=json.dumps({}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_post_tasks_empty_title_returns_400(self, client):
        token = register_and_login(client)
        resp = client.post("/tasks", data=json.dumps({"title": ""}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400

    def test_post_tasks_whitespace_title_returns_400(self, client):
        token = register_and_login(client)
        resp = client.post("/tasks", data=json.dumps({"title": "   "}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400

    def test_post_tasks_title_too_long_returns_400(self, client):
        token = register_and_login(client)
        resp = client.post("/tasks", data=json.dumps({"title": "x" * 201}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400

    def test_post_tasks_invalid_json_returns_400(self, client):
        token = register_and_login(client)
        resp = client.post("/tasks", data=b"not-json", content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400

    def test_post_tasks_without_description_sets_null(self, client):
        token = register_and_login(client)
        resp = client.post("/tasks", data=json.dumps({"title": "No desc"}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 201
        assert resp.get_json()["description"] is None

    def test_post_tasks_with_valid_deadline_returns_201(self, client):
        token = register_and_login(client)
        resp = _create_task(client, token, deadline=VALID_DEADLINE)
        assert resp.status_code == 201
        assert resp.get_json()["deadline"] is not None

    def test_post_tasks_with_invalid_deadline_returns_400(self, client):
        token = register_and_login(client)
        resp = _create_task(client, token, deadline="not-a-date")
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_post_tasks_without_deadline_sets_null(self, client):
        token = register_and_login(client)
        resp = _create_task(client, token)
        assert resp.status_code == 201
        assert resp.get_json()["deadline"] is None


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------

class TestGetTasks:
    def test_get_tasks_empty_db_returns_empty_list(self, client):
        token = register_and_login(client)
        resp = client.get("/tasks", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_get_tasks_returns_all_tasks(self, client):
        token = register_and_login(client)
        _create_task(client, token, title="Task 1")
        _create_task(client, token, title="Task 2")
        assert len(client.get("/tasks", headers=auth_headers(token)).get_json()) == 2

    def test_get_tasks_returns_json_array(self, client):
        token = register_and_login(client)
        assert isinstance(client.get("/tasks", headers=auth_headers(token)).get_json(), list)


# ---------------------------------------------------------------------------
# GET /tasks/<id>
# ---------------------------------------------------------------------------

class TestGetTaskById:
    def test_get_task_by_id_returns_200(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        assert client.get(f"/tasks/{task_id}", headers=auth_headers(token)).status_code == 200

    def test_get_task_by_id_returns_correct_task(self, client):
        token = register_and_login(client)
        created = _create_task(client, token, title="Specific Task").get_json()
        assert client.get(f"/tasks/{created['id']}", headers=auth_headers(token)).get_json()["title"] == "Specific Task"

    def test_get_task_not_found_returns_404(self, client):
        token = register_and_login(client)
        resp = client.get("/tasks/99999", headers=auth_headers(token))
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ---------------------------------------------------------------------------
# PUT /tasks/<id>
# ---------------------------------------------------------------------------

class TestPutTask:
    def test_put_task_returns_200(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"status": "in_progress"}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_put_task_updates_status(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"status": "done"}), content_type="application/json", headers=auth_headers(token))
        assert resp.get_json()["status"] == "done"

    def test_put_task_updates_updated_at(self, client):
        token = register_and_login(client)
        created = _create_task(client, token).get_json()
        resp = client.put(f"/tasks/{created['id']}", data=json.dumps({"title": "Updated"}), content_type="application/json", headers=auth_headers(token))
        assert resp.get_json()["updated_at"] >= created["updated_at"]

    def test_put_task_not_found_returns_404(self, client):
        token = register_and_login(client)
        resp = client.put("/tasks/99999", data=json.dumps({"title": "X"}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 404
        assert "error" in resp.get_json()

    def test_put_task_invalid_status_returns_400(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"status": "invalid"}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400

    def test_put_task_invalid_json_returns_400(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=b"bad-json", content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400

    def test_put_task_updates_deadline(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"deadline": VALID_DEADLINE}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.get_json()["deadline"] is not None

    def test_put_task_clears_deadline_with_null(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token, deadline=VALID_DEADLINE).get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"deadline": None}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.get_json()["deadline"] is None

    def test_put_task_invalid_deadline_returns_400(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"deadline": "not-a-date"}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /tasks/<id>
# ---------------------------------------------------------------------------

class TestDeleteTask:
    def test_delete_task_returns_200(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        assert client.delete(f"/tasks/{task_id}", headers=auth_headers(token)).status_code == 200

    def test_delete_task_returns_message(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        assert "message" in client.delete(f"/tasks/{task_id}", headers=auth_headers(token)).get_json()

    def test_delete_task_not_found_returns_404(self, client):
        token = register_and_login(client)
        resp = client.delete("/tasks/99999", headers=auth_headers(token))
        assert resp.status_code == 404
        assert "error" in resp.get_json()

    def test_delete_task_removes_from_db(self, client):
        token = register_and_login(client)
        task_id = _create_task(client, token).get_json()["id"]
        client.delete(f"/tasks/{task_id}", headers=auth_headers(token))
        assert client.get(f"/tasks/{task_id}", headers=auth_headers(token)).status_code == 404


# ---------------------------------------------------------------------------
# Auth protection: 401 without token
# ---------------------------------------------------------------------------

class TestAuthProtection:
    def test_get_tasks_without_token_returns_401(self, client):
        resp = client.get("/tasks")
        assert resp.status_code == 401

    def test_post_tasks_without_token_returns_401(self, client):
        resp = client.post("/tasks", data=json.dumps({"title": "T"}), content_type="application/json")
        assert resp.status_code == 401

    def test_get_task_by_id_without_token_returns_401(self, client):
        assert client.get("/tasks/1").status_code == 401

    def test_put_task_without_token_returns_401(self, client):
        resp = client.put("/tasks/1", data=json.dumps({"title": "T"}), content_type="application/json")
        assert resp.status_code == 401

    def test_delete_task_without_token_returns_401(self, client):
        assert client.delete("/tasks/1").status_code == 401

    def test_get_tasks_with_invalid_token_returns_401(self, client):
        resp = client.get("/tasks", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401

    def test_get_tasks_with_expired_token_returns_401(self, client):
        import jwt as pyjwt
        from datetime import datetime, timezone
        payload = {"user_id": 1, "email": "x@x.com", "iat": 1000, "exp": 1001}
        expired_token = pyjwt.encode(payload, "dev-secret-key", algorithm="HS256")
        resp = client.get("/tasks", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Data isolation: user A cannot see user B's tasks
# ---------------------------------------------------------------------------

class TestDataIsolation:
    def test_user_a_cannot_see_user_b_tasks(self, client):
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        _create_task(client, token_b, title="User B Task")
        tasks_a = client.get("/tasks", headers=auth_headers(token_a)).get_json()
        assert tasks_a == []

    def test_user_a_get_task_owned_by_b_returns_403(self, client):
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        task_id = _create_task(client, token_b, title="B's Task").get_json()["id"]
        resp = client.get(f"/tasks/{task_id}", headers=auth_headers(token_a))
        assert resp.status_code == 403

    def test_user_a_put_task_owned_by_b_returns_403(self, client):
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        task_id = _create_task(client, token_b, title="B's Task").get_json()["id"]
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"title": "Hacked"}), content_type="application/json", headers=auth_headers(token_a))
        assert resp.status_code == 403

    def test_user_a_delete_task_owned_by_b_returns_403(self, client):
        token_a = register_and_login(client, "a@example.com", "password123")
        token_b = register_and_login(client, "b@example.com", "password123")
        task_id = _create_task(client, token_b, title="B's Task").get_json()["id"]
        resp = client.delete(f"/tasks/{task_id}", headers=auth_headers(token_a))
        assert resp.status_code == 403

    def test_new_task_associated_with_token_user(self, client):
        token = register_and_login(client, "owner@example.com", "password123")
        task = _create_task(client, token, title="My Task").get_json()
        # Verify task is visible to its owner
        fetched = client.get(f"/tasks/{task['id']}", headers=auth_headers(token)).get_json()
        assert fetched["id"] == task["id"]


# ---------------------------------------------------------------------------
# 500 error handler coverage
# ---------------------------------------------------------------------------

class TestInternalServerError:
    def test_500_handler_returns_json_error(self, client):
        token = register_and_login(client)
        with patch("app.services.get_all_tasks", side_effect=RuntimeError("boom")):
            resp = client.get("/tasks", headers=auth_headers(token))
        assert resp.status_code == 500
        assert "error" in resp.get_json()
        assert "Traceback" not in resp.get_json()["error"]

    def test_500_create_task_returns_json_error(self, client):
        token = register_and_login(client)
        with patch("app.services.create_task", side_effect=RuntimeError("boom")):
            resp = client.post("/tasks", data=json.dumps({"title": "T"}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 500

    def test_500_get_task_by_id_returns_json_error(self, client):
        token = register_and_login(client)
        with patch("app.services.get_task_by_id", side_effect=RuntimeError("boom")):
            assert client.get("/tasks/1", headers=auth_headers(token)).status_code == 500

    def test_500_update_task_returns_json_error(self, client):
        token = register_and_login(client)
        with patch("app.services.update_task", side_effect=RuntimeError("boom")):
            resp = client.put("/tasks/1", data=json.dumps({"title": "T"}), content_type="application/json", headers=auth_headers(token))
        assert resp.status_code == 500

    def test_500_delete_task_returns_json_error(self, client):
        token = register_and_login(client)
        with patch("app.services.delete_task", side_effect=RuntimeError("boom")):
            assert client.delete("/tasks/1", headers=auth_headers(token)).status_code == 500


# ---------------------------------------------------------------------------
# Property-based tests (existing, updated for auth)
# ---------------------------------------------------------------------------

@given(st.integers(min_value=0, max_value=20))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_4_get_tasks_mengembalikan_semua_task(client, n):
    """Property 4: GET /tasks returns exactly N tasks after N tasks are inserted."""
    token = register_and_login(client)
    for task in client.get("/tasks", headers=auth_headers(token)).get_json():
        client.delete(f"/tasks/{task['id']}", headers=auth_headers(token))
    for i in range(n):
        _create_task(client, token, title=f"Task {i}")
    resp = client.get("/tasks", headers=auth_headers(token))
    assert resp.status_code == 200
    assert len(resp.get_json()) == n


@given(st.integers(min_value=2, max_value=10))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_5_urutan_task_descending_created_at(client, n):
    """Property 5: GET /tasks always returns tasks sorted by created_at descending."""
    import app.models as models
    from datetime import datetime, timedelta

    # RC1 fix: re-set models.DATABASE at the start of each Hypothesis example.
    # With suppress_health_check=[HealthCheck.function_scoped_fixture], Hypothesis
    # calls this function multiple times with the same fixture instance without
    # running teardown/setup between examples. We read the db_path stored in the
    # Flask app config by the fixture to ensure each example uses the correct database.
    models.DATABASE = client.application.config["TEST_DB_PATH"]

    token = register_and_login(client)
    for task in client.get("/tasks", headers=auth_headers(token)).get_json():
        client.delete(f"/tasks/{task['id']}", headers=auth_headers(token))

    base_time = datetime(2024, 1, 1, 0, 0, 0)
    # Fetch user_id from token
    import jwt as pyjwt
    import os
    secret = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
    payload = pyjwt.decode(token, secret, algorithms=["HS256"])
    user_id = payload["user_id"]

    for i in range(n):
        ts = (base_time + timedelta(seconds=i)).isoformat()
        models.insert_task(title=f"Task {i}", description=None, status="pending", deadline=None, user_id=user_id, created_at=ts, updated_at=ts)

    tasks = client.get("/tasks", headers=auth_headers(token)).get_json()
    created_ats = [t["created_at"] for t in tasks]
    assert created_ats == sorted(created_ats, reverse=True)


@given(st.text(min_size=1, max_size=200).filter(lambda s: s.strip()))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_6_get_task_by_id_round_trip(client, title):
    """Property 6: GET /tasks/{id} returns identical data to the POST /tasks response."""
    token = register_and_login(client)
    post_data = client.post("/tasks", data=json.dumps({"title": title}), content_type="application/json", headers=auth_headers(token)).get_json()
    assert client.get(f"/tasks/{post_data['id']}", headers=auth_headers(token)).get_json() == post_data


@given(st.text(min_size=1, max_size=200).filter(lambda s: s.strip()))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_7_update_task_memperbarui_updated_at(client, title):
    """Property 7: PUT /tasks/{id} always results in updated_at >= the previous updated_at."""
    token = register_and_login(client)
    task = client.post("/tasks", data=json.dumps({"title": title}), content_type="application/json", headers=auth_headers(token)).get_json()
    updated = client.put(f"/tasks/{task['id']}", data=json.dumps({"status": "in_progress"}), content_type="application/json", headers=auth_headers(token)).get_json()
    assert updated["updated_at"] >= task["updated_at"]


@given(st.text(min_size=1, max_size=200).filter(lambda s: s.strip()))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_12_delete_task_round_trip(client, title):
    """Property 12: DELETE /tasks/{id} returns 200; subsequent GET returns 404."""
    token = register_and_login(client)
    task_id = client.post("/tasks", data=json.dumps({"title": title}), content_type="application/json", headers=auth_headers(token)).get_json()["id"]
    assert client.delete(f"/tasks/{task_id}", headers=auth_headers(token)).status_code == 200
    assert client.get(f"/tasks/{task_id}", headers=auth_headers(token)).status_code == 404


# ---------------------------------------------------------------------------
# Property 8: Request tanpa atau dengan token tidak valid selalu ditolak 401
# Feature: task-auth-deadline-calendar, Property 8
# ---------------------------------------------------------------------------

PROTECTED_ENDPOINTS = [
    ("GET", "/tasks", None, None),
    ("POST", "/tasks", json.dumps({"title": "T"}).encode(), "application/json"),
    ("GET", "/tasks/1", None, None),
    ("PUT", "/tasks/1", json.dumps({"title": "T"}).encode(), "application/json"),
    ("DELETE", "/tasks/1", None, None),
]

INVALID_TOKENS = [
    "",
    "not-a-token",
    "Bearer",
    "Bearer invalid.token.value",
]


def _do_request(client, method, path, body, content_type, headers=None):
    kwargs = {}
    if body is not None:
        kwargs["data"] = body
    if content_type is not None:
        kwargs["content_type"] = content_type
    if headers:
        kwargs["headers"] = headers
    if method == "GET":
        return client.get(path, **kwargs)
    if method == "POST":
        return client.post(path, **kwargs)
    if method == "PUT":
        return client.put(path, **kwargs)
    if method == "DELETE":
        return client.delete(path, **kwargs)
    raise ValueError(f"Unknown method: {method}")


@given(
    endpoint=st.sampled_from(PROTECTED_ENDPOINTS),
    bad_token=st.sampled_from(INVALID_TOKENS),
)
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_8_invalid_token_returns_401(client, endpoint, bad_token):
    """Property 8: Requests without or with invalid tokens always return 401."""
    method, path, body, content_type = endpoint
    # No token at all
    resp_no_token = _do_request(client, method, path, body, content_type)
    assert resp_no_token.status_code == 401

    # Invalid token
    resp_bad = _do_request(client, method, path, body, content_type, headers={"Authorization": bad_token})
    assert resp_bad.status_code == 401


# ---------------------------------------------------------------------------
# Property 9: Isolasi data antar user
# Feature: task-auth-deadline-calendar, Property 9
# ---------------------------------------------------------------------------

@given(n=st.integers(min_value=1, max_value=5))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_9_data_isolation_between_users(client, n):
    """Property 9: GET /tasks with user A's token never returns tasks created by user B."""
    token_a = register_and_login(client, "prop9a@example.com", "password123")
    token_b = register_and_login(client, "prop9b@example.com", "password123")

    b_ids = set()
    for i in range(n):
        task = _create_task(client, token_b, title=f"B Task {i}").get_json()
        b_ids.add(task["id"])

    tasks_a = client.get("/tasks", headers=auth_headers(token_a)).get_json()
    returned_ids = {t["id"] for t in tasks_a}
    assert returned_ids.isdisjoint(b_ids)


# ---------------------------------------------------------------------------
# Property 10: Akses task milik user lain menghasilkan 403
# Feature: task-auth-deadline-calendar, Property 10
# ---------------------------------------------------------------------------

@given(method=st.sampled_from(["GET", "PUT", "DELETE"]))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_10_cross_user_access_returns_403(client, method):
    """Property 10: Accessing another user's task always returns 403."""
    token_a = register_and_login(client, "prop10a@example.com", "password123")
    token_b = register_and_login(client, "prop10b@example.com", "password123")
    task_id = _create_task(client, token_b, title="B's Task").get_json()["id"]

    if method == "GET":
        resp = client.get(f"/tasks/{task_id}", headers=auth_headers(token_a))
    elif method == "PUT":
        resp = client.put(f"/tasks/{task_id}", data=json.dumps({"title": "X"}), content_type="application/json", headers=auth_headers(token_a))
    else:
        resp = client.delete(f"/tasks/{task_id}", headers=auth_headers(token_a))

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Property 11: Task baru terasosiasi dengan user_id dari token
# Feature: task-auth-deadline-calendar, Property 11
# ---------------------------------------------------------------------------

@given(title=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_11_new_task_associated_with_token_user(client, title):
    """Property 11: A newly created task is only visible to the user whose token was used."""
    token = register_and_login(client, "prop11@example.com", "password123")
    token_other = register_and_login(client, "prop11other@example.com", "password123")

    task = _create_task(client, token, title=title).get_json()
    task_id = task["id"]

    # Owner can access it
    assert client.get(f"/tasks/{task_id}", headers=auth_headers(token)).status_code == 200
    # Other user cannot
    assert client.get(f"/tasks/{task_id}", headers=auth_headers(token_other)).status_code == 403


# ---------------------------------------------------------------------------
# Property 12 (new): Deadline round-trip (create dan update)
# Feature: task-auth-deadline-calendar, Property 12
# ---------------------------------------------------------------------------

VALID_ISO_DEADLINES = [
    "2099-01-15T10:30:00",
    "2099-06-30T23:59:59",
    "2099-12-31T00:00:00",
    "2099-03-01T12:00:00+00:00",
]


@given(deadline=st.sampled_from(VALID_ISO_DEADLINES))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_12_deadline_round_trip_create(client, deadline):
    """Property 12: Creating a task with a valid ISO 8601 deadline preserves it in the response."""
    from datetime import datetime, timezone

    token = register_and_login(client, "prop12c@example.com", "password123")
    resp = _create_task(client, token, title="Deadline Task", deadline=deadline)
    assert resp.status_code == 201
    returned_deadline = resp.get_json()["deadline"]
    assert returned_deadline is not None

    # Semantically equivalent: both parse to the same UTC moment
    dt_sent = datetime.fromisoformat(deadline)
    dt_returned = datetime.fromisoformat(returned_deadline)
    if dt_sent.tzinfo is None:
        dt_sent = dt_sent.replace(tzinfo=timezone.utc)
    if dt_returned.tzinfo is None:
        dt_returned = dt_returned.replace(tzinfo=timezone.utc)
    assert dt_sent == dt_returned


@given(deadline=st.sampled_from(VALID_ISO_DEADLINES))
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_12_deadline_round_trip_update(client, deadline):
    """Property 12: Updating a task's deadline preserves the value in the response."""
    from datetime import datetime, timezone

    token = register_and_login(client, "prop12u@example.com", "password123")
    task_id = _create_task(client, token, title="Task").get_json()["id"]
    resp = client.put(f"/tasks/{task_id}", data=json.dumps({"deadline": deadline}), content_type="application/json", headers=auth_headers(token))
    assert resp.status_code == 200
    returned_deadline = resp.get_json()["deadline"]
    assert returned_deadline is not None

    dt_sent = datetime.fromisoformat(deadline)
    dt_returned = datetime.fromisoformat(returned_deadline)
    if dt_sent.tzinfo is None:
        dt_sent = dt_sent.replace(tzinfo=timezone.utc)
    if dt_returned.tzinfo is None:
        dt_returned = dt_returned.replace(tzinfo=timezone.utc)
    assert dt_sent == dt_returned


# ---------------------------------------------------------------------------
# Property 14: Field deadline selalu ada di setiap respons task
# Feature: task-auth-deadline-calendar, Property 14
# ---------------------------------------------------------------------------

@given(
    title=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    include_deadline=st.booleans(),
)
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_14_deadline_field_always_present(client, title, include_deadline):
    """Property 14: Every task response always contains a 'deadline' field (string or null)."""
    token = register_and_login(client, "prop14@example.com", "password123")
    deadline = VALID_DEADLINE if include_deadline else None
    task = _create_task(client, token, title=title, deadline=deadline).get_json()
    assert "deadline" in task

    # Also check in GET /tasks list
    tasks = client.get("/tasks", headers=auth_headers(token)).get_json()
    for t in tasks:
        assert "deadline" in t

    # And in GET /tasks/{id}
    fetched = client.get(f"/tasks/{task['id']}", headers=auth_headers(token)).get_json()
    assert "deadline" in fetched


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

class TestGlobalErrorHandler:
    def test_global_handler_returns_500_json(self, real_app_client):
        resp = real_app_client.get("/_test_error")
        assert resp.status_code == 500
        data = resp.get_json()
        assert "error" in data
        assert "Traceback" not in data["error"]

    def test_global_handler_returns_404_json_for_unknown_route(self, real_app_client):
        resp = real_app_client.get("/_unknown_route_xyz")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data is not None
        assert "error" in data
