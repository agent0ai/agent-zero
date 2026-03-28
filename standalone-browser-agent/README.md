# Browser Agent

A standalone browser automation library that uses natural language instructions to control a web browser. Built on top of [browser-use](https://github.com/browser-use/browser-use) and [Playwright](https://playwright.dev/).

## Features

- 🤖 **Natural Language Control**: Describe what you want to do in plain English
- 🌐 **Multi-Provider LLM Support**: Works with OpenAI, Anthropic, Google Gemini, and more via LiteLLM
- 🎭 **Playwright-Powered**: Reliable browser automation with full Chrome/Chromium support
- 📸 **Screenshot Capture**: Take screenshots at any point during automation
- ⚙️ **Configurable**: Customize browser settings, LLM parameters, and agent behavior
- 🐍 **Python & CLI**: Use as a Python library or command-line tool
- 🔄 **Async Support**: Built with asyncio for efficient concurrent operations

## Installation

```bash
# Clone or download this directory
cd standalone-browser-agent

# Install dependencies
pip install -r requirements.txt

# Install playwright browsers
python -m playwright install chromium

# Or use the setup command
python cli.py setup
```

## Quick Start

### Python API

```python
from browser_agent import BrowserAgent
import asyncio

async def main():
    async with BrowserAgent() as agent:
        result = await agent.run("Go to google.com and search for 'Python'")
        print(result.response)

asyncio.run(main())
```

### Command Line

```bash
# Set your API key
export OPENAI_API_KEY="your-api-key-here"

# Run a task
python cli.py run "Go to example.com and tell me what you see"

# With options
python cli.py run "Search for AI news" --model gpt-4o --no-headless
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=your-api-key-here
LLM_TEMPERATURE=0.7
LLM_USE_VISION=true

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_WIDTH=1024
BROWSER_HEIGHT=2048
BROWSER_DOWNLOADS_PATH=./downloads

# Agent Configuration
AGENT_MAX_STEPS=50
AGENT_LLM_TIMEOUT=300
AGENT_ENABLE_MEMORY=false
```

### Python Configuration

```python
from browser_agent import BrowserAgent, Config, BrowserConfig, LLMConfig

config = Config(
    browser=BrowserConfig(
        headless=False,
        width=1920,
        height=1080,
    ),
    llm=LLMConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        api_key="your-api-key",
    ),
)

agent = BrowserAgent(config)
```

## Supported LLM Providers

Thanks to [LiteLLM](https://github.com/BerriAI/litellm), this library supports:

- **OpenAI**: GPT-4, GPT-4o, GPT-3.5-turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **Google**: Gemini Pro, Gemini Flash
- **And many more**: Azure OpenAI, Cohere, Replicate, etc.

Set the provider and model:

```python
# OpenAI
config.llm.provider = "openai"
config.llm.model = "gpt-4o"

# Anthropic
config.llm.provider = "anthropic"
config.llm.model = "claude-3-5-sonnet-20241022"

# Google
config.llm.provider = "gemini"
config.llm.model = "gemini-1.5-pro"
```

## Examples

### Basic Navigation

```python
from browser_agent import BrowserAgent
import asyncio

async def main():
    agent = BrowserAgent()
    result = await agent.run("Go to example.com")
    print(result.response)
    await agent.close()

asyncio.run(main())
```

### Web Search

```python
async with BrowserAgent() as agent:
    result = await agent.run(
        "Go to google.com and search for 'Python tutorials'. "
        "Tell me the title of the first result."
    )
    print(result.response)
```

### Form Interaction

```python
async with BrowserAgent() as agent:
    result = await agent.run(
        "Go to example.com/contact and fill out the contact form "
        "with name 'John Doe' and email 'john@example.com'"
    )
    print(result.response)
```

### Screenshots

```python
async with BrowserAgent() as agent:
    await agent.run("Go to wikipedia.org")
    await agent.screenshot("screenshot.png", full_page=True)
```

### Step Callbacks

```python
async def on_step_start(agent):
    print("Starting step...")

async def on_step_end(agent):
    print("Step completed!")

async with BrowserAgent() as agent:
    result = await agent.run(
        "Navigate to hacker news and get the top story",
        on_step_start=on_step_start,
        on_step_end=on_step_end,
    )
```

See the [examples](./examples) directory for more examples.

## CLI Usage

```bash
# Run a task
python cli.py run "Go to google.com"

# Custom model
python cli.py run "Search for Python tutorials" --model gpt-4o --provider openai

# Save screenshot
python cli.py run "Go to example.com" --screenshot result.png

# Show browser (non-headless)
python cli.py run "Navigate to reddit.com" --no-headless

# Check configuration
python cli.py config

# Show examples
python cli.py example

# Install browsers
python cli.py setup
```

## API Reference

### BrowserAgent

Main class for browser automation.

#### Methods

- `__init__(config: Optional[Config] = None)`: Initialize agent
- `async run(task: str, max_steps: Optional[int] = None, on_step_start: Optional[Callable] = None, on_step_end: Optional[Callable] = None) -> TaskResult`: Run a task
- `async screenshot(path: str, full_page: bool = False)`: Take a screenshot
- `async close()`: Close browser session

### TaskResult

Result of a task execution.

#### Attributes

- `title: str`: Task title
- `response: str`: Main response/answer
- `page_summary: str`: Summary of the final page
- `success: bool`: Whether task completed successfully
- `final_url: Optional[str]`: Final URL visited

### Config

Configuration for the browser agent.

#### Sub-configs

- `browser: BrowserConfig`: Browser settings
- `llm: LLMConfig`: LLM settings
- `agent: AgentConfig`: Agent behavior settings

## How It Works

1. **Natural Language Input**: You provide a task in natural language
2. **LLM Processing**: The LLM interprets the task and decides actions
3. **Browser Control**: Actions are executed via Playwright
4. **Vision Analysis**: Screenshots are analyzed to understand page state
5. **Iteration**: Process repeats until task is complete or max steps reached
6. **Result**: Final result with response and page summary

## Troubleshooting

### Browser Installation Issues

```bash
# Manually install playwright browsers
python -m playwright install chromium

# Or with dependencies
python -m playwright install --with-deps chromium
```

### API Key Issues

Ensure your API key is set:

```bash
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"
```

### Import Errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Architecture

```
browser_agent/
├── agent.py              # Main BrowserAgent class
├── config.py             # Configuration management
├── helpers/
│   ├── browser_use_monkeypatch.py  # Compatibility patches
│   └── playwright_helper.py        # Browser setup
├── prompts/
│   └── system_prompt.md  # Agent behavior instructions
└── js/
    └── init_override.js  # Browser initialization script
```

## Contributing

This is a standalone extraction from [Agent Zero](https://github.com/frdel/agent-zero).

## License

MIT License - See the main Agent Zero repository for details.

## Credits

Built on top of:
- [browser-use](https://github.com/browser-use/browser-use) - Browser automation framework
- [Playwright](https://playwright.dev/) - Browser automation library
- [LiteLLM](https://github.com/BerriAI/litellm) - LLM API abstraction
- [Agent Zero](https://github.com/frdel/agent-zero) - Original implementation

## Related Projects

- [Agent Zero](https://github.com/frdel/agent-zero) - Full AI agent framework
- [browser-use](https://github.com/browser-use/browser-use) - Browser automation with LLMs
- [Playwright](https://playwright.dev/) - End-to-end testing framework
