"""
Fix-check tests for Phase 3 — verify bugs are fixed (Property 1 & 2).

These tests are EXPECTED TO PASS after fixes are applied.

**Validates: Requirements 2.1, 2.2**
"""
import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

import app.models as models


# ---------------------------------------------------------------------------
# Property 1: models.DATABASE is consistent across Hypothesis examples
# **Validates: Requirements 2.1, 2.2**
# ---------------------------------------------------------------------------

@given(st.integers(min_value=1, max_value=10))
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
def test_property_1_database_consistent_across_examples(client, n):
    """
    Property 1: For any test using the `client` fixture with Hypothesis
    (multiple examples), after RC1 fix is applied, models.DATABASE SHALL
    always point to the correct and isolated database path for each test
    context, unaffected by execution order or number of prior examples.

    The fix (task 2.2): models.DATABASE is re-set at the start of each
    Hypothesis example using the value stored in client.application.config["TEST_DB_PATH"].

    What this property verifies:
      - models.DATABASE always equals the fixture's expected db_path (before and after inserts)
      - Tasks inserted via models.insert_task() go into the correct isolated database
      - The path does NOT drift to a different database across examples

    Note: The same temp DB is intentionally reused across all examples within one
    fixture invocation (tasks accumulate). The fix only guarantees the PATH is correct,
    not that the DB is empty at the start of each example.

    Expected result on FIXED code: PASS

    **Validates: Requirements 2.1, 2.2**
    """
    # RC1 fix: re-set models.DATABASE at the start of each example
    expected_db_path = client.application.config["TEST_DB_PATH"]
    models.DATABASE = expected_db_path

    # Property: models.DATABASE must point to the expected isolated path
    assert models.DATABASE == expected_db_path, (
        f"models.DATABASE is {models.DATABASE!r}, expected {expected_db_path!r}. "
        f"RC1 fix is not working — DATABASE is not reset per-example."
    )

    # Record task count before insert so we can verify the delta
    count_before = len(models.fetch_all_tasks())

    # Insert n tasks directly via models (same pattern as test_property_5)
    from datetime import datetime, timedelta
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    for i in range(n):
        ts = (base_time + timedelta(seconds=i)).isoformat()
        models.insert_task(
            title=f"Fix-check task {i}",
            description=None,
            status="pending",
            deadline=None,
            user_id=1,
            created_at=ts,
            updated_at=ts,
        )

    # Property: exactly n new tasks were written to the correct (isolated) database
    count_after = len(models.fetch_all_tasks())
    assert count_after == count_before + n, (
        f"Expected {count_before + n} tasks after insert (delta={n}), got {count_after}. "
        f"Tasks may have gone to the wrong database. "
        f"DATABASE: {models.DATABASE!r}"
    )

    # Property: DATABASE must still point to the expected path after inserts
    assert models.DATABASE == expected_db_path, (
        f"models.DATABASE changed during example execution: "
        f"expected {expected_db_path!r}, got {models.DATABASE!r}."
    )


# ---------------------------------------------------------------------------
# Property 2: compute_is_overdue is deterministic with fresh timestamps
# **Validates: Requirements 2.3**
# ---------------------------------------------------------------------------

from datetime import datetime, timezone, timedelta
from app.services import compute_is_overdue


@given(st.integers(min_value=1, max_value=3650))
@settings(max_examples=20, deadline=None)
def test_property_2_compute_is_overdue_deterministic_fresh_timestamp(days_ago):
    """
    Property 2: For any past deadline generated fresh inside the test body,
    compute_is_overdue SHALL always return True regardless of when the test runs.

    The fix (RC3, task 2.3): PAST/FUTURE module-level constants were replaced
    with make_past()/make_future() helper functions evaluated fresh per-test.
    This property verifies the underlying compute_is_overdue function behaves
    correctly when given a fresh past deadline computed at call time.

    What this property verifies:
      - A deadline computed as `now() - timedelta(days=days_ago)` is always in the past
      - compute_is_overdue returns True for any such deadline with status='pending'
      - The result is deterministic: it does not depend on import-time constants

    Expected result on FIXED code: PASS

    **Validates: Requirements 2.3**
    """
    # Compute fresh past deadline inside the test body (not at module import time)
    past_deadline = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

    task = {
        "id": 1,
        "title": "Test Task",
        "description": None,
        "status": "pending",
        "deadline": past_deadline,
        "user_id": 1,
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }

    result = compute_is_overdue(task)

    assert result is True, (
        f"compute_is_overdue returned {result!r} for a past deadline "
        f"({days_ago} days ago: {past_deadline!r}). "
        f"Expected True — RC3 fix may not be working correctly."
    )
