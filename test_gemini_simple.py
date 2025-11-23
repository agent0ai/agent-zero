import os
from litellm import completion

# Set API key
os.environ["GEMINI_API_KEY"] = "AIzaSyCi16EEkxxSPcPbhaNSWdd10TC2ipvrLUA"

print("🧪 Testing Gemini Models...")
print("=" * 60)

# Test 1: Chat Model
print("\n1️⃣ Testing gemini/gemini-1.5-pro-latest...")
try:
    response = completion(
        model="gemini/gemini-1.5-pro-latest",
        messages=[{"role": "user", "content": "Say 'Hello from Gemini Pro!' in exactly 5 words."}],
        max_tokens=20
    )
    print(f"   ✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)[:200]}")

# Test 2: Utility Model
print("\n2️⃣ Testing gemini/gemini-1.5-flash-latest...")
try:
    response = completion(
        model="gemini/gemini-1.5-flash-latest",
        messages=[{"role": "user", "content": "Say 'Hello from Gemini Flash!' in exactly 5 words."}],
        max_tokens=20
    )
    print(f"   ✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)[:200]}")

print("\n" + "=" * 60)
print("✅ Model testing complete!")
print("=" * 60)
