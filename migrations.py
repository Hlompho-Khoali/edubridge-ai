# migrations.py
from app import app, db
from sqlalchemy import inspect, text

def run_migrations():
    with app.app_context():
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('games')]
        
        new_columns = {
            'grade_level': 'INTEGER DEFAULT 1',
            'subcategory': 'VARCHAR(50) DEFAULT \'default\'',
            'accessibility_features': 'TEXT DEFAULT \'{}\'',
            'visual_style': 'VARCHAR(50) DEFAULT \'default\'',
            'audio_support': 'BOOLEAN DEFAULT FALSE',
            'movement_breaks': 'BOOLEAN DEFAULT FALSE',
            'progress_tracking': 'BOOLEAN DEFAULT TRUE',
            'max_questions': 'INTEGER DEFAULT 10'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    db.session.execute(text(f'ALTER TABLE games ADD COLUMN {col_name} {col_type}'))
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"⚠️ Could not add {col_name}: {e}")
        
        db.session.commit()
        print("✅ Migration complete!")

if __name__ == '__main__':
    run_migrations()