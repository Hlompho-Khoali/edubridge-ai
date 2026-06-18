# migrate_render.py
import os
from flask import Flask
from sqlalchemy import inspect, text

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db
db.init_app(app)

def run_migration():
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Games table columns
        games_columns = [col['name'] for col in inspector.get_columns('games')]
        games_new_columns = {
            'grade_level': 'INTEGER DEFAULT 1',
            'subcategory': 'VARCHAR(50) DEFAULT \'default\'',
            'accessibility_features': 'TEXT DEFAULT \'{}\'',
            'visual_style': 'VARCHAR(50) DEFAULT \'default\'',
            'audio_support': 'BOOLEAN DEFAULT FALSE',
            'movement_breaks': 'BOOLEAN DEFAULT FALSE',
            'progress_tracking': 'BOOLEAN DEFAULT TRUE',
            'max_questions': 'INTEGER DEFAULT 10',
            'disability_type': 'VARCHAR(50) DEFAULT \'none\'',
            'recommended_for': 'VARCHAR(50) DEFAULT \'all\''
        }
        
        print("Checking games table...")
        for col_name, col_type in games_new_columns.items():
            if col_name not in games_columns:
                try:
                    db.session.execute(text(f'ALTER TABLE games ADD COLUMN {col_name} {col_type}'))
                    print(f"Added column to games: {col_name}")
                except Exception as e:
                    print(f"Error adding {col_name} to games: {e}")
        
        # Learners table columns
        learners_columns = [col['name'] for col in inspector.get_columns('learners')]
        learners_new_columns = {
            'accessibility_preferences': 'TEXT DEFAULT \'{}\'',
            'disability_type': 'VARCHAR(50) DEFAULT \'none\'',
            'disability_notes': 'TEXT',
            'assessment_completed': 'BOOLEAN DEFAULT FALSE',
            'assessment_date': 'DATETIME',
            'cognitive_scores': 'TEXT DEFAULT \'{}\'',
            'condition_probabilities': 'TEXT DEFAULT \'{}\'',
            'recommendations': 'TEXT DEFAULT \'[]\'',
            'last_assessment': 'DATETIME'
        }
        
        print("Checking learners table...")
        for col_name, col_type in learners_new_columns.items():
            if col_name not in learners_columns:
                try:
                    db.session.execute(text(f'ALTER TABLE learners ADD COLUMN {col_name} {col_type}'))
                    print(f"Added column to learners: {col_name}")
                except Exception as e:
                    print(f"Error adding {col_name} to learners: {e}")
        
        db.session.commit()
        print("Migration complete!")

if __name__ == '__main__':
    run_migration()