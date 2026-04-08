"""Preservation property tests — verifikasi CRUD API behavior tidak berubah setelah fix.

Property 4: For any test that does NOT involve the bug condition (not dependent on
global state or real clock), the fixed code SHALL produce identical results to the
original code.

These tests are EXPECTED TO PASS — they verify no regressions were introduced.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
"""
import json
import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

from conftest import register_and_login, auth_headers


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

valid_title = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())

valid_status = st.sampled_from(["pending", "in_progress", "done"])

# ISO 8601 deadline strings far in the future (no risk of becoming overdue during test)
valid_deadline = st.one_of(
    st.none(),
    st.sampled_from([
        "2099-01-15T10:30:00",
        "2099-06-30T23:59:59",
        "2099-12-31T00:00:00",
        "2099-03-01T12:00:00",
    ]),
)


def _create_task(client, token, title="Test Task", status=None, deadline=None):
    payload = {"title": title}
    if status is not None:
        payload["status"] = status
    if deadline is not None:
        payload["deadline"] = deadline
    return client.post(
        "/tasks",
        data=json.dumps(payload),
        content_type="application/json",
        headers=auth_headers(token),
    )


# ---------------------------------------------------------------------------
# Preservation Property: POST /tasks
# **Validates: Requirements 3.1, 3.2**
# ---------------------------------------------------------------------------

@given(title=valid_title, deadline=valid_deadline)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_preservation_post_tasks_status_code_and_structure(client, title, deadline):
    """Preservation Property 4: POST /tasks dengan title/deadline valid selalu mengembalikan
    201 dan response body dengan field yang diharapkan — behavior tidak berubah setelah fix.

    **Validates: Requirements 3.1, 3.2**
    """
    token = register_and_login(client)
    resp = _create_task(client, token, title=title, deadline=deadline)

    assert resp.status_code == 201, (
        f"POST /tasks returned {resp.status_code}, expected 201. "
        f"title={title!r}, deadline={deadline!r}"
    )

    data = resp.get_json()
    required_fields = ("id", "title", "status", "created_at", "updated_at", "deadline", "is_overdue")
    for field in required_fields:
        assert field in data, (
            f"Field '{field}' missing from POST /tasks response. "
            f"Got keys: {list(data.keys())}"
        )

    assert data["status"] == "pending", (
        f"New task status should be 'pending', got {data['status']!r}"
    )
    assert data["title"] == title.strip() or data["title"] == title, (
        f"Returned title {data['title']!r} does not match input {title!r}"
    )


# ---------------------------------------------------------------------------
# Preservation Property: GET /tasks
# **Validates: Requirements 3.1, 3.2**
# ---------------------------------------------------------------------------

@given(n=st.integers(min_value=0, max_value=10), title=valid_title)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_preservation_get_tasks_returns_correct_count(client, n, title):
    """Preservation Property 4: GET /tasks mengembalikan tepat N task setelah N task dibuat
    — behavior tidak berubah setelah fix.

    **Validates: Requirements 3.1, 3.2**
    """
    token = register_and_login(client)

    # Clear any existing tasks
    existing = client.get("/tasks", headers=auth_headers(token)).get_json()
    for task in existing:
        client.delete(f"/tasks/{task['id']}", headers=auth_headers(token))

    for i in range(n):
        _create_task(client, token, title=f"{title[:50]}-{i}" if len(title) > 50 else f"{title}-{i}")

    resp = client.get("/tasks", headers=auth_headers(token))
    assert resp.status_code == 200, f"GET /tasks returned {resp.status_code}, expected 200"
    assert isinstance(resp.get_json(), list), "GET /tasks should return a JSON array"
    assert len(resp.get_json()) == n, (
        f"Expected {n} tasks, got {len(resp.get_json())}. "
        "Task count mismatch — possible regression in GET /tasks."
    )


# ---------------------------------------------------------------------------
# Preservation Property: GET /tasks/{id}
# **Validates: Requirements 3.1, 3.2**
# ---------------------------------------------------------------------------

@given(title=valid_title, deadline=valid_deadline)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_preservation_get_task_by_id_round_trip(client, title, deadline):
    """Preservation Property 4: GET /tasks/{id} mengembalikan data identik dengan POST /tasks
    — round-trip behavior tidak berubah setelah fix.

    **Validates: Requirements 3.1, 3.2**
    """
    token = register_and_login(client)
    created = _create_task(client, token, title=title, deadline=deadline).get_json()
    task_id = created["id"]

    resp = client.get(f"/tasks/{task_id}", headers=auth_headers(token))
    assert resp.status_code == 200, (
        f"GET /tasks/{task_id} returned {resp.status_code}, expected 200"
    )
    fetched = resp.get_json()
    assert fetched == created, (
        f"GET /tasks/{{id}} returned different data than POST /tasks. "
        f"Created: {created}, Fetched: {fetched}"
    )


