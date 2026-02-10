import sqlite3

conn = sqlite3.connect('cip_data.db')
cursor = conn.cursor()

# Remove bids from NIC portals that have garbage bid numbers or titles
# Garbage bid numbers usually start with page text or have unusual lengths/content
garbage_patterns = [
    "Designed, Developed%",
    "National Informatics%",
    "Rights reserved%",
    "Site best viewed%"
]

total_removed = 0
for pattern in garbage_patterns:
    cursor.execute("DELETE FROM bids WHERE bid_number LIKE ? OR items LIKE ?", (pattern, pattern))
    total_removed += cursor.rowcount

# Also remove any bids where bid_number is too long (footer text)
cursor.execute("DELETE FROM bids WHERE LENGTH(bid_number) > 100")
total_removed += cursor.rowcount

conn.commit()
print(f"Cleanup complete. Removed {total_removed} garbage entries.")
conn.close()
