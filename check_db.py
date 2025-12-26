from database import CIPDatabase
import pandas as pd

def check_db():
    db = CIPDatabase()
    conn = db.get_connection()
    
    print("--- Checking Bids Table ---")
    bids = pd.read_sql("SELECT * FROM bids ORDER BY last_updated DESC LIMIT 5", conn)
    if not bids.empty:
        print(bids[['bid_number', 'items', 'category', 'last_updated']])
    else:
        print("No bids found in database.")
        
    print("\n--- Checking AI Analysis Table ---")
    analysis = pd.read_sql("SELECT * FROM ai_analysis ORDER BY analyzed_at DESC LIMIT 5", conn)
    if not analysis.empty:
        print(analysis[['bid_number', 'cfs_score', 'cfs_verdict', 'analyzed_at']])
    else:
        print("No AI analysis found in database.")
        
    conn.close()

if __name__ == "__main__":
    check_db()
