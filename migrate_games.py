# migrate_games.py
import sqlite3
import os
import json

def add_game_columns():
    # Path to your database
    db_path = 'instance/database.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(games)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("Current columns:", columns)
        
        # Add new columns if they don't exist
        new_columns = {
            'is_latest': 'BOOLEAN DEFAULT 0',
            'generated_at': 'DATETIME',
            'grade_level': 'INTEGER DEFAULT 1',
            'subcategory': 'VARCHAR(50) DEFAULT "default"',
            'accessibility_features': 'TEXT DEFAULT "{}"',
            'visual_style': 'VARCHAR(50) DEFAULT "default"',
            'audio_support': 'BOOLEAN DEFAULT 0',
            'movement_breaks': 'BOOLEAN DEFAULT 0',
            'progress_tracking': 'BOOLEAN DEFAULT 1',
            'max_questions': 'INTEGER DEFAULT 10'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Adding {col_name} column...")
                cursor.execute(f"ALTER TABLE games ADD COLUMN {col_name} {col_type}")
        
        conn.commit()
        print("Columns added successfully!")
        
        # Update existing games with default values
        cursor.execute("SELECT id, questions FROM games")
        games = cursor.fetchall()
        
        for game_id, questions_json in games:
            try:
                questions = json.loads(questions_json) if questions_json else []
                # Update max_questions if it's null or 0
                cursor.execute(
                    "UPDATE games SET max_questions = ? WHERE id = ? AND (max_questions IS NULL OR max_questions = 0)",
                    (len(questions), game_id)
                )
            except:
                pass
        
        conn.commit()
        print("Existing games updated with default values!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_game_columns()
    print("Migration complete!")