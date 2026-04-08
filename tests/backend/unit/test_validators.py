import pytest
import string
from hypothesis import given, settings
from hypothesis import strategies as st
from app.validators import (
    validate_title,
    validate_status,
    validate_create_payload,
    validate_update_payload,
    validate_email,
    validate_password,
    validate_deadline,
)


# --- validate_title ---

def test_validate_title_valid():
    validate_title("Valid title")


def test_validate_title_exactly_200_chars():
    validate_title("a" * 200)


def test_validate_title_none_raises():
    with pytest.raises(ValueError, match="title wajib diisi dan tidak boleh kosong"):
        validate_title(None)


def test_validate_title_empty_string_raises():
    with pytest.raises(ValueError, match="title wajib diisi dan tidak boleh kosong"):
        validate_title("")


def test_validate_title_whitespace_only_raises():
    with pytest.raises(ValueError, match="title wajib diisi dan tidak boleh kosong"):
        validate_title("   ")


def test_validate_title_tab_only_raises():
    with pytest.raises(ValueError, match="title wajib diisi dan tidak boleh kosong"):
        validate_title("\t")


def test_validate_title_201_chars_raises():
    with pytest.raises(ValueError, match="title tidak boleh melebihi 200 karakter"):
        validate_title("a" * 201)


def test_validate_title_very_long_raises():
    with pytest.raises(ValueError, match="title tidak boleh melebihi 200 karakter"):
        validate_title("x" * 500)


# --- validate_status ---

def test_validate_status_pending():
    validate_status("pending")


def test_validate_status_in_progress():
    validate_status("in_progress")


def test_validate_status_done():
    validate_status("done")


def test_validate_status_invalid_raises():
    with pytest.raises(ValueError, match="status tidak valid"):
        validate_status("invalid")


def test_validate_status_empty_raises():
    with pytest.raises(ValueError, match="status tidak valid"):
        validate_status("")


def test_validate_status_none_raises():
    with pytest.raises(ValueError, match="status tidak valid"):
        validate_status(None)


def test_validate_status_uppercase_raises():
    with pytest.raises(ValueError, match="status tidak valid"):
        validate_status("PENDING")


# --- validate_create_payload ---

def test_validate_create_payload_valid():
    validate_create_payload({"title": "My task"})


def test_validate_create_payload_missing_title_raises():
    with pytest.raises(ValueError, match="title wajib diisi dan tidak boleh kosong"):
        validate_create_payload({})


def test_validate_create_payload_empty_title_raises():
    with pytest.raises(ValueError, match="title wajib diisi dan tidak boleh kosong"):
        validate_create_payload({"title": ""})


def test_validate_create_payload_long_title_raises():
    with pytest.raises(ValueError, match="title tidak boleh melebihi 200 karakter"):
        validate_create_payload({"title": "a" * 201})


# --- validate_update_payload ---

def test_validate_update_payload_empty_dict():
    validate_update_payload({})


def test_validate_update_payload_valid_title():
    validate_update_payload({"title": "Updated title"})


def test_validate_update_payload_valid_status():
    validate_update_payload({"status": "done"})


def test_validate_update_payload_valid_both():
    validate_update_payload({"title": "New title", "status": "in_progress"})


def test_validate_update_payload_invalid_title_raises():
    with pytest.raises(ValueError, match="title wajib diisi dan tidak boleh kosong"):
        validate_update_payload({"title": "  "})


def test_validate_update_payload_invalid_status_raises():
    with pytest.raises(ValueError, match="status tidak valid"):
        validate_update_payload({"status": "unknown"})


def test_validate_update_payload_title_not_validated_when_absent():
    validate_update_payload({"status": "pending"})


def test_validate_update_payload_status_not_validated_when_absent():
    validate_update_payload({"title": "Hello"})


# --- Property-Based Tests ---

@given(st.text(alphabet=string.whitespace, min_size=1))
@settings(max_examples=10)
def test_property_2_whitespace_title_selalu_ditolak(title):
    """Property: validate_title always raises ValueError for whitespace-only strings."""
    with pytest.raises(ValueError):
        validate_title(title)


@given(st.text(min_size=201))
@settings(max_examples=10)
def test_property_3_title_panjang_selalu_ditolak(title):
    """Property: validate_title always raises ValueError for titles longer than 200 chars."""
    with pytest.raises(ValueError):
        validate_title(title)


def test_property_3_title_tepat_200_karakter_diterima():
    validate_title("a" * 200)


@given(st.text().filter(lambda s: s not in {"pending", "in_progress", "done"}))
@settings(max_examples=10)
def test_property_8_status_tidak_valid_selalu_ditolak(status):
    """Property: validate_status always raises ValueError for any string not in the valid set."""
    with pytest.raises(ValueError):
        validate_status(status)


# --- validate_email ---

