# utils/game_categories.py

class GameCategories:
    """Game categories for different learning needs and grade levels"""
    
    @staticmethod
    def get_categories():
        """Get all game categories with their configurations"""
        return {
            'memory': {
                'name': 'Memory Games',
                'description': 'Build working memory and recall skills',
                'icon': '🧠',
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
                'icon': '🎯',
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
                'icon': '📖',
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
                'icon': '🔢',
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
                'icon': '🎨',
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
    def get_grade_levels():
        """Get available grade levels"""
        return [1, 2, 3]
    
    @staticmethod
    def get_accessibility_types():
        """Get accessibility types"""
        return ['adhd', 'dyslexia', 'cognitive_pace']
    
    @staticmethod
    def get_accessibility_label(access_type):
        """Get human-readable label for accessibility type"""
        labels = {
            'adhd': 'ADHD Support',
            'dyslexia': 'Dyslexia Support',
            'cognitive_pace': 'Cognitive Pace Support'
        }
        return labels.get(access_type, access_type)