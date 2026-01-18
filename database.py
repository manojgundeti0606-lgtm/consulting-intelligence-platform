"""
Database module for Consulting Intelligence Platform
SQLite-based storage for bids, AI analysis, and watchlist
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import DATABASE_CONFIG, NOTIFICATION_CONFIG

# Optional PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class CIPDatabase:
    """Database manager for CIP"""
    
    def __init__(self, db_path=None, db_type=None):
        self.db_type = db_type or os.getenv('DATABASE_TYPE', DATABASE_CONFIG.get('db_type', 'sqlite'))
        if db_path is None:
            db_path = DATABASE_CONFIG['db_path']
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection based on db_type"""
        if self.db_type == 'postgres':
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2-binary is required for PostgreSQL support. Install it via pip.")
            
            pg_config = DATABASE_CONFIG.get('postgres', {})
            return psycopg2.connect(
                host=pg_config.get('host'),
                port=pg_config.get('port'),
                dbname=pg_config.get('database'),
                user=pg_config.get('user'),
                password=pg_config.get('password')
            )
        else:
            return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Bids table
        id_col = "id SERIAL PRIMARY KEY" if self.db_type == 'postgres' else "id INTEGER PRIMARY KEY AUTOINCREMENT"
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS bids (
                {id_col},
                bid_number TEXT UNIQUE NOT NULL,
                items TEXT,
                quantity TEXT,
                department TEXT,
                start_date TEXT,
                end_date TEXT,
                document_link TEXT,
                category TEXT,
                source_portal TEXT DEFAULT 'gem',
                location TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migration: Add source_portal column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE bids ADD COLUMN source_portal TEXT DEFAULT 'gem'")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE bids ADD COLUMN location TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # AI Analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bid_number TEXT NOT NULL,
                cfs_score INTEGER,
                cfs_verdict TEXT,
                cfs_reasoning TEXT,
                go_no_go_recommendation TEXT,
                exec_summary_json TEXT,
                sow_summary TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bid_number) REFERENCES bids(bid_number)
            )
        ''')
        
        # Watchlist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bid_number TEXT UNIQUE NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP,
                FOREIGN KEY (bid_number) REFERENCES bids(bid_number)
            )
        ''')
        
        # Change log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bid_number TEXT NOT NULL,
                change_type TEXT,
                old_value TEXT,
                new_value TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bid_number) REFERENCES bids(bid_number)
            )
        ''')
        
        # Email Recipients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Seed initial emails if table is empty
        cursor.execute("SELECT COUNT(*) FROM email_recipients")
        if cursor.fetchone()[0] == 0:
            initial_emails = NOTIFICATION_CONFIG.get('team_emails', [])
            for email in initial_emails:
                try:
                    cursor.execute("INSERT INTO email_recipients (email, name) VALUES (?, ?)", (email, email.split('@')[0]))
                except sqlite3.IntegrityError:
                    pass

        
        conn.commit()
        conn.close()
    
    def save_bid(self, bid_data: Dict):
        """Save or update bid data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgres':
            cursor.execute('''
                INSERT INTO bids 
                (bid_number, items, quantity, department, start_date, end_date, document_link, category, source_portal, location, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT(bid_number) DO UPDATE SET
                    items=EXCLUDED.items,
                    quantity=EXCLUDED.quantity,
                    department=EXCLUDED.department,
                    start_date=EXCLUDED.start_date,
                    end_date=EXCLUDED.end_date,
                    document_link=EXCLUDED.document_link,
                    category=EXCLUDED.category,
                    source_portal=EXCLUDED.source_portal,
                    location=EXCLUDED.location,
                    last_updated=CURRENT_TIMESTAMP
            ''', (
                bid_data.get('Bid Number'),
                bid_data.get('Items'),
                str(bid_data.get('Quantity', '')),
                bid_data.get('Department'),
                bid_data.get('Start Date'),
                bid_data.get('End Date'),
                bid_data.get('Document Link'),
                bid_data.get('Category'),
                bid_data.get('Source Portal', 'gem'),
                bid_data.get('Location', '')
            ))
        else:
            cursor.execute('''
                INSERT INTO bids 
                (bid_number, items, quantity, department, start_date, end_date, document_link, category, source_portal, location, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(bid_number) DO UPDATE SET
                    items=excluded.items,
                    quantity=excluded.quantity,
                    department=excluded.department,
                    start_date=excluded.start_date,
                    end_date=excluded.end_date,
                    document_link=excluded.document_link,
                    category=excluded.category,
                    source_portal=excluded.source_portal,
                    location=excluded.location,
                    last_updated=CURRENT_TIMESTAMP
            ''', (
                bid_data.get('Bid Number'),
                bid_data.get('Items'),
                str(bid_data.get('Quantity', '')),
                bid_data.get('Department'),
                bid_data.get('Start Date'),
                bid_data.get('End Date'),
                bid_data.get('Document Link'),
                bid_data.get('Category'),
                bid_data.get('Source Portal', 'gem'),
                bid_data.get('Location', '')
            ))
        
        conn.commit()
        conn.close()
    
    def save_ai_analysis(self, analysis_data: Dict):
        """Save AI analysis results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cfs = analysis_data.get('cfs', {})
        gng = analysis_data.get('go_no_go', {})
        summary = analysis_data.get('executive_summary', {})
        
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        
        cursor.execute(f'''
            INSERT INTO ai_analysis 
            (bid_number, cfs_score, cfs_verdict, cfs_reasoning, 
             go_no_go_recommendation, exec_summary_json, sow_summary)
            VALUES ({", ".join([placeholder]*7)})
        ''', (
            analysis_data.get('bid_number'),
            cfs.get('score'),
            cfs.get('verdict'),
            cfs.get('reasoning'),
            gng.get('overall_recommendation'),
            json.dumps(summary),
            analysis_data.get('sow_summary')
        ))
        
        conn.commit()
        conn.close()
    
    def get_bid(self, bid_number: str) -> Optional[Dict]:
        """Retrieve bid by number"""
        conn = self.get_connection()
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        cursor = conn.cursor()
        
        if self.db_type == 'postgres':
            # In PostgreSQL, we use RealDictCursor which is set at the connection level usually, 
            # but we can do it here for simplicity
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
        cursor.execute(f'SELECT * FROM bids WHERE bid_number = {placeholder}', (bid_number,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_bids(self, limit=100) -> List[Dict]:
        """Get recent bids"""
        conn = self.get_connection()
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        conn = self.get_connection()
        
        if self.db_type == 'postgres':
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
        cursor.execute(f'SELECT * FROM bids ORDER BY last_updated DESC LIMIT {placeholder}', (limit,))
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_to_watchlist(self, bid_number: str):
        """Add bid to watchlist"""
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            ignore = "ON CONFLICT DO NOTHING" if self.db_type == 'postgres' else "OR IGNORE"
            cursor.execute(f'''
                INSERT {ignore if self.db_type != 'postgres' else ''} INTO watchlist (bid_number) VALUES ({placeholder}) {ignore if self.db_type == 'postgres' else ''}
            ''', (bid_number,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False
        finally:
            conn.close()
    
    def remove_from_watchlist(self, bid_number: str):
        """Remove bid from watchlist"""
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'DELETE FROM watchlist WHERE bid_number = {placeholder}', (bid_number,))
        conn.commit()
        conn.close()
    
    def get_watchlist(self) -> List[str]:
        """Get all watched bid numbers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT bid_number FROM watchlist')
        rows = cursor.fetchall()
        
        conn.close()
        
        return [row[0] for row in rows]
    
    def log_change(self, bid_number: str, change_type: str, old_value: str, new_value: str):
        """Log a detected change"""
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'''
            INSERT INTO change_log (bid_number, change_type, old_value, new_value)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', (bid_number, change_type, old_value, new_value))
        
        conn.commit()
        conn.close()
    
    def get_changes(self, bid_number: str = None, limit=50) -> List[Dict]:
        """Get change log"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if bid_number:
            cursor.execute('''
                SELECT * FROM change_log 
                WHERE bid_number = ? 
                ORDER BY detected_at DESC 
                LIMIT ?
            ''', (bid_number, limit))
        else:
            cursor.execute('''
                SELECT * FROM change_log 
                ORDER BY detected_at DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_bid_with_analysis(self, bid_number: str) -> Optional[Dict]:
        """Get bid data with AI analysis"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, a.cfs_score, a.cfs_verdict, a.cfs_reasoning,
                   a.go_no_go_recommendation, a.exec_summary_json, a.sow_summary, a.analyzed_at
            FROM bids b
            LEFT JOIN ai_analysis a ON b.bid_number = a.bid_number
            WHERE b.bid_number = ?
            ORDER BY a.analyzed_at DESC
            LIMIT 1
        ''', (bid_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            # Parse JSON summary
            if result.get('exec_summary_json'):
                result['executive_summary'] = json.loads(result['exec_summary_json'])
            return result
        return None
    
    def get_recent_bids_with_analysis(self, limit=50) -> List[Dict]:
        """Get recent bids with AI analysis included"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, a.cfs_score, a.cfs_verdict, a.cfs_reasoning,
                   a.go_no_go_recommendation, a.exec_summary_json, a.sow_summary, a.analyzed_at
            FROM bids b
            LEFT JOIN ai_analysis a ON b.bid_number = a.bid_number
            ORDER BY b.last_updated DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            res = dict(row)
            # Map DB fields to UI expected fields
            res['Bid Number'] = res['bid_number']
            res['Items'] = res['items']
            res['Department'] = res['department']
            res['Category'] = res['category']
            res['End Date'] = res['end_date']
            res['Document Link'] = res['document_link']
            
            if res.get('cfs_score') is not None:
                res['CFS Score'] = res['cfs_score']
                res['Verdict'] = res['cfs_verdict']
                res['Recommendation'] = res['go_no_go_recommendation']
            
            results.append(res)
            
        return results
    
    def get_bids_in_period(self, days: int) -> List[Dict]:
        """Get bids analyzed in the last N days"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # calculate date threshold
        from datetime import datetime, timedelta
        threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT b.*, a.cfs_score, a.cfs_verdict, a.cfs_reasoning,
                   a.go_no_go_recommendation, a.exec_summary_json, a.sow_summary, a.analyzed_at
            FROM bids b
            LEFT JOIN ai_analysis a ON b.bid_number = a.bid_number
            WHERE a.analyzed_at >= ?
            ORDER BY a.analyzed_at DESC
        ''', (threshold_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            res = dict(row)
            # Map DB fields to UI expected fields
            res['Bid Number'] = res['bid_number']
            res['Items'] = res['items']
            res['Department'] = res['department']
            res['Category'] = res['category']
            res['End Date'] = res['end_date']
            res['Document Link'] = res['document_link']
            
            if res.get('cfs_score') is not None:
                res['CFS Score'] = res['cfs_score']
                res['Verdict'] = res['cfs_verdict']
                res['Recommendation'] = res['go_no_go_recommendation']
            
            # Parse JSON summary
            if res.get('exec_summary_json'):
                try:
                    res['executive_summary'] = json.loads(res['exec_summary_json'])
                except json.JSONDecodeError:
                    pass  # Invalid JSON, skip parsing
            
            results.append(res)
            
        return results

    def add_recipient(self, email: str, name: str = None) -> bool:
        """Add a new email recipient"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        
        try:
            cursor.execute(f'''
                INSERT INTO email_recipients (email, name) VALUES ({placeholder}, {placeholder})
            ''', (email, name or email.split('@')[0]))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding recipient: {e}")
            return False
        finally:
            conn.close()

    def remove_recipient(self, email: str):
        """Remove an email recipient"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = "%s" if self.db_type == 'postgres' else "?"
        
        cursor.execute(f'DELETE FROM email_recipients WHERE email = {placeholder}', (email,))
        conn.commit()
        conn.close()

    def get_all_recipients(self) -> List[Dict]:
        """Get all email recipients"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM email_recipients ORDER BY name')
        rows = cursor.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    # Test database
    db = CIPDatabase()
    
    # Test bid
    test_bid = {
        "Bid Number": "TEST/2024/001",
        "Items": "Consultancy for Digital Transformation",
        "Department": "Ministry of IT",
        "Start Date": "2024-12-01",
        "End Date": "2024-12-31",
        "Document Link": "https://example.com/doc",
        "Category": "Tech & Digital"
    }
    
    db.save_bid(test_bid)
    retrieved = db.get_bid("TEST/2024/001")
    print("Retrieved bid:", retrieved)
    
    # Test watchlist
    db.add_to_watchlist("TEST/2024/001")
    watchlist = db.get_watchlist()
    print("Watchlist:", watchlist)
