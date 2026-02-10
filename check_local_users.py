import sqlite3
import os

db_path = "cip_database.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, email, is_admin FROM users")
        users = cursor.fetchall()
        print("Users in cip_database.db:")
        for user in users:
            print(f"- {user[0]} ({user[1]}), Admin: {bool(user[2])}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"File {db_path} not found.")
