"""
Search example for Browser Agent.

This example shows how to use the browser agent to perform a web search
and extract information.
"""

import asyncio
from browser_agent import BrowserAgent, Config, LLMConfig


async def main():
    """Run a web search task."""
    # Configure the agent (optional - can use environment variables instead)
    config = Config(
        llm=LLMConfig(
            model="gpt-4o",
            provider="openai",
            temperature=0.7,
        )
    )

    # Use context manager for automatic cleanup
    async with BrowserAgent(config) as agent:
        # Perform a web search
        print("Searching for Python tutorials...")
        result = await agent.run(
            "Go to google.com and search for 'Python tutorials for beginners'. "
            "Tell me the title of the first result."
        )

        print(f"\n{result.response}")


if __name__ == "__main__":
    asyncio.run(main())
