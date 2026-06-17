# ai_config.py
import os
from dotenv import load_dotenv

load_dotenv()

class AIConfig:
    """AI Configuration - Using Rule-Based System"""
    
    # Feature flags
    AI_ENABLED = os.getenv('AI_ENABLED', 'true').lower() == 'true'
    
    # Limits
    MAX_TOKENS = 500
    TEMPERATURE = 0.7
    
    @classmethod
    def is_configured(cls):
        """Check if AI is properly configured"""
        return cls.AI_ENABLED