# utils/badges.py
from models import db, User, Badge, LearnerBadge, TestAssignment, TestResult
from datetime import datetime

class BadgeService:
    """Service for managing badges and achievements"""
    
    @staticmethod
    def initialize_badges():
        """Initialize default badges if they don't exist"""
        default_badges = [
            {
                'name': 'First Steps',
                'description': 'Completed your first game',
                'icon': '⭐',
                'category': 'achievement',
                'criteria': 'complete_first_game'
            },
            {
                'name': 'Perfect Score',
                'description': 'Got 100% on a game',
                'icon': '🏆',
                'category': 'achievement',
                'criteria': 'perfect_score'
            },
            {
                'name': 'Hard Worker',
                'description': 'Completed 10 games',
                'icon': '💪',
                'category': 'achievement',
                'criteria': 'complete_10_games'
            },
            {
                'name': 'Star Learner',
                'description': 'Completed 25 games',
                'icon': '⭐',
                'category': 'achievement',
                'criteria': 'complete_25_games'
            },
            {
                'name': 'Mastery',
                'description': 'Passed 5 games with 80%+',
                'icon': '🎯',
                'category': 'achievement',
                'criteria': 'mastery'
            },
            {
                'name': 'Quick Learner',
                'description': 'Passed 3 games in a row',
                'icon': '🚀',
                'category': 'achievement',
                'criteria': 'streak'
            }
        ]
        
        for badge_data in default_badges:
            existing = Badge.query.filter_by(name=badge_data['name']).first()
            if not existing:
                badge = Badge(
                    name=badge_data['name'],
                    description=badge_data['description'],
                    icon=badge_data['icon'],
                    category=badge_data['category'],
                    criteria=badge_data['criteria']
                )
                db.session.add(badge)
        
        db.session.commit()
        print("Badges initialized")
    
    @staticmethod
    def check_and_award_badges(learner):
        """Check if learner qualifies for any badges and award them"""
        # Get all completed assignments for this learner
        assignments = TestAssignment.query.filter_by(
            learner_id=learner.id, 
            status='completed'
        ).all()
        
        if not assignments:
            return []
        
        # Get all results
        results = TestResult.query.filter(
            TestResult.assignment_id.in_([a.id for a in assignments])
        ).all()
        
        # Calculate stats
        total_completed = len(assignments)
        total_passed = len([r for r in results if r.passed])
        perfect_scores = len([r for r in results if r.percentage == 100])
        high_scores = len([r for r in results if r.percentage >= 80])
        
        # Get already earned badges
        earned_badge_ids = [lb.badge_id for lb in LearnerBadge.query.filter_by(learner_id=learner.id).all()]
        
        # Check each badge criteria
        all_badges = Badge.query.all()
        new_badges = []
        
        for badge in all_badges:
            if badge.id in earned_badge_ids:
                continue
            
            should_award = False
            
            if badge.criteria == 'complete_first_game' and total_completed >= 1:
                should_award = True
            elif badge.criteria == 'perfect_score' and perfect_scores >= 1:
                should_award = True
            elif badge.criteria == 'complete_10_games' and total_completed >= 10:
                should_award = True
            elif badge.criteria == 'complete_25_games' and total_completed >= 25:
                should_award = True
            elif badge.criteria == 'mastery' and high_scores >= 5:
                should_award = True
            elif badge.criteria == 'streak':
                # Check for 3 consecutive passes
                recent_results = sorted(results, key=lambda r: r.completed_at, reverse=True)[:3]
                if len(recent_results) >= 3 and all(r.passed for r in recent_results):
                    should_award = True
            
            if should_award:
                learner_badge = LearnerBadge(
                    learner_id=learner.id,
                    badge_id=badge.id,
                    awarded_at=datetime.utcnow()
                )
                db.session.add(learner_badge)
                new_badges.append(badge)
        
        if new_badges:
            db.session.commit()
            print(f"Awarded {len(new_badges)} badges to {learner.user.name}")
        
        return new_badges
    
    @staticmethod
    def get_learner_badges(learner):
        """Get all badges earned by a learner"""
        learner_badges = LearnerBadge.query.filter_by(learner_id=learner.id).all()
        badges = []
        for lb in learner_badges:
            badge = Badge.query.get(lb.badge_id)
            if badge:
                badges.append({
                    'badge': badge,
                    'awarded_at': lb.awarded_at
                })
        return badges
    
    @staticmethod
    def get_badge_count(learner):
        """Get total number of badges earned"""
        return LearnerBadge.query.filter_by(learner_id=learner.id).count()