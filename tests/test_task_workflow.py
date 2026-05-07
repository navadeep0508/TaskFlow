from app import app
from database import db
from models.user import User, UserRole
from models.project import Project
from models.task import Task, TaskStatus, TaskPriority
from services.task_service import can_transition


def test_blocked_dependency_prevents_completion():
    with app.app_context():
        db.drop_all()
        db.create_all()

        owner = User(name="Admin", email="admin@test.local", role=UserRole.ADMIN)
        owner.set_password("admin12345")
        db.session.add(owner)
        db.session.commit()

        project = Project(title="P1", description="x", created_by=owner.id)
        db.session.add(project)
        db.session.commit()

        dep = Task(title="Dependency", project_id=project.id, status=TaskStatus.TODO, priority=TaskPriority.MEDIUM)
        task = Task(title="Main", project_id=project.id, status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM)
        task.dependencies.append(dep)
        db.session.add_all([dep, task])
        db.session.commit()

        assert can_transition(task, TaskStatus.COMPLETED) is False
