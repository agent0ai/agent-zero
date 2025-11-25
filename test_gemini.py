# Test Gemini API Call with LiteLLM
import os
os.environ["GEMINI_API_KEY"] = "AIzaSyAFotWDR7-wz9eS4kk18pIwBlRfQy9IG8U"

from litellm import completion

try:
    response = completion(
        model="gemini/gemini-1.5-pro",
        messages=[{"role": "user", "content": "Say 'Hello from test'"}],
        max_tokens=10
    )
    print("SUCCESS!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
