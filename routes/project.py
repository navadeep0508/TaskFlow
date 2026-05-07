from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.project import Project
from models.user import User, UserRole
from database import db
from utils.decorators import admin_required, permission_required

project_bp = Blueprint('project', __name__)

@project_bp.route('/projects/<int:project_id>')
@login_required
@permission_required("project.manage")
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    all_users = User.query.all()
    from models.task import TaskStatus, TaskPriority
    return render_template('project_details.html', 
                         project=project, 
                         users=all_users,
                         TaskStatus=TaskStatus,
                         TaskPriority=TaskPriority)

@project_bp.route('/projects')
@login_required
@permission_required("project.manage")
def projects():
    all_projects = Project.query.all()
    return render_template('projects.html', projects=all_projects)

@project_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
@permission_required("project.manage")
def create_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Title is required.', 'error')
            return redirect(url_for('project.projects'))

        project = Project(title=title, description=description, created_by=current_user.id)
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('project.projects'))
    
    return redirect(url_for('project.projects'))

@project_bp.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
@permission_required("project.manage")
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        
        if not project.title:
            flash('Title is required.', 'error')
            return redirect(url_for('project.projects'))
            
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('project.projects'))
    
    return render_template('edit_project.html', project=project)

@project_bp.route('/projects/delete/<int:project_id>', methods=['POST'])
@login_required
@permission_required("project.manage")
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('project.projects'))

