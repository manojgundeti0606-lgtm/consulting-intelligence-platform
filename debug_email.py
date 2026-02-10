"""Check all database files for bid data and sow_summary"""
import sqlite3
import os

db_files = ['cip_bids.db', 'cip_database.db', 'cip_data.db']

for db_file in db_files:
    if not os.path.exists(db_file):
        print(f"❌ {db_file} not found")
        continue
    
    print(f"\n{'='*60}")
    print(f"Checking: {db_file}")
    print("="*60)
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")
            
            # Check for sow_summary column
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            if 'sow_summary' in columns:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE sow_summary IS NOT NULL AND sow_summary != ''")
                sow_count = cursor.fetchone()[0]
                print(f"    -> Has sow_summary column: {sow_count} non-empty values")
                
                if sow_count > 0:
                    cursor.execute(f"SELECT * FROM {table} WHERE sow_summary IS NOT NULL AND sow_summary != '' LIMIT 1")
                    row = cursor.fetchone()
                    print(f"    -> Sample: {row[:3]}...")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
