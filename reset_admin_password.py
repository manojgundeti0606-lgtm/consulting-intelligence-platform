import sqlite3
import hashlib
import secrets

def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}", salt

def reset_admin():
    db_path = "cip_database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    username = "admin"
    new_password = "Admin@123"
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    
    password_hash, _ = hash_password(new_password)
    
    if row:
        print(f"Updating password for user '{username}'...")
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
        print("Password updated successfully.")
    else:
        print(f"Creating new admin user '{username}'...")
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, is_active, auth_method)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, "admin@cip.local", password_hash, True, True, 'local'))
        print("Admin user created successfully.")

    conn.commit()
    conn.close()
    
    print(f"\nAdmin Credentials:")
    print(f"Username: {username}")
    print(f"Password: {new_password}")

if __name__ == "__main__":
    reset_admin()
