# migrate_db.py
import sqlite3
import os

def add_difficulty_column():
    # Path to your database
    db_path = 'instance/database.db'  # or 'database.db' depending on your setup
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(games)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'difficulty' not in columns:
            print("Adding 'difficulty' column to games table...")
            cursor.execute("ALTER TABLE games ADD COLUMN difficulty TEXT DEFAULT 'Intermediate'")
            conn.commit()
            print("✅ Column added successfully!")
        else:
            print("✅ 'difficulty' column already exists.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_difficulty_column()