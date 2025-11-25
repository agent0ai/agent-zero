import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from litellm import completion, embedding
import os

os.environ["VERTEX_PROJECT"] = "andre-467020"
os.environ["VERTEX_LOCATION"] = "us-central1"

async def test_models():
    print("🧪 Testing Vertex AI Models...")
    print("=" * 60)
    
    # Test 1: Chat Model (Gemini 1.5 Pro)
    print("\n1️⃣ Testing Chat Model (gemini-1.5-pro)...")
    try:
        response = completion(
            model="vertex_ai/gemini-1.5-pro",
            messages=[{"role": "user", "content": "Say 'Hello from Gemini Pro!' in exactly 5 words."}],
            max_tokens=20
        )
        print(f"   ✅ Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Utility Model (Gemini 1.5 Flash)
    print("\n2️⃣ Testing Utility Model (gemini-1.5-flash)...")
    try:
        response = completion(
            model="vertex_ai/gemini-1.5-flash",
            messages=[{"role": "user", "content": "Say 'Hello from Gemini Flash!' in exactly 5 words."}],
            max_tokens=20
        )
        print(f"   ✅ Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Embedding Model
    print("\n3️⃣ Testing Embedding Model (text-embedding-004)...")
    try:
        response = embedding(
            model="vertex_ai/text-embedding-004",
            input=["test embedding"]
        )
        dims = len(response.data[0]['embedding'])
        print(f"   ✅ Embedding dimensions: {dims}")
        if dims != 768:
            print(f"   ⚠️ Warning: Expected 768 dimensions, got {dims}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All models working correctly!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_models())
    sys.exit(0 if success else 1)
