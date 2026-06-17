# utils/daily_challenge.py
from datetime import datetime, date
from models import db, Game, TestAssignment, Learner
import random

class DailyChallengeService:
    """Service for managing daily challenges"""
    
    @staticmethod
    def get_daily_challenge():
        """Get today's challenge game"""
        # Get today's date as seed
        today = date.today()
        seed = today.strftime('%Y%m%d')
        random.seed(int(seed))
        
        # Get all games
        games = Game.query.all()
        if not games:
            return None
        
        # Select a random game based on today's date (same for everyone)
        selected_game = random.choice(games)
        return selected_game
    
    @staticmethod
    def assign_daily_challenge():
        """Assign today's challenge to all learners"""
        challenge_game = DailyChallengeService.get_daily_challenge()
        if not challenge_game:
            return False
        
        today = date.today()
        
        # Get all learners
        learners = Learner.query.all()
        assigned_count = 0
        
        for learner in learners:
            # Check if already assigned today
            existing = TestAssignment.query.filter(
                TestAssignment.learner_id == learner.id,
                TestAssignment.game_id == challenge_game.id,
                db.func.date(TestAssignment.assigned_at) == today
            ).first()
            
            if not existing:
                # Check if already completed this game
                completed = TestAssignment.query.filter(
                    TestAssignment.learner_id == learner.id,
                    TestAssignment.game_id == challenge_game.id,
                    TestAssignment.status == 'completed'
                ).first()
                
                if not completed:
                    assignment = TestAssignment(
                        game_id=challenge_game.id,
                        learner_id=learner.id,
                        educator_id=1,  # System assignment (you may want to create a system educator)
                        status='pending'
                    )
                    db.session.add(assignment)
                    assigned_count += 1
        
        db.session.commit()
        return assigned_count
    
    @staticmethod
    def get_learner_challenge_status(learner_id):
        """Check if learner has completed today's challenge"""
        today = date.today()
        challenge_game = DailyChallengeService.get_daily_challenge()
        
        if not challenge_game:
            return {'has_challenge': False}
        
        assignment = TestAssignment.query.filter(
            TestAssignment.learner_id == learner_id,
            TestAssignment.game_id == challenge_game.id,
            db.func.date(TestAssignment.assigned_at) == today
        ).first()
        
        if not assignment:
            return {'has_challenge': False, 'game': challenge_game}
        
        return {
            'has_challenge': True,
            'game': challenge_game,
            'assignment': assignment,
            'completed': assignment.status == 'completed',
            'started': assignment.status == 'in_progress'
        }