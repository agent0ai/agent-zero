import ollama
try:
    client = ollama.Client()
    models = client.list()
    print("Successfully connected to Ollama.")
    print("Available models:")
    for model in models['models']:
        print(f"- {model['name']}")
except Exception as e:
    print(f"Failed to connect to Ollama: {e}")
