# test_deepseek.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv('DEEPSEEK_API_KEY')

print("=" * 50)
print("🔍 Testing DeepSeek API Connection")
print("=" * 50)

if not api_key:
    print("❌ No DeepSeek API key found in .env")
    print("   Please add: DEEPSEEK_API_KEY=sk-...")
    exit()

print(f"✅ API key found: {api_key[:15]}... (hidden)")

try:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    print("\n📡 Testing API connection...")
    
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, EduBridge is working with DeepSeek!'"}
        ],
        max_tokens=50
    )
    
    print("\n✅ SUCCESS! API is working!")
    print(f"   Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")