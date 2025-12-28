"""
Authentication module for Consulting Intelligence Platform
Provides user registration, login, and role management
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import streamlit as st


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """Hash password using SHA-256 with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}", salt


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, expected_hash = stored_hash.split('$')
        actual_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return actual_hash == expected_hash
    except (ValueError, AttributeError):
        return False


class AuthManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, db_path: str = "cip_database.db"):
        self.db_path = db_path
        self.init_auth_tables()
        self.create_default_admin()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_auth_tables(self):
        """Create users table if not exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                auth_method TEXT DEFAULT 'local',
                google_id TEXT,
                profile_picture TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Add new columns if they don't exist (for migration)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN auth_method TEXT DEFAULT 'local'")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()
    
    def login_with_google(self, google_user_info: Dict) -> Dict:
        """Login or register user via Google OAuth"""
        email = google_user_info.get('email', '').lower()
        name = google_user_info.get('name', email.split('@')[0])
        google_id = google_user_info.get('sub', '')
        picture = google_user_info.get('picture', '')
        
        if not email:
            return {"success": False, "error": "No email provided from Google"}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if user exists by email or google_id
        cursor.execute('''
            SELECT id, username, email, is_admin, is_active, auth_method
            FROM users WHERE email = ? OR google_id = ?
        ''', (email, google_id))
        
        user = cursor.fetchone()
        
        if user:
            # Existing user - update and login
            user_id, username, user_email, is_admin, is_active, auth_method = user
            
            if not is_active:
                conn.close()
                return {"success": False, "error": "Account is deactivated"}
            
            # Update google_id and last login
            cursor.execute('''
                UPDATE users SET google_id = ?, profile_picture = ?, last_login = ?, auth_method = COALESCE(?, auth_method)
                WHERE id = ?
            ''', (google_id, picture, datetime.now().isoformat(), 'google' if not auth_method else None, user_id))
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": user_email,
                    "is_admin": bool(is_admin),
                    "profile_picture": picture
                }
            }
        else:
            # New user - register via Google
            username = name.replace(' ', '_').lower()[:20]
            
            # Ensure unique username
            base_username = username
            counter = 1
            while True:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                username = f"{base_username}_{counter}"
                counter += 1
            
            try:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin, auth_method, google_id, profile_picture)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (username, email, '', False, 'google', google_id, picture))
                conn.commit()
                user_id = cursor.lastrowid
                conn.close()
                
                return {
                    "success": True,
                    "user": {
                        "id": user_id,
                        "username": username,
                        "email": email,
                        "is_admin": False,
                        "profile_picture": picture
                    }
                }
            except sqlite3.IntegrityError:
                conn.close()
                return {"success": False, "error": "Registration failed"}

    
    def create_default_admin(self):
        """Create default admin user if no admin exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if any admin exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Create default admin (username: manoj, password: admin123)
            password_hash, _ = hash_password("admin123")
            try:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, is_admin)
                    VALUES (?, ?, ?, ?)
                ''', ("manoj", "manoj@admin.com", password_hash, True))
                conn.commit()
                print("✅ Default admin user created: manoj / admin123")
            except sqlite3.IntegrityError:
                pass  # User already exists
        
        conn.close()
    
    def register_user(self, username: str, email: str, password: str) -> Dict:
        """Register a new user"""
        if len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters"}
        
        if len(username) < 3:
            return {"success": False, "error": "Username must be at least 3 characters"}
        
        password_hash, _ = hash_password(password)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, email.lower(), password_hash, False))
            conn.commit()
            conn.close()
            return {"success": True, "message": "Registration successful!"}
        except sqlite3.IntegrityError as e:
            conn.close()
            if "username" in str(e):
                return {"success": False, "error": "Username already exists"}
            elif "email" in str(e):
                return {"success": False, "error": "Email already registered"}
            return {"success": False, "error": "Registration failed"}
    
    def login(self, username: str, password: str) -> Dict:
        """Authenticate user login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, is_admin, is_active
            FROM users WHERE username = ? OR email = ?
        ''', (username, username.lower()))
        
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {"success": False, "error": "User not found"}
        
        user_id, uname, email, password_hash, is_admin, is_active = user
        
        if not is_active:
            conn.close()
            return {"success": False, "error": "Account is deactivated"}
        
        if not verify_password(password, password_hash):
            conn.close()
            return {"success": False, "error": "Invalid password"}
        
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "user": {
                "id": user_id,
                "username": uname,
                "email": email,
                "is_admin": bool(is_admin)
            }
        }
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, is_admin, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "is_admin": bool(row[3]),
                "is_active": bool(row[4]),
                "created_at": row[5],
                "last_login": row[6]
            })
        
        conn.close()
        return users
    
    def set_admin_status(self, user_id: int, is_admin: bool) -> bool:
        """Grant or revoke admin status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET is_admin = ? WHERE id = ?
        ''', (is_admin, user_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def toggle_user_active(self, user_id: int) -> bool:
        """Activate/deactivate user account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET is_active = NOT is_active WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password"""
        if len(new_password) < 6:
            return False
        
        password_hash, _ = hash_password(new_password)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET password_hash = ? WHERE id = ?
        ''', (password_hash, user_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success


# Session management functions
def init_session():
    """Initialize session state for authentication"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()


def is_logged_in() -> bool:
    """Check if user is logged in"""
    return st.session_state.get('logged_in', False)


def is_admin() -> bool:
    """Check if current user is admin"""
    user = st.session_state.get('user')
    return user is not None and user.get('is_admin', False)


def get_current_user() -> Optional[Dict]:
    """Get current logged in user"""
    return st.session_state.get('user')


def login_user(user: Dict):
    """Set user as logged in"""
    st.session_state.logged_in = True
    st.session_state.user = user


def logout_user():
    """Log out current user"""
    st.session_state.logged_in = False
    st.session_state.user = None


def require_login():
    """Decorator/check to require login"""
    if not is_logged_in():
        st.warning("Please login to access this page")
        st.stop()


def require_admin():
    """Decorator/check to require admin access"""
    require_login()
    if not is_admin():
        st.error("Admin access required")
        st.stop()
