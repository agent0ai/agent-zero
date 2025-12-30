"""
Form filling example for Browser Agent.

This example shows how to use the browser agent to fill out web forms.
"""

import asyncio
from browser_agent import BrowserAgent, Config, BrowserConfig


async def main():
    """Fill out a web form."""
    # Configure with visible browser for demonstration
    config = Config(
        browser=BrowserConfig(
            headless=False,  # Show the browser window
            width=1920,
            height=1080,
        )
    )

    async with BrowserAgent(config) as agent:
        # Fill out a form
        print("Filling out a demo form...")
        result = await agent.run(
            "Go to https://www.w3schools.com/html/html_forms.asp and "
            "find any input fields on the page. Tell me what form elements you found."
        )

        print(f"\nResult: {result.response}")


if __name__ == "__main__":
    asyncio.run(main())
