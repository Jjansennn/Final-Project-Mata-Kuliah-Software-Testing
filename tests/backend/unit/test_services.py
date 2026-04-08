"""Unit tests for TaskService functions (isolated, no DB or HTTP)."""
import pytest
from unittest.mock import patch, call
from datetime import datetime, timezone, timedelta
from hypothesis import given, settings, assume
import hypothesis.strategies as st

from app.models import TaskNotFoundError
from app.services import (
    create_task,
    get_all_tasks,
    get_task_by_id,
    update_task,
    delete_task,
    compute_is_overdue,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_past() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


def make_future() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

def make_task(**kwargs):
    base = {
        "id": 1,
        "title": "Test Task",
        "description": "A description",
        "status": "pending",
        "deadline": None,
        "user_id": 1,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    base.update(kwargs)
    return base


SAMPLE_TASK = make_task()


# ---------------------------------------------------------------------------
# compute_is_overdue
# ---------------------------------------------------------------------------

class TestComputeIsOverdue:
    def test_past_deadline_pending_is_overdue(self):
        task = make_task(deadline=make_past(), status="pending")
        assert compute_is_overdue(task) is True

    def test_past_deadline_in_progress_is_overdue(self):
        task = make_task(deadline=make_past(), status="in_progress")
        assert compute_is_overdue(task) is True

    def test_past_deadline_done_not_overdue(self):
        task = make_task(deadline=make_past(), status="done")
        assert compute_is_overdue(task) is False

    def test_future_deadline_not_overdue(self):
        task = make_task(deadline=make_future(), status="pending")
        assert compute_is_overdue(task) is False

    def test_no_deadline_not_overdue(self):
        task = make_task(deadline=None, status="pending")
        assert compute_is_overdue(task) is False

    def test_naive_datetime_treated_as_utc(self):
        past_naive = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        task = make_task(deadline=past_naive, status="pending")
        assert compute_is_overdue(task) is True

    def test_invalid_deadline_string_not_overdue(self):
        task = make_task(deadline="not-a-date", status="pending")
        assert compute_is_overdue(task) is False


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------

class TestCreateTask:
    def test_create_task_returns_dict_with_is_overdue(self):
        with patch("app.services.insert_task", return_value=1), \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            result = create_task("Test Task", user_id=1)
            assert "is_overdue" in result

    def test_create_task_sets_status_pending(self):
        with patch("app.services.insert_task", return_value=1) as mock_insert, \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            create_task("Test Task", user_id=1)
            assert mock_insert.call_args.kwargs["status"] == "pending"

    def test_create_task_sets_timestamps(self):
        with patch("app.services.insert_task", return_value=1) as mock_insert, \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            create_task("Test Task", user_id=1)
            kw = mock_insert.call_args.kwargs
            assert kw["created_at"] == kw["updated_at"]

    def test_create_task_with_description(self):
        with patch("app.services.insert_task", return_value=1) as mock_insert, \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            create_task("Test Task", description="Some desc", user_id=1)
            assert mock_insert.call_args.kwargs["description"] == "Some desc"

    def test_create_task_without_description(self):
        with patch("app.services.insert_task", return_value=1) as mock_insert, \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            create_task("Test Task", user_id=1)
            assert mock_insert.call_args.kwargs["description"] is None

    def test_create_task_raises_on_empty_title(self):
        with pytest.raises(ValueError):
            create_task("", user_id=1)

    def test_create_task_raises_on_none_title(self):
        with pytest.raises(ValueError):
            create_task(None, user_id=1)

    def test_create_task_raises_on_whitespace_title(self):
        with pytest.raises(ValueError):
            create_task("   ", user_id=1)

    def test_create_task_raises_on_title_too_long(self):
        with pytest.raises(ValueError):
            create_task("x" * 201, user_id=1)

    def test_create_task_accepts_title_exactly_200_chars(self):
        with patch("app.services.insert_task", return_value=1), \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            result = create_task("x" * 200, user_id=1)
            assert result is not None

    def test_create_task_with_valid_deadline(self):
        future = make_future()
        task_with_deadline = make_task(deadline=future)
        with patch("app.services.insert_task", return_value=1) as mock_insert, \
             patch("app.services.fetch_task_by_id", return_value=task_with_deadline):
            result = create_task("Task", deadline=future, user_id=1)
            assert mock_insert.call_args.kwargs["deadline"] == future
            assert result["deadline"] == future
            assert result["is_overdue"] is False

    def test_create_task_with_invalid_deadline_raises(self):
        with pytest.raises(ValueError):
            create_task("Task", deadline="not-a-date", user_id=1)

    def test_create_task_without_deadline_is_none(self):
        with patch("app.services.insert_task", return_value=1) as mock_insert, \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            create_task("Task", user_id=1)
            assert mock_insert.call_args.kwargs["deadline"] is None

    def test_create_task_passes_user_id(self):
        with patch("app.services.insert_task", return_value=1) as mock_insert, \
             patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            create_task("Task", user_id=42)
            assert mock_insert.call_args.kwargs["user_id"] == 42


# ---------------------------------------------------------------------------
# get_all_tasks
# ---------------------------------------------------------------------------

class TestGetAllTasks:
    def test_get_all_tasks_returns_list_with_is_overdue(self):
        with patch("app.services.fetch_all_tasks", return_value=[SAMPLE_TASK]):
            result = get_all_tasks(user_id=1)
            assert isinstance(result, list)
            assert "is_overdue" in result[0]

    def test_get_all_tasks_empty(self):
        with patch("app.services.fetch_all_tasks", return_value=[]):
            assert get_all_tasks(user_id=1) == []

    def test_get_all_tasks_passes_user_id(self):
        with patch("app.services.fetch_all_tasks", return_value=[]) as mock_fetch:
            get_all_tasks(user_id=7)
            mock_fetch.assert_called_once_with(user_id=7)

    def test_get_all_tasks_without_user_id(self):
        with patch("app.services.fetch_all_tasks", return_value=[]) as mock_fetch:
            get_all_tasks()
            mock_fetch.assert_called_once_with(user_id=None)


# ---------------------------------------------------------------------------
# get_task_by_id
# ---------------------------------------------------------------------------

class TestGetTaskById:
    def test_get_task_by_id_returns_task_with_is_overdue(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            result = get_task_by_id(1, user_id=1)
            assert "is_overdue" in result

    def test_get_task_by_id_raises_not_found(self):
        with patch("app.services.fetch_task_by_id", return_value=None):
            with pytest.raises(TaskNotFoundError):
                get_task_by_id(999, user_id=1)

    def test_get_task_by_id_error_message_contains_id(self):
        with patch("app.services.fetch_task_by_id", return_value=None):
            with pytest.raises(TaskNotFoundError, match="999"):
                get_task_by_id(999, user_id=1)

    def test_get_task_by_id_raises_permission_error_for_other_user(self):
        task = make_task(user_id=1)
        with patch("app.services.fetch_task_by_id", return_value=task):
            with pytest.raises(PermissionError):
                get_task_by_id(1, user_id=2)

    def test_get_task_by_id_no_user_id_skips_ownership_check(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            result = get_task_by_id(1)
            assert result["id"] == 1


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------

class TestUpdateTask:
    def test_update_task_returns_updated_dict_with_is_overdue(self):
        updated = make_task(title="New Title")
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=updated):
            result = update_task(1, {"title": "New Title"}, user_id=1)
            assert result["title"] == "New Title"
            assert "is_overdue" in result

    def test_update_task_raises_not_found(self):
        with patch("app.services.fetch_task_by_id", return_value=None):
            with pytest.raises(TaskNotFoundError):
                update_task(999, {"title": "X"}, user_id=1)

    def test_update_task_raises_permission_error_for_other_user(self):
        task = make_task(user_id=1)
        with patch("app.services.fetch_task_by_id", return_value=task):
            with pytest.raises(PermissionError):
                update_task(1, {"title": "X"}, user_id=2)

    def test_update_task_filters_unknown_fields(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=SAMPLE_TASK) as mock_update:
            update_task(1, {"title": "X", "unknown_field": "ignored"}, user_id=1)
            assert "unknown_field" not in mock_update.call_args[0][1]

    def test_update_task_sets_updated_at(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=SAMPLE_TASK) as mock_update:
            update_task(1, {"title": "X"}, user_id=1)
            assert "updated_at" in mock_update.call_args[0][1]

    def test_update_task_raises_on_invalid_status(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            with pytest.raises(ValueError):
                update_task(1, {"status": "invalid_status"}, user_id=1)

    def test_update_task_raises_on_empty_title(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            with pytest.raises(ValueError):
                update_task(1, {"title": ""}, user_id=1)

    def test_update_task_allows_valid_status(self):
        updated = make_task(status="done")
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=updated):
            assert update_task(1, {"status": "done"}, user_id=1)["status"] == "done"

    def test_update_task_allows_deadline_update(self):
        future = make_future()
        updated = make_task(deadline=future)
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=updated) as mock_update:
            result = update_task(1, {"deadline": future}, user_id=1)
            assert "deadline" in mock_update.call_args[0][1]
            assert result["deadline"] == future

    def test_update_task_allows_deadline_null(self):
        updated = make_task(deadline=None)
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=updated) as mock_update:
            result = update_task(1, {"deadline": None}, user_id=1)
            assert mock_update.call_args[0][1].get("deadline") is None
            assert result["deadline"] is None

    def test_update_task_raises_on_invalid_deadline(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK):
            with pytest.raises(ValueError):
                update_task(1, {"deadline": "bad-date"}, user_id=1)

    def test_update_task_only_passes_allowed_fields(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=SAMPLE_TASK) as mock_update:
            update_task(1, {"title": "T", "description": "D", "status": "done", "id": 99}, user_id=1)
            assert set(mock_update.call_args[0][1].keys()) <= {"title", "description", "status", "deadline", "updated_at"}

    def test_update_task_no_user_id_skips_ownership_check(self):
        updated = make_task(title="New")
        with patch("app.services.fetch_task_by_id", return_value=None), \
             patch("app.services.update_task_fields", return_value=updated):
            # No ownership check when user_id is None — fetch_task_by_id not called for ownership
            result = update_task(1, {"title": "New"})
            assert result["title"] == "New"


# ---------------------------------------------------------------------------
# delete_task
# ---------------------------------------------------------------------------

class TestDeleteTask:
    def test_delete_task_succeeds(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.delete_task_by_id", return_value=True):
            delete_task(1, user_id=1)  # should not raise

    def test_delete_task_raises_not_found_via_ownership_check(self):
        with patch("app.services.fetch_task_by_id", return_value=None):
            with pytest.raises(TaskNotFoundError):
                delete_task(999, user_id=1)

    def test_delete_task_raises_not_found_without_user_id(self):
        with patch("app.services.delete_task_by_id", return_value=False):
            with pytest.raises(TaskNotFoundError):
                delete_task(999)

    def test_delete_task_raises_permission_error_for_other_user(self):
        task = make_task(user_id=1)
        with patch("app.services.fetch_task_by_id", return_value=task):
            with pytest.raises(PermissionError):
                delete_task(1, user_id=2)

    def test_delete_task_returns_none(self):
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.delete_task_by_id", return_value=True):
            assert delete_task(1, user_id=1) is None

    def test_delete_task_error_message_contains_id(self):
        with patch("app.services.delete_task_by_id", return_value=False):
            with pytest.raises(TaskNotFoundError, match="42"):
                delete_task(42)


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

class TestPropertyUnknownFields:
    @given(st.fixed_dictionaries({
        "title": st.text(min_size=1, max_size=200).filter(lambda s: s.strip()),
        "unknown_field": st.text(),
    }))
    @settings(max_examples=10)
    def test_property_unknown_fields_ignored(self, data):
        """Unknown fields in update payload are silently ignored."""
        updated = make_task(title=data["title"])
        with patch("app.services.fetch_task_by_id", return_value=SAMPLE_TASK), \
             patch("app.services.update_task_fields", return_value=updated) as mock_update:
            result = update_task(1, data, user_id=1)
            assert "unknown_field" not in mock_update.call_args[0][1]
            assert result is not None


class TestPropertyCreateTask:
    @given(st.text(min_size=1, max_size=200).filter(lambda s: s.strip()))
    @settings(max_examples=10)
    def test_property_create_task_status_awal_pending(self, title):
        """create_task always produces status='pending' and includes is_overdue."""
        fake_task = make_task(title=title)
        with patch("app.services.insert_task", return_value=1), \
             patch("app.services.fetch_task_by_id", return_value=fake_task):
            result = create_task(title, user_id=1)
            assert result["status"] == "pending"
            assert "is_overdue" in result
            assert "id" in result
            assert "created_at" in result
            assert "updated_at" in result


# ---------------------------------------------------------------------------
# Feature: task-auth-deadline-calendar
# Property 15: Komputasi is_overdue konsisten dengan definisi
# Validates: Requirements 5.1, 5.2, 5.3
# ---------------------------------------------------------------------------

# Strategies for generating ISO 8601 datetimes
def _iso(dt: datetime) -> str:
    return dt.isoformat()

past_deadline_st = st.integers(min_value=1, max_value=365 * 5).map(
    lambda d: _iso(datetime.now(timezone.utc) - timedelta(days=d))
)
future_deadline_st = st.integers(min_value=1, max_value=365 * 5).map(
    lambda d: _iso(datetime.now(timezone.utc) + timedelta(days=d))
)
non_done_status_st = st.sampled_from(["pending", "in_progress"])


class TestProperty15IsOverdueConsistency:
    @given(deadline=past_deadline_st, status=non_done_status_st)
    @settings(max_examples=20)
    def test_past_deadline_non_done_is_overdue_true(self, deadline, status):
        """Past deadline + non-done status → is_overdue must be True."""
        task = make_task(deadline=deadline, status=status)
        assert compute_is_overdue(task) is True

    @given(deadline=future_deadline_st, status=non_done_status_st)
    @settings(max_examples=20)
    def test_future_deadline_is_overdue_false(self, deadline, status):
        """Future deadline → is_overdue must be False regardless of status."""
        task = make_task(deadline=deadline, status=status)
        assert compute_is_overdue(task) is False

    @given(deadline=past_deadline_st)
    @settings(max_examples=20)
    def test_done_status_is_overdue_false(self, deadline):
        """status='done' → is_overdue must be False even with past deadline."""
        task = make_task(deadline=deadline, status="done")
        assert compute_is_overdue(task) is False

    @given(status=st.sampled_from(["pending", "in_progress", "done"]))
    @settings(max_examples=10)
    def test_no_deadline_is_overdue_false(self, status):
        """No deadline → is_overdue must always be False."""
        task = make_task(deadline=None, status=status)
        assert compute_is_overdue(task) is False

    @given(
        deadline=past_deadline_st,
        status=non_done_status_st,
    )
    @settings(max_examples=20)
    def test_get_all_tasks_includes_correct_is_overdue(self, deadline, status):
        """get_all_tasks propagates is_overdue correctly for each task."""
        raw_task = make_task(deadline=deadline, status=status)
        with patch("app.services.fetch_all_tasks", return_value=[raw_task]):
            results = get_all_tasks(user_id=1)
            assert len(results) == 1
            assert results[0]["is_overdue"] is True

    @given(
        deadline=future_deadline_st,
        status=non_done_status_st,
    )
    @settings(max_examples=20)
    def test_get_all_tasks_future_deadline_not_overdue(self, deadline, status):
        """get_all_tasks marks future-deadline tasks as not overdue."""
        raw_task = make_task(deadline=deadline, status=status)
        with patch("app.services.fetch_all_tasks", return_value=[raw_task]):
            results = get_all_tasks(user_id=1)
            assert results[0]["is_overdue"] is False


# ---------------------------------------------------------------------------
# Repository branch coverage
# ---------------------------------------------------------------------------

class TestUpdateTaskFieldsDirectly:
    def test_update_task_fields_empty_dict_calls_fetch(self):
        from app.models import update_task_fields
        with patch("app.models.fetch_task_by_id") as mock_fetch:
            mock_fetch.return_value = {"id": 1, "title": "T"}
            result = update_task_fields(1, {})
            mock_fetch.assert_called_once_with(1)
            assert result == {"id": 1, "title": "T"}


# ---------------------------------------------------------------------------
# delete_task without user_id — TaskNotFoundError when delete_task_by_id returns False
# (covers services.py line 90)
# ---------------------------------------------------------------------------

class TestDeleteTaskNoBranch:
    def test_delete_task_no_user_id_not_found_raises(self):
        with patch("app.services.delete_task_by_id", return_value=False):
            with pytest.raises(TaskNotFoundError, match="99"):
                delete_task(99)


class TestUpdateTaskNoUserIdNotFound:
    def test_update_task_no_user_id_update_fields_returns_none_raises(self):
        """update_task raises TaskNotFoundError when update_task_fields returns None (no user_id path)."""
        with patch("app.services.update_task_fields", return_value=None):
            with pytest.raises(TaskNotFoundError, match="55"):
                update_task(55, {"title": "X"})
