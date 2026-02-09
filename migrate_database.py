"""
Migration Script: Migrate all data from cip_data.db to cip_database.db
Then delete cip_data.db to avoid confusion
"""
import sqlite3
import os

SOURCE_DB = 'cip_data.db'
TARGET_DB = 'cip_database.db'

print(f"🔄 Migrating data from {SOURCE_DB} to {TARGET_DB}")
print("="*60)

# Check source exists
if not os.path.exists(SOURCE_DB):
    print(f"❌ Source database {SOURCE_DB} not found!")
    exit(1)

# Connect to both databases
source_conn = sqlite3.connect(SOURCE_DB)
target_conn = sqlite3.connect(TARGET_DB)

source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

# Get tables from source
source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
tables = [row[0] for row in source_cursor.fetchall()]
print(f"Tables to migrate: {tables}")

for table in tables:
    print(f"\n📦 Migrating table: {table}")
    
    # Get source count
    source_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    source_count = source_cursor.fetchone()[0]
    print(f"   Source records: {source_count}")
    
    if source_count == 0:
        print(f"   Skipping empty table")
        continue
    
    # Get column names
    source_cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in source_cursor.fetchall()]
    
    # Check if table exists in target
    target_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
    if not target_cursor.fetchone():
        print(f"   ⚠️ Table {table} doesn't exist in target, creating...")
        # Get CREATE statement from source
        source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        create_sql = source_cursor.fetchone()[0]
        target_cursor.execute(create_sql)
        target_conn.commit()
    
    # Get existing records in target to avoid duplicates
    target_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    target_before = target_cursor.fetchone()[0]
    print(f"   Target records (before): {target_before}")
    
    # Get all records from source
    source_cursor.execute(f"SELECT * FROM {table}")
    records = source_cursor.fetchall()
    
    # Build INSERT OR IGNORE statement
    placeholders = ','.join(['?' for _ in columns])
    columns_str = ','.join(columns)
    insert_sql = f"INSERT OR IGNORE INTO {table} ({columns_str}) VALUES ({placeholders})"
    
    # Insert records
    inserted = 0
    for record in records:
        try:
            target_cursor.execute(insert_sql, record)
            if target_cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"   ⚠️ Error inserting record: {e}")
    
    target_conn.commit()
    
    # Get count after
    target_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    target_after = target_cursor.fetchone()[0]
    print(f"   Target records (after): {target_after}")
    print(f"   ✅ Inserted {inserted} new records")

# Close connections
source_conn.close()
target_conn.close()

print("\n" + "="*60)
print("✅ Migration complete!")

# Verify target database
print("\n📊 Verification:")
verify_conn = sqlite3.connect(TARGET_DB)
verify_cursor = verify_conn.cursor()
for table in tables:
    verify_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = verify_cursor.fetchone()[0]
    print(f"   {table}: {count} records")
verify_conn.close()

# Ask to delete source
print(f"\n🗑️ Deleting source database: {SOURCE_DB}")
os.remove(SOURCE_DB)
print(f"✅ {SOURCE_DB} deleted successfully!")

# Also clean up cip_bids.db if empty
if os.path.exists('cip_bids.db'):
    conn = sqlite3.connect('cip_bids.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    if not cursor.fetchall():
        conn.close()
        print(f"🗑️ Deleting empty database: cip_bids.db")
        os.remove('cip_bids.db')
        print(f"✅ cip_bids.db deleted successfully!")
    else:
        conn.close()

print("\n🎉 All done! Now using cip_database.db as the only database.")
