import os
import sys
from pathlib import Path
import subprocess
sys.path.insert(0, str(Path(__file__).parent))
from litellm import embedding

os.environ["VERTEX_PROJECT"] = "andre-467020"
os.environ["VERTEX_LOCATION"] = "us-central1"

# Get access token
try:
    token = subprocess.check_output(["gcloud", "auth", "print-access-token"], shell=True).decode("utf-8").strip()
    print("Got access token.")
except Exception as e:
    print(f"Failed to get token: {e}")
    token = None

print("Testing Vertex AI Embedding...")
try:
    response = embedding(
        model="vertex_ai/text-embedding-004",
        input=["hello"],
        access_token=token
    )
    print("Success!")
    print(response)
except Exception as e:
    print(f"Error: {e}")
