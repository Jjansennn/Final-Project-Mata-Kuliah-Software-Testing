"""Blueprint autentikasi: /auth/register dan /auth/login."""
import logging

from flask import Blueprint, jsonify, request

from app.auth_service import AuthError, ConflictError, login_user, register_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body harus berupa JSON valid"}), 400

    email = data.get("email")
    password = data.get("password")

    try:
        user = register_user(email, password)
        return jsonify(user), 201
    except ConflictError as e:
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error registering user: %s", e, exc_info=True)
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body harus berupa JSON valid"}), 400

    email = data.get("email")
    password = data.get("password")

    try:
        token = login_user(email, password)
        return jsonify({"token": token}), 200
    except AuthError as e:
        return jsonify({"error": str(e)}), 401
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error logging in user: %s", e, exc_info=True)
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500