# ---------------------------------------------------------------------------
# Preservation Property: PUT /tasks/{id}
# **Validates: Requirements 3.1, 3.2**
# ---------------------------------------------------------------------------

@given(title=valid_title, new_status=valid_status, deadline=valid_deadline)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_preservation_put_task_updates_fields(client, title, new_status, deadline):
    """Preservation Property 4: PUT /tasks/{id} memperbarui field dengan benar dan mengembalikan
    200 — behavior tidak berubah setelah fix.

    **Validates: Requirements 3.1, 3.2**
    """
    token = register_and_login(client)
    task_id = _create_task(client, token, title=title).get_json()["id"]

    update_payload = {"status": new_status}
    if deadline is not None:
        update_payload["deadline"] = deadline

    resp = client.put(
        f"/tasks/{task_id}",
        data=json.dumps(update_payload),
        content_type="application/json",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200, (
        f"PUT /tasks/{task_id} returned {resp.status_code}, expected 200. "
        f"payload={update_payload}"
    )

    data = resp.get_json()
    assert data["status"] == new_status, (
        f"PUT /tasks did not update status: expected {new_status!r}, got {data['status']!r}"
    )
    if deadline is not None:
        assert data["deadline"] is not None, (
            f"PUT /tasks did not preserve deadline: expected non-null, got None"
        )


# ---------------------------------------------------------------------------
# Preservation Property: DELETE /tasks/{id}
# **Validates: Requirements 3.1, 3.2**
# ---------------------------------------------------------------------------

@given(title=valid_title)
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_preservation_delete_task_removes_resource(client, title):
    """Preservation Property 4: DELETE /tasks/{id} mengembalikan 200 dan task tidak lagi
    dapat diakses — behavior tidak berubah setelah fix.

    **Validates: Requirements 3.1, 3.2**
    """
    token = register_and_login(client)
    task_id = _create_task(client, token, title=title).get_json()["id"]

    del_resp = client.delete(f"/tasks/{task_id}", headers=auth_headers(token))
    assert del_resp.status_code == 200, (
        f"DELETE /tasks/{task_id} returned {del_resp.status_code}, expected 200"
    )
    assert "message" in del_resp.get_json(), (
        "DELETE /tasks response should contain 'message' field"
    )

    get_resp = client.get(f"/tasks/{task_id}", headers=auth_headers(token))
    assert get_resp.status_code == 404, (
        f"After DELETE, GET /tasks/{task_id} returned {get_resp.status_code}, expected 404. "
        "Task was not properly removed — possible regression."
    )


# ---------------------------------------------------------------------------
# Preservation Property: full CRUD lifecycle
# **Validates: Requirements 3.1, 3.2, 3.3**
# ---------------------------------------------------------------------------

@given(title=valid_title, status=valid_status, deadline=valid_deadline)
@settings(
    max_examples=10,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_preservation_full_crud_lifecycle(client, title, status, deadline):
    """Preservation Property 4: Untuk setiap kombinasi title/status/deadline yang valid,
    full CRUD lifecycle (POST → GET → PUT → DELETE) menghasilkan status code dan response
    body yang benar — tidak ada regresi setelah fix.

    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    token = register_and_login(client)

    # CREATE
    create_resp = _create_task(client, token, title=title, deadline=deadline)
    assert create_resp.status_code == 201
    task = create_resp.get_json()
    task_id = task["id"]
    assert task["status"] == "pending"

    # READ
    get_resp = client.get(f"/tasks/{task_id}", headers=auth_headers(token))
    assert get_resp.status_code == 200
    assert get_resp.get_json() == task

    # UPDATE
    update_resp = client.put(
        f"/tasks/{task_id}",
        data=json.dumps({"status": status}),
        content_type="application/json",
        headers=auth_headers(token),
    )
    assert update_resp.status_code == 200
    updated = update_resp.get_json()
    assert updated["status"] == status
    assert updated["id"] == task_id
    assert updated["updated_at"] >= task["updated_at"]

    # DELETE
    del_resp = client.delete(f"/tasks/{task_id}", headers=auth_headers(token))
    assert del_resp.status_code == 200

    # VERIFY GONE
    gone_resp = client.get(f"/tasks/{task_id}", headers=auth_headers(token))
    assert gone_resp.status_code == 404
