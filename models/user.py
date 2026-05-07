from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import db
import enum


class UserRole(enum.Enum):
    ADMIN = 'admin'
    MEMBER = 'member'


DEFAULT_ROLE_PERMISSIONS = {
    UserRole.ADMIN.value: {
        "task.create",
        "task.edit",
        "task.delete",
        "task.assign",
        "task.transition",
        "task.comment",
        "task.dependency.manage",
        "task.watch",
        "project.manage",
        "report.view",
        "api.access",
        "admin.permissions.manage",
        "audit.view",
    },
    UserRole.MEMBER.value: {
        "task.transition",
        "task.comment",
        "task.watch",
        "api.access",
    },
}


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False, index=True)
    permission = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('role', 'permission', name='uq_role_permission'),
    )

    def __repr__(self):
        return f'<RolePermission {self.role}:{self.permission}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    skills = db.Column(db.Text, nullable=True)  # Comma-separated skills or free text
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    projects = db.relationship('Project', back_populates='creator', lazy=True, cascade='all, delete-orphan')
    assigned_tasks = db.relationship('Task', back_populates='assignee', lazy=True)
    
    def set_password(self, password):
        if not password or len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def role_value(self):
        return self.role.value if self.role else UserRole.MEMBER.value

    def has_permission(self, permission: str) -> bool:
        if self.is_admin():
            return True

        role = self.role_value
        default_permissions = DEFAULT_ROLE_PERMISSIONS.get(role, set())
        if permission in default_permissions:
            return True

        exists = RolePermission.query.filter_by(role=role, permission=permission).first()
        return exists is not None
    
    def __repr__(self):
        return f'<User {self.name} ({self.email})>'
