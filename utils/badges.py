# utils/badges.py
from models import db, Badge, LearnerBadge, TestAssignment, TestResult
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
                'condition_type': 'total_completed',
                'condition_value': 1
            },
            {
                'name': 'Perfect Score',
                'description': 'Got 100% on a game',
                'icon': '🏆',
                'condition_type': 'perfect_scores',
                'condition_value': 1
            },
            {
                'name': 'Hard Worker',
                'description': 'Completed 10 games',
                'icon': '💪',
                'condition_type': 'total_completed',
                'condition_value': 10
            },
            {
                'name': 'Star Learner',
                'description': 'Completed 25 games',
                'icon': '⭐',
                'condition_type': 'total_completed',
                'condition_value': 25
            },
            {
                'name': 'Mastery',
                'description': 'Passed 5 games with 80%+',
                'icon': '🎯',
                'condition_type': 'high_scores',
                'condition_value': 5
            },
            {
                'name': 'Quick Learner',
                'description': 'Passed 3 games in a row',
                'icon': '🚀',
                'condition_type': 'streak',
                'condition_value': 3
            }
        ]
        
        for badge_data in default_badges:
            existing = Badge.query.filter_by(name=badge_data['name']).first()
            if not existing:
                # Provide all required fields
                badge = Badge(
                    name=badge_data['name'],
                    description=badge_data['description'],
                    icon=badge_data['icon'],
                    condition_type=badge_data['condition_type'],
                    condition_value=badge_data['condition_value'],
                    created_at=datetime.utcnow()
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
            
            # Check based on condition_type and condition_value
            if badge.condition_type == 'total_completed' and total_completed >= badge.condition_value:
                should_award = True
            elif badge.condition_type == 'perfect_scores' and perfect_scores >= badge.condition_value:
                should_award = True
            elif badge.condition_type == 'high_scores' and high_scores >= badge.condition_value:
                should_award = True
            elif badge.condition_type == 'streak':
                recent_results = sorted(results, key=lambda r: r.completed_at, reverse=True)[:badge.condition_value]
                if len(recent_results) >= badge.condition_value and all(r.passed for r in recent_results):
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