import os
import json
from io import BytesIO
from flask import Response
from python.helpers.api import ApiHandler, Request
from python.helpers import files, runtime, settings


class GenerateVsixScript(ApiHandler):
    """Generate a script to package and install the VS Code extension as VSIX"""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> Response:
        # Check if login/password is configured
        from python.helpers import dotenv, login
        
        auth_login = dotenv.get_dotenv_value("AUTH_LOGIN")
        auth_password = dotenv.get_dotenv_value("AUTH_PASSWORD")
        
        if not auth_login or not auth_password:
            error_msg = (
                "UI Login and Password must be configured before generating the VSIX script.\n\n"
                "Please go to Settings → Authentication and set:\n"
                "- UI Login\n"
                "- UI Password\n\n"
                "The API key is generated from these credentials and is required for the VS Code extension."
            )
            return Response(
                error_msg,
                status=400,
                mimetype='text/plain',
                headers={
                    'Content-Type': 'text/plain; charset=utf-8',
                }
            )
        
        # Get current settings
        current_settings = settings.get_settings()
        
        # Get the extension directory path
        extension_dir = files.get_abs_path("ide-extensions/vscode/agent-zero-provider")
        
        # Get the absolute path for the script
        if runtime.is_development():
            # In development, use the actual path
            abs_extension_dir = os.path.abspath(extension_dir)
        else:
            # In docker, we need to map container path to host path
            # The script will run on the host, so we need the host path
            # Try to detect from environment or use relative path from repo root
            base_dir = files.get_base_dir()
            # In Docker, base_dir is /a0, so we need to map it to host
            # Use relative path from repo root - user should run script from repo root
            abs_extension_dir = "ide-extensions/vscode/agent-zero-provider"
        
        # Read package.json to get version
        package_json_path = os.path.join(abs_extension_dir, "package.json")
        version = "0.0.1"  # default
        vsix_name = "agent-zero-provider-0.0.1.vsix"  # default
        
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    version = package_data.get("version", "0.0.1")
                    vsix_name = f"agent-zero-provider-{version}.vsix"
            except Exception:
                pass
        
        # Get configuration values
        # For the script running on host, use localhost with common port mapping
        # Default to 55000 (common Docker port mapping) or use port from runtime
        api_port = runtime.get_web_ui_port()
        # If port is 80 (container default), use 55000 (common host mapping)
        # Otherwise use the port as-is (might be custom)
        if api_port == 80:
            api_url = "http://localhost:55000"
        else:
            api_host = runtime.get_arg("host") or "localhost"
            # Replace 0.0.0.0 with localhost for host access
            if api_host == "0.0.0.0":
                api_host = "localhost"
            api_url = f"http://{api_host}:{api_port}"
        
        # Get API key (mcp_server_token is used for external API)
        api_key = current_settings.get("mcp_server_token", "")
        
        # Get host path and container path
        # Try to infer host path from base directory
        base_dir = files.get_base_dir()
        host_path = base_dir if runtime.is_development() else ""
        container_path = "/a0-01"  # default container path
        
        # If we're in docker, try to get the host path from environment or use a placeholder
        if runtime.is_dockerized():
            # In docker, we can't easily determine the host path, so use a placeholder
            host_path = "~/Projects"  # Common default
        
        # Generate the script content
        # Note: vsix_full_path will be set in the script itself since we use relative paths
        vsix_full_path = "$EXTENSION_DIR/" + vsix_name
        
        # Escape values for shell script
        def escape_shell(value):
            return str(value).replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
        
        api_url_escaped = escape_shell(api_url)
        api_key_escaped = escape_shell(api_key)
        host_path_escaped = escape_shell(host_path)
        container_path_escaped = escape_shell(container_path)
        
        script_content = f"""#!/bin/bash
# Script to package and install Agent Zero VS Code extension
# Generated by Agent Zero
# 
# Platform Support: macOS, Linux, Windows (Git Bash)
# 
# IMPORTANT: Before running this script:
# 1. Make sure Agent Zero is running in Docker
# 2. Place this script in the same directory that your Docker container 
#    has mounted (the directory bound to /a0-01 or similar in your docker run command)
# 3. Ensure the Agent Zero repository is accessible from that location
# 4. Run this script from the Agent Zero repository root directory

set -e

# Configuration values
API_HOST_URL="{api_url_escaped}"
API_KEY="{api_key_escaped}"
HOST_PATH="{host_path_escaped}"
CONTAINER_PATH="{container_path_escaped}"

echo "Agent Zero VS Code Extension Setup"
echo "==================================="
echo ""
echo "Platform: $(uname -s)"
echo ""
echo "IMPORTANT: This script must be run from the Agent Zero repository root directory."
echo "The repository should be in the same directory that Docker has mounted."
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r
echo ""

# Determine extension directory path
# Try to find the extension directory relative to script location or current directory
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
EXTENSION_DIR=""

# Try multiple possible locations
if [ -d "$SCRIPT_DIR/ide-extensions/vscode/agent-zero-provider" ]; then
    EXTENSION_DIR="$SCRIPT_DIR/ide-extensions/vscode/agent-zero-provider"
elif [ -d "$SCRIPT_DIR/../ide-extensions/vscode/agent-zero-provider" ]; then
    EXTENSION_DIR="$SCRIPT_DIR/../ide-extensions/vscode/agent-zero-provider"
elif [ -d "./ide-extensions/vscode/agent-zero-provider" ]; then
    EXTENSION_DIR="./ide-extensions/vscode/agent-zero-provider"
elif [ -d "$HOME/Projects/a0/agent-zero/ide-extensions/vscode/agent-zero-provider" ]; then
    EXTENSION_DIR="$HOME/Projects/a0/agent-zero/ide-extensions/vscode/agent-zero-provider"
elif [ -d "$HOME/Projects/agent-zero/ide-extensions/vscode/agent-zero-provider" ]; then
    EXTENSION_DIR="$HOME/Projects/agent-zero/ide-extensions/vscode/agent-zero-provider"
else
    echo "Error: Could not find extension directory."
    echo "Please run this script from the Agent Zero repository root directory,"
    echo "or place it in the repository root and run it from there."
    echo ""
    echo "Expected location: ide-extensions/vscode/agent-zero-provider"
    exit 1
fi

echo "Found extension directory: $EXTENSION_DIR"
echo ""

# Navigate to extension directory
cd "$EXTENSION_DIR"

# Check if vsce is installed
if ! command -v vsce &> /dev/null; then
    echo "Installing @vscode/vsce..."
    npm install -g @vscode/vsce
fi

# Package the extension
echo "Packaging VSIX extension..."
vsce package

# Install the extension
VSIX_FILE="$EXTENSION_DIR/{vsix_name}"
if [ ! -f "$VSIX_FILE" ]; then
    echo "Error: VSIX file not found at $VSIX_FILE"
    echo "Packaging may have failed. Check the output above."
    exit 1
fi

echo "Installing extension in VS Code..."
code --install-extension "$VSIX_FILE" --force

echo ""
echo "Configuring VS Code extension settings..."

# Determine VS Code settings.json location based on platform
# Supports: macOS, Linux, Windows (Git Bash)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    VSCODE_SETTINGS="$HOME/Library/Application Support/Code/User/settings.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux-musl"* ]]; then
    # Linux (GNU and musl-based)
    VSCODE_SETTINGS="$HOME/.config/Code/User/settings.json"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash, Cygwin, or native)
    if [ -n "$APPDATA" ]; then
        VSCODE_SETTINGS="$APPDATA/Code/User/settings.json"
    else
        # Fallback for Windows
        VSCODE_SETTINGS="$HOME/AppData/Roaming/Code/User/settings.json"
    fi
else
    echo "Warning: Unknown OS type ($OSTYPE). Please configure settings manually."
    echo "Supported platforms: macOS, Linux, Windows (Git Bash)"
    VSCODE_SETTINGS=""
fi

if [ -n "$VSCODE_SETTINGS" ]; then
    # Create settings.json if it doesn't exist
    mkdir -p "$(dirname "$VSCODE_SETTINGS")"
    if [ ! -f "$VSCODE_SETTINGS" ]; then
        echo "{{}}" > "$VSCODE_SETTINGS"
    fi
    
    # Read existing settings
    SETTINGS_JSON=$(cat "$VSCODE_SETTINGS")
    
    # Parse JSON and update agentZero settings
    # Use Python for reliable JSON manipulation
    python3 << PYTHON_SCRIPT
import json
import sys
import os

settings_file = "$VSCODE_SETTINGS"
api_host = "{api_url_escaped}"
api_key = "{api_key_escaped}"
host_path = "{host_path_escaped}"
container_path = "{container_path_escaped}"

try:
    # Read existing settings
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    else:
        settings = {{}}
    
    # Update agentZero settings
    if "agentZero" not in settings:
        settings["agentZero"] = {{}}
    
    settings["agentZero"]["apiHost"] = api_host
    settings["agentZero"]["apiKey"] = api_key
    settings["agentZero"]["hostPath"] = host_path
    settings["agentZero"]["containerPath"] = container_path
    settings["agentZero"]["useStreaming"] = True
    settings["agentZero"]["pollInterval"] = 100
    settings["agentZero"]["timeout"] = 300000
    
    # Write back
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)
    
    print("Settings updated successfully!")
except Exception as e:
    print(f"Error updating settings: {{e}}")
    sys.exit(1)
PYTHON_SCRIPT
    
    if [ $? -eq 0 ]; then
        echo "✓ VS Code extension settings configured"
    else
        echo "⚠ Failed to update settings automatically. Please configure manually:"
        echo "  - API Host: $API_HOST_URL"
        echo "  - API Key: $API_KEY"
        echo "  - Host Path: $HOST_PATH"
        echo "  - Container Path: $CONTAINER_PATH"
    fi
fi

echo ""
echo "==================================="
echo "Extension installed successfully!"
echo "VSIX file location: $VSIX_FILE"
echo ""
echo "Configuration:"
echo "  API Host: $API_HOST_URL"
if [ -n "$API_KEY" ]; then
    echo "  API Key: $(echo "$API_KEY" | sed 's/./*/g')"
else
    echo "  API Key: (not set)"
fi
echo "  Host Path: $HOST_PATH"
echo "  Container Path: $CONTAINER_PATH"
echo ""
echo "You can now use Agent Zero in VS Code Chat!"
"""

        # Create a BytesIO object with the script content
        script_bytes = BytesIO(script_content.encode('utf-8'))
        script_bytes.seek(0)
        
        # Create response with proper headers for script download
        response = Response(
            script_bytes.read(),
            content_type='text/x-shellscript',
            headers={
                'Content-Disposition': f'attachment; filename="package-vsix.sh"',
                'Cache-Control': 'no-cache',
            }
        )
        
        return response

