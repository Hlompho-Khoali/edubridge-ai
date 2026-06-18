# run_migration.py
from app import app, db
from sqlalchemy import inspect, text

def run_migration():
    with app.app_context():
        # Check if grade_level exists
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('games')]
        
        print("Existing columns:", existing_columns)
        
        if 'grade_level' not in existing_columns:
            print("Adding new columns...")
            
            # Add columns one by one
            try:
                db.session.execute(text('ALTER TABLE games ADD COLUMN grade_level INTEGER DEFAULT 1'))
                db.session.execute(text('ALTER TABLE games ADD COLUMN subcategory VARCHAR(50) DEFAULT "default"'))
                db.session.execute(text('ALTER TABLE games ADD COLUMN accessibility_features TEXT DEFAULT "{}"'))
                db.session.execute(text('ALTER TABLE games ADD COLUMN visual_style VARCHAR(50) DEFAULT "default"'))
                db.session.execute(text('ALTER TABLE games ADD COLUMN audio_support BOOLEAN DEFAULT FALSE'))
                db.session.execute(text('ALTER TABLE games ADD COLUMN movement_breaks BOOLEAN DEFAULT FALSE'))
                db.session.execute(text('ALTER TABLE games ADD COLUMN progress_tracking BOOLEAN DEFAULT TRUE'))
                db.session.execute(text('ALTER TABLE games ADD COLUMN max_questions INTEGER DEFAULT 10'))
                db.session.commit()
                print("Migration complete!")
            except Exception as e:
                print(f"Error during migration: {e}")
                db.session.rollback()
        else:
            print("Columns already exist!")

if __name__ == '__main__':
    run_migration()