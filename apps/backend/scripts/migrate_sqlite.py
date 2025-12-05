import sqlite3
import os

def run_migration():
    db_path = "apps/backend/fairmind.db"
    sql_path = "apps/backend/database/migrations/init_users.sql"
    
    print(f"Migrating {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(sql_path, 'r') as f:
        sql_script = f.read()
        
    # SQLite doesn't support timestamptz, replace with text or datetime
    sql_script = sql_script.replace("timestamptz default current_timestamp", "datetime default CURRENT_TIMESTAMP")
    sql_script = sql_script.replace("boolean", "integer") # SQLite uses 0/1 for boolean
    
    try:
        cursor.executescript(sql_script)
        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
