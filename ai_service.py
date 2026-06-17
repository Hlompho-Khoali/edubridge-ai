# ai_service.py - Complete file with game generation (No API Required)
import json
import re
import random
from datetime import datetime
from ai_config import AIConfig

class AIService:
    """AI Service with Game Generation"""
    
    # ===== RECOMMENDATIONS METHOD =====
    
    @staticmethod
    def get_recommendations(learner_data):
        """Generate personalized learning recommendations"""
        name = learner_data.get('name', 'Student')
        avg_score = learner_data.get('avg_score', 0)
        games_completed = learner_data.get('games_completed', 0)
        strengths = learner_data.get('strengths', 'Not yet identified')
        weaknesses = learner_data.get('weaknesses', 'Not yet identified')
        
        # Determine performance level
        if avg_score >= 80:
            level = 'excellent'
            emoji = '🌟'
            level_text = 'Excellent Progress!'
        elif avg_score >= 60:
            level = 'good'
            emoji = '📈'
            level_text = 'Good Progress!'
        elif avg_score >= 40:
            level = 'developing'
            emoji = '📖'
            level_text = 'Building Skills'
        else:
            level = 'needs_support'
            emoji = '💪'
            level_text = 'Keep Going!'
        
        recommendations = []
        
        if games_completed == 0:
            recommendations.append({
                'title': '🌟 Getting Started',
                'description': f"{name} hasn't completed any games yet. Start with beginner-level games to build confidence."
            })
            recommendations.append({
                'title': '🎯 First Steps',
                'description': "Try 'Penguin Says' or 'Memory Match' - these are great for beginners!"
            })
            recommendations.append({
                'title': '📅 Daily Practice',
                'description': "Set aside 15 minutes daily for game-based learning."
            })
        elif level == 'excellent':
            recommendations.append({
                'title': '🏆 Excellent Progress!',
                'description': f"{name} is mastering the material with a {avg_score:.0f}% average score!"
            })
            recommendations.append({
                'title': '📚 Challenge Yourself',
                'description': "Try more advanced games to continue growing."
            })
            recommendations.append({
                'title': '👨‍🏫 Peer Tutor',
                'description': f"Encourage {name} to help classmates who are struggling."
            })
        elif level == 'good':
            recommendations.append({
                'title': '📈 Good Progress!',
                'description': f"{name} is doing well with a {avg_score:.0f}% average score. Keep it up!"
            })
            recommendations.append({
                'title': '🎯 Focus Areas',
                'description': f"Practice more in: {weaknesses if weaknesses != 'Not yet identified' else 'areas with lower scores'}."
            })
            recommendations.append({
                'title': '⏰ Consistent Practice',
                'description': "Continue practicing 15-20 minutes daily to improve."
            })
        elif level == 'developing':
            recommendations.append({
                'title': '📖 Building Skills',
                'description': f"{name} is developing skills with a {avg_score:.0f}% average."
            })
            recommendations.append({
                'title': '💪 Keep Going!',
                'description': "Every game teaches something new. Review mistakes and try again."
            })
            recommendations.append({
                'title': '🎮 Simplify First',
                'description': "Try easier games to build confidence before moving to harder ones."
            })
        else:
            recommendations.append({
                'title': '🤝 Support Needed',
                'description': f"{name} needs extra support with a {avg_score:.0f}% average."
            })
            recommendations.append({
                'title': '📝 Review Together',
                'description': "Go over game instructions together before starting."
            })
            recommendations.append({
                'title': '⏳ Short Sessions',
                'description': "Try 10-minute sessions to avoid frustration."
            })
            recommendations.append({
                'title': '🏅 Celebrate Small Wins',
                'description': "Celebrate every improvement to keep motivation high."
            })
        
        # Format as string
        result = ""
        for rec in recommendations:
            result += f"**{rec['title']}**\n{rec['description']}\n\n"
        
        return result.strip()
    
    # ===== CHAT RESPONSE METHOD =====
    
    @staticmethod
    def get_chat_response(question, context=None):
        """Get chatbot response"""
        question_lower = question.lower()
        
        responses = {
            'game': "🎮 Great question! You can play games by clicking on the 'Start Game' button on your assigned games. Each game helps you learn something new and fun!",
            'score': "📊 Your scores show how well you're doing! The more you practice, the higher your scores will get. Keep trying and you'll see improvement!",
            'help': "🤗 I'm here to help! If you're stuck on a game, try reading the instructions carefully. You can also ask your teacher or parent for help!",
            'progress': "📈 You're making progress! Every game you complete helps you learn more. Check your dashboard to see all your achievements!",
            'memory': "🧠 Memory games help your brain get stronger! Try 'Penguin Says' or 'Memory Match' to practice your memory skills.",
            'math': "🔢 Math games make numbers fun! Keep practicing and you'll become a math superstar.",
            'penguin': "🐧 Penguin Says is a fun memory game! You repeat patterns and try to remember them. It's great for practicing your memory skills!",
            'red light': "🚦 Red Light Green Light is a reaction game! You have to respond quickly when the light changes. It helps with attention and reaction time!",
        }
        
        for keyword, response in responses.items():
            if keyword in question_lower:
                return response
        
        return "😊 That's a great question! I'm here to help you learn. Keep playing games and you'll get better every day! If you need more help, ask your teacher or parent."
    
    # ===== LEARNING PATH METHOD =====
    
    @staticmethod
    def generate_learning_path(learner_data, curriculum):
        """Generate a learning path"""
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
📚 **4-Week Learning Path for {name} (Grade {grade})**

