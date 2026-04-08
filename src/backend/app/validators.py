from datetime import datetime

VALID_STATUSES = {"pending", "in_progress", "done"}


def validate_title(title) -> None:
    """Validate task title. Raises ValueError on invalid input."""
    if title is None or str(title).strip() == "":
        raise ValueError("title wajib diisi dan tidak boleh kosong")
    if len(title) > 200:
        raise ValueError("title tidak boleh melebihi 200 karakter")


def validate_status(status) -> None:
    """Validate task status. Raises ValueError on invalid input."""
    if status not in VALID_STATUSES:
        raise ValueError("status tidak valid")


def validate_email(email) -> None:
    """Validate email format. Raises ValueError on invalid input."""
    if email is None or str(email).strip() == "":
        raise ValueError("Format email tidak valid")
    email_str = str(email)
    if " " in email_str:
        raise ValueError("Format email tidak valid")
    parts = email_str.split("@")
    if len(parts) != 2:
        raise ValueError("Format email tidak valid")
    domain = parts[1]
    if "." not in domain:
        raise ValueError("Format email tidak valid")


def validate_password(password) -> None:
    """Validate password length. Raises ValueError if too short or too long for bcrypt."""
    if password is None or len(password) < 8:
        raise ValueError("Password minimal 8 karakter")
    # bcrypt silently truncates at 72 bytes — reject passwords that exceed this
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password tidak boleh melebihi 72 bytes")


def validate_deadline(deadline) -> None:
    """Validate ISO 8601 deadline string. None is allowed."""
    if deadline is None:
        return
    try:
        datetime.fromisoformat(str(deadline))
    except (ValueError, TypeError):
        raise ValueError("Format deadline tidak valid, gunakan ISO 8601")


def validate_create_payload(data: dict) -> None:
    """Validate payload for task creation."""
    validate_title(data.get("title"))
    if "deadline" in data:
        validate_deadline(data.get("deadline"))


def validate_update_payload(data: dict) -> None:
    """Validate payload for task update (partial)."""
    if "title" in data:
        validate_title(data["title"])
    if "status" in data:
        validate_status(data["status"])
    if "deadline" in data:
        validate_deadline(data.get("deadline"))
