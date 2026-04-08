"""
Exploratory tests for flaky test root causes — Integration (Phase 1).

RC2: Global flag `_real_app_routes_registered` has been replaced with a URL map
     guard: `if '/_test_error' not in [r.rule for r in app.url_map.iter_rules()]`.
     This test verifies that the route is correctly registered (or skipped if
     already present) on every fixture invocation, without relying on a global flag.

Validates: Requirements 1.2 (bugfix.md)
"""
import pytest
import app as app_module
import app.models as models


# ---------------------------------------------------------------------------
# RC2 — URL map guard ensures route registration on every fixture invocation
# **Validates: Requirements 1.2**
# ---------------------------------------------------------------------------


def _run_real_app_client_logic(tmp_path, suffix=""):
    """
    Execute the fixed fixture logic from conftest.real_app_client inline.
    Uses the URL map guard instead of the global flag.
    Returns a Flask test client.
    """
    db_path = str(tmp_path / f"real_test{suffix}.db")
    original_db = models.DATABASE
    models.DATABASE = db_path
    models.init_db()

    # ---- fixed guard from conftest.py ----
    if '/_test_error' not in [r.rule for r in app_module.app.url_map.iter_rules()]:
        @app_module.app.route("/_test_error")
        def _trigger_error():
            raise RuntimeError("global handler test")
    # --------------------------------------

    app_module.app.config["TESTING"] = False
    client = app_module.app.test_client()
    models.DATABASE = original_db
    return client


def test_rc2_route_available_on_second_invocation(tmp_path):
    """
    RC2 fix verification: even when `/_test_error` is absent from the url_map
    at the start of a fixture invocation (simulating a fresh or reset state),
    the URL map guard correctly registers the route so GET `/_test_error`
    returns 500.

    Setup:
      1. Remove `/_test_error` from the app's url_map (clean slate).
      2. Call the fixture logic — the guard detects the route is absent and
         registers it.
      3. Assert the route returns 500.

    Expected result on FIXED code: PASS
      (route is registered by the URL map guard → returns 500)
    """
    url_map = app_module.app.url_map

    # Snapshot full app state before we touch anything
    original_rules_by_endpoint = dict(url_map._rules_by_endpoint)
    original_view_functions = dict(app_module.app.view_functions)
    original_got_first_request = app_module.app._got_first_request

    # --- Step 1: remove /_test_error from the app singleton (clean slate) ---
    url_map._rules_by_endpoint = {
        ep: rules
        for ep, rules in url_map._rules_by_endpoint.items()
        if ep != "_trigger_error"
    }
    app_module.app.view_functions = {
        ep: fn
        for ep, fn in app_module.app.view_functions.items()
        if ep != "_trigger_error"
    }
    app_module.app._got_first_request = False

    try:
        # --- Step 2: run the fixed fixture logic ---
        # The URL map guard detects the route is absent and registers it.
        client = _run_real_app_client_logic(tmp_path, suffix="_rc2")

        registered_rules = [r.rule for r in url_map.iter_rules()]
        assert "/_test_error" in registered_rules, (
            "Route /_test_error was not registered by the URL map guard."
        )

        # --- Step 3: assert the route returns 500 ---
        resp = client.get("/_test_error")
        assert resp.status_code == 500, (
            f"Expected 500 from /_test_error but got {resp.status_code}. "
            f"The URL map guard should have registered the route."
        )
    finally:
        # Restore full app state so subsequent tests are not affected
        url_map._rules_by_endpoint = original_rules_by_endpoint
        app_module.app.view_functions = original_view_functions
        app_module.app._got_first_request = original_got_first_request