📊 **Your Level: {level}**

🎯 **Overall Goal:** {goal}

---

**Week 1: Getting Started**
- 📅 Daily: {daily_time} of game time
- 🎮 Focus on: {game_type} games to build foundation
- 📝 Goal: Complete 3 games
- 🏆 Reward: Complete 3 games = Achievement Badge

**Week 2: Building Skills**
- 📅 Daily: {daily_time} of game time
- 🎮 Focus on: Games that match your learning level
- 📝 Goal: Improve scores by 10%
- 🏆 Reward: 10% improvement = Progress Badge

**Week 3: Growing Stronger**
- 📅 Daily: {daily_time} of game time
- 🎮 Focus on: More challenging games
- 📝 Goal: {goal}
- 🏆 Reward: Reach your goal = Master Badge

**Week 4: Mastering Skills**
- 📅 Daily: {daily_time} of game time
- 🎮 Focus on: {focus}
- 📝 Goal: Pass 70% of games
- 🏆 Reward: Complete all 4 weeks = Learning Champion Badge

---

💡 **Tips for Success:**
- 🎯 Take breaks between games to rest your brain
- 📝 Review mistakes to learn from them
- 🏅 Celebrate every achievement, big or small
- 🤗 Ask for help when you need it

🌟 **You've got this, {name}! Every game makes you smarter!**
"""
    
    # ===== EDUCATOR RECOMMENDATIONS =====
    
    @staticmethod
    def get_educator_recommendations(question, educator_data, learners_data):
        """Get educator recommendations for games"""
        
        question_lower = question.lower()
        
        # Check if asking about a specific student
        student_name = None
        for learner in learners_data:
            if learner['name'].lower() in question_lower:
                student_name = learner['name']
                break
        
        if student_name:
            return f"📚 **Recommendations for {student_name}**\n\nBased on their performance, I recommend:\n• **Penguin Says** - Builds memory skills\n• **Memory Match** - Improves visual memory\n• **Number Bonds** - Develops math skills\n\nKeep practicing regularly to see improvement!"
        
        if 'class' in question_lower or 'all students' in question_lower:
            return "📚 **Class Recommendations**\n\nFor the whole class, I recommend:\n• **Penguin Says** - Good for group memory practice\n• **Memory Match** - Fun for the whole class\n• **Red Light Green Light** - Great for attention and reaction\n\nAssign these games to your students today!"
        
        return "📚 I can help you recommend games for your students!\n\nTry asking:\n• 'What games should I recommend for Sarah?'\n• 'Games for the whole class'\n• 'Math games for my students'\n• 'What games help with memory?'"
    
    # ===== GAME GENERATION =====
    
    @staticmethod
    def generate_game(topic, grade, game_type, num_questions=15):
        """Generate a new educational game - Simplified version"""
        return AIService._generate_rule_based_game(topic, grade, game_type, num_questions)
    
    @staticmethod
    def _generate_rule_based_game(topic, grade, game_type, num_questions):
        """Generate a game using rules (no API needed)"""
        
        # Game templates
        templates = {
            'memory': {
                'name': f'Memory Match: {topic}',
                'description': f'Test your memory by recalling {topic} facts and details',
                'category': 'Memory'
            },
            'math': {
                'name': f'Math Challenge: {topic}',
                'description': f'Solve math problems about {topic}',
                'category': 'Math'
            },
            'vocabulary': {
                'name': f'Word Builder: {topic}',
                'description': f'Learn and practice {topic} vocabulary',
                'category': 'Vocabulary'
            },
            'attention': {
                'name': f'Focus Finder: {topic}',
                'description': f'Find and identify {topic} items quickly',
                'category': 'Attention'
            },
            'logic': {
                'name': f'Logic Puzzle: {topic}',
                'description': f'Solve logic puzzles about {topic}',
                'category': 'Logic'
            },
            'default': {
                'name': f'Learning Game: {topic}',
                'description': f'Learn about {topic} in a fun way',
                'category': 'General'
            }
        }
        
        template = templates.get(game_type, templates['default'])
        
        # Determine difficulty
        if grade <= 1:
            difficulty = 'beginner'
        elif grade == 2:
            difficulty = 'intermediate'
        else:
            difficulty = 'advanced'
        
        # Generate questions based on topic
        questions = AIService._generate_questions_for_topic(topic, grade, num_questions)
        
        return {
            "name": template['name'],
            "description": template['description'],
            "category": template['category'],
            "difficulty": difficulty,
            "questions": questions
        }
    
    @staticmethod
    def _generate_questions_for_topic(topic, grade, num_questions):
        """Generate questions for a specific topic"""
        
        # Topic-specific question banks
        topic_questions = {
            'space': [
                {"question": "What is the closest star to Earth?", "options": ["The Sun", "The Moon", "Venus", "Mars"], "correct": "The Sun", "points": 2},
                {"question": "How many planets are in our solar system?", "options": ["7", "8", "9", "10"], "correct": "8", "points": 2},
                {"question": "What is the largest planet in our solar system?", "options": ["Saturn", "Neptune", "Jupiter", "Uranus"], "correct": "Jupiter", "points": 2},
                {"question": "What is the Moon?", "options": ["A Planet", "A Star", "A Satellite", "A Comet"], "correct": "A Satellite", "points": 2},
                {"question": "Which planet is known as the Red Planet?", "options": ["Venus", "Jupiter", "Mars", "Saturn"], "correct": "Mars", "points": 2},
                {"question": "What is the Sun made of?", "options": ["Rock", "Water", "Gas", "Ice"], "correct": "Gas", "points": 2},
                {"question": "Which planet is the hottest?", "options": ["Mercury", "Venus", "Mars", "Jupiter"], "correct": "Venus", "points": 2},
                {"question": "What is the largest moon in our solar system?", "options": ["Moon", "Titan", "Ganymede", "Europa"], "correct": "Ganymede", "points": 2},
            ],
            'animals': [
                {"question": "What is the largest land animal?", "options": ["Lion", "Elephant", "Giraffe", "Hippo"], "correct": "Elephant", "points": 2},
                {"question": "Which animal is known as the King of the Jungle?", "options": ["Tiger", "Lion", "Leopard", "Cheetah"], "correct": "Lion", "points": 2},
                {"question": "What is the fastest animal on land?", "options": ["Lion", "Cheetah", "Leopard", "Horse"], "correct": "Cheetah", "points": 2},
                {"question": "Where do penguins live?", "options": ["North Pole", "South Pole", "Desert", "Forest"], "correct": "South Pole", "points": 2},
                {"question": "What do pandas eat?", "options": ["Meat", "Bamboo", "Fish", "Grass"], "correct": "Bamboo", "points": 2},
                {"question": "Which animal has the longest neck?", "options": ["Elephant", "Giraffe", "Camel", "Horse"], "correct": "Giraffe", "points": 2},
                {"question": "What animal is known for building dams?", "options": ["Beaver", "Otter", "Muskrat", "Capybara"], "correct": "Beaver", "points": 2},
                {"question": "Which animal has stripes?", "options": ["Lion", "Tiger", "Leopard", "Cheetah"], "correct": "Tiger", "points": 2},
            ],
            'math': [
                {"question": "What is 5 + 3?", "options": ["6", "7", "8", "9"], "correct": "8", "points": 2},
                {"question": "What is 10 - 4?", "options": ["5", "6", "7", "8"], "correct": "6", "points": 2},
                {"question": "What is 3 x 4?", "options": ["10", "11", "12", "13"], "correct": "12", "points": 2},
                {"question": "What is 15 ÷ 3?", "options": ["3", "4", "5", "6"], "correct": "5", "points": 2},
                {"question": "What is 7 + 6?", "options": ["11", "12", "13", "14"], "correct": "13", "points": 2},
                {"question": "What is 20 - 8?", "options": ["10", "11", "12", "13"], "correct": "12", "points": 2},
                {"question": "What is 4 x 6?", "options": ["22", "23", "24", "25"], "correct": "24", "points": 2},
                {"question": "What is 18 ÷ 2?", "options": ["7", "8", "9", "10"], "correct": "9", "points": 2},
            ],
            'colors': [
                {"question": "What color is the sky?", "options": ["Red", "Green", "Blue", "Yellow"], "correct": "Blue", "points": 2},
                {"question": "What color do you get mixing red and yellow?", "options": ["Purple", "Orange", "Green", "Brown"], "correct": "Orange", "points": 2},
                {"question": "What is the color of grass?", "options": ["Red", "Blue", "Green", "Yellow"], "correct": "Green", "points": 2},
                {"question": "What color is a banana?", "options": ["Red", "Blue", "Green", "Yellow"], "correct": "Yellow", "points": 2},
                {"question": "What color is a strawberry?", "options": ["Red", "Blue", "Green", "Yellow"], "correct": "Red", "points": 2},
                {"question": "What color do you get mixing blue and yellow?", "options": ["Purple", "Green", "Orange", "Brown"], "correct": "Green", "points": 2},
                {"question": "What color is a pumpkin?", "options": ["Red", "Orange", "Yellow", "Brown"], "correct": "Orange", "points": 2},
                {"question": "What color is the ocean?", "options": ["Green", "Blue", "Purple", "Gray"], "correct": "Blue", "points": 2},
            ],
            'emotions': [
                {"question": "How do you feel when you get a present?", "options": ["Sad", "Happy", "Angry", "Scared"], "correct": "Happy", "points": 2},
                {"question": "How do you feel when you lose your toy?", "options": ["Happy", "Sad", "Angry", "Excited"], "correct": "Sad", "points": 2},
                {"question": "How do you feel when someone takes your turn?", "options": ["Happy", "Sad", "Angry", "Calm"], "correct": "Angry", "points": 2},
                {"question": "How do you feel in the dark?", "options": ["Happy", "Sad", "Scared", "Excited"], "correct": "Scared", "points": 2},
                {"question": "How do you feel when you win a game?", "options": ["Sad", "Angry", "Happy", "Scared"], "correct": "Happy", "points": 2},
                {"question": "How do you feel when you get a hug?", "options": ["Loved", "Sad", "Angry", "Scared"], "correct": "Loved", "points": 2},
                {"question": "How do you feel when you see a rainbow?", "options": ["Happy", "Sad", "Angry", "Scared"], "correct": "Happy", "points": 2},
                {"question": "How do you feel when you hear loud thunder?", "options": ["Happy", "Excited", "Scared", "Calm"], "correct": "Scared", "points": 2},
            ],
            'dinosaurs': [
                {"question": "What is the biggest dinosaur?", "options": ["T-Rex", "Brachiosaurus", "Velociraptor", "Triceratops"], "correct": "Brachiosaurus", "points": 2},
                {"question": "Which dinosaur is known for its three horns?", "options": ["T-Rex", "Stegosaurus", "Triceratops", "Velociraptor"], "correct": "Triceratops", "points": 2},
                {"question": "Which dinosaur had a spiked tail?", "options": ["T-Rex", "Stegosaurus", "Triceratops", "Velociraptor"], "correct": "Stegosaurus", "points": 2},
                {"question": "Which dinosaur is famous for being a meat-eater?", "options": ["T-Rex", "Brachiosaurus", "Stegosaurus", "Triceratops"], "correct": "T-Rex", "points": 2},
                {"question": "What did most dinosaurs eat?", "options": ["Meat", "Plants", "Both", "Fish"], "correct": "Plants", "points": 2},
                {"question": "How did dinosaurs move?", "options": ["Flying", "Swimming", "Walking", "All of the above"], "correct": "Walking", "points": 2},
                {"question": "What is a fossil?", "options": ["A living dinosaur", "A dinosaur egg", "Remains of a dinosaur", "A dinosaur toy"], "correct": "Remains of a dinosaur", "points": 2},
                {"question": "Where did dinosaurs live?", "options": ["Only in Africa", "All around the world", "Only in Asia", "Only in North America"], "correct": "All around the world", "points": 2},
            ],
            'multiplication': [
                {"question": "What is 2 x 2?", "options": ["2", "3", "4", "5"], "correct": "4", "points": 2},
                {"question": "What is 3 x 3?", "options": ["6", "7", "8", "9"], "correct": "9", "points": 2},
                {"question": "What is 4 x 4?", "options": ["12", "14", "16", "18"], "correct": "16", "points": 2},
                {"question": "What is 5 x 5?", "options": ["20", "25", "30", "35"], "correct": "25", "points": 2},
                {"question": "What is 6 x 6?", "options": ["30", "32", "34", "36"], "correct": "36", "points": 2},
                {"question": "What is 7 x 7?", "options": ["42", "44", "46", "49"], "correct": "49", "points": 2},
                {"question": "What is 8 x 8?", "options": ["56", "58", "62", "64"], "correct": "64", "points": 2},
                {"question": "What is 9 x 9?", "options": ["72", "76", "81", "84"], "correct": "81", "points": 2},
            ]
        }
        
        # Get topic-specific questions or use generic ones
        topic_key = topic.lower()
        selected_questions = []
        
        for key, questions in topic_questions.items():
            if key in topic_key or topic_key in key:
                selected_questions = questions.copy()
                break
        
        # If no topic match, use generic questions
        if not selected_questions:
            selected_questions = [
                {"question": f"What do you know about {topic}?", "options": ["Fact A", "Fact B", "Fact C", "Fact D"], "correct": "Fact A", "points": 2},
                {"question": f"Which of these is related to {topic}?", "options": ["Option 1", "Option 2", "Option 3", "Option 4"], "correct": "Option 1", "points": 2},
                {"question": f"Can you identify the {topic}?", "options": ["Item A", "Item B", "Item C", "Item D"], "correct": "Item A", "points": 2},
                {"question": f"What is the main idea about {topic}?", "options": ["Idea 1", "Idea 2", "Idea 3", "Idea 4"], "correct": "Idea 1", "points": 2},
                {"question": f"Why is {topic} important?", "options": ["Reason 1", "Reason 2", "Reason 3", "Reason 4"], "correct": "Reason 1", "points": 2},
            ]
        
        # Shuffle and select the required number
        random.shuffle(selected_questions)
        selected_questions = selected_questions[:num_questions]
        
        # If we don't have enough, pad with generic questions
        while len(selected_questions) < num_questions:
            selected_questions.append({
                "question": f"Question {len(selected_questions)+1} about {topic}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": "Option A",
                "points": 2
            })
        
        return selected_questions
    
    @staticmethod
    def enhance_game(game_data):
        """Enhance an existing game"""
        # Return original if enhancement is not possible
        return game_data

# Create instance
ai_service = AIService()