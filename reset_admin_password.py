from auth import AuthManager, hash_password

def reset_admin():
    print("Initializing AuthManager...")
    auth = AuthManager()
    
    username = "admin"
    new_password = "Admin@123"
    
    conn = auth.get_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if auth.db_type == 'postgres' else "?"
    
    # Check if admin exists
    cursor.execute(f"SELECT id FROM users WHERE username = {placeholder}", (username,))
    row = cursor.fetchone()
    
    password_hash, _ = hash_password(new_password)
    
    if row:
        print(f"Updating password for user '{username}'...")
        cursor.execute(f"UPDATE users SET password_hash = {placeholder} WHERE username = {placeholder}", (password_hash, username))
        print("Password updated successfully.")
    else:
        print(f"Creating new admin user '{username}'...")
        try:
            cursor.execute(f'''
                INSERT INTO users (username, email, password_hash, is_admin, is_active, auth_method)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (username, "admin@cip.local", password_hash, True, True, 'local'))
            print("Admin user created successfully.")
        except Exception as e:
            print(f"Error creating admin: {e}")

    conn.commit()
    conn.close()
    
    print(f"\nAdmin Credentials (updated in {auth.db_type}):")
    print(f"Username: {username}")
    print(f"Password: {new_password}")

if __name__ == "__main__":
    reset_admin()
