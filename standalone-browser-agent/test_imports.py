#!/usr/bin/env python3
"""
Simple test to verify all imports work correctly.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing imports...")

try:
    # Test basic imports
    print("✓ Importing browser_agent...")
    from browser_agent import BrowserAgent, TaskResult, Config
    print("  - BrowserAgent imported")
    print("  - TaskResult imported")
    print("  - Config imported")

    print("\n✓ Importing config classes...")
    from browser_agent import BrowserConfig, LLMConfig, AgentConfig
    print("  - BrowserConfig imported")
    print("  - LLMConfig imported")
    print("  - AgentConfig imported")

    print("\n✓ Importing helpers...")
    from browser_agent.helpers import apply_monkeypatch, ensure_playwright_installed
    print("  - apply_monkeypatch imported")
    print("  - ensure_playwright_installed imported")

    print("\n✓ Checking file paths...")
    agent_file = Path(__file__).parent / "browser_agent" / "agent.py"
    assert agent_file.exists(), f"agent.py not found at {agent_file}"
    print(f"  - agent.py exists at {agent_file}")

    config_file = Path(__file__).parent / "browser_agent" / "config.py"
    assert config_file.exists(), f"config.py not found at {config_file}"
    print(f"  - config.py exists at {config_file}")

    js_file = Path(__file__).parent / "browser_agent" / "js" / "init_override.js"
    assert js_file.exists(), f"init_override.js not found at {js_file}"
    print(f"  - init_override.js exists at {js_file}")

    prompt_file = Path(__file__).parent / "browser_agent" / "prompts" / "system_prompt.md"
    assert prompt_file.exists(), f"system_prompt.md not found at {prompt_file}"
    print(f"  - system_prompt.md exists at {prompt_file}")

    print("\n✓ Testing Config.from_env()...")
    config = Config.from_env()
    print(f"  - Config loaded successfully")
    print(f"  - LLM Provider: {config.llm.provider}")
    print(f"  - LLM Model: {config.llm.model}")
    print(f"  - Browser headless: {config.browser.headless}")
    print(f"  - Max steps: {config.agent.max_steps}")

    print("\n✓ All imports successful!")
    print("\n" + "="*60)
    print("Package structure is valid and ready to use!")
    print("="*60)

except ImportError as e:
    print(f"\n✗ Import error: {e}")
    sys.exit(1)
except AssertionError as e:
    print(f"\n✗ Assertion error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
