# test_openai.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('OPENAI_API_KEY')

print("=" * 50)
print("🔍 Testing OpenAI API Connection")
print("=" * 50)

# Check if API key exists
if not api_key:
    print("❌ ERROR: No API key found in .env file")
    print("   Please add: OPENAI_API_KEY=sk-your-key-here")
    exit()
else:
    print(f"✅ API key found: {api_key[:15]}... (hidden)")

# Check if key is valid format
if not api_key.startswith('sk-'):
    print("⚠️  WARNING: API key doesn't start with 'sk-'")
    print("   Please check your API key format")

# Test the API using new syntax
print("\n📡 Testing API connection...")

try:
    # Initialize client
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, EduBridge is working!'"}
        ],
        max_tokens=30,
        temperature=0.7
    )
    
    result = response.choices[0].message.content
    print("\n✅ SUCCESS! API is working!")
    print(f"   Response: {result}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")