#!/usr/bin/env python3
"""
Command-line interface for the standalone browser agent.
"""

import asyncio
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path

from browser_agent import BrowserAgent, Config

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Browser Agent - Natural Language Web Automation

    Control your browser using natural language instructions.
    """
    pass


@cli.command()
@click.argument("task")
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Run browser in headless mode (default: headless)",
)
@click.option(
    "--model",
    default="gpt-4o",
    help="LLM model to use (default: gpt-4o)",
)
@click.option(
    "--provider",
    default="openai",
    help="LLM provider (openai, anthropic, google, etc.)",
)
@click.option(
    "--max-steps",
    default=50,
    type=int,
    help="Maximum number of steps (default: 50)",
)
@click.option(
    "--screenshot",
    type=click.Path(),
    help="Save screenshot to this path after task completion",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Path to .env file for configuration",
)
def run(task, headless, model, provider, max_steps, screenshot, env_file):
    """
    Run a browser automation task.

    TASK: Natural language description of what to do

    Examples:

        browser-agent run "Go to google.com and search for 'Python'"

        browser-agent run "Navigate to reddit.com and get the top post title" --model gpt-4o

        browser-agent run "Go to example.com" --screenshot result.png
    """
    asyncio.run(_run_task(task, headless, model, provider, max_steps, screenshot, env_file))


async def _run_task(task, headless, model, provider, max_steps, screenshot, env_file):
    """Internal async function to run the task."""
    console.print(
        Panel(
            f"[bold cyan]Task:[/bold cyan] {task}",
            title="Browser Agent",
            border_style="cyan",
        )
    )

    # Load config
    config = Config.from_env(env_file)
    config.browser.headless = headless
    config.llm.model = model
    config.llm.provider = provider
    config.agent.max_steps = max_steps

    # Initialize agent
    agent = BrowserAgent(config)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress_task = progress.add_task("Running browser agent...", total=None)

            # Run the task
            result = await agent.run(task, max_steps=max_steps)

            progress.update(progress_task, completed=True)

        # Display result
        console.print()
        console.print(Panel(
            f"[bold green]Title:[/bold green] {result.title}\n\n"
            f"[bold green]Response:[/bold green]\n{result.response}\n\n"
            f"[bold green]Page Summary:[/bold green]\n{result.page_summary}",
            title="✓ Task Completed" if result.success else "⚠ Task Incomplete",
            border_style="green" if result.success else "yellow",
        ))

        if result.final_url:
            console.print(f"[dim]Final URL: {result.final_url}[/dim]")

        # Take screenshot if requested
        if screenshot:
            await agent.screenshot(screenshot, full_page=True)
            console.print(f"\n[green]Screenshot saved to:[/green] {screenshot}")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        raise
    finally:
        await agent.close()


@cli.command()
def setup():
    """
    Install playwright browsers and check setup.
    """
    console.print("[cyan]Installing playwright browsers...[/cyan]")

    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            console.print("[green]✓ Playwright browsers installed successfully![/green]")
        else:
            console.print(f"[red]Error installing browsers:[/red]\n{result.stderr}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@cli.command()
def config():
    """
    Show current configuration.
    """
    cfg = Config.from_env()

    config_text = f"""
## Browser Configuration
- Headless: {cfg.browser.headless}
- Viewport: {cfg.browser.width}x{cfg.browser.height}
- Downloads: {cfg.browser.downloads_path}

## LLM Configuration
- Provider: {cfg.llm.provider}
- Model: {cfg.llm.model}
- Temperature: {cfg.llm.temperature}
- Use Vision: {cfg.llm.use_vision}

## Agent Configuration
- Max Steps: {cfg.agent.max_steps}
- LLM Timeout: {cfg.agent.llm_timeout}s
- Enable Memory: {cfg.agent.enable_memory}
    """

    console.print(Panel(Markdown(config_text.strip()), title="Configuration", border_style="cyan"))


@cli.command()
def example():
    """
    Show example usage.
    """
    examples = """
# Browser Agent Examples

## Basic Usage

```python
from browser_agent import BrowserAgent
import asyncio

async def main():
    agent = BrowserAgent()
    result = await agent.run("Go to google.com and search for 'Python'")
    print(result.response)
    await agent.close()

asyncio.run(main())
```

## Using Context Manager

```python
from browser_agent import BrowserAgent
import asyncio

async def main():
    async with BrowserAgent() as agent:
        result = await agent.run("Navigate to example.com and get the page title")
        print(f"Title: {result.title}")
        print(f"Response: {result.response}")

asyncio.run(main())
```

## Custom Configuration

```python
from browser_agent import BrowserAgent, Config, BrowserConfig, LLMConfig

config = Config(
    browser=BrowserConfig(
        headless=False,  # Show browser
        width=1920,
        height=1080,
    ),
    llm=LLMConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        temperature=0.5,
    ),
)

async def main():
    async with BrowserAgent(config) as agent:
        result = await agent.run("Search for AI news on reddit")
        print(result.response)

asyncio.run(main())
```

## CLI Usage

```bash
# Basic task
browser-agent run "Go to google.com"

# With custom model
browser-agent run "Search for Python tutorials" --model gpt-4o --provider openai

# Save screenshot
browser-agent run "Go to example.com" --screenshot result.png

# Show browser window
browser-agent run "Navigate to reddit.com" --no-headless
```
    """

    console.print(Markdown(examples.strip()))


if __name__ == "__main__":
    cli()
