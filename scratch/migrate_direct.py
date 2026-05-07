import sqlite3
import os

db_path = "instance/taskflow.db"
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"Attempting to add 'skills' column to 'users' table in {db_path}...")
        cursor.execute("ALTER TABLE users ADD COLUMN skills TEXT")
        conn.commit()
        conn.close()
        print("Success: Column 'skills' added.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'skills' already exists.")
        else:
            print(f"OperationalError: {e}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database file {db_path} not found.")
