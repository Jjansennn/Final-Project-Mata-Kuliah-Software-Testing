"""Fix-check tests untuk memverifikasi bug RC2 sudah diperbaiki.

Property 2: route `/_test_error` tersedia pada setiap invocation `real_app_client`.
"""
import pytest


def test_route_test_error_tersedia_pada_invocation_pertama(real_app_client):
    """Assert GET /_test_error mengembalikan 500 (bukan 404) pada invocation pertama.

    Validates: Requirements 2.2
    """
    response = real_app_client.get("/_test_error")
    assert response.status_code == 500, (
        f"Invocation pertama: expected 500, got {response.status_code}. "
        "Route /_test_error tidak terdaftar dengan benar."
    )


def test_route_test_error_tersedia_pada_invocation_kedua(real_app_client):
    """Assert GET /_test_error mengembalikan 500 (bukan 404) pada invocation kedua.

    Validates: Requirements 2.2
    """
    response = real_app_client.get("/_test_error")
    assert response.status_code == 500, (
        f"Invocation kedua: expected 500, got {response.status_code}. "
        "Global flag RC2 mungkin masih mencegah re-registration route."
    )
