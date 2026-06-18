# utils/badges.py - Minimal version
from models import db, Badge, LearnerBadge, TestAssignment, TestResult
from datetime import datetime

class BadgeService:
    
    @staticmethod
    def initialize_badges():
        """Initialize default badges if they don't exist"""
        badge_names = [
            'First Steps',
            'Perfect Score', 
            'Hard Worker',
            'Star Learner',
            'Mastery',
            'Quick Learner'
        ]
        
        for name in badge_names:
            existing = Badge.query.filter_by(name=name).first()
            if not existing:
                badge = Badge(name=name)
                db.session.add(badge)
        
        db.session.commit()
        print("Badges initialized")
    
    @staticmethod
    def check_and_award_badges(learner):
        """Check if learner qualifies for any badges and award them"""
        assignments = TestAssignment.query.filter_by(learner_id=learner.id, status='completed').all()
        if not assignments:
            return []
        
        results = TestResult.query.filter(TestResult.assignment_id.in_([a.id for a in assignments])).all()
        total_completed = len(assignments)
        perfect_scores = len([r for r in results if r.percentage == 100])
        high_scores = len([r for r in results if r.percentage >= 80])
        
        earned_badge_ids = [lb.badge_id for lb in LearnerBadge.query.filter_by(learner_id=learner.id).all()]
        all_badges = Badge.query.all()
        new_badges = []
        
        for badge in all_badges:
            if badge.id in earned_badge_ids:
                continue
            
            should_award = False
            if badge.name == 'First Steps' and total_completed >= 1:
                should_award = True
            elif badge.name == 'Perfect Score' and perfect_scores >= 1:
                should_award = True
            elif badge.name == 'Hard Worker' and total_completed >= 10:
                should_award = True
            elif badge.name == 'Star Learner' and total_completed >= 25:
                should_award = True
            elif badge.name == 'Mastery' and high_scores >= 5:
                should_award = True
            elif badge.name == 'Quick Learner':
                recent = sorted(results, key=lambda r: r.completed_at, reverse=True)[:3]
                if len(recent) >= 3 and all(r.passed for r in recent):
                    should_award = True
            
            if should_award:
                learner_badge = LearnerBadge(learner_id=learner.id, badge_id=badge.id, awarded_at=datetime.utcnow())
                db.session.add(learner_badge)
                new_badges.append(badge)
        
        if new_badges:
            db.session.commit()
        return new_badges
    
    @staticmethod
    def get_learner_badges(learner):
        learner_badges = LearnerBadge.query.filter_by(learner_id=learner.id).all()
        return [{'badge': Badge.query.get(lb.badge_id), 'awarded_at': lb.awarded_at} for lb in learner_badges if Badge.query.get(lb.badge_id)]
    
    @staticmethod
    def get_badge_count(learner):
        return LearnerBadge.query.filter_by(learner_id=learner.id).count()