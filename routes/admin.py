from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from database import db
from models.user import UserRole, RolePermission, DEFAULT_ROLE_PERMISSIONS
from models.governance import AuditLog
from utils.decorators import permission_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/permissions", methods=["GET", "POST"])
@login_required
@permission_required("admin.permissions.manage")
def permissions():
    if request.method == "POST":
        role = request.form.get("role", "").strip()
        permission = request.form.get("permission", "").strip()
        if not role or not permission:
            flash("Role and permission are required.", "error")
            return redirect(url_for("admin.permissions"))

        existing = RolePermission.query.filter_by(role=role, permission=permission).first()
        if not existing:
            db.session.add(RolePermission(role=role, permission=permission))
            db.session.add(AuditLog(actor_id=current_user.id, entity_type="permission", action="permission.grant", details=f"{role}:{permission}"))
            db.session.commit()
            flash("Permission granted.", "success")
        else:
            flash("Permission already exists.", "warning")

    role_permissions = {}
    for role in UserRole:
        dynamic = [rp.permission for rp in RolePermission.query.filter_by(role=role.value).all()]
        role_permissions[role.value] = sorted(set(DEFAULT_ROLE_PERMISSIONS.get(role.value, set())).union(dynamic))
    return render_template("admin_permissions.html", role_permissions=role_permissions)


@admin_bp.route("/admin/audit-logs")
@login_required
@permission_required("audit.view")
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("audit_logs.html", logs=logs)
