"""
Basic usage example for Browser Agent.

This example shows how to use the browser agent to navigate to a website
and perform simple tasks.
"""

import asyncio
from browser_agent import BrowserAgent


async def main():
    """Run a basic browser automation task."""
    # Create agent instance
    agent = BrowserAgent()

    try:
        # Run a simple task
        print("Running task: Navigate to example.com")
        result = await agent.run("Go to example.com and tell me what you see")

        # Print results
        print(f"\nTitle: {result.title}")
        print(f"Response: {result.response}")
        print(f"Page Summary: {result.page_summary}")
        print(f"Success: {result.success}")

    finally:
        # Always close the browser
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
