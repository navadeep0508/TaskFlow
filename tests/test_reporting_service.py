from app import app
from database import db
from models.user import User, UserRole
from models.project import Project
from models.task import Task, TaskStatus, TaskPriority
from services.reporting_service import workspace_metrics


def test_workspace_metrics_workload_non_admin_no_limit_filter_error():
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(name="Admin", email="admin@test.local", role=UserRole.ADMIN)
        admin.set_password("admin12345")
        member = User(name="Member", email="member@test.local", role=UserRole.MEMBER)
        member.set_password("member12345")
        db.session.add_all([admin, member])
        db.session.commit()

        project = Project(title="P1", description="x", created_by=admin.id)
        db.session.add(project)
        db.session.commit()

        db.session.add_all(
            [
                Task(
                    title="A1",
                    project_id=project.id,
                    assigned_to=member.id,
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                ),
                Task(
                    title="A2",
                    project_id=project.id,
                    assigned_to=member.id,
                    status=TaskStatus.IN_PROGRESS,
                    priority=TaskPriority.MEDIUM,
                ),
                Task(
                    title="B1",
                    project_id=project.id,
                    assigned_to=admin.id,
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                ),
            ]
        )
        db.session.commit()

        metrics = workspace_metrics(member)

        assert "workload" in metrics
        assert len(metrics["workload"]) == 1
        assert metrics["workload"][0]["id"] == member.id
