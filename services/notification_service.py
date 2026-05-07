from database import db
from models.governance import Notification
from services.task_service import due_soon_tasks


def enqueue_due_soon_notifications(hours: int = 24) -> int:
    queued = 0
    for task in due_soon_tasks(hours=hours):
        recipients = list(task.watchers)
        if task.assignee and task.assignee not in recipients:
            recipients.append(task.assignee)
        for user in recipients:
            exists = Notification.query.filter_by(
                user_id=user.id,
                source_type="task_due_soon",
                source_id=task.id,
                is_read=False,
            ).first()
            if exists:
                continue
            db.session.add(
                Notification(
                    user_id=user.id,
                    title=f"Task due soon: {task.title}",
                    message=f"Task #{task.id} is due soon. Please review before deadline.",
                    source_type="task_due_soon",
                    source_id=task.id,
                )
            )
            queued += 1
    if queued:
        db.session.commit()
    return queued
