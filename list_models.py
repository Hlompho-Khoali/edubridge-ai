# list_models.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

print("=" * 50)
print("🔍 Listing Available Gemini Models")
print("=" * 50)

if not api_key:
    print("❌ No API key found!")
    exit()

try:
    client = genai.Client(api_key=api_key)
    
    print("\n📡 Fetching available models...")
    models = client.models.list()
    
    print("\n✅ Available Models:")
    for model in models:
        print(f"  - {model.name}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")