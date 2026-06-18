# utils/cognitive_assessment.py
import json
import math
from datetime import datetime
from models import db, Learner, TestResult, TestAssignment, Game

class CognitiveAssessmentService:
    """Service for analyzing learner performance and detecting learning conditions"""
    
    @staticmethod
    def analyze_learner_performance(learner_id):
        """Analyze learner's game performance to detect potential learning conditions"""
        
        learner = Learner.query.get(learner_id)
        if not learner:
            return None
        
        # Get all completed assignments
        assignments = TestAssignment.query.filter_by(
            learner_id=learner.id,
            status='completed'
        ).all()
        
        if len(assignments) < 3:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 3 completed games for analysis',
                'games_played': len(assignments)
            }
        
        # Collect all results with categories and timing
        results = []
        language_scores = []
        attention_scores = []
        memory_scores = []
        all_scores = []
        time_taken_list = []
        
        for assignment in assignments:
            result = TestResult.query.filter_by(assignment_id=assignment.id).first()
            if result:
                game = Game.query.get(assignment.game_id)
                
                # Calculate time taken
                time_taken = 0
                if assignment.started_at and assignment.completed_at:
                    time_taken = (assignment.completed_at - assignment.started_at).total_seconds()
                
                result_data = {
                    'score': result.percentage,
                    'passed': result.passed,
                    'category': game.category if game else 'Unknown',
                    'time_taken': time_taken,
                    'game_id': game.id if game else None
                }
                results.append(result_data)
                all_scores.append(result.percentage)
                
                if time_taken > 0:
                    time_taken_list.append(time_taken)
                
                # Track category-specific scores
                if game and game.category == 'Language':
                    language_scores.append(result.percentage)
                if game and game.category == 'Attention':
                    attention_scores.append(result.percentage)
                if game and game.category == 'Memory':
                    memory_scores.append(result.percentage)
        
        # Calculate cognitive domain scores
        cognitive_scores = CognitiveAssessmentService._calculate_cognitive_scores(results)
        
        # DETECT DISABILITY - Calculate condition probabilities
        condition_probs = CognitiveAssessmentService._detect_conditions(
            cognitive_scores, 
            results,
            learner,
            language_scores,
            attention_scores,
            memory_scores,
            all_scores,
            time_taken_list
        )
        
        # Generate recommendations based on detection
        recommendations = CognitiveAssessmentService._generate_recommendations(
            cognitive_scores,
            condition_probs,
            learner
        )
        
        # Save assessment to learner
        learner.cognitive_scores = json.dumps(cognitive_scores)
        learner.condition_probabilities = json.dumps(condition_probs)
        learner.recommendations = json.dumps(recommendations)
        learner.assessment_completed = True
        learner.last_assessment = datetime.utcnow()
        db.session.commit()
        
        return {
            'cognitive_scores': cognitive_scores,
            'condition_probabilities': condition_probs,
            'recommendations': recommendations,
            'games_analyzed': len(results),
            'analysis_date': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _calculate_cognitive_scores(results):
        """Calculate scores for each cognitive domain"""
        
        if not results:
            return {'attention': 50, 'memory': 50, 'processing_speed': 50, 'problem_solving': 50}
        
        all_scores = [r['score'] for r in results]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 50
        
        # Attention score - weighted by category
        attention_score = avg_score
        attention_results = [r for r in results if r['category'] == 'Attention']
        if attention_results:
            attention_score = sum([r['score'] for r in attention_results]) / len(attention_results)
        
        # Memory score
        memory_score = avg_score
        memory_results = [r for r in results if r['category'] == 'Memory']
        if memory_results:
            memory_score = sum([r['score'] for r in memory_results]) / len(memory_results)
        
        # Processing speed (based on time taken)
        time_taken_list = [r['time_taken'] for r in results if r['time_taken'] > 0]
        processing_score = 50
        if time_taken_list:
            avg_time = sum(time_taken_list) / len(time_taken_list)
            if avg_time < 60:  # Under 1 minute - fast
                processing_score = 85
            elif avg_time < 120:  # Under 2 minutes - average
                processing_score = 60
            elif avg_time < 180:  # Under 3 minutes - slow
                processing_score = 35
            else:  # Over 3 minutes - very slow
                processing_score = 20
        
        # Problem solving (accuracy on harder questions)
        problem_solving = avg_score
        if len(results) > 0:
            weighted_scores = []
            for r in results:
                # Weight by time spent (more time often means harder problems)
                if r['time_taken'] > 0:
                    weight = min(1.5, r['time_taken'] / 60)
                    weighted_scores.append(r['score'] * weight)
                else:
                    weighted_scores.append(r['score'])
            
            if weighted_scores:
                problem_solving = sum(weighted_scores) / len(weighted_scores)
        
        return {
            'attention': round(min(100, attention_score), 1),
            'memory': round(min(100, memory_score), 1),
            'processing_speed': round(min(100, processing_score), 1),
            'problem_solving': round(min(100, problem_solving), 1)
        }
    
    @staticmethod
    def _detect_conditions(cognitive_scores, results, learner, language_scores, attention_scores, memory_scores, all_scores, time_taken_list):
        """DETECT DISABILITY - Calculate probability of each learning condition"""
        
        # === DETECT ADHD ===
        adhd_score = 0
        adhd_indicators = []
        
        # Indicator 1: Low attention score
        attention = cognitive_scores.get('attention', 50)
        if attention < 60:
            adhd_score += 30
            adhd_indicators.append(f"Low attention score: {attention}% (below 60%)")
        elif attention < 50:
            adhd_score += 40
            adhd_indicators.append(f"Very low attention score: {attention}% (below 50%)")
        
        # Indicator 2: High score variability (inconsistent performance)
        if len(all_scores) > 1:
            mean = sum(all_scores) / len(all_scores)
            variance = sum((s - mean) ** 2 for s in all_scores) / len(all_scores)
            std_dev = math.sqrt(variance)
            
            if std_dev > 25:
                adhd_score += 20
                adhd_indicators.append(f"High score variability: std_dev {std_dev:.1f} (above 25)")
            elif std_dev > 20:
                adhd_score += 10
                adhd_indicators.append(f"Moderate score variability: std_dev {std_dev:.1f}")
        
        # Indicator 3: Impulsivity (quick wrong answers)
        quick_wrong = sum(1 for r in results if r['time_taken'] < 30 and r['score'] < 50)
        total_questions = len(results) if results else 1
        quick_wrong_ratio = quick_wrong / total_questions
        
        if quick_wrong_ratio > 0.3:
            adhd_score += 20
            adhd_indicators.append(f"Impulsivity: {quick_wrong} quick wrong answers ({quick_wrong_ratio*100:.0f}%)")
        elif quick_wrong_ratio > 0.2:
            adhd_score += 10
            adhd_indicators.append(f"Some impulsivity: {quick_wrong} quick wrong answers ({quick_wrong_ratio*100:.0f}%)")
        
        # Indicator 4: Multiple failed attempts on easy games
        failed_games = sum(1 for r in results if not r['passed'] and r['score'] < 40)
        if total_questions > 0 and failed_games / total_questions > 0.3:
            adhd_score += 10
            adhd_indicators.append(f"Struggled with easy games: {failed_games} failed attempts")
        
        # === DETECT DYSLEXIA ===
        dyslexia_score = 0
        dyslexia_indicators = []
        
        # Indicator 1: Low language scores
        if language_scores and len(language_scores) > 0:
            avg_language = sum(language_scores) / len(language_scores)
            
            if avg_language < 50:
                dyslexia_score += 30
                dyslexia_indicators.append(f"Low language score: {avg_language:.1f}% (below 50%)")
            elif avg_language < 60:
                dyslexia_score += 20
                dyslexia_indicators.append(f"Moderate language score: {avg_language:.1f}% (below 60%)")
            
            # Compare with other categories
            other_scores = [r['score'] for r in results if r['category'] != 'Language']
            if other_scores:
                avg_other = sum(other_scores) / len(other_scores)
                if avg_language < avg_other - 20:
                    dyslexia_score += 30
                    dyslexia_indicators.append(f"Language significantly lower than other areas: {avg_language:.1f}% vs {avg_other:.1f}% (-{avg_other - avg_language:.1f}%)")
                elif avg_language < avg_other - 10:
                    dyslexia_score += 15
                    dyslexia_indicators.append(f"Language lower than other areas: {avg_language:.1f}% vs {avg_other:.1f}%")
        
        # Indicator 2: Slow response to text questions
        language_times = [r['time_taken'] for r in results if r['category'] == 'Language' and r['time_taken'] > 0]
        non_language_times = [r['time_taken'] for r in results if r['category'] != 'Language' and r['time_taken'] > 0]
        
        if language_times and non_language_times:
            avg_lang_time = sum(language_times) / len(language_times)
            avg_non_lang_time = sum(non_language_times) / len(non_language_times)
            
            if avg_lang_time > avg_non_lang_time * 1.5:
                dyslexia_score += 20
                dyslexia_indicators.append(f"Slow text response: {avg_lang_time:.0f}s vs non-text {avg_non_lang_time:.0f}s")
        
        # Indicator 3: Better performance in visual vs text
        if attention_scores and language_scores:
            avg_attention = sum(attention_scores) / len(attention_scores)
            avg_language = sum(language_scores) / len(language_scores)
            if avg_attention > avg_language + 20:
                dyslexia_score += 10
                dyslexia_indicators.append(f"Better visual performance: Attention {avg_attention:.1f}% vs Language {avg_language:.1f}%")
        
        # === DETECT COGNITIVE PACE ===
        pace_score = 0
        pace_indicators = []
        
        # Indicator 1: Slow processing speed
        processing_speed = cognitive_scores.get('processing_speed', 50)
        if processing_speed < 45:
            pace_score += 30
            pace_indicators.append(f"Slow processing speed: {processing_speed}% (below 45%)")
        elif processing_speed < 55:
            pace_score += 20
            pace_indicators.append(f"Moderate processing speed: {processing_speed}% (below 55%)")
        
        # Indicator 2: Takes longer but gets correct answers
        slow_correct = sum(1 for r in results if r['time_taken'] > 120 and r['score'] >= 70)
        slow_correct_ratio = slow_correct / len(results) if results else 0
        
        if slow_correct_ratio > 0.4:
            pace_score += 30
            pace_indicators.append(f"Slow but accurate: {slow_correct} questions ({slow_correct_ratio*100:.0f}%) took >2min and got correct")
        elif slow_correct_ratio > 0.25:
            pace_score += 20
            pace_indicators.append(f"Some slow but accurate responses: {slow_correct} questions")
        
        # Indicator 3: Consistent but slow performance
        if len(all_scores) > 1 and time_taken_list:
            mean = sum(all_scores) / len(all_scores)
            variance = sum((s - mean) ** 2 for s in all_scores) / len(all_scores)
            std_dev = math.sqrt(variance)
            
            avg_time = sum(time_taken_list) / len(time_taken_list)
            if std_dev < 10 and avg_time > 120:
                pace_score += 10
                pace_indicators.append(f"Consistent but slow: std_dev {std_dev:.1f} (<10) with avg time {avg_time:.0f}s")
        
        # Normalize scores to 0-100
        adhd_score = min(100, adhd_score)
        dyslexia_score = min(100, dyslexia_score)
        pace_score = min(100, pace_score)
        
        # Age adjustment (younger children may show signs that resolve with age)
        if learner.grade <= 1:
            adhd_score *= 0.7
            dyslexia_score *= 0.7
            pace_score *= 0.7
        elif learner.grade <= 2:
            adhd_score *= 0.8
            dyslexia_score *= 0.8
            pace_score *= 0.8
        
        return {
            'adhd': round(adhd_score, 1),
            'dyslexia': round(dyslexia_score, 1),
            'cognitive_pace': round(pace_score, 1),
            'adhd_indicators': adhd_indicators,
            'dyslexia_indicators': dyslexia_indicators,
            'pace_indicators': pace_indicators
        }
    
    @staticmethod
    def _generate_recommendations(cognitive_scores, condition_probs, learner):
        """Generate personalized recommendations based on detected conditions"""
        
        recommendations = []
        
        # Get condition probabilities
        adhd_prob = condition_probs.get('adhd', 0)
        dyslexia_prob = condition_probs.get('dyslexia', 0)
        pace_prob = condition_probs.get('cognitive_pace', 0)
        
        # === ADHD Recommendations ===
        if adhd_prob >= 70:
            recommendations.append({
                'title': 'ADHD Support Strategies (High Priority)',
                'description': f'The learner shows strong signs of ADHD ({adhd_prob:.0f}% probability). Immediate support is recommended.',
                'interventions': [
                    'Implement short, focused learning sessions (15-20 minutes)',
                    'Use visual rewards and immediate positive reinforcement',
                    'Incorporate movement breaks between tasks',
                    'Provide clear, simple instructions with visual cues',
                    'Use timers to help with time management',
                    'Consider seating near the teacher to minimize distractions',
                    'Break tasks into smaller, manageable chunks'
                ],
                'recommended_games': ['Attention Games', 'Memory Games', 'Sensory Games']
            })
        elif adhd_prob >= 50:
            recommendations.append({
                'title': 'ADHD Support Strategies (Moderate)',
                'description': f'The learner shows some signs of ADHD ({adhd_prob:.0f}% probability). Monitor and provide support.',
                'interventions': [
                    'Use short, engaging activities',
                    'Provide frequent breaks',
                    'Use positive reinforcement',
                    'Monitor attention levels',
                    'Consider a quiet work space'
                ],
                'recommended_games': ['Attention Games', 'Memory Games']
            })
        
        # === Dyslexia Recommendations ===
        if dyslexia_prob >= 70:
            recommendations.append({
                'title': 'Dyslexia Support Strategies (High Priority)',
                'description': f'The learner shows strong signs of dyslexia ({dyslexia_prob:.0f}% probability). Immediate support is recommended.',
                'interventions': [
                    'Provide text-to-speech support for reading materials',
                    'Use large, dyslexia-friendly fonts (OpenDyslexic, Arial)',
                    'Implement multi-sensory learning approaches',
                    'Allow extra time for reading and writing tasks',
                    'Use visual aids and graphic organizers',
                    'Break tasks into smaller, manageable steps',
                    'Use colored overlays to reduce visual stress'
                ],
                'recommended_games': ['Language Games', 'Memory Games', 'Sensory Games']
            })
        elif dyslexia_prob >= 50:
            recommendations.append({
                'title': 'Dyslexia Support Strategies (Moderate)',
                'description': f'The learner shows some signs of dyslexia ({dyslexia_prob:.0f}% probability). Monitor and provide support.',
                'interventions': [
                    'Use audio support for text',
                    'Provide extra time for reading tasks',
                    'Use visual learning materials',
                    'Consider reading accommodations'
                ],
                'recommended_games': ['Language Games', 'Memory Games']
            })
        
        # === Cognitive Pace Recommendations ===
        if pace_prob >= 70:
            recommendations.append({
                'title': 'Cognitive Pace Support Strategies (High Priority)',
                'description': f'The learner shows strong signs of needing cognitive pace support ({pace_prob:.0f}% probability).',
                'interventions': [
                    'Allow extended time for completing tasks',
                    'Provide step-by-step instructions',
                    'Use visual progress tracking to show completion',
                    'Allow multiple attempts to reinforce learning',
                    'Break complex tasks into simple steps',
                    'Use calming colors and minimal distractions',
                    'Provide regular progress updates'
                ],
                'recommended_games': ['Math Games', 'Memory Games', 'Attention Games']
            })
        elif pace_prob >= 50:
            recommendations.append({
                'title': 'Cognitive Pace Support Strategies (Moderate)',
                'description': f'The learner shows some signs of needing cognitive pace support ({pace_prob:.0f}% probability).',
                'interventions': [
                    'Provide extra time for tasks',
                    'Use step-by-step instructions',
                    'Allow multiple attempts',
                    'Monitor processing speed'
                ],
                'recommended_games': ['Math Games', 'Memory Games']
            })
        
        # === General Recommendations Based on Cognitive Scores ===
        for domain, score in cognitive_scores.items():
            if score < 35:
                recommendations.append({
                    'title': f'{domain.replace("_", " ").title()} Development - Critical',
                    'description': f'Score: {score}%. Immediate intervention needed.',
                    'interventions': [
                        f'Daily practice activities for {domain}',
                        f'Use games that target {domain} skills',
                        'Work with a specialist if available'
                    ]
                })
            elif score < 50:
                recommendations.append({
                    'title': f'{domain.replace("_", " ").title()} Development - Needs Support',
                    'description': f'Score: {score}%. Regular practice recommended.',
                    'interventions': [
                        f'Practice {domain} skills 3-4 times per week',
                        f'Use specific games for {domain} development',
                        'Monitor progress weekly'
                    ]
                })
        
        # Add overall summary
        if recommendations:
            recommendations.append({
                'title': 'Overall Learning Plan',
                'description': 'Based on the complete analysis, the following overall strategies are recommended:',
                'interventions': [
                    'Consistent practice with targeted games',
                    'Regular progress monitoring (weekly)',
                    'Collaboration between educators and parents',
                    'Celebrate small achievements to build confidence',
                    'Adjust interventions based on ongoing progress'
                ]
            })
        
        return recommendations[:10]