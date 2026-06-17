# reset_games.py
from app import app, db
from models import Game, TestAssignment, TestResult
from datetime import datetime

def reset_games():
    with app.app_context():
        try:
            print("🔄 Resetting games...")
            
            # Delete in correct order
            print("Deleting test results...")
            results_deleted = TestResult.query.delete()
            print(f"  ✅ Deleted {results_deleted} results")
            
            print("Deleting test assignments...")
            assignments_deleted = TestAssignment.query.delete()
            print(f"  ✅ Deleted {assignments_deleted} assignments")
            
            print("Deleting games...")
            games_deleted = Game.query.delete()
            print(f"  ✅ Deleted {games_deleted} games")
            
            db.session.commit()
            print("\n✅ All games have been wiped successfully!")
            print("📝 You can now generate new games using the AI Game Generator.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    reset_games()