def test_validate_email_valid():
    validate_email("user@example.com")


def test_validate_email_none_raises():
    with pytest.raises(ValueError, match="Format email tidak valid"):
        validate_email(None)


def test_validate_email_empty_raises():
    with pytest.raises(ValueError, match="Format email tidak valid"):
        validate_email("")


def test_validate_email_no_at_raises():
    with pytest.raises(ValueError, match="Format email tidak valid"):
        validate_email("userexample.com")


def test_validate_email_multiple_at_raises():
    with pytest.raises(ValueError, match="Format email tidak valid"):
        validate_email("user@@example.com")


def test_validate_email_no_dot_in_domain_raises():
    with pytest.raises(ValueError, match="Format email tidak valid"):
        validate_email("user@examplecom")


def test_validate_email_with_space_raises():
    with pytest.raises(ValueError, match="Format email tidak valid"):
        validate_email("user @example.com")


# --- validate_password ---

def test_validate_password_valid():
    validate_password("password123")


def test_validate_password_exactly_8_chars():
    validate_password("12345678")


def test_validate_password_none_raises():
    with pytest.raises(ValueError, match="Password minimal 8 karakter"):
        validate_password(None)


def test_validate_password_too_short_raises():
    with pytest.raises(ValueError, match="Password minimal 8 karakter"):
        validate_password("short")


def test_validate_password_7_chars_raises():
    with pytest.raises(ValueError, match="Password minimal 8 karakter"):
        validate_password("1234567")


# --- validate_deadline ---

def test_validate_deadline_none_allowed():
    validate_deadline(None)


def test_validate_deadline_valid_date():
    validate_deadline("2024-12-31")


def test_validate_deadline_valid_datetime():
    validate_deadline("2024-12-31T23:59:59")


def test_validate_deadline_invalid_raises():
    with pytest.raises(ValueError, match="Format deadline tidak valid, gunakan ISO 8601"):
        validate_deadline("not-a-date")


def test_validate_deadline_invalid_format_raises():
    with pytest.raises(ValueError, match="Format deadline tidak valid, gunakan ISO 8601"):
        validate_deadline("31-12-2024")


# --- validate_create_payload with deadline ---

def test_validate_create_payload_with_valid_deadline():
    validate_create_payload({"title": "Task", "deadline": "2024-12-31"})


def test_validate_create_payload_with_invalid_deadline_raises():
    with pytest.raises(ValueError, match="Format deadline tidak valid, gunakan ISO 8601"):
        validate_create_payload({"title": "Task", "deadline": "bad-date"})


def test_validate_create_payload_without_deadline_key():
    validate_create_payload({"title": "Task"})


# --- validate_update_payload with deadline ---

def test_validate_update_payload_with_valid_deadline():
    validate_update_payload({"deadline": "2024-06-15T10:00:00"})


def test_validate_update_payload_with_invalid_deadline_raises():
    with pytest.raises(ValueError, match="Format deadline tidak valid, gunakan ISO 8601"):
        validate_update_payload({"deadline": "not-valid"})


def test_validate_update_payload_deadline_none_allowed():
    validate_update_payload({"deadline": None})


# --- Property-Based Tests (Task 3.3) ---

# Property 3: Email tidak valid ditolak saat registrasi
# Validates: Requirements 1.3
@given(st.one_of(
    st.text(min_size=1).filter(lambda s: "@" not in s),
    st.text(min_size=1).filter(lambda s: " " in s),
))
@settings(max_examples=10)
def test_property_3_email_tidak_valid_ditolak(email):
    """Property 3: validate_email always raises ValueError for invalid email strings."""
    with pytest.raises(ValueError):
        validate_email(email)


# Property 4: Password pendek ditolak saat registrasi
# Validates: Requirements 1.4
@given(st.text(max_size=7))
@settings(max_examples=10)
def test_property_4_password_pendek_ditolak(password):
    """Property 4: validate_password always raises ValueError for passwords shorter than 8 chars."""
    with pytest.raises(ValueError):
        validate_password(password)


# Property 13: Deadline tidak valid selalu ditolak dengan ValueError
# Validates: Requirements 4.3, 10.3
@given(st.sampled_from(["not-a-date", "31-12-2024", "2024/12/31", "hello world", "12345", "2024-13-01", "abc"]))
@settings(max_examples=10)
def test_property_13_deadline_tidak_valid_ditolak(deadline):
    """Property 13: validate_deadline always raises ValueError for invalid ISO 8601 strings."""
    with pytest.raises(ValueError):
        validate_deadline(deadline)


# --- validate_password: > 72 bytes ---

def test_validate_password_over_72_bytes_raises():
    # A string that exceeds 72 bytes when UTF-8 encoded
    long_password = "a" * 73
    with pytest.raises(ValueError, match="Password tidak boleh melebihi 72 bytes"):
        validate_password(long_password)
