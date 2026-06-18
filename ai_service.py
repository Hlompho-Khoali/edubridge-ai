# ai_service.py - Complete file with game generation and accessibility features
import json
import re
import random
from datetime import datetime
from ai_config import AIConfig

class AIService:
    """AI Service with Game Generation and Accessibility Features"""
    
    # ===== DISABILITY TYPES METHOD =====
    
    @staticmethod
    def get_disability_types():
        """Get available disability types with their features"""
        return {
            'none': {
                'name': 'No Specific Disability',
                'description': 'Standard game for all learners',
                'features': {}
            },
            'adhd': {
                'name': 'ADHD Support',
                'description': 'Games designed for learners with ADHD',
                'features': {
                    'short_rounds': True,
                    'visual_rewards': True,
                    'movement_breaks': True,
                    'sound_effects': True,
                    'progress_tracking': True,
                    'max_questions': 5,
                    'time_limit': 3,
                    'visual_style': 'high_contrast',
                    'tips': [
                        'Take movement breaks between questions',
                        'Use visual rewards for each correct answer',
                        'Keep sessions short and focused',
                        'Provide immediate positive feedback'
                    ]
                }
            },
            'dyslexia': {
                'name': 'Dyslexia Support',
                'description': 'Games designed for learners with dyslexia',
                'features': {
                    'read_aloud': True,
                    'large_font': True,
                    'high_contrast': True,
                    'audio_support': True,
                    'no_time_limit': True,
                    'visual_cues': True,
                    'max_questions': 8,
                    'time_limit': None,
                    'visual_style': 'dyslexia_friendly',
                    'tips': [
                        'Use read-aloud feature for all text',
                        'Use large, clear fonts',
                        'Take your time - no time limit',
                        'Use visual cues alongside text',
                        'Color-code important information'
                    ]
                }
            },
            'cognitive_pace': {
                'name': 'Cognitive Pace Support',
                'description': 'Games designed for learners who need more time',
                'features': {
                    'adjustable_speed': True,
                    'multiple_attempts': True,
                    'step_by_step': True,
                    'visual_progress': True,
                    'positive_reinforcement': True,
                    'max_questions': 6,
                    'time_limit': 10,
                    'visual_style': 'calm_colors',
                    'tips': [
                        'Go at your own pace',
                        'You can adjust the speed of games',
                        'Multiple attempts are allowed',
                        'Step-by-step instructions are available',
                        'Visual progress tracking helps you see your growth'
                    ]
                }
            }
        }
    
    @staticmethod
    def generate_game_for_disability(topic, grade, disability_type, game_type='default', num_questions=10):
        """Generate a game specifically designed for a disability type"""
        
        # Get disability configuration
        disability_config = AIService.get_disability_types().get(disability_type, {})
        features = disability_config.get('features', {})
        
        # Get category configuration
        categories = AIService.get_game_categories()
        category_config = categories.get(game_type, categories.get('memory'))
        
        # Generate age-appropriate questions
        questions = AIService._get_grade_questions(topic, grade, disability_type)
        
        # Limit questions based on disability
        max_q = features.get('max_questions', num_questions)
        if len(questions) > max_q:
            questions = questions[:max_q]
        
        # Get disability tips
        tips = features.get('tips', [])
        
        # Build game data with disability features
        game_data = {
            'name': f'{disability_config.get("name", "Learning")} - {topic.capitalize()} Explorer',
            'description': f'Educational game designed for learners with {disability_config.get("name", "learning needs")}. {category_config.get("description", "Fun learning game")}',
            'category': game_type,
            'subcategory': disability_type,
            'grade_level': grade,
            'difficulty': AIService._get_difficulty(grade),
            'questions': questions,
            'accessibility_features': features,
            'visual_style': features.get('visual_style', 'default'),
            'audio_support': features.get('audio_support', False),
            'movement_breaks': features.get('movement_breaks', False),
            'progress_tracking': features.get('progress_tracking', True),
            'max_questions': len(questions),
            'time_limit': features.get('time_limit', 10),
            'disability_type': disability_type,
            'recommended_for': disability_type,
            'tips': tips
        }
        
        return game_data
    
    @staticmethod
    def get_game_categories():
        """Get all game categories with accessibility configurations"""
        return {
            'memory': {
                'name': 'Memory Games',
                'description': 'Build working memory and recall skills',
                'grade_levels': [1, 2, 3],
                'accessibility': {
                    'adhd': {
                        'short_rounds': True,
                        'visual_rewards': True,
                        'movement_breaks': True,
                        'sound_effects': True,
                        'progress_tracking': True,
                        'max_questions': 5,
                        'time_limit': 3,
                        'description': 'Short, engaging memory games with frequent rewards'
                    },
                    'dyslexia': {
                        'read_aloud': True,
                        'large_font': True,
                        'high_contrast': True,
                        'audio_support': True,
                        'no_time_limit': True,
                        'visual_cues': True,
                        'max_questions': 8,
                        'time_limit': None,
                        'description': 'Memory games with visual and audio support'
                    },
                    'cognitive_pace': {
                        'adjustable_speed': True,
                        'multiple_attempts': True,
                        'step_by_step': True,
                        'visual_progress': True,
                        'positive_reinforcement': True,
                        'max_questions': 6,
                        'time_limit': 10,
                        'description': 'Memory games at your own pace'
                    }
                }
            },
            'attention': {
                'name': 'Attention Games',
                'description': 'Build focus and concentration skills',
                'grade_levels': [1, 2, 3],
                'accessibility': {
                    'adhd': {
                        'short_rounds': True,
                        'visual_rewards': True,
                        'movement_breaks': True,
                        'sound_effects': True,
                        'progress_tracking': True,
                        'max_questions': 5,
                        'time_limit': 3,
                        'description': 'Quick attention games with movement breaks'
                    },
                    'dyslexia': {
                        'read_aloud': True,
                        'large_font': True,
                        'high_contrast': True,
                        'audio_support': True,
                        'no_time_limit': True,
                        'visual_cues': True,
                        'max_questions': 8,
                        'time_limit': None,
                        'description': 'Focus games with visual and audio support'
                    },
                    'cognitive_pace': {
                        'adjustable_speed': True,
                        'multiple_attempts': True,
                        'step_by_step': True,
                        'visual_progress': True,
                        'positive_reinforcement': True,
                        'max_questions': 6,
                        'time_limit': 10,
                        'description': 'Attention games at your own pace'
                    }
                }
            },
            'language': {
                'name': 'Language Games',
                'description': 'Build reading and language skills',
                'grade_levels': [1, 2, 3],
                'accessibility': {
                    'adhd': {
                        'short_rounds': True,
                        'visual_rewards': True,
                        'movement_breaks': True,
                        'sound_effects': True,
                        'progress_tracking': True,
                        'max_questions': 5,
                        'time_limit': 4,
                        'description': 'Quick language games with rewards'
                    },
                    'dyslexia': {
                        'read_aloud': True,
                        'large_font': True,
                        'high_contrast': True,
                        'audio_support': True,
                        'no_time_limit': True,
                        'visual_cues': True,
                        'max_questions': 8,
                        'time_limit': None,
                        'description': 'Language games with dyslexia-friendly features'
                    },
                    'cognitive_pace': {
                        'adjustable_speed': True,
                        'multiple_attempts': True,
                        'step_by_step': True,
                        'visual_progress': True,
                        'positive_reinforcement': True,
                        'max_questions': 6,
                        'time_limit': 10,
                        'description': 'Language games at your own pace'
                    }
                }
            },
            'math': {
                'name': 'Math Games',
                'description': 'Build basic math and logic skills',
                'grade_levels': [1, 2, 3],
                'accessibility': {
                    'adhd': {
                        'short_rounds': True,
                        'visual_rewards': True,
                        'movement_breaks': True,
                        'sound_effects': True,
                        'progress_tracking': True,
                        'max_questions': 5,
                        'time_limit': 3,
                        'description': 'Quick math games with visual rewards'
                    },
                    'dyslexia': {
                        'read_aloud': True,
                        'large_font': True,
                        'high_contrast': True,
                        'audio_support': True,
                        'no_time_limit': True,
                        'visual_cues': True,
                        'max_questions': 8,
                        'time_limit': None,
                        'description': 'Math games with visual and audio support'
                    },
                    'cognitive_pace': {
                        'adjustable_speed': True,
                        'multiple_attempts': True,
                        'step_by_step': True,
                        'visual_progress': True,
                        'positive_reinforcement': True,
                        'max_questions': 6,
                        'time_limit': 10,
                        'description': 'Math games at your own pace'
                    }
                }
            },
            'sensory': {
                'name': 'Sensory Games',
                'description': 'Provide sensory breaks and movement',
                'grade_levels': [1, 2, 3],
                'accessibility': {
                    'adhd': {
                        'short_rounds': True,
                        'visual_rewards': True,
                        'movement_breaks': True,
                        'sound_effects': True,
                        'progress_tracking': True,
                        'max_questions': 4,
                        'time_limit': 2,
                        'description': 'Quick sensory games with movement'
                    },
                    'dyslexia': {
                        'read_aloud': True,
                        'large_font': True,
                        'high_contrast': True,
                        'audio_support': True,
                        'no_time_limit': True,
                        'visual_cues': True,
                        'max_questions': 6,
                        'time_limit': None,
                        'description': 'Sensory games with clear visual cues'
                    },
                    'cognitive_pace': {
                        'adjustable_speed': True,
                        'multiple_attempts': True,
                        'step_by_step': True,
                        'visual_progress': True,
                        'positive_reinforcement': True,
                        'max_questions': 5,
                        'time_limit': 8,
                        'description': 'Sensory games at your own pace'
                    }
                }
            }
        }
    
    @staticmethod
    def get_accessibility_types():
        """Get available accessibility types"""
        return ['default', 'adhd', 'dyslexia', 'cognitive_pace']
    
    @staticmethod
    def get_grade_levels():
        """Get available grade levels"""
        return [1, 2, 3]
    
    @staticmethod
    def get_accessibility_label(access_type):
        """Get human-readable label for accessibility type"""
        labels = {
            'default': 'Standard',
            'adhd': 'ADHD Support',
            'dyslexia': 'Dyslexia Support',
            'cognitive_pace': 'Cognitive Pace Support'
        }
        return labels.get(access_type, access_type)
    
    @staticmethod
    def _get_visual_style(access_type):
        """Get appropriate visual style based on accessibility type"""
        styles = {
            'default': 'default',
            'adhd': 'high_contrast',
            'dyslexia': 'dyslexia_friendly',
            'cognitive_pace': 'calm_colors'
        }
        return styles.get(access_type, 'default')
    
    @staticmethod
    def _get_difficulty(grade):
        """Get difficulty level based on grade"""
        if grade <= 1:
            return 'Beginner'
        elif grade == 2:
            return 'Intermediate'
        else:
            return 'Advanced'
    
    @staticmethod
    def get_recommendations(learner_data):
        """Generate personalized learning recommendations"""
        name = learner_data.get('name', 'Student')
        avg_score = learner_data.get('avg_score', 0)
        games_completed = learner_data.get('games_completed', 0)
        grade = learner_data.get('grade', 1)
        
        if avg_score >= 80:
            level = 'excellent'
            level_text = 'Excellent Progress!'
        elif avg_score >= 60:
            level = 'good'
            level_text = 'Good Progress!'
        elif avg_score >= 40:
            level = 'developing'
            level_text = 'Building Skills'
        else:
            level = 'needs_support'
            level_text = 'Keep Going!'
        
        recommendations = []
        
        if games_completed == 0:
            recommendations.append({
                'title': 'Getting Started',
                'description': f"{name} hasn't completed any games yet. Start with beginner-level games to build confidence."
            })
            recommendations.append({
                'title': 'First Steps',
                'description': "Try simple memory or attention games - these are great for beginners!"
            })
            recommendations.append({
                'title': 'Daily Practice',
                'description': "Set aside 15 minutes daily for game-based learning."
            })
        elif level == 'excellent':
            recommendations.append({
                'title': 'Excellent Progress!',
                'description': f"{name} is mastering the material with a {avg_score:.0f}% average score!"
            })
            recommendations.append({
                'title': 'Challenge Yourself',
                'description': "Try more advanced games to continue growing."
            })
            recommendations.append({
                'title': 'Peer Tutor',
                'description': f"Encourage {name} to help classmates who are struggling."
            })
        elif level == 'good':
            recommendations.append({
                'title': 'Good Progress!',
                'description': f"{name} is doing well with a {avg_score:.0f}% average score. Keep it up!"
            })
            recommendations.append({
                'title': 'Focus Areas',
                'description': "Practice more in areas with lower scores."
            })
            recommendations.append({
                'title': 'Consistent Practice',
                'description': "Continue practicing 15-20 minutes daily to improve."
            })
        elif level == 'developing':
            recommendations.append({
                'title': 'Building Skills',
                'description': f"{name} is developing skills with a {avg_score:.0f}% average."
            })
            recommendations.append({
                'title': 'Keep Going!',
                'description': "Every game teaches something new. Review mistakes and try again."
            })
            recommendations.append({
                'title': 'Simplify First',
                'description': "Try easier games to build confidence before moving to harder ones."
            })
        else:
            recommendations.append({
                'title': 'Support Needed',
                'description': f"{name} needs extra support with a {avg_score:.0f}% average."
            })
            recommendations.append({
                'title': 'Review Together',
                'description': "Go over game instructions together before starting."
            })
            recommendations.append({
                'title': 'Short Sessions',
                'description': "Try 10-minute sessions to avoid frustration."
            })
            recommendations.append({
                'title': 'Celebrate Small Wins',
                'description': "Celebrate every improvement to keep motivation high."
            })
        
        result = ""
        for rec in recommendations:
            result += f"**{rec['title']}**\n{rec['description']}\n\n"
        
        return result.strip()
    
    @staticmethod
    def get_chat_response(question, context=None):
        """Get chatbot response with accessibility considerations"""
        question_lower = question.lower()
        
        responses = {
            'game': "Great question! You can play games by clicking on the 'Start Game' button on your assigned games. Each game helps you learn something new and fun!",
            'score': "Your scores show how well you're doing! The more you practice, the higher your scores will get.",
            'help': "I'm here to help! If you're stuck on a game, try reading the instructions carefully. You can also ask your teacher or parent for help!",
            'progress': "You're making progress! Every game you complete helps you learn more.",
            'memory': "Memory games help your brain get stronger! Try memory match games to practice your memory skills.",
            'math': "Math games make numbers fun! Keep practicing and you'll become a math superstar.",
            'adhd': "For ADHD support, try games with short rounds and movement breaks. I recommend focus games with visual rewards.",
            'dyslexia': "For dyslexia support, try games with read-aloud features and large fonts. I recommend language games with audio support.",
            'cognitive': "For cognitive pace support, try games with adjustable speed and step-by-step instructions."
        }
        
        for keyword, response in responses.items():
            if keyword in question_lower:
                return response
        
        return "That's a great question! I'm here to help you learn. Keep playing games and you'll get better every day!"
    
    @staticmethod
    def generate_learning_path(learner_data, curriculum):
        """Generate a learning path with accessibility considerations"""
        name = learner_data.get('name', 'Student')
        avg_score = learner_data.get('avg_score', 0)
        grade = learner_data.get('grade', 1)
        
        if avg_score >= 70:
            level = "Advanced"
            focus = "challenge yourself with harder games"
            daily_time = "25 minutes"
            goal = "Pass 80% of games"
            game_type = "challenging"
        elif avg_score >= 40:
            level = "Intermediate"
            focus = "practice regularly to improve"
            daily_time = "20 minutes"
            goal = "Pass 60% of games"
            game_type = "grade-appropriate"
        else:
            level = "Beginner"
            focus = "build confidence with simpler games"
            daily_time = "15 minutes"
            goal = "Pass 40% of games"
            game_type = "beginner-friendly"
        
        return f"""
**4-Week Learning Path for {name} (Grade {grade})**

**Your Level: {level}**

**Overall Goal:** {goal}

---

**Week 1: Getting Started**
- Daily: {daily_time} of game time
- Focus on: {game_type} games to build foundation
- Goal: Complete 3 games
- Reward: Complete 3 games = Achievement Badge

**Week 2: Building Skills**
- Daily: {daily_time} of game time
- Focus on: Games that match your learning level
- Goal: Improve scores by 10%
- Reward: 10% improvement = Progress Badge

**Week 3: Growing Stronger**
- Daily: {daily_time} of game time
- Focus on: More challenging games
- Goal: {goal}
- Reward: Reach your goal = Master Badge

**Week 4: Mastering Skills**
- Daily: {daily_time} of game time
- Focus on: {focus}
- Goal: Pass 70% of games
- Reward: Complete all 4 weeks = Learning Champion Badge

---

**Tips for Success:**
- Take breaks between games to rest your brain
- Review mistakes to learn from them
- Celebrate every achievement, big or small
- Ask for help when you need it

**You've got this, {name}! Every game makes you smarter!**
"""
    
    @staticmethod
    def get_educator_recommendations(question, educator_data, learners_data):
        """Get educator recommendations for games with accessibility features"""
        question_lower = question.lower()
        
        student_name = None
        for learner in learners_data:
            if learner['name'].lower() in question_lower:
                student_name = learner['name']
                break
        
        if student_name:
            return f"**Recommendations for {student_name}**\n\nBased on their performance, I recommend:\n- Memory Games - Builds memory skills\n- Attention Games - Improves focus\n- Math Games - Develops math skills\n\nKeep practicing regularly to see improvement!"
        
        if 'class' in question_lower or 'all students' in question_lower:
            return "**Class Recommendations**\n\nFor the whole class, I recommend:\n- Memory Match - Good for group practice\n- Attention Games - Fun for the whole class\n- Math Games - Great for building skills"
        
        if 'adhd' in question_lower:
            return "**ADHD-Friendly Game Recommendations**\n\nFor students with ADHD, I recommend:\n- Focus Finder - Short rounds with visual rewards\n- Memory Match - Quick games with movement breaks\n- Color Match - Fast-paced with immediate feedback\n\nKeep sessions short and rewarding!"
        
        if 'dyslexia' in question_lower:
            return "**Dyslexia-Friendly Game Recommendations**\n\nFor students with dyslexia, I recommend:\n- Word Builder - With read-aloud and large fonts\n- Picture Match - Visual cues with audio support\n- Language Games - Audio-rich with clear pronunciation\n\nNo time limits and visual support are key!"
        
        if 'cognitive' in question_lower or 'pace' in question_lower:
            return "**Cognitive Pace Game Recommendations**\n\nFor students who need cognitive pace support, I recommend:\n- Pattern Recognition - Step-by-step instructions\n- Logic Puzzle - Adjustable speed settings\n- Counting Fun - Visual progress tracking\n\nAllow multiple attempts and positive reinforcement!"
        
        return "I can help you recommend games for your students!\n\nTry asking:\n- 'What games should I recommend for Sarah?'\n- 'Games for the whole class'\n- 'Math games for my students'\n- 'ADHD-friendly games'\n- 'Dyslexia support games'\n- 'Cognitive pace games'"
    
    @staticmethod
    def generate_game(topic, grade, access_type='default', num_questions=10):
        """Generate a new educational game with accessibility features"""
        
        categories = AIService.get_game_categories()
        category_config = categories.get(topic.lower(), categories.get('memory'))
        accessibility_config = category_config.get('accessibility', {}).get(access_type, {})
        
        questions = AIService._get_grade_questions(topic, grade, access_type)
        
        max_q = accessibility_config.get('max_questions', num_questions)
        if len(questions) > max_q:
            questions = questions[:max_q]
        
        game_data = {
            'name': f'{topic.capitalize()} Explorer',
            'description': category_config.get('description', 'Fun learning game'),
            'category': topic.lower(),
            'subcategory': access_type,
            'grade_level': grade,
            'difficulty': AIService._get_difficulty(grade),
            'questions': questions,
            'accessibility_features': accessibility_config,
            'visual_style': AIService._get_visual_style(access_type),
            'audio_support': accessibility_config.get('audio_support', False),
            'movement_breaks': accessibility_config.get('movement_breaks', False),
            'progress_tracking': accessibility_config.get('progress_tracking', True),
            'max_questions': len(questions),
            'time_limit': accessibility_config.get('time_limit', 10)
        }
        
        return game_data
    
    @staticmethod
    def _get_grade_questions(topic, grade_level, access_type):
        """Get questions appropriate for the grade level with accessibility"""
        
        grade_1_questions = {
            'memory': [
                {'question': 'Find the matching picture', 'options': ['Cat', 'Dog', 'Cat', 'Bird'], 'correct_answer': 'Cat', 'points': 1},
                {'question': 'Find the matching picture', 'options': ['Apple', 'Banana', 'Apple', 'Grape'], 'correct_answer': 'Apple', 'points': 1},
                {'question': 'Find the matching picture', 'options': ['Ball', 'Doll', 'Ball', 'Car'], 'correct_answer': 'Ball', 'points': 1},
                {'question': 'What color is missing?', 'options': ['Red', 'Blue', 'Green', 'Yellow'], 'correct_answer': 'Blue', 'points': 1},
                {'question': 'What animal is missing?', 'options': ['Lion', 'Elephant', 'Tiger', 'Bear'], 'correct_answer': 'Tiger', 'points': 1}
            ],
            'attention': [
                {'question': 'Find the odd one out', 'options': ['Circle', 'Circle', 'Circle', 'Square'], 'correct_answer': 'Square', 'points': 1},
                {'question': 'Find the odd one out', 'options': ['Apple', 'Apple', 'Apple', 'Ball'], 'correct_answer': 'Ball', 'points': 1},
                {'question': 'Find the odd one out', 'options': ['Red', 'Red', 'Red', 'Blue'], 'correct_answer': 'Blue', 'points': 1}
            ],
            'language': [
                {'question': 'What letter does cat start with?', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'C', 'points': 1},
                {'question': 'What letter does dog start with?', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'D', 'points': 1},
                {'question': 'What letter does apple start with?', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'A', 'points': 1}
            ],
            'math': [
                {'question': 'How many apples?', 'options': ['1', '2', '3', '4'], 'correct_answer': '2', 'points': 1},
                {'question': 'How many stars?', 'options': ['1', '2', '3', '4'], 'correct_answer': '3', 'points': 1},
                {'question': 'How many circles?', 'options': ['1', '2', '3', '4'], 'correct_answer': '1', 'points': 1}
            ],
            'sensory': [
                {'question': 'What sound does a dog make?', 'options': ['Meow', 'Woof', 'Moo', 'Quack'], 'correct_answer': 'Woof', 'points': 1},
                {'question': 'What sound does a cat make?', 'options': ['Meow', 'Woof', 'Moo', 'Quack'], 'correct_answer': 'Meow', 'points': 1},
                {'question': 'What sound does a cow make?', 'options': ['Meow', 'Woof', 'Moo', 'Quack'], 'correct_answer': 'Moo', 'points': 1}
            ]
        }
        
        grade_2_questions = {
            'memory': [
                {'question': 'Remember the sequence: 1, 2, 3, ?', 'options': ['1', '2', '3', '4'], 'correct_answer': '4', 'points': 2},
                {'question': 'Remember the sequence: A, B, C, ?', 'options': ['A', 'B', 'C', 'D'], 'correct_answer': 'D', 'points': 2},
                {'question': 'Find the matching pair: dog, cat, dog, ?', 'options': ['dog', 'cat', 'bird', 'fish'], 'correct_answer': 'dog', 'points': 2}
            ],
            'attention': [
                {'question': 'Find the different one: apple, apple, apple, ?', 'options': ['apple', 'banana', 'grape', 'orange'], 'correct_answer': 'banana', 'points': 2},
                {'question': 'Find the different one: circle, circle, circle, ?', 'options': ['circle', 'square', 'triangle', 'rectangle'], 'correct_answer': 'square', 'points': 2}
            ],
            'language': [
                {'question': 'What is the opposite of big?', 'options': ['small', 'large', 'huge', 'tall'], 'correct_answer': 'small', 'points': 2},
                {'question': 'What is the opposite of hot?', 'options': ['cold', 'warm', 'cool', 'freezing'], 'correct_answer': 'cold', 'points': 2},
                {'question': 'What is the opposite of fast?', 'options': ['slow', 'quick', 'rapid', 'swift'], 'correct_answer': 'slow', 'points': 2}
            ],
            'math': [
                {'question': '2 + 2 = ?', 'options': ['3', '4', '5', '6'], 'correct_answer': '4', 'points': 2},
                {'question': '1 + 3 = ?', 'options': ['3', '4', '5', '6'], 'correct_answer': '4', 'points': 2},
                {'question': '3 + 1 = ?', 'options': ['3', '4', '5', '6'], 'correct_answer': '4', 'points': 2}
            ],
            'sensory': [
                {'question': 'Which is a fruit?', 'options': ['apple', 'carrot', 'broccoli', 'potato'], 'correct_answer': 'apple', 'points': 2},
                {'question': 'Which is a vegetable?', 'options': ['apple', 'carrot', 'banana', 'grape'], 'correct_answer': 'carrot', 'points': 2}
            ]
        }
        
        grade_3_questions = {
            'memory': [
                {'question': 'What comes next in the pattern: 1, 4, 7, 10, ?', 'options': ['11', '12', '13', '14'], 'correct_answer': '13', 'points': 2},
                {'question': 'What comes next in the pattern: A, C, E, G, ?', 'options': ['H', 'I', 'J', 'K'], 'correct_answer': 'I', 'points': 2}
            ],
            'attention': [
                {'question': 'What is the main idea? The cat is sleeping on the mat.', 'options': ['cat is sleeping', 'cat is playing', 'cat is eating', 'cat is running'], 'correct_answer': 'cat is sleeping', 'points': 2}
            ],
            'language': [
                {'question': 'What is the meaning of "happy"?', 'options': ['sad', 'glad', 'angry', 'tired'], 'correct_answer': 'glad', 'points': 2},
                {'question': 'What is the meaning of "big"?', 'options': ['small', 'large', 'tiny', 'little'], 'correct_answer': 'large', 'points': 2}
            ],
            'math': [
                {'question': '5 + 3 = ?', 'options': ['6', '7', '8', '9'], 'correct_answer': '8', 'points': 2},
                {'question': '10 - 3 = ?', 'options': ['5', '6', '7', '8'], 'correct_answer': '7', 'points': 2},
                {'question': '4 x 2 = ?', 'options': ['6', '8', '10', '12'], 'correct_answer': '8', 'points': 2}
            ],
            'sensory': [
                {'question': 'Which animal lives in water?', 'options': ['fish', 'bird', 'lion', 'dog'], 'correct_answer': 'fish', 'points': 2},
                {'question': 'Which animal lives on land?', 'options': ['fish', 'bird', 'lion', 'whale'], 'correct_answer': 'lion', 'points': 2}
            ]
        }
        
        topic_lower = topic.lower()
        if grade_level == 1:
            questions_pool = grade_1_questions.get(topic_lower, grade_1_questions['memory'])
        elif grade_level == 2:
            questions_pool = grade_2_questions.get(topic_lower, grade_2_questions['memory'])
        elif grade_level == 3:
            questions_pool = grade_3_questions.get(topic_lower, grade_3_questions['memory'])
        else:
            questions_pool = grade_1_questions.get(topic_lower, grade_1_questions['memory'])
        
        if not questions_pool:
            questions_pool = [
                {'question': f'What do you know about {topic}?', 'options': ['Fact A', 'Fact B', 'Fact C', 'Fact D'], 'correct_answer': 'Fact A', 'points': 2},
                {'question': f'Which of these is related to {topic}?', 'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'], 'correct_answer': 'Option 1', 'points': 2}
            ]
        
        random.shuffle(questions_pool)
        return questions_pool
    
    @staticmethod
    def enhance_game(game_data):
        """Enhance an existing game with more questions and correct answers"""
        if not game_data or not game_data.get('questions'):
            return game_data
        
        questions = game_data.get('questions', [])
        
        for question in questions:
            if 'correct_answer' not in question or question['correct_answer'] == '':
                options = question.get('options', [])
                if options:
                    question['correct_answer'] = options[0]
                else:
                    question['correct_answer'] = 'Not specified'
                question['points'] = question.get('points', 2)
        
        return game_data

ai_service = AIService()