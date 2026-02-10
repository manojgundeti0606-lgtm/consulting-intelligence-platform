from auth import AuthManager

def create_backup_admin():
    print("Initializing AuthManager...")
    auth = AuthManager()
    
    username = "admin2"
    email = "admin2@cip.local"
    password = "Admin@123"
    
    print(f"Creating user {username}...")
    result = auth.register_user(username, email, password)
    print(f"Registration result: {result}")
    
    if result.get("success") or "already exists" in str(result.get("error")):
        conn = auth.get_connection()
        cursor = conn.cursor()
        
        # Get user ID
        placeholder = "%s" if auth.db_type == 'postgres' else "?"
        cursor.execute(f"SELECT id FROM users WHERE username = {placeholder}", (username,))
        row = cursor.fetchone()
        
        if row:
            if isinstance(row, dict):
                user_id = row['id']
            else:
                user_id = row[0]
            
            print(f"Granting admin status to user ID {user_id}...")
            auth.set_admin_status(user_id, True)
            print("✅ Backup admin created/updated successfully")
            print(f"Username: {username}")
            print(f"Password: {password}")
        
    conn.close()

if __name__ == "__main__":
    create_backup_admin()
