import os
import functools
from datetime import datetime, timezone
import bcrypt
import jwt
from flask import request, jsonify, g
from app.models import insert_user, fetch_user_by_email
from app.validators import validate_email, validate_password

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")


class ConflictError(Exception):
    pass


class AuthError(Exception):
    pass


def register_user(email: str, password: str) -> dict:
    validate_email(email)
    validate_password(password)

    if fetch_user_by_email(email):
        raise ConflictError("Email sudah terdaftar")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    password_hash_str = password_hash.decode()

    created_at = datetime.now(timezone.utc)
    created_at_str = created_at.isoformat()

    user_id = insert_user(email, password_hash_str, created_at_str)

    return {"id": user_id, "email": email, "created_at": created_at_str}


def login_user(email: str, password: str) -> str:
    user = fetch_user_by_email(email)
    if not user:
        raise AuthError("Email atau password salah")

    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        raise AuthError("Email atau password salah")

    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "iat": now_ts,
        "exp": now_ts + 86400,
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token


def jwt_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token autentikasi diperlukan"}), 401

        token = auth_header[len("Bearer "):]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token tidak valid atau sudah kedaluwarsa"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token tidak valid atau sudah kedaluwarsa"}), 401

        g.current_user_id = payload["user_id"]
        return f(*args, **kwargs)

    return decorated
