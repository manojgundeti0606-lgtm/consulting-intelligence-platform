import sqlite3
import os

db_path = 'cip_data.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT source_portal, COUNT(*) FROM bids GROUP BY source_portal")
        results = cursor.fetchall()
        print("Portal Distribution in Database:")
        for portal, count in results:
            print(f"  - {portal}: {count}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
