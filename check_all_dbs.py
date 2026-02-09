"""Test the get_recent_bids_with_analysis function"""
import sys
sys.path.insert(0, '.')

from database import CIPDatabase

db = CIPDatabase()
print(f"Database type: {db.db_type}")
print(f"Database path: {db.db_path}")

# Test with different limits
for limit in [50, 100, 500]:
    bids = db.get_recent_bids_with_analysis(limit=limit)
    print(f"Limit {limit}: Got {len(bids)} bids")

# Check total count in database
import sqlite3
conn = sqlite3.connect(db.db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM bids")
total = cursor.fetchone()[0]
print(f"\nTotal bids in database: {total}")

cursor.execute("SELECT COUNT(*) FROM ai_analysis")
analysis = cursor.fetchone()[0]
print(f"Total analysis records: {analysis}")
conn.close()
