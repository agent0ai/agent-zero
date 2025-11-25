from litellm import completion

print("🧪 Testing Ollama Models...")
print("=" * 60)

# Test 1: Chat Model
print("\n1️⃣ Testing ollama/qwen2.5:32b...")
try:
    response = completion(
        model="ollama/qwen2.5:32b",
        api_base="http://localhost:11434",
        messages=[{"role": "user", "content": "Say 'Hello from Ollama!' in exactly 4 words."}],
        max_tokens=20
    )
    print(f"   ✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)[:200]}")

# Test 2: Utility Model
print("\n2️⃣ Testing ollama/qwen2.5:7b...")
try:
    response = completion(
        model="ollama/qwen2.5:7b",
        api_base="http://localhost:11434",
        messages=[{"role": "user", "content": "Say 'Fast Ollama response!' in exactly 3 words."}],
        max_tokens=20
    )
    print(f"   ✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)[:200]}")

# Test 3: Embedding Model
print("\n3️⃣ Testing ollama/nomic-embed-text...")
try:
    from litellm import embedding
    response = embedding(
        model="ollama/nomic-embed-text",
        api_base="http://localhost:11434",
        input=["test embedding"]
    )
    dims = len(response.data[0]['embedding'])
    print(f"   ✅ SUCCESS: {dims}D embeddings")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)[:200]}")

print("\n" + "=" * 60)
print("✅ Ollama testing complete!")
print("=" * 60)
