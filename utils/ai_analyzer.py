import json
from datetime import datetime

class AIAnalyzer:
    """Analyzes game results to generate cognitive and ADHD reports"""
    
    def __init__(self, learner, game_results):
        self.learner = learner
        self.results = game_results
        self.age = learner.age if learner.age else 8
        
    def analyze(self):
        """Main analysis method"""
        cognitive_scores = self._calculate_cognitive_scores()
        adhd_indicators = self._calculate_adhd_indicators()
        
        return {
            'cognitive_scores': cognitive_scores,
            'adhd_indicators': adhd_indicators,
            'strengths': self._identify_strengths(cognitive_scores),
            'concerns': self._identify_concerns(cognitive_scores, adhd_indicators),
            'recommendations': self._generate_recommendations(cognitive_scores, adhd_indicators),
            'summary': self._generate_summary(cognitive_scores, adhd_indicators, len(self.results)),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    
    def _calculate_cognitive_scores(self):
        """Calculate scores for each cognitive domain"""
        scores = {
            'attention': 0,
            'impulse_control': 0,
            'working_memory': 0,
            'processing_speed': 0,
            'problem_solving': 0,
            'language': 0
        }
        
        counts = {k: 0 for k in scores}
        
        for result in self.results:
            game_name = result.get('game_name', '').lower()
            score = result.get('percentage', 0)
            
            if not score:
                continue
            
            # Map games to cognitive domains
            if 'penguin' in game_name or 'simon' in game_name or 'red light' in game_name:
                scores['impulse_control'] += score
                counts['impulse_control'] += 1
            elif 'memory' in game_name or 'recall' in game_name or 'match' in game_name:
                scores['working_memory'] += score
                counts['working_memory'] += 1
            elif 'attention' in game_name or 'vigilance' in game_name:
                scores['attention'] += score
                counts['attention'] += 1
            elif 'math' in game_name or 'number' in game_name or 'slice' in game_name:
                scores['processing_speed'] += score
                counts['processing_speed'] += 1
            elif 'puzzle' in game_name or 'tower' in game_name or 'maze' in game_name:
                scores['problem_solving'] += score
                counts['problem_solving'] += 1
            elif 'word' in game_name or 'rhyme' in game_name or 'builder' in game_name:
                scores['language'] += score
                counts['language'] += 1
        
        # Calculate averages, default to 50 if no data
        for key in scores:
            if counts[key] > 0:
                scores[key] = round(scores[key] / counts[key], 1)
            else:
                scores[key] = 50  # Default neutral score instead of None
        
        return scores
    
    def _calculate_adhd_indicators(self):
        """Calculate ADHD risk scores based on performance patterns"""
        indicators = {
            'attention_deficit': 0,
            'hyperactivity': 0,
            'impulsivity': 0
        }
        
        counts = {k: 0 for k in indicators}
        
        for result in self.results:
            score = result.get('percentage', 0)
            reaction_time = result.get('reaction_time', 500)
            errors = result.get('errors', 0)
            game_name = result.get('game_name', '').lower()
            
            # Attention deficit indicators
            if 'attention' in game_name or 'vigilance' in game_name:
                if score and score < 60:
                    indicators['attention_deficit'] += (60 - score)
                counts['attention_deficit'] += 1
            
            # Hyperactivity indicators
            if 'penguin' in game_name or 'simon' in game_name:
                if errors > 3:
                    indicators['hyperactivity'] += min(errors * 5, 100)
                counts['hyperactivity'] += 1
            
            # Impulsivity indicators
            if reaction_time < 300 and errors > 0:
                indicators['impulsivity'] += min((300 - reaction_time) / 3, 100)
                counts['impulsivity'] += 1
        
        # Normalize to 0-100 scale
        for key in indicators:
            if counts[key] > 0:
                indicators[key] = min(100, round(indicators[key] / counts[key], 1))
            else:
                indicators[key] = 30  # Default neutral score
        
        # Overall ADHD risk
        overall = (
            indicators['attention_deficit'] * 0.4 +
            indicators['hyperactivity'] * 0.3 +
            indicators['impulsivity'] * 0.3
        )
        
        return {
            'overall_risk': round(overall, 1),
            'attention_deficit_risk': indicators['attention_deficit'],
            'hyperactivity_risk': indicators['hyperactivity'],
            'impulsivity_risk': indicators['impulsivity']
        }
    
    def _identify_strengths(self, scores):
        """Identify cognitive strengths based on scores"""
        strengths = []
        
        domain_names = {
            'attention': 'Attention',
            'impulse_control': 'Impulse Control',
            'working_memory': 'Working Memory',
            'processing_speed': 'Processing Speed',
            'problem_solving': 'Problem Solving',
            'language': 'Language'
        }
        
        for domain, score in scores.items():
            if score and score >= 70:
                strengths.append({
                    'domain': domain_names.get(domain, domain),
                    'score': score,
                    'message': self._get_strength_message(domain)
                })
        
        if not strengths and len(self.results) > 0:
            # Find the highest score
            best_domain = max(scores.items(), key=lambda x: x[1] if x[1] else 0)
            if best_domain[1]:
                strengths.append({
                    'domain': domain_names.get(best_domain[0], best_domain[0]),
                    'score': best_domain[1],
                    'message': 'Relative strength compared to other areas.'
                })
        
        return strengths
    
    def _identify_concerns(self, scores, adhd):
        """Identify areas needing support"""
        concerns = []
        
        domain_names = {
            'attention': 'Attention',
            'impulse_control': 'Impulse Control',
            'working_memory': 'Working Memory',
            'processing_speed': 'Processing Speed',
            'problem_solving': 'Problem Solving',
            'language': 'Language'
        }
        
        for domain, score in scores.items():
            if score and score < 50:
                severity = 'High' if score < 30 else 'Moderate'
                concerns.append({
                    'domain': domain_names.get(domain, domain),
                    'score': score,
                    'severity': severity,
                    'message': self._get_concern_message(domain)
                })
        
        if adhd['overall_risk'] > 60:
            concerns.append({
                'domain': 'ADHD Indicators',
                'score': adhd['overall_risk'],
                'severity': 'High',
                'message': 'Multiple indicators suggest further evaluation may be beneficial. Please consult a healthcare professional for a formal assessment.'
            })
        
        return concerns
    
    def _generate_recommendations(self, scores, adhd):
        """Generate personalized recommendations"""
        recommendations = []
        
        # Helper function to safely get score (default to 50 if None or invalid)
        def get_score(domain):
            val = scores.get(domain, 50)
            return val if val is not None and isinstance(val, (int, float)) else 50
        
        # Attention recommendations
        if get_score('attention') < 55:
            recommendations.append({
                'priority': 'High',
                'area': 'Attention',
                'recommendation': 'Practice with short, focused activities. Start with 5-minute sessions and gradually increase duration.',
                'strategy': 'Use timers, minimize distractions, provide clear step-by-step instructions.',
                'suggested_games': ['Space Signal Keeper', 'Lookout Keeper'],
                'expected_improvement': 'Increased sustained attention and focus'
            })
        
        # Impulse control recommendations
        if get_score('impulse_control') < 55 or adhd.get('impulsivity_risk', 0) > 50:
            recommendations.append({
                'priority': 'High',
                'area': 'Impulse Control',
                'recommendation': 'Practice "stop and think" strategies before responding. Encourage counting to three before acting.',
                'strategy': 'Use visual cues and verbal reminders to pause before responding.',
                'suggested_games': ['Penguin Says', 'Red Light, Green Light'],
                'expected_improvement': 'Better response inhibition and self-regulation'
            })
        
        # Memory recommendations
        if get_score('working_memory') < 55:
            recommendations.append({
                'priority': 'Medium',
                'area': 'Working Memory',
                'recommendation': 'Use visual aids, repetition, and break tasks into smaller steps.',
                'strategy': 'Chunk information, use mnemonics, practice verbal rehearsal.',
                'suggested_games': ['Memory Match', 'Grocery Run'],
                'expected_improvement': 'Improved recall and information retention'
            })
        
        # Processing speed recommendations
        if get_score('processing_speed') < 55:
            recommendations.append({
                'priority': 'Medium',
                'area': 'Processing Speed',
                'recommendation': 'Allow extra time for tasks. Use timed practice activities at a comfortable pace.',
                'strategy': 'Build automaticity through repetition and practice.',
                'suggested_games': ['Number Slice', 'Fruit Shop Math'],
                'expected_improvement': 'Faster information processing with practice'
            })
        
        # Problem-solving recommendations
        if get_score('problem_solving') < 55:
            recommendations.append({
                'priority': 'Low',
                'area': 'Problem Solving',
                'recommendation': 'Encourage step-by-step thinking and verbalizing solutions.',
                'strategy': 'Model problem-solving strategies, use graphic organizers.',
                'suggested_games': ['Tower of Hanoi', 'Find the Cheese'],
                'expected_improvement': 'Better strategic planning and flexible thinking'
            })
        
        if not recommendations and len(self.results) > 5:
            recommendations.append({
                'priority': 'Low',
                'area': 'Maintenance',
                'recommendation': 'Continue regular practice to maintain and build upon current skill levels.',
                'strategy': 'Engage with a variety of games across all cognitive domains.',
                'suggested_games': ['All games'],
                'expected_improvement': 'Continued progress and skill consolidation'
            })
        
        return recommendations
    
    def _generate_summary(self, scores, adhd, total_games):
        """Generate a readable summary report"""
        
        # Calculate average score safely
        valid_scores = [s for s in scores.values() if isinstance(s, (int, float))]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 50
        
        # Determine overall level
        if avg_score >= 75:
            message = "performing well above age expectations"
        elif avg_score >= 55:
            message = "meeting expected developmental milestones"
        else:
            message = "would benefit from additional support and practice"
        
        summary = f"""
COGNITIVE ASSESSMENT SUMMARY

Learner: {self.learner.user.name if self.learner.user else 'N/A'}
Age: {self.age} years
Grade: {self.learner.grade}
Games Completed: {total_games}
Assessment Date: {datetime.now().strftime('%Y-%m-%d')}

OVERALL ASSESSMENT
Based on {total_games} completed games, this learner is {message}.

COGNITIVE PROFILE
- Attention: {scores.get('attention', 50)}%
- Impulse Control: {scores.get('impulse_control', 50)}%
- Working Memory: {scores.get('working_memory', 50)}%
- Processing Speed: {scores.get('processing_speed', 50)}%
- Problem Solving: {scores.get('problem_solving', 50)}%
- Language: {scores.get('language', 50)}%

ADHD SCREENING INDICATORS
- Overall Risk Level: {adhd.get('overall_risk', 0)}%
- Attention Deficit Indicators: {adhd.get('attention_deficit_risk', 0)}%
- Hyperactivity Indicators: {adhd.get('hyperactivity_risk', 0)}%
- Impulsivity Indicators: {adhd.get('impulsivity_risk', 0)}%

INTERPRETATION GUIDELINES
- 0-30%: Minimal indicators
- 31-60%: Moderate indicators - may benefit from strategies
- 61-100%: Significant indicators - consider professional consultation

IMPORTANT NOTE
This is an AI-generated screening report based on game performance data. 
It is not a clinical diagnosis. For medical advice or ADHD diagnosis, 
please consult a qualified healthcare professional or educational psychologist.
"""
        
        return summary.strip()
    
    def _get_strength_message(self, domain):
        messages = {
            'attention': 'Strong ability to focus and sustain attention on tasks.',
            'impulse_control': 'Excellent self-control and ability to think before acting.',
            'working_memory': 'Good at holding and manipulating information in mind.',
            'processing_speed': 'Quick and efficient information processing abilities.',
            'problem_solving': 'Strong analytical and strategic thinking skills.',
            'language': 'Excellent verbal and language processing abilities.'
        }
        return messages.get(domain, 'Notable strength in this cognitive area.')

    def _get_concern_message(self, domain):
        messages = {
            'attention': 'May benefit from strategies to improve focus and reduce distractions.',
            'impulse_control': 'May benefit from practicing pause-and-think strategies before responding.',
            'working_memory': 'May benefit from using visual aids, repetition, and breaking tasks into chunks.',
            'processing_speed': 'May benefit from extra time and breaking tasks into smaller steps.',
            'problem_solving': 'May benefit from guided practice and verbalizing solutions step by step.',
            'language': 'May benefit from additional language-rich activities and explicit instruction.'
        }
        return messages.get(domain, 'May benefit from targeted support in this area.')