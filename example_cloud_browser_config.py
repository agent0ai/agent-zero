"""
Example configuration for Agent Zero with Browser Use Cloud integration

This example shows how to configure Agent Zero to use cloud browsers
instead of local browser installations.

Setup:
1. Get API key from https://cloud.browser-use.com/new-api-key
2. Set environment variable: export BROWSER_USE_API_KEY=your_key
3. Run this configuration

For more details, see docs/CLOUD_BROWSER_SETUP.md
"""

import os
from agent import AgentConfig, AgentContext, Agent
import models

# ============================================================================
# Model Configurations
# ============================================================================

# Chat model for main agent conversations
chat_model = models.ModelConfig(
    type=models.ModelType.CHAT,
    provider="openai",
    name="gpt-4",
    ctx_length=8000,
)

# Utility model for quick tasks
utility_model = models.ModelConfig(
    type=models.ModelType.CHAT,
    provider="openai",
    name="gpt-3.5-turbo",
    ctx_length=4000,
)

# Browser model with vision support
browser_model = models.ModelConfig(
    type=models.ModelType.CHAT,
    provider="openai",
    name="gpt-4-vision-preview",
    vision=True,
    ctx_length=8000,
)

# Embeddings model for memory/knowledge
embeddings_model = models.ModelConfig(
    type=models.ModelType.EMBEDDING,
    provider="openai",
    name="text-embedding-3-small",
)

# ============================================================================
# Agent Configuration with Cloud Browser
# ============================================================================

config = AgentConfig(
    # Model configurations
    chat_model=chat_model,
    utility_model=utility_model,
    browser_model=browser_model,
    embeddings_model=embeddings_model,

    # MCP servers (if any)
    mcp_servers="",

    # Cloud Browser Configuration
    # =============================
    browser_use_cloud=True,  # Enable cloud browsers (set to False for local)
    browser_use_stealth=True,  # Use stealth mode to avoid detection
    browser_cloud_api_key="",  # Leave empty to use BROWSER_USE_API_KEY env var

    # Optional: Custom HTTP headers for browser requests
    browser_http_headers={},

    # Other configurations
    profile="",  # Agent profile (optional)
    memory_subdir="",  # Memory subdirectory (optional)
    knowledge_subdirs=["default", "custom"],  # Knowledge directories

    # Code execution via SSH (optional)
    code_exec_ssh_enabled=True,
    code_exec_ssh_addr="localhost",
    code_exec_ssh_port=55022,
    code_exec_ssh_user="root",
    code_exec_ssh_pass="",
)

# ============================================================================
# Environment-Based Configuration
# ============================================================================

def get_environment_config():
    """
    Create configuration based on environment.
    - Production: Use cloud browsers
    - Development: Use local browsers
    """
    is_production = os.getenv("ENVIRONMENT") == "production"

    config_env = AgentConfig(
        chat_model=chat_model,
        utility_model=utility_model,
        browser_model=browser_model,
        embeddings_model=embeddings_model,
        mcp_servers="",

        # Use cloud browsers in production, local in development
        browser_use_cloud=is_production,
        browser_use_stealth=True,
    )

    return config_env


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    print("=== Agent Zero Cloud Browser Configuration ===\n")

    # Check if API key is set
    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        print("⚠️  Warning: BROWSER_USE_API_KEY environment variable not set")
        print("   Get your API key: https://cloud.browser-use.com/new-api-key")
        print("   Set it with: export BROWSER_USE_API_KEY=your_key\n")
    else:
        print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}\n")

    # Display configuration
    print("Configuration:")
    print(f"  Cloud Browser: {config.browser_use_cloud}")
    print(f"  Stealth Mode: {config.browser_use_stealth}")
    print(f"  Browser Model: {config.browser_model.name}")
    print(f"  Vision Support: {config.browser_model.vision}")
    print()

    # Create agent context
    print("Creating agent context...")
    context = AgentContext(config=config)

    # Create agent
    print("Creating agent...")
    agent = Agent(0, config, context)

    print("\n✅ Agent initialized with cloud browser support!")
    print("\nExample usage:")
    print('  await agent.message_loop("Go to google.com and search for Agent Zero")')
    print()
    print("For more examples, see docs/CLOUD_BROWSER_SETUP.md")


# ============================================================================
# Example: Multiple Parallel Browser Sessions
# ============================================================================

async def example_parallel_browsers():
    """
    Example showing how cloud browsers enable parallel execution
    without local resource constraints.
    """
    import asyncio

    async def search_task(query):
        """Perform a search task with browser"""
        agent = Agent(0, config, AgentContext(config=config))
        return await agent.message_loop(f"Search for '{query}' and summarize results")

    # With cloud browsers, you can run many tasks in parallel
    tasks = [
        search_task("AI agents"),
        search_task("Browser automation"),
        search_task("Web scraping"),
        search_task("Python frameworks"),
        search_task("Cloud computing"),
    ]

    # Run all searches in parallel
    results = await asyncio.gather(*tasks)
    return results


# ============================================================================
# Example: Fallback Configuration
# ============================================================================

def create_config_with_fallback():
    """
    Create configuration that falls back to local browser
    if cloud API key is not available.
    """
    has_api_key = bool(os.getenv("BROWSER_USE_API_KEY"))

    return AgentConfig(
        chat_model=chat_model,
        utility_model=utility_model,
        browser_model=browser_model,
        embeddings_model=embeddings_model,
        mcp_servers="",

        # Use cloud if API key available, otherwise local
        browser_use_cloud=has_api_key,
        browser_use_stealth=True,
    )


# ============================================================================
# Example: Cost-Optimized Configuration
# ============================================================================

def create_cost_optimized_config():
    """
    Configuration optimized for cost:
    - Use cheaper models where possible
    - Enable cloud browsers only when needed
    """
    return AgentConfig(
        # Use GPT-3.5 for most tasks
        chat_model=models.ModelConfig(
            type=models.ModelType.CHAT,
            provider="openai",
            name="gpt-3.5-turbo",
        ),

        # Use GPT-3.5 for utility
        utility_model=models.ModelConfig(
            type=models.ModelType.CHAT,
            provider="openai",
            name="gpt-3.5-turbo-instruct",
        ),

        # Only use GPT-4 Vision for browser (when necessary)
        browser_model=models.ModelConfig(
            type=models.ModelType.CHAT,
            provider="openai",
            name="gpt-4-vision-preview",
            vision=True,
        ),

        embeddings_model=embeddings_model,
        mcp_servers="",

        # Enable cloud browsers (more reliable at scale)
        browser_use_cloud=True,
        browser_use_stealth=True,
    )
