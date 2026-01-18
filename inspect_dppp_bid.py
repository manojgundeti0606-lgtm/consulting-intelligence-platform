import sqlite3
import json

conn = sqlite3.connect('cip_data.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM bids WHERE source_portal = 'dppp'")
row = cursor.fetchone()
if row:
    print("DPPP Bid Found:")
    for key in row.keys():
        print(f"  {key}: {row[key]}")
else:
    print("No DPPP bid found.")
conn.close()
