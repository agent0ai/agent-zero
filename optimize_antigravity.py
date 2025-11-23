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
    
    # Update for Google AI (Gemini API) - simpler than Vertex AI
    # Uses direct Gemini API instead of Vertex AI
    updates = {
        "chat_model_provider": "gemini",
        "chat_model_name": "gemini-1.5-pro",
        "chat_model_ctx_length": 1000000,
        
        "util_model_provider": "gemini",
        "util_model_name": "gemini-1.5-flash",
        "util_model_ctx_length": 1000000,
        
        "embed_model_provider": "gemini",
        "embed_model_name": "text-embedding-004",
        
        "agent_memory_subdir": "mlcreator",
        "agent_knowledge_subdir": "mlcreator",
        
        # Enable memory features
        "memory_recall_enabled": True,
        "memory_recall_query_prep": True,
        "memory_recall_post_filter": True,
        
        # Parallelization limits
        "chat_model_rl_requests": 60, 
        "util_model_rl_requests": 60,
        "embed_model_rl_requests": 10,
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
