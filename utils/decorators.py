from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from models.user import UserRole
from models.task import Task
from models.project import Project


def permission_required(permission):
    def outer(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login first.', 'error')
                return redirect(url_for('auth.login'))
            if not current_user.has_permission(permission):
                flash('Permission denied.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return outer


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def can_manage_task(f):
    @wraps(f)
    def decorated_function(task_id, *args, **kwargs):
        task = Task.query.get_or_404(task_id)
        # Admins can manage all, Members can only manage if they own the project (not just assigned)
        # Based on requirement "Admin can manage all tasks", members only "update status"
        if current_user.role == UserRole.ADMIN or current_user.has_permission("task.edit"):
            return f(task_id, *args, **kwargs)
        
        flash('You do not have permission to modify this task.', 'error')
        return redirect(url_for('task.tasks'))
    return decorated_function

def can_update_status(f):
    @wraps(f)
    def decorated_function(task_id, *args, **kwargs):
        task = Task.query.get_or_404(task_id)
        # Admin OR assigned user OR project owner can update status
        if current_user.role == UserRole.ADMIN or \
           task.assigned_to == current_user.id or \
           task.project.created_by == current_user.id or \
           current_user.has_permission("task.transition"):
            return f(task_id, *args, **kwargs)
        
        flash('Permission denied.', 'error')
        return redirect(url_for('task.tasks'))
    return decorated_function

