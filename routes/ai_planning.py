from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.user import User, UserRole
from models.project import Project
from models.task import Task, TaskStatus, TaskPriority
from database import db
from services.ai_service import ai_service
from utils.decorators import permission_required
import json
from datetime import datetime

ai_planning_bp = Blueprint('ai_planning', __name__, url_prefix='/admin/ai-planning')

@ai_planning_bp.route('', methods=['GET'])
@login_required
@permission_required("project.manage")
def planning_index():
    projects = Project.query.all()
    users = User.query.filter_by(role=UserRole.MEMBER).all()
    return render_template('ai_planning.html', projects=projects, users=users)

@ai_planning_bp.route('/generate', methods=['POST'])
@login_required
@permission_required("project.manage")
def generate_plan():
    data = request.get_json()
    project_id = data.get('project_id')
    user_ids = data.get('user_ids', [])
    deadline = data.get('deadline')
    
    project = Project.query.get_or_404(project_id)
    team = User.query.filter(User.id.in_(user_ids)).all()
    
    team_data = [
        {"id": u.id, "name": u.name, "skills": u.skills or "General team member"}
        for u in team
    ]
    
    plan = ai_service.generate_project_plan(
        project.title, 
        project.description, 
        team_data, 
        deadline
    )
    
    if isinstance(plan, dict) and "error" in plan:
        return jsonify(plan), 500
        
    return jsonify({"project_id": project_id, "tasks": plan})

@ai_planning_bp.route('/save', methods=['POST'])
@login_required
@permission_required("project.manage")
def save_plan():
    data = request.get_json()
    project_id = data.get('project_id')
    tasks_data = data.get('tasks', [])
    
    project = Project.query.get_or_404(project_id)
    
    try:
        for t_data in tasks_data:
            # Map priority string to Enum
            priority_str = t_data.get('priority', 'Medium').capitalize()
            try:
                priority = TaskPriority(priority_str)
            except ValueError:
                priority = TaskPriority.MEDIUM
            
            due_date = None
            if t_data.get('due_date'):
                try:
                    due_date = datetime.strptime(t_data['due_date'], '%Y-%m-%d')
                except ValueError:
                    pass

            task = Task(
                title=t_data.get('title'),
                description=t_data.get('description'),
                status=TaskStatus.TODO,
                priority=priority,
                project_id=project_id,
                assigned_to=t_data.get('assigned_to'),
                estimate_hours=t_data.get('estimate_hours'),
                due_date=due_date
            )
            db.session.add(task)
        
        db.session.commit()
        return jsonify({"success": True, "message": f"Successfully created {len(tasks_data)} tasks."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
