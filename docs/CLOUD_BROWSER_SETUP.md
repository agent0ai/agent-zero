# Browser Use Cloud Integration for Agent Zero

This document explains how to configure Agent Zero to use Browser Use Cloud instead of local browsers, making browser automation independent from the host system and scalable.

## Table of Contents

1. [Overview](#overview)
2. [Benefits of Cloud Browsers](#benefits-of-cloud-browsers)
3. [Setup Instructions](#setup-instructions)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Agent Zero now supports **Browser Use Cloud**, allowing browser automation to run on cloud infrastructure instead of requiring local browser installations. This makes Agent Zero:

- **Host-independent**: No need to install Chrome/Chromium locally
- **Scalable**: Cloud infrastructure handles memory and resource management
- **Stealth-capable**: Cloud browsers are optimized to avoid CAPTCHA and bot detection
- **Production-ready**: Handles parallel execution and proxy rotation automatically

### How It Works

When cloud browser mode is enabled, Agent Zero connects to Browser Use Cloud API instead of launching a local browser instance. All browser automation runs in the cloud, with results streamed back to Agent Zero.

---

## Benefits of Cloud Browsers

### 1. **No Local Browser Required**
- No need to install or maintain Chromium/Chrome
- No Playwright binary management
- Reduces local resource consumption

### 2. **Scalable Infrastructure**
- Run multiple agents in parallel without memory concerns
- Cloud handles resource allocation automatically
- Better performance under load

### 3. **Stealth Browsers**
- Designed to avoid bot detection
- Reduced CAPTCHA challenges
- Better success rates for web scraping

### 4. **Production Features**
- Proxy rotation
- Browser fingerprinting
- Memory management
- High-performance execution

---

## Setup Instructions

### Step 1: Get Browser Use Cloud API Key

1. Visit [Browser Use Cloud](https://cloud.browser-use.com/new-api-key)
2. Sign up for an account
3. New signups receive **$10 free credits**
4. Copy your API key

### Step 2: Configure API Key

You have two options to provide the API key:

#### Option A: Environment Variable (Recommended)

Add to your `.env` file:

```bash
BROWSER_USE_API_KEY=your_api_key_here
```

Or export in your shell:

```bash
export BROWSER_USE_API_KEY=your_api_key_here
```

#### Option B: Configuration File

When initializing Agent Zero, set the API key in config:

```python
from agent import AgentConfig

config = AgentConfig(
    # ... other config ...
    browser_use_cloud=True,
    browser_cloud_api_key="your_api_key_here",
    browser_use_stealth=True,
)
```

### Step 3: Enable Cloud Browser Mode

Set `browser_use_cloud=True` in your agent configuration:

```python
config = AgentConfig(
    # ... model configs ...
    browser_use_cloud=True,  # Enable cloud browsers
    browser_use_stealth=True,  # Use stealth mode (recommended)
)
```

---

## Configuration

### Configuration Options

Agent Zero provides three new configuration options for cloud browsers:

#### `browser_use_cloud` (bool)
- **Default**: `False`
- **Description**: Enable Browser Use Cloud instead of local browser
- **Usage**: Set to `True` to use cloud browsers

```python
config.browser_use_cloud = True
```

#### `browser_use_stealth` (bool)
- **Default**: `True`
- **Description**: Use stealth mode for cloud browsers
- **Usage**: Helps avoid detection and CAPTCHA challenges

```python
config.browser_use_stealth = True
```

#### `browser_cloud_api_key` (str)
- **Default**: `""` (empty string)
- **Description**: Browser Use Cloud API key
- **Usage**: Can also use `BROWSER_USE_API_KEY` environment variable

```python
config.browser_cloud_api_key = "your_api_key"
```

### Complete Configuration Example

```python
from agent import AgentConfig, AgentContext
import models

# Define model configurations
chat_model = models.ModelConfig(
    type=models.ModelType.CHAT,
    provider="openai",
    name="gpt-4",
)

browser_model = models.ModelConfig(
    type=models.ModelType.CHAT,
    provider="openai",
    name="gpt-4-vision",
    vision=True,
)

utility_model = models.ModelConfig(
    type=models.ModelType.CHAT,
    provider="openai",
    name="gpt-3.5-turbo",
)

embeddings_model = models.ModelConfig(
    type=models.ModelType.EMBEDDING,
    provider="openai",
    name="text-embedding-3-small",
)

# Create configuration with cloud browser enabled
config = AgentConfig(
    chat_model=chat_model,
    utility_model=utility_model,
    embeddings_model=embeddings_model,
    browser_model=browser_model,
    mcp_servers="",

    # Cloud browser configuration
    browser_use_cloud=True,
    browser_use_stealth=True,
    browser_cloud_api_key="",  # Or set BROWSER_USE_API_KEY env var
)

# Create agent context
context = AgentContext(config=config)
```

---

## Usage Examples

### Example 1: Basic Cloud Browser Usage

```python
# Agent automatically uses cloud browser when configured
user_message = "Go to google.com and search for 'Agent Zero'"

# The browser_agent tool will use cloud browser
response = await agent.message_loop(user_message)
```

### Example 2: Switching Between Local and Cloud

```python
# Use cloud browser for production
if os.getenv("ENVIRONMENT") == "production":
    config.browser_use_cloud = True
else:
    # Use local browser for development
    config.browser_use_cloud = False
```

### Example 3: Multiple Parallel Browser Sessions

With cloud browsers, you can run multiple agents in parallel without worrying about memory:

```python
import asyncio

async def run_browser_task(task_description):
    # Each agent uses cloud browser
    agent = Agent(0, config, context)
    return await agent.message_loop(task_description)

# Run 10 browser tasks in parallel (not feasible with local browsers)
tasks = [
    run_browser_task(f"Search for product {i}")
    for i in range(10)
]

results = await asyncio.gather(*tasks)
```

---

## Comparison: Local vs Cloud Browsers

| Feature | Local Browser | Cloud Browser |
|---------|--------------|---------------|
| **Setup** | Requires Chromium/Chrome installation | API key only |
| **Resources** | Uses local CPU/RAM | Cloud-managed |
| **Scalability** | Limited by local resources | Highly scalable |
| **Stealth** | Basic | Advanced anti-detection |
| **CAPTCHA** | Common challenges | Reduced challenges |
| **Memory** | Can consume significant RAM | Managed by cloud |
| **Parallel Execution** | Limited | High-performance |
| **Cost** | Free (but uses local resources) | Pay-per-use (free credits available) |
| **Proxy Support** | Manual configuration | Automatic rotation |

---

## Troubleshooting

### API Key Not Found

**Error**: "No Browser Use Cloud API key found"

**Solution**:
1. Verify API key is set in environment variable:
   ```bash
   echo $BROWSER_USE_API_KEY
   ```
2. Or set in configuration:
   ```python
   config.browser_cloud_api_key = "your_key"
   ```

### Cloud Browser Initialization Failed

**Error**: Browser session initialization error

**Solution**:
1. Check API key is valid
2. Verify you have remaining credits
3. Check internet connectivity
4. Review Browser Use Cloud status: https://cloud.browser-use.com/status

### Different Behavior Between Local and Cloud

Some features may behave differently between local and cloud browsers:

- **Downloads**: Cloud browsers may handle downloads differently
- **Custom headers**: May need adjustment for cloud environment
- **Init scripts**: Only applied to local browsers

**Solution**: Test your automation with cloud browsers and adjust as needed.

### Want to Revert to Local Browser

Set `browser_use_cloud=False` in configuration:

```python
config.browser_use_cloud = False
```

Or remove/comment out the environment variable.

---

## Best Practices

### 1. Use Cloud Browsers for Production
- More reliable and scalable
- Better for high-volume automation
- Reduced infrastructure management

### 2. Use Local Browsers for Development
- Faster iteration during development
- No API costs
- Easier debugging

### 3. Enable Stealth Mode
Always use `browser_use_stealth=True` for cloud browsers to:
- Reduce CAPTCHA challenges
- Improve success rates
- Better mimic human browsing

### 4. Monitor API Usage
- Track your cloud browser usage
- Set up alerts for high usage
- Optimize automation to reduce costs

### 5. Handle Errors Gracefully
- Cloud browsers can fail (network issues, API limits)
- Implement retry logic
- Have fallback mechanisms

---

## API Pricing and Credits

- **Free Credits**: $10 for new signups
- **Pricing**: Pay-per-use based on browser time
- **Check Usage**: [Browser Use Cloud Dashboard](https://cloud.browser-use.com/dashboard)

For detailed pricing, visit: https://cloud.browser-use.com/pricing

---

## Additional Resources

- **Browser Use Cloud Docs**: https://docs.cloud.browser-use.com
- **Browser Use GitHub**: https://github.com/browser-use/browser-use
- **Agent Zero Docs**: [Main Documentation](./README.md)
- **Get API Key**: https://cloud.browser-use.com/new-api-key

---

## Migration Guide: Local to Cloud

### Before (Local Browser)

```python
config = AgentConfig(
    # ... models ...
    browser_use_cloud=False,  # Default
)
```

### After (Cloud Browser)

```python
# 1. Get API key from https://cloud.browser-use.com/new-api-key
# 2. Set environment variable
export BROWSER_USE_API_KEY=your_key_here

# 3. Update config
config = AgentConfig(
    # ... models ...
    browser_use_cloud=True,
    browser_use_stealth=True,
)
```

That's it! Agent Zero will now use cloud browsers instead of local ones.

---

## Summary

Browser Use Cloud integration makes Agent Zero:
- ✅ Host-independent
- ✅ Highly scalable
- ✅ Production-ready
- ✅ Stealth-capable
- ✅ Easy to configure

Get started with $10 free credits: https://cloud.browser-use.com/new-api-key
