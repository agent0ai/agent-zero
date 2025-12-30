"""
Advanced usage example for Browser Agent.

This example demonstrates advanced features like step callbacks and
custom configuration.
"""

import asyncio
from browser_agent import BrowserAgent, Config, BrowserConfig, LLMConfig, AgentConfig


async def on_step_start(agent):
    """Callback before each step."""
    print("→ Starting new step...")


async def on_step_end(agent):
    """Callback after each step."""
    print("✓ Step completed")


async def main():
    """Run an advanced automation task."""
    # Full configuration
    config = Config(
        browser=BrowserConfig(
            headless=True,
            width=1920,
            height=1080,
            downloads_path="./downloads",
        ),
        llm=LLMConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.5,
            use_vision=True,
        ),
        agent=AgentConfig(
            max_steps=30,
            llm_timeout=300,
            enable_memory=False,
        ),
    )

    async with BrowserAgent(config) as agent:
        # Run complex task with callbacks
        print("Running advanced task with step callbacks...\n")
        result = await agent.run(
            task=(
                "Go to hacker news (news.ycombinator.com) and tell me "
                "the title and points of the top 3 stories"
            ),
            max_steps=20,
            on_step_start=on_step_start,
            on_step_end=on_step_end,
        )

        print(f"\n{'='*60}")
        print(f"Title: {result.title}")
        print(f"{'='*60}")
        print(f"\n{result.response}\n")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
