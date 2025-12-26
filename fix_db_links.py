import sqlite3
import re

DB_PATH = 'cip_data.db'

def fix_links():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all bids
    cursor.execute("SELECT bid_number, document_link FROM bids")
    bids = cursor.fetchall()
    
    fixed_count = 0
    for bid_num, link in bids:
        if '[' in link or ']' in link:
            # Remove brackets
            new_link = link.replace('[', '').replace(']', '').replace("'", "")
            
            cursor.execute(
                "UPDATE bids SET document_link = ? WHERE bid_number = ?",
                (new_link, bid_num)
            )
            fixed_count += 1
            print(f"Fixed {bid_num}: {link} -> {new_link}")
            
    conn.commit()
    conn.close()
    print(f"Total fixed: {fixed_count}")

if __name__ == "__main__":
    fix_links()
