"""
Standalone Browser Agent - Natural Language Web Automation

A lightweight browser automation library that uses natural language instructions
to control a web browser. Built on top of browser-use and playwright.

Example:
    ```python
    from browser_agent import BrowserAgent

    async def main():
        agent = BrowserAgent()
        result = await agent.run("Go to google.com and search for 'Python'")
        print(result.response)
        await agent.close()

    # Or use as context manager
    async def main():
        async with BrowserAgent() as agent:
            result = await agent.run("Go to example.com")
            print(result.response)
    ```
"""

from .agent import BrowserAgent, TaskResult
from .config import Config, BrowserConfig, LLMConfig, AgentConfig

__version__ = "1.0.0"
__all__ = [
    "BrowserAgent",
    "TaskResult",
    "Config",
    "BrowserConfig",
    "LLMConfig",
    "AgentConfig",
]
