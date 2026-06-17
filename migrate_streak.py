# migrate_streak.py
import sqlite3
import os

def add_streak_columns():
    # Path to your database
    db_path = 'instance/database.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(learners)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add streak columns if they don't exist
        if 'streak_count' not in columns:
            print("Adding streak_count column...")
            cursor.execute("ALTER TABLE learners ADD COLUMN streak_count INTEGER DEFAULT 0")
        
        if 'last_activity_date' not in columns:
            print("Adding last_activity_date column...")
            cursor.execute("ALTER TABLE learners ADD COLUMN last_activity_date DATETIME")
        
        if 'best_streak' not in columns:
            print("Adding best_streak column...")
            cursor.execute("ALTER TABLE learners ADD COLUMN best_streak INTEGER DEFAULT 0")
        
        conn.commit()
        print("✅ Streak columns added successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_streak_columns()