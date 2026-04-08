from datetime import datetime, timezone

from app.models import (
    TaskNotFoundError,
    insert_task,
    fetch_all_tasks,
    fetch_task_by_id,
    update_task_fields,
    delete_task_by_id,
)
from app.validators import validate_create_payload, validate_update_payload, validate_deadline


def compute_is_overdue(task: dict) -> bool:
    """Return True iff task has a past deadline and status is not 'done'."""
    deadline = task.get("deadline")
    if not deadline or task.get("status") == "done":
        return False
    try:
        dl = datetime.fromisoformat(str(deadline))
        # Make deadline timezone-aware if naive
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        return dl < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def _with_is_overdue(task: dict) -> dict:
    """Return a copy of task with the computed is_overdue field."""
    return {**task, "is_overdue": compute_is_overdue(task)}


def create_task(title: str, description: str = None, deadline=None, user_id=None) -> dict:
    """Create a new task after validation. Returns the created task dict."""
    validate_create_payload({"title": title, "deadline": deadline})
    now = datetime.now(timezone.utc).isoformat()
    task_id = insert_task(
        title=title,
        description=description,
        status="pending",
        deadline=deadline,
        user_id=user_id,
        created_at=now,
        updated_at=now,
    )
    task = fetch_task_by_id(task_id)
    return _with_is_overdue(task)


def get_all_tasks(user_id=None) -> list:
    """Return all tasks for the given user, ordered by created_at descending."""
    tasks = fetch_all_tasks(user_id=user_id)
    return [_with_is_overdue(t) for t in tasks]


def get_task_by_id(task_id: int, user_id=None) -> dict:
    """Return a single task by ID.

    Raises TaskNotFoundError if not found.
    Raises PermissionError if user_id is provided and doesn't match task owner.
    """
    task = fetch_task_by_id(task_id)
    if task is None:
        raise TaskNotFoundError(f"Task dengan id {task_id} tidak ditemukan")
    if user_id is not None and task.get("user_id") != user_id:
        raise PermissionError("Akses ditolak")
    return _with_is_overdue(task)


def update_task(task_id: int, data: dict, user_id=None) -> dict:
    """Update allowed fields of a task.

    Raises TaskNotFoundError if not found.
    Raises PermissionError if user_id is provided and doesn't match task owner.
    """
    # Ownership check
    if user_id is not None:
        existing = fetch_task_by_id(task_id)
        if existing is None:
            raise TaskNotFoundError(f"Task dengan id {task_id} tidak ditemukan")
        if existing.get("user_id") != user_id:
            raise PermissionError("Akses ditolak")

    allowed = {k: v for k, v in data.items() if k in ("title", "description", "status", "deadline")}
    validate_update_payload(allowed)
    allowed["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = update_task_fields(task_id, allowed)
    if result is None:
        raise TaskNotFoundError(f"Task dengan id {task_id} tidak ditemukan")
    return _with_is_overdue(result)


def delete_task(task_id: int, user_id=None) -> None:
    """Delete a task by ID.

    Raises TaskNotFoundError if not found.
    Raises PermissionError if user_id is provided and doesn't match task owner.
    """
    if user_id is not None:
        existing = fetch_task_by_id(task_id)
        if existing is None:
            raise TaskNotFoundError(f"Task dengan id {task_id} tidak ditemukan")
        if existing.get("user_id") != user_id:
            raise PermissionError("Akses ditolak")

    deleted = delete_task_by_id(task_id)
    if not deleted:
        raise TaskNotFoundError(f"Task dengan id {task_id} tidak ditemukan")
