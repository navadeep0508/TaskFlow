from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from database import db
from models.task import Task, TaskStatus, TaskPriority
from models.governance import Notification
from services.task_service import query_tasks, transition_task
from utils.decorators import permission_required

api_task_bp = Blueprint("api_task", __name__, url_prefix="/api/tasks")


def _serialize_task(task: Task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "project_id": task.project_id,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "story_points": task.story_points,
        "estimate_hours": task.estimate_hours,
        "watchers": [u.id for u in task.watchers],
        "dependencies": [dep.id for dep in task.dependencies],
    }


@api_task_bp.route("", methods=["GET"])
@login_required
@permission_required("api.access")
def list_tasks():
    filters = {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", "").strip(),
        "project_id": request.args.get("project_id", "").strip(),
        "assignee_id": request.args.get("assignee_id", "").strip(),
        "priority": request.args.get("priority", "").strip(),
    }
    page = max(1, request.args.get("page", default=1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", default=20, type=int)))
    sort_by = request.args.get("sort_by", default="updated_at")
    order = request.args.get("order", default="desc")

    query = query_tasks(filters)
    if current_user.role.value != "admin":
        query = query.filter(Task.assigned_to == current_user.id)
    sort_attr = getattr(Task, sort_by, Task.updated_at)
    if order == "asc":
        query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(sort_attr.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [_serialize_task(task) for task in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@api_task_bp.route("/<int:task_id>/transition", methods=["POST"])
@login_required
@permission_required("task.transition")
def transition(task_id):
    task = Task.query.get_or_404(task_id)
    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status")
    if not new_status:
        return jsonify({"error": "status is required"}), 400
    try:
        target = TaskStatus(new_status)
    except ValueError:
        return jsonify({"error": "invalid status"}), 400

    if not transition_task(task, current_user.id, target):
        return jsonify({"error": "invalid transition"}), 400
    db.session.commit()
    return jsonify(_serialize_task(task))


@api_task_bp.route("/notifications", methods=["GET"])
@login_required
@permission_required("api.access")
def list_notifications():
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify(
        [
            {
                "id": item.id,
                "title": item.title,
                "message": item.message,
                "is_read": item.is_read,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ]
    )


@api_task_bp.route("/notifications/<int:notification_id>/ack", methods=["POST"])
@login_required
@permission_required("api.access")
def ack_notification(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True})
