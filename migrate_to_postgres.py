import sqlite3
import os
import json
from datetime import datetime
from database import CIPDatabase
from auth import AuthManager, hash_password
from config import DATABASE_CONFIG

def migrate():
    # 1. Setup PostgreSQL Connection (Target) via CIPDatabase
    # Force db_type to postgres for this script
    os.environ['DATABASE_TYPE'] = 'postgres'
    
    # Re-import config to ensure env var is picked up if needed, 
    # though our updated config.py does this on import.
    db_target = CIPDatabase(db_type='postgres')
    auth_target = AuthManager(db_type='postgres')
    
    print(f"Target Database Type: {db_target.db_type}")
    
    # 2. Source Databases
    bids_db_path = "cip_data.db"
    users_db_path = "cip_database.db"
    
    if not os.path.exists(bids_db_path):
        print(f"❌ Source bids database not found: {bids_db_path}")
        return
    
    # --- Migrate Users ---
    print("\n--- Migrating Users ---")
    if os.path.exists(users_db_path):
        conn_u = sqlite3.connect(users_db_path)
        conn_u.row_factory = sqlite3.Row
        cursor_u = conn_u.cursor()
        
        cursor_u.execute("SELECT * FROM users")
        users = cursor_u.fetchall()
        
        target_conn = auth_target.get_connection()
        target_cursor = target_conn.cursor()
        
        for user in users:
            u = dict(user)
            print(f"Migrating user: {u['username']}")
            
            # Using basic INSERT with conflict handling
            target_cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin, is_active, auth_method, google_id, profile_picture)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            ''', (
                u['username'], u['email'], u['password_hash'], 
                bool(u['is_admin']), bool(u['is_active']), 
                u.get('auth_method', 'local'), u.get('google_id'), u.get('profile_picture')
            ))
        
        target_conn.commit()
        target_conn.close()
        conn_u.close()
        print(f"✅ Migrated {len(users)} users.")
    else:
        print("⚠️ Source users database not found.")

    # --- Migrate Bids ---
    print("\n--- Migrating Bids ---")
    conn_b = sqlite3.connect(bids_db_path)
    conn_b.row_factory = sqlite3.Row
    cursor_b = conn_b.cursor()
    
    cursor_b.execute("SELECT * FROM bids")
    bids = cursor_b.fetchall()
    
    print(f"Total bids in source: {len(bids)}")
    for i, bid in enumerate(bids):
        b = dict(bid)
        # Convert sqlite row to format expected by save_bid
        bid_data = {
            'Bid Number': b['bid_number'],
            'Items': b['items'],
            'Quantity': b['quantity'],
            'Department': b['department'],
            'Start Date': b['start_date'],
            'End Date': b['end_date'],
            'Document Link': b['document_link'],
            'Category': b['category'],
            'Source Portal': b.get('source_portal', 'gem'),
            'Location': b.get('location', '')
        }
        db_target.save_bid(bid_data)
        if (i+1) % 50 == 0:
            print(f"  Processed {i+1} bids...")

    # --- Migrate AI Analysis ---
    print("\n--- Migrating AI Analysis ---")
    cursor_b.execute("SELECT * FROM ai_analysis")
    analyses = cursor_b.fetchall()
    print(f"Total analyses in source: {len(analyses)}")
    
    target_conn = db_target.get_connection()
    target_cursor = target_conn.cursor()
    
    for analysis in analyses:
        a = dict(analysis)
        # Use simpler approach to handle nested JSON
        target_cursor.execute('''
            INSERT INTO ai_analysis 
            (bid_number, cfs_score, cfs_verdict, cfs_reasoning, go_no_go_recommendation, exec_summary_json, sow_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            a['bid_number'], a['cfs_score'], a['cfs_verdict'], a['cfs_reasoning'],
            a['go_no_go_recommendation'], a['exec_summary_json'], a['sow_summary']
        ))
    
    target_conn.commit()
    target_conn.close()
    conn_b.close()
    
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
