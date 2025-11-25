import os
os.environ["FAISS_ENABLE_GPU"] = "1"
import sys
import os
import json
import subprocess
from pathlib import Path

# Add Agent Zero to path
sys.path.insert(0, str(Path(__file__).parent))

from python.helpers import settings

def optimize():
    print("🚀 Optimizing Antigravity for GCP...")
    
    # Check for ADC
    adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    if os.name == 'nt':
        adc_path = os.path.expandvars("%APPDATA%/gcloud/application_default_credentials.json")
    
    if not os.path.exists(adc_path):
        print("\n⚠️ WARNING: Application Default Credentials not found!")
        print("Please run the following command in your terminal to enable Vertex AI:")
        print("    gcloud auth application-default login")
        print("\nContinuing with configuration, but execution may fail...\n")

    # Load current settings (defaults)
    current = settings.get_settings()
    
    # Set Vertex AI env vars
    os.environ["VERTEX_PROJECT"] = "andre-467020"
    os.environ["VERTEX_LOCATION"] = "us-central1"
    
    # Use Ollama (local) as primary, Gemini as fallback
    updates = {
        "chat_model_provider": "ollama",
        "chat_model_name": "llama3.2:3b",  # Fast, capable chat model
        "chat_model_api_base": "http://localhost:11434",
        "chat_model_ctx_length": 128000,
        
        "util_model_provider": "ollama",
        "util_model_name": "llama3.2:1b",  # Ultra-fast utility model
        "util_model_api_base": "http://localhost:11434",
        "util_model_ctx_length": 128000,
        
        "embed_model_provider": "ollama",
        "embed_model_name": "nomic-embed-text",
        "embed_model_api_base": "http://localhost:11434",
        
        "agent_memory_subdir": "mlcreator",
        "agent_knowledge_subdir": "mlcreator",
        
        # Enable memory features
        "memory_recall_enabled": True,
        "memory_recall_query_prep": True,
        "memory_recall_post_filter": True,
        
        # Parallelization limits (Ollama is local, can handle more)
        "chat_model_rl_requests": 0,  # Unlimited for local
        "util_model_rl_requests": 0,
        "embed_model_rl_requests": 0,
    }
    
    # Add fallback models
    updates["chat_model_kwargs"] = {
        "fallbacks": ["gemini/gemini-1.5-pro-latest"]
    }
    updates["util_model_kwargs"] = {
        "fallbacks": ["gemini/gemini-1.5-flash-latest"]
    }
    
    # Merge updates
    new_settings = settings.merge_settings(current, updates)
    
    # Save to tmp/settings.json
    settings_path = Path("tmp/settings.json")
    settings_path.parent.mkdir(exist_ok=True)
    
    with open(settings_path, "w") as f:
        json.dump(new_settings, f, indent=4)
        
    print(f"✅ Settings updated and saved to {settings_path}")
    print("Configuration:")
    print(f"  Chat: {new_settings['chat_model_provider']}/{new_settings['chat_model_name']}")
    print(f"  Util: {new_settings['util_model_provider']}/{new_settings['util_model_name']}")
    print(f"  Embed: {new_settings['embed_model_provider']}/{new_settings['embed_model_name']}")
    
    # Run memory initialization
    print("\n🧠 Running Memory Initialization...")
    import init_mlcreator_memory
    import asyncio
    
    initializer = init_mlcreator_memory.MLCreatorMemoryInitializer()
    asyncio.run(initializer.run())

if __name__ == "__main__":
    optimize()
