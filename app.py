from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv
import os
from sqlalchemy.engine.url import make_url
from database import db
from models.user import User, UserRole, RolePermission, DEFAULT_ROLE_PERMISSIONS
from models.project import Project
from models.task import Task, TaskStatus, TaskPriority
from models.governance import Notification

from routes.auth import auth_bp
from routes.project import project_bp
from routes.task import task_bp
from routes.admin import admin_bp
from routes.notifications import notification_bp
from routes.api_tasks import api_task_bp
from routes.ai_planning import ai_planning_bp
from services.reporting_service import workspace_metrics

load_dotenv()

app = Flask(__name__)

def _normalize_database_url(raw: str) -> str:
    # Supabase requires SSL; adding this here avoids confusing runtime errors later.
    # (Does not affect local Postgres.)
    url = make_url(raw)
    if url.drivername.startswith("postgres") and url.host and url.host.endswith(".supabase.co"):
        q = dict(url.query or {})
        q.setdefault("sslmode", "require")
        url = url.set(query=q)
    return str(url)


def _choose_database_uri() -> str:
    raw = os.getenv("DATABASE_URL")
    if not raw:
        return "sqlite:///taskflow.db"

    normalized = _normalize_database_url(raw)
    try:
        make_url(normalized)
    except Exception:
        return "sqlite:///taskflow.db"

    return normalized


def _ensure_admin_user() -> None:
    admin_email = "admin@taskflow.com"
    admin_password = "admin123"
    admin_name = "System Administrator"

    if not admin_email or not admin_password:
        return

    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        needs_commit = False
        if existing_admin.role != UserRole.ADMIN:
            existing_admin.role = UserRole.ADMIN
            needs_commit = True
        
        # Always ensure the password matches the hardcoded one
        existing_admin.set_password(admin_password)
        needs_commit = True
        
        if needs_commit:
            db.session.commit()
        return

    admin_user = User(name=admin_name or "Administrator", email=admin_email, role=UserRole.ADMIN)
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.commit()


def _ensure_role_permissions() -> None:
    for role, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        for permission in permissions:
            exists = RolePermission.query.filter_by(role=role, permission=permission).first()
            if not exists:
                db.session.add(RolePermission(role=role, permission=permission))
    db.session.commit()


app.config['SQLALCHEMY_DATABASE_URI'] = _choose_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(project_bp)
app.register_blueprint(task_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(api_task_bp)
app.register_blueprint(ai_planning_bp)

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('splash.html')


@app.route('/landing')
def landing():
    from datetime import datetime
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html', current_year=datetime.utcnow().year)


@app.route('/dashboard')
def dashboard():
    from flask_login import current_user
    from datetime import datetime

    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    metrics = workspace_metrics(current_user)
    return render_template('dashboard.html', now=datetime.utcnow(), **metrics)


@app.context_processor
def inject_notification_count():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return {"unread_notifications_count": 0}
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return {"unread_notifications_count": unread_count}


with app.app_context():
    _ensure_admin_user()
    _ensure_role_permissions()


@app.route('/test')
def test_route():
    return "Test"


if __name__ == '__main__':
    app.run(debug=True)
