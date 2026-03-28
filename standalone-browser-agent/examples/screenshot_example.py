"""
Screenshot example for Browser Agent.

This example shows how to capture screenshots during automation.
"""

import asyncio
from browser_agent import BrowserAgent


async def main():
    """Navigate and capture a screenshot."""
    async with BrowserAgent() as agent:
        # Navigate to a website
        print("Navigating to Wikipedia...")
        result = await agent.run("Go to wikipedia.org")

        print(f"Result: {result.response}")

        # Take a screenshot
        screenshot_path = "wikipedia_homepage.png"
        await agent.screenshot(screenshot_path, full_page=True)
        print(f"\nScreenshot saved to: {screenshot_path}")


if __name__ == "__main__":
    asyncio.run(main())
