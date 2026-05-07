from sqlalchemy import func
from database import db
from models.task import Task, TaskStatus
from models.project import Project
from models.user import User


def workspace_metrics(user=None):
    base_query = Task.query
    if user and not user.is_admin():
        base_query = base_query.filter(Task.assigned_to == user.id)

    total_tasks = base_query.count()
    completed = base_query.filter(Task.status == TaskStatus.COMPLETED).count()
    pending = base_query.filter(Task.status != TaskStatus.COMPLETED).count()
    overdue = base_query.filter(Task.status != TaskStatus.COMPLETED, Task.due_date.isnot(None), Task.due_date < func.now()).count()

    throughput = (
        db.session.query(func.date(Task.completed_at), func.count(Task.id))
        .filter(Task.completed_at.isnot(None))
        .group_by(func.date(Task.completed_at))
        .order_by(func.date(Task.completed_at).desc())
        .limit(7)
        .all()
    )
    throughput = [{"date": str(row[0]), "count": row[1]} for row in throughput]

    recent_tasks = base_query.order_by(Task.updated_at.desc()).limit(6).all()

    workload_query = (
        db.session.query(User.id, User.name, func.count(Task.id))
        .join(Task, Task.assigned_to == User.id)
    )
    if user and not user.is_admin():
        workload_query = workload_query.filter(User.id == user.id)
    workload_query = (
        workload_query
        .group_by(User.id, User.name)
        .order_by(func.count(Task.id).desc())
    )
    if not user or user.is_admin():
        workload_query = workload_query.limit(6)
    workload = [{"id": row[0], "name": row[1], "count": row[2]} for row in workload_query.all()]

    return {
        "project_count": Project.query.count(),
        "task_count": total_tasks,
        "completed_count": completed,
        "pending_count": pending,
        "overdue_count": overdue,
        "completion_rate": round((completed / total_tasks) * 100, 2) if total_tasks else 0,
        "throughput": throughput,
        "workload": workload,
        "recent_tasks": recent_tasks,
    }
