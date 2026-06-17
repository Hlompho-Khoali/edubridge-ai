# utils/badges.py
from models import db, Badge, LearnerBadge

class BadgeService:
    """Badge and achievement service"""
    
    @staticmethod
    def initialize_badges():
        """Create default badges if they don't exist"""
        badges = [
            {'name': '🌟 First Game', 'description': 'Completed your first game!', 'icon': '🎮', 'condition_type': 'games_completed', 'condition_value': 1},
            {'name': '⭐ Perfect Score', 'description': 'Got 100% on a game!', 'icon': '💯', 'condition_type': 'perfect_score', 'condition_value': 1},
            {'name': '🏅 5 Games', 'description': 'Completed 5 games', 'icon': '🎯', 'condition_type': 'games_completed', 'condition_value': 5},
            {'name': '🏆 10 Games', 'description': 'Completed 10 games', 'icon': '🏆', 'condition_type': 'games_completed', 'condition_value': 10},
            {'name': '🔥 3-Day Streak', 'description': 'Played games for 3 days in a row', 'icon': '🔥', 'condition_type': 'streak', 'condition_value': 3},
            {'name': '📚 Memory Master', 'description': 'Passed 3 memory games', 'icon': '🧠', 'condition_type': 'category_master', 'condition_value': 3},
            {'name': '🔢 Math Whiz', 'description': 'Passed 3 math games', 'icon': '🔢', 'condition_type': 'category_master', 'condition_value': 3},
            {'name': '🎓 Learning Champion', 'description': 'Completed 20 games', 'icon': '🎓', 'condition_type': 'games_completed', 'condition_value': 20},
        ]
        
        for badge_data in badges:
            existing = Badge.query.filter_by(name=badge_data['name']).first()
            if not existing:
                badge = Badge(**badge_data)
                db.session.add(badge)
        
        db.session.commit()
    
    @staticmethod
    def check_and_award_badges(learner):
        """Check and award badges to a learner"""
        awarded = []
        
        # Get all badges
        all_badges = Badge.query.all()
        
        # Get learner's completed games
        assignments = TestAssignment.query.filter_by(learner_id=learner.id, status='completed').all()
        completed_count = len(assignments)
        
        # Get perfect scores
        perfect_scores = 0
        for assignment in assignments:
            result = TestResult.query.filter_by(assignment_id=assignment.id).first()
            if result and result.percentage == 100:
                perfect_scores += 1
        
        # Check each badge
        for badge in all_badges:
            # Check if already earned
            existing = LearnerBadge.query.filter_by(
                learner_id=learner.id, 
                badge_id=badge.id
            ).first()
            
            if existing:
                continue
            
            earned = False
            
            if badge.condition_type == 'games_completed':
                if completed_count >= badge.condition_value:
                    earned = True
            
            elif badge.condition_type == 'perfect_score':
                if perfect_scores >= badge.condition_value:
                    earned = True
            
            elif badge.condition_type == 'streak':
                # Check streak
                streak = BadgeService._calculate_streak(learner)
                if streak >= badge.condition_value:
                    earned = True
            
            elif badge.condition_type == 'category_master':
                # Check category mastery
                categories = BadgeService._get_category_mastery(learner)
                for category, count in categories.items():
                    if count >= badge.condition_value:
                        earned = True
                        break
            
            if earned:
                learner_badge = LearnerBadge(
                    learner_id=learner.id,
                    badge_id=badge.id,
                    earned_at=datetime.utcnow()
                )
                db.session.add(learner_badge)
                awarded.append(badge)
        
        if awarded:
            db.session.commit()
        
        return awarded
    
    @staticmethod
    def _calculate_streak(learner):
        """Calculate current streak of playing games"""
        assignments = TestAssignment.query.filter_by(
            learner_id=learner.id,
            status='completed'
        ).order_by(TestAssignment.completed_at.desc()).all()
        
        if not assignments:
            return 0
        
        streak = 0
        current_date = datetime.now().date()
        
        for assignment in assignments:
            if assignment.completed_at:
                assignment_date = assignment.completed_at.date()
                days_diff = (current_date - assignment_date).days
                if days_diff == 0 or days_diff == 1:
                    streak += 1
                    current_date = assignment_date
                else:
                    break
        
        return streak
    
    @staticmethod
    def _get_category_mastery(learner):
        """Get number of games passed per category"""
        assignments = TestAssignment.query.filter_by(
            learner_id=learner.id,
            status='completed'
        ).all()
        
        categories = {}
        
        for assignment in assignments:
            result = TestResult.query.filter_by(assignment_id=assignment.id).first()
            if result and result.passed:
                game = Game.query.get(assignment.game_id)
                if game:
                    categories[game.category] = categories.get(game.category, 0) + 1
        
        return categories