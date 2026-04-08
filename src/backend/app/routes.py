import logging

from flask import Blueprint, jsonify, request, g

from app.models import TaskNotFoundError
from app import services as task_service
from app.auth_service import jwt_required

logger = logging.getLogger(__name__)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.route("", methods=["POST"])
@jwt_required
def create_task():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body harus berupa JSON valid"}), 400
    try:
        task = task_service.create_task(
            title=data.get("title"),
            description=data.get("description"),
            deadline=data.get("deadline"),
            user_id=g.current_user_id,
        )
        return jsonify(task), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error creating task: %s", e, exc_info=True)
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500


@tasks_bp.route("", methods=["GET"])
@jwt_required
def get_all_tasks():
    try:
        tasks = task_service.get_all_tasks(user_id=g.current_user_id)
        return jsonify(tasks), 200
    except Exception as e:
        logger.error("Error fetching tasks: %s", e, exc_info=True)
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required
def get_task(task_id):
    try:
        task = task_service.get_task_by_id(task_id, user_id=g.current_user_id)
        return jsonify(task), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except TaskNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error("Error fetching task %s: %s", task_id, e, exc_info=True)
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required
def update_task(task_id):
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body harus berupa JSON valid"}), 400
    try:
        task = task_service.update_task(task_id, data, user_id=g.current_user_id)
        return jsonify(task), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except TaskNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error("Error updating task %s: %s", task_id, e, exc_info=True)
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required
def delete_task(task_id):
    try:
        task_service.delete_task(task_id, user_id=g.current_user_id)
        return jsonify({"message": "Task berhasil dihapus"}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except TaskNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error("Error deleting task %s: %s", task_id, e, exc_info=True)
        return jsonify({"error": "Terjadi kesalahan internal pada server"}), 500
