# 🌐 Cloud Browser Integration for Agent Zero

Agent Zero now supports **Browser Use Cloud**, enabling browser automation without local browser installations. This makes Agent Zero truly scalable and cloud-native.

---

## 🚀 Quick Start

### 1. Get API Key
Visit [Browser Use Cloud](https://cloud.browser-use.com/new-api-key) and get your API key.
- **New signups get $10 free credits!**

### 2. Set Environment Variable
```bash
export BROWSER_USE_API_KEY=your_api_key_here
```

### 3. Enable Cloud Browser
```python
from agent import AgentConfig

config = AgentConfig(
    # ... your model configs ...
    browser_use_cloud=True,  # Enable cloud browsers
    browser_use_stealth=True,  # Use stealth mode
)
```

### 4. Run Agent Zero
```python
context = AgentContext(config=config)
agent = Agent(0, config, context)

# Browser automation now runs in the cloud!
await agent.message_loop("Go to google.com and search for Agent Zero")
```

---

## ✨ Benefits

### Host-Independent
- ✅ No local Chrome/Chromium required
- ✅ No Playwright binary management
- ✅ Works on any machine

### Scalable
- ✅ Run multiple agents in parallel
- ✅ Cloud manages resources
- ✅ Better performance under load

### Stealth
- ✅ Advanced anti-detection
- ✅ Reduced CAPTCHA challenges
- ✅ Better success rates

### Production-Ready
- ✅ Proxy rotation
- ✅ Memory management
- ✅ High-performance execution

---

## 📚 Documentation

- **[Complete Setup Guide](docs/CLOUD_BROWSER_SETUP.md)** - Detailed configuration and usage
- **[Example Configuration](example_cloud_browser_config.py)** - Ready-to-use code examples
- **[Environment Variables](.env.example.cloud)** - Environment variable template

---

## 🆚 Local vs Cloud Browsers

| Feature | Local Browser | Cloud Browser |
|---------|--------------|---------------|
| Setup | Install Chrome | API key only |
| Resources | Uses local RAM/CPU | Cloud-managed |
| Scalability | Limited | Unlimited |
| Stealth | Basic | Advanced |
| CAPTCHA | Common | Rare |
| Cost | Free (local resources) | Pay-per-use |

---

## 💡 Configuration Examples

### Simple Cloud Browser

```python
config = AgentConfig(
    # ... models ...
    browser_use_cloud=True,
)
```

### Environment-Based

```python
import os

config = AgentConfig(
    # ... models ...
    # Use cloud in production, local in development
    browser_use_cloud=(os.getenv("ENVIRONMENT") == "production"),
)
```

### With Custom API Key

```python
config = AgentConfig(
    # ... models ...
    browser_use_cloud=True,
    browser_cloud_api_key="your_key_here",
)
```

---

## 🔧 Configuration Options

### `browser_use_cloud` (bool)
- **Default**: `False`
- **Description**: Enable cloud browsers
- **Usage**: Set to `True` to use Browser Use Cloud

### `browser_use_stealth` (bool)
- **Default**: `True`
- **Description**: Use stealth mode
- **Usage**: Helps avoid bot detection

### `browser_cloud_api_key` (str)
- **Default**: `""` (uses env var)
- **Description**: API key for Browser Use Cloud
- **Usage**: Can also use `BROWSER_USE_API_KEY` environment variable

---

## 🎯 Use Cases

### Web Scraping at Scale
```python
# Run 10 parallel scraping tasks (not possible with local browsers)
tasks = [scrape_website(url) for url in urls]
results = await asyncio.gather(*tasks)
```

### E-commerce Automation
```python
# Automate product research without CAPTCHA challenges
await agent.message_loop("Find the best deals on laptops under $1000")
```

### Testing in Production
```python
# Run browser tests without local Chrome
await agent.message_loop("Test the checkout flow on our website")
```

---

## 🛠️ Migration from Local Browsers

### Before (Local)
```python
config = AgentConfig(
    # ... models ...
    # Uses local browser by default
)
```

### After (Cloud)
```python
# 1. Get API key: https://cloud.browser-use.com/new-api-key
# 2. Set environment variable
export BROWSER_USE_API_KEY=your_key

# 3. Enable cloud browser
config = AgentConfig(
    # ... models ...
    browser_use_cloud=True,
)
```

**That's it!** No other code changes required.

---

## 📊 Cost and Pricing

- **Free Tier**: $10 credits for new signups
- **Pricing**: Pay-per-use based on browser time
- **Dashboard**: [Track usage](https://cloud.browser-use.com/dashboard)

For detailed pricing: https://cloud.browser-use.com/pricing

---

## 🔍 Troubleshooting

### API Key Not Found
```bash
# Check if environment variable is set
echo $BROWSER_USE_API_KEY

# If not, set it
export BROWSER_USE_API_KEY=your_key
```

### Want to Use Local Browser Again?
```python
# Simply set to False
config.browser_use_cloud = False
```

### Getting Rate Limit Errors?
- Check your credit balance
- Reduce parallel browser sessions
- Contact Browser Use Cloud support

---

## 📖 Additional Resources

- **Browser Use Cloud**: https://cloud.browser-use.com
- **Documentation**: https://docs.cloud.browser-use.com
- **GitHub**: https://github.com/browser-use/browser-use
- **Agent Zero Docs**: [Main README](README.md)

---

## 🎉 Summary

Cloud browser integration makes Agent Zero:
- ✅ **Independent** from host system
- ✅ **Scalable** for production use
- ✅ **Stealth-capable** for better success rates
- ✅ **Easy to configure** with just an API key

Get started now: [Get API Key](https://cloud.browser-use.com/new-api-key) 🚀

---

**Questions?** See the [Complete Setup Guide](docs/CLOUD_BROWSER_SETUP.md) for detailed information.
