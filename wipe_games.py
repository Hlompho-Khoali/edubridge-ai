# wipe_games.py
from app import app, db
from models import Game, TestAssignment, TestResult

def wipe_all_games():
    with app.app_context():
        try:
            print("=" * 50)
            print("🗑️  WIPING ALL GAMES")
            print("=" * 50)
            
            # Delete in correct order (foreign key constraints)
            print("\n📊 Deleting test results...")
            results_count = TestResult.query.count()
            TestResult.query.delete()
            print(f"  ✅ Deleted {results_count} results")
            
            print("\n📋 Deleting test assignments...")
            assignments_count = TestAssignment.query.count()
            TestAssignment.query.delete()
            print(f"  ✅ Deleted {assignments_count} assignments")
            
            print("\n🎮 Deleting games...")
            games_count = Game.query.count()
            Game.query.delete()
            print(f"  ✅ Deleted {games_count} games")
            
            db.session.commit()
            print("\n" + "=" * 50)
            print("✅ ALL GAMES HAVE BEEN WIPED!")
            print(f"   - {results_count} results deleted")
            print(f"   - {assignments_count} assignments deleted")
            print(f"   - {games_count} games deleted")
            print("=" * 50)
            print("\n📝 Now you can generate new games using the AI Game Generator.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    wipe_all_games()