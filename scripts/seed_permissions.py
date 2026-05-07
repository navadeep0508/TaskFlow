from app import app
from database import db
from models.user import RolePermission, DEFAULT_ROLE_PERMISSIONS


def run():
    with app.app_context():
        added = 0
        for role, permissions in DEFAULT_ROLE_PERMISSIONS.items():
            for permission in permissions:
                existing = RolePermission.query.filter_by(role=role, permission=permission).first()
                if not existing:
                    db.session.add(RolePermission(role=role, permission=permission))
                    added += 1
        db.session.commit()
        print(f"Seed complete. Added {added} permission rows.")


if __name__ == "__main__":
    run()
