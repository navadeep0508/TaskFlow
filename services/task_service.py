from datetime import datetime, timedelta
from sqlalchemy import or_
from database import db
from models.task import Task, TaskStatus, TaskPriority, TaskActivity, TaskComment
from models.governance import Notification, AuditLog


ALLOWED_TRANSITIONS = {
    TaskStatus.BACKLOG: {TaskStatus.TODO, TaskStatus.IN_PROGRESS},
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
    TaskStatus.IN_PROGRESS: {TaskStatus.BLOCKED, TaskStatus.REVIEW, TaskStatus.COMPLETED},
    TaskStatus.BLOCKED: {TaskStatus.TODO, TaskStatus.IN_PROGRESS},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED},
    TaskStatus.COMPLETED: set(),
}


def can_transition(task: Task, target_status: TaskStatus) -> bool:
    if target_status == task.status:
        return True
    allowed = ALLOWED_TRANSITIONS.get(task.status, set())
    if target_status not in allowed:
        return False
    if target_status == TaskStatus.COMPLETED and task.is_blocked:
        return False
    return True


def transition_task(task: Task, actor_id: int, target_status: TaskStatus) -> bool:
    if not can_transition(task, target_status):
        return False

    previous = task.status
    task.status = target_status
    if target_status == TaskStatus.IN_PROGRESS and not task.start_date:
        task.start_date = datetime.utcnow()
    if target_status == TaskStatus.COMPLETED:
        task.completed_at = datetime.utcnow()

    details = f"{previous.value} -> {target_status.value}"
    task.activities.append(TaskActivity(actor_id=actor_id, action="status_changed", details=details))
    db.session.add(AuditLog(actor_id=actor_id, entity_type="task", entity_id=task.id, action="task.transition", details=details))

    for watcher in task.watchers:
        if watcher.id == actor_id:
            continue
        db.session.add(
            Notification(
                user_id=watcher.id,
                title=f"Task status changed: {task.title}",
                message=f"Status changed from {previous.value} to {target_status.value}.",
                source_type="task",
                source_id=task.id,
            )
        )
    return True


def add_comment(task: Task, actor_id: int, body: str) -> TaskComment:
    comment = TaskComment(task_id=task.id, author_id=actor_id, body=body)
    db.session.add(comment)
    task.activities.append(TaskActivity(actor_id=actor_id, action="comment_added", details=body[:120]))
    db.session.add(AuditLog(actor_id=actor_id, entity_type="task", entity_id=task.id, action="task.comment", details=body[:200]))
    return comment


def due_soon_tasks(hours: int = 24):
    now = datetime.utcnow()
    upper = now + timedelta(hours=hours)
    return Task.query.filter(
        Task.due_date.isnot(None),
        Task.status != TaskStatus.COMPLETED,
        Task.due_date >= now,
        Task.due_date <= upper,
    ).all()


def query_tasks(filters: dict):
    query = Task.query
    if filters.get("q"):
        term = f"%{filters['q']}%"
        query = query.filter(or_(Task.title.ilike(term), Task.description.ilike(term)))
    if filters.get("status"):
        query = query.filter(Task.status == TaskStatus(filters["status"]))
    if filters.get("project_id"):
        query = query.filter(Task.project_id == int(filters["project_id"]))
    if filters.get("assignee_id"):
        query = query.filter(Task.assigned_to == int(filters["assignee_id"]))
    if filters.get("priority"):
        query = query.filter(Task.priority == TaskPriority(filters["priority"]))
    return query
