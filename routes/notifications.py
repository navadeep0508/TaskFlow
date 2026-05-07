from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from database import db
from models.governance import Notification

notification_bp = Blueprint("notification", __name__)


@notification_bp.route("/notifications")
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", notifications=notifications)


@notification_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("notification.list_notifications"))
