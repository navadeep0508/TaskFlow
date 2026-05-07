from datetime import datetime
from database import db
import enum


class TaskStatus(enum.Enum):
    BACKLOG = 'Backlog'
    TODO = 'Todo'
    IN_PROGRESS = 'In Progress'
    BLOCKED = 'Blocked'
    REVIEW = 'Review'
    COMPLETED = 'Completed'


class TaskPriority(enum.Enum):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'


task_watchers = db.Table(
    'task_watchers',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False),
)


task_dependencies = db.Table(
    'task_dependencies',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('depends_on_task_id', db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False),
)


class TaskLabel(db.Model):
    __tablename__ = 'task_labels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class TaskComment(db.Model):
    __tablename__ = 'task_comments'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    task = db.relationship('Task', back_populates='comments')
    author = db.relationship('User', lazy=True)


class TaskActivity(db.Model):
    __tablename__ = 'task_activities'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    task = db.relationship('Task', back_populates='activities')
    actor = db.relationship('User', lazy=True)


class TaskAttachment(db.Model):
    __tablename__ = 'task_attachments'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    task = db.relationship('Task', back_populates='attachments')
    uploader = db.relationship('User', lazy=True)


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority = db.Column(db.Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    estimate_hours = db.Column(db.Float, nullable=True)
    story_points = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    assignee = db.relationship('User', back_populates='assigned_tasks')
    project = db.relationship('Project', back_populates='tasks')
    labels = db.relationship('TaskLabel', secondary='task_label_links', lazy='joined')
    watchers = db.relationship('User', secondary=task_watchers, lazy='subquery')
    dependencies = db.relationship(
        'Task',
        secondary=task_dependencies,
        primaryjoin=id == task_dependencies.c.task_id,
        secondaryjoin=id == task_dependencies.c.depends_on_task_id,
        lazy='subquery'
    )
    blocked_by = db.relationship(
        'Task',
        secondary=task_dependencies,
        primaryjoin=id == task_dependencies.c.depends_on_task_id,
        secondaryjoin=id == task_dependencies.c.task_id,
        lazy='subquery',
        overlaps="dependencies"
    )
    comments = db.relationship('TaskComment', back_populates='task', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('TaskActivity', back_populates='task', lazy=True, cascade='all, delete-orphan')
    attachments = db.relationship('TaskAttachment', back_populates='task', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_overdue(self):
        if self.status.value == 'Completed' or not self.due_date:
            return False
        return self.due_date < datetime.utcnow()

    @property
    def is_blocked(self):
        return any(dep.status != TaskStatus.COMPLETED for dep in self.dependencies)

    @property
    def cycle_time_hours(self):
        if not self.start_date or not self.completed_at:
            return None
        delta = self.completed_at - self.start_date
        return round(delta.total_seconds() / 3600, 2)

    def __repr__(self):
        return f'<Task {self.title} ({self.status.value})>'


class TaskLabelLink(db.Model):
    __tablename__ = 'task_label_links'

    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey('task_labels.id', ondelete='CASCADE'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

