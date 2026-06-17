# migrate_games.py
import sqlite3
import os

def add_game_columns():
    # Path to your database
    db_path = 'instance/database.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(games)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("📊 Current columns:", columns)
        
        if 'is_latest' not in columns:
            print("✅ Adding is_latest column...")
            cursor.execute("ALTER TABLE games ADD COLUMN is_latest BOOLEAN DEFAULT 0")
        
        if 'generated_at' not in columns:
            print("✅ Adding generated_at column...")
            cursor.execute("ALTER TABLE games ADD COLUMN generated_at DATETIME")
        
        conn.commit()
        print("✅ Columns added successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_game_columns()