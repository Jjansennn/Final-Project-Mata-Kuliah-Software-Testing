"""
Preservation property tests for Phase 4 — verify no regressions in compute_is_overdue
for non-buggy inputs (deadline=None or status='done').

These tests are EXPECTED TO PASS (no regressions after fix).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
"""
from datetime import datetime, timezone, timedelta

from hypothesis import given, settings
import hypothesis.strategies as st

from app.services import compute_is_overdue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(**kwargs):
    base = {
        "id": 1,
        "title": "Test Task",
        "description": None,
        "status": "pending",
        "deadline": None,
        "user_id": 1,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    base.update(kwargs)
    return base


# Strategies
any_status_st = st.sampled_from(["pending", "in_progress", "done"])

past_deadline_st = st.integers(min_value=1, max_value=365 * 5).map(
    lambda d: (datetime.now(timezone.utc) - timedelta(days=d)).isoformat()
)
future_deadline_st = st.integers(min_value=1, max_value=365 * 5).map(
    lambda d: (datetime.now(timezone.utc) + timedelta(days=d)).isoformat()
)
any_deadline_st = st.one_of(past_deadline_st, future_deadline_st)


# ---------------------------------------------------------------------------
# Property 4 (Preservation): deadline=None always returns False
#
# For any task with deadline=None, compute_is_overdue must return False
# regardless of status. This behavior was correct before the fix and must
# remain unchanged after the fix.
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
# ---------------------------------------------------------------------------

@given(status=any_status_st)
@settings(max_examples=20, deadline=None)
def test_preservation_no_deadline_always_false(status):
    """
    Property 4 (Preservation): For any task with deadline=None,
    compute_is_overdue SHALL return False regardless of status.

    This is a non-buggy input — the fix (RC3) must not change this behavior.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    task = make_task(deadline=None, status=status)
    result = compute_is_overdue(task)
    assert result is False, (
        f"compute_is_overdue returned {result!r} for deadline=None, status={status!r}. "
        f"Expected False — this is a regression in preservation behavior."
    )


# ---------------------------------------------------------------------------
# Property 4 (Preservation): status='done' always returns False
#
# For any task with status='done', compute_is_overdue must return False
# regardless of deadline value. This behavior was correct before the fix
# and must remain unchanged after the fix.
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
# ---------------------------------------------------------------------------

@given(deadline=any_deadline_st)
@settings(max_examples=20, deadline=None)
def test_preservation_done_status_always_false(deadline):
    """
    Property 4 (Preservation): For any task with status='done',
    compute_is_overdue SHALL return False regardless of deadline.

    This is a non-buggy input — the fix (RC3) must not change this behavior.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    task = make_task(deadline=deadline, status="done")
    result = compute_is_overdue(task)
    assert result is False, (
        f"compute_is_overdue returned {result!r} for status='done', deadline={deadline!r}. "
        f"Expected False — this is a regression in preservation behavior."
    )


# ---------------------------------------------------------------------------
# Property 4 (Preservation): deadline=None AND status='done' always returns False
#
# Combined case: both non-buggy conditions apply simultaneously.
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
# ---------------------------------------------------------------------------

def test_preservation_no_deadline_done_status_false():
    """
    Property 4 (Preservation): Task with deadline=None and status='done'
    must return False — the most trivially non-overdue case.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """
    task = make_task(deadline=None, status="done")
    assert compute_is_overdue(task) is False
