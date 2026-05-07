from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            print("Attempting to add 'skills' column to 'users' table...")
            db.session.execute(text('ALTER TABLE users ADD COLUMN skills TEXT'))
            db.session.commit()
            print("Migration successful: Added 'skills' column.")
        except Exception as e:
            db.session.rollback()
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'skills' already exists. No action needed.")
            else:
                print(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    migrate()
