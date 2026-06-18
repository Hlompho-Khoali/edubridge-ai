# migrate_render.py
import os
import sys
from flask import Flask
from sqlalchemy import inspect, text

# Create a minimal app just for migration
app = Flask(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db from models
from models import db
db.init_app(app)

def run_migration():
    """Add missing columns to games table"""
    with app.app_context():
        try:
            # Check existing columns
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('games')]
            
            print(f"🔍 Existing columns: {existing_columns}")
            
            # Columns to add
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
            
            added = []
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    try:
                        db.session.execute(text(f'ALTER TABLE games ADD COLUMN {col_name} {col_type}'))
                        print(f"✅ Added column: {col_name}")
                        added.append(col_name)
                    except Exception as e:
                        print(f"⚠️ Error adding {col_name}: {e}")
            
            db.session.commit()
            
            if added:
                print(f"✅ Migration complete! Added columns: {added}")
            else:
                print("✅ All columns already exist!")
                
        except Exception as e:
            print(f"❌ Migration error: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    print("🚀 Starting migration...")
    run_migration()
    print("✅ Migration completed successfully!")