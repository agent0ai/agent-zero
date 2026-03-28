import subprocess
import os


def execute(runtime_path: str, agent, state: dict) -> dict:
    """Clean up any previous jc installation to ensure fresh test."""
    result = {"cleanup": []}
    
    # Try to uninstall jc if it exists
    try:
        subprocess.run(
            ["pip", "uninstall", "jc", "-y"],
            capture_output=True,
            text=True,
            timeout=60
        )
        result["cleanup"].append("Uninstalled existing jc package")
    except Exception as e:
        result["cleanup"].append(f"No existing jc to uninstall: {e}")
    
    # Clean the runtime directory
    for item in os.listdir(runtime_path):
        item_path = os.path.join(runtime_path, item)
        if os.path.isdir(item_path):
            try:
                subprocess.run(["rm", "-rf", item_path], timeout=30)
                result["cleanup"].append(f"Removed directory: {item}")
            except Exception:
                pass
    
    return result