from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.task import Task, TaskStatus, TaskPriority
from models.project import Project
from models.user import User, UserRole
from database import db
from datetime import datetime
from utils.decorators import admin_required, can_update_status, permission_required
from services.task_service import transition_task, add_comment, query_tasks

task_bp = Blueprint('task', __name__)

@task_bp.route('/tasks')
@login_required
def tasks():
    filters = {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", "").strip(),
        "project_id": request.args.get("project_id", "").strip(),
        "assignee_id": request.args.get("assignee_id", "").strip(),
    }
    query = query_tasks(filters)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Task.assigned_to == current_user.id)
    all_tasks = query.order_by(Task.updated_at.desc()).all()
        
    projects = Project.query.all()
    users = User.query.all()

    return render_template(
        'tasks.html',
        tasks=all_tasks,
        projects=projects,
        users=users,
        TaskStatus=TaskStatus,
        TaskPriority=TaskPriority,
        now=datetime.utcnow(),
        active_filters=filters,
    )

@task_bp.route('/tasks/create', methods=['POST'])
@login_required
@permission_required("task.create")
def create_task():
    title = request.form.get('title')
    description = request.form.get('description')
    project_id = request.form.get('project_id')
    due_date_str = request.form.get('due_date')
    status_str = request.form.get('status', 'Todo')
    priority_str = request.form.get('priority', 'Medium')
    assigned_to = request.form.get('assigned_to')
    estimate_hours = request.form.get('estimate_hours')
    story_points = request.form.get('story_points')
    
    if not title or not project_id:
        flash('Title and Project are required.', 'error')
        return redirect(url_for('task.tasks'))

    due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
    
    task = Task(
        title=title,
        description=description,
        project_id=project_id,
        due_date=due_date,
        status=TaskStatus(status_str),
        priority=TaskPriority(priority_str),
        assigned_to=int(assigned_to) if assigned_to and assigned_to != 'None' else None,
        estimate_hours=float(estimate_hours) if estimate_hours else None,
        story_points=int(story_points) if story_points else None
    )
    if task.assigned_to:
        task.watchers.append(User.query.get(task.assigned_to))
    db.session.add(task)
    db.session.commit()
    
    flash('Task created and assigned successfully!', 'success')
    next_url = request.form.get('next') or url_for('task.tasks')
    return redirect(next_url)

@task_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required("task.edit")
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.project_id = request.form.get('project_id')
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        task.status = TaskStatus(request.form.get('status'))
        task.priority = TaskPriority(request.form.get('priority'))
        assigned_to = request.form.get('assigned_to')
        task.assigned_to = int(assigned_to) if assigned_to and assigned_to != 'None' else None
        estimate_hours = request.form.get('estimate_hours')
        story_points = request.form.get('story_points')
        task.estimate_hours = float(estimate_hours) if estimate_hours else None
        task.story_points = int(story_points) if story_points else None
        
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('task.tasks'))
    
    projects = Project.query.all()
    users = User.query.all()
    return render_template('edit_task.html', task=task, projects=projects, users=users, TaskStatus=TaskStatus, TaskPriority=TaskPriority)

@task_bp.route('/tasks/<int:task_id>/update-status', methods=['POST'])
@login_required
@can_update_status
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    new_status = request.form.get('status')
    if new_status:
        target = TaskStatus(new_status)
        if transition_task(task, current_user.id, target):
            db.session.commit()
            flash('Status updated!', 'success')
        else:
            flash('Invalid transition or task is blocked by dependencies.', 'error')
    
    next_url = request.form.get('next') or url_for('task.tasks')
    return redirect(next_url)


@task_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
@permission_required("task.delete")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully!', 'success')
    next_url = request.form.get('next') or url_for('task.tasks')
    return redirect(next_url)


@task_bp.route('/tasks/<int:task_id>/comment', methods=['POST'])
@login_required
@permission_required("task.comment")
def comment_task(task_id):
    task = Task.query.get_or_404(task_id)
    body = request.form.get("body", "").strip()
    if not body:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("task.tasks"))
    add_comment(task, current_user.id, body)
    db.session.commit()
    flash("Comment added.", "success")
    return redirect(url_for("task.tasks"))


@task_bp.route('/tasks/<int:task_id>/watch', methods=['POST'])
@login_required
@permission_required("task.watch")
def watch_task(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user not in task.watchers:
        task.watchers.append(current_user)
        db.session.commit()
    flash("You are now watching this task.", "success")
    return redirect(url_for("task.tasks"))


@task_bp.route('/tasks/<int:task_id>/dependency', methods=['POST'])
@login_required
@permission_required("task.dependency.manage")
def add_dependency(task_id):
    task = Task.query.get_or_404(task_id)
    depends_on_id = request.form.get("depends_on_id")
    if not depends_on_id:
        flash("Dependency task is required.", "error")
        return redirect(url_for("task.tasks"))
    dependency = Task.query.get_or_404(int(depends_on_id))
    if dependency.id == task.id:
        flash("Task cannot depend on itself.", "error")
        return redirect(url_for("task.tasks"))
    if dependency not in task.dependencies:
        task.dependencies.append(dependency)
        db.session.commit()
    flash("Dependency added.", "success")
    return redirect(url_for("task.tasks"))


