# Troubleshooting and FAQ
This page addresses frequently asked questions (FAQ) and provides troubleshooting steps for common issues encountered while using Agent Zero.

## Frequently Asked Questions
**1. How do I ask Agent Zero to work directly on my files or dirs?**
- Place the files/dirs in `/a0/usr`. Agent Zero will be able to perform tasks on them.

**2. When I input something in the chat, nothing happens. What's wrong?**
- Check if you have set up API keys in the Settings page. If not, the application cannot call LLM providers.

**3. I get “Invalid model ID.” What does that mean?**
- Verify the **provider** and **model naming**. For example, `openai/gpt-5.3` is correct for OpenRouter, but **incorrect** for the native OpenAI provider, which goes without prefix.

**4. Does ChatGPT Plus include API access?**
- No. ChatGPT Plus does not include API credits. You must provide an OpenAI API key in Settings.

**5. Where is chat history stored?**
- Chat history lives at `/a0/usr/chats/` inside the container.

**6. How do I integrate open-source models with Agent Zero?**
Refer to the [Choosing your LLMs](../setup/installation.md#installing-and-using-ollama-local-models) section for configuring local models (Ollama, LM Studio, etc.).

> [!TIP]
> Some LLM providers offer free usage tiers, for example Groq, Mistral, SambaNova, or CometAPI.

**7. How can I make Agent Zero retain memory between sessions?**
Use **Settings → Backup & Restore** and avoid mapping the entire `/a0` directory. See [How to update Agent Zero](../setup/installation.md#how-to-update-agent-zero).

**8. My browser agent fails or says Playwright is missing. What now?**
The built-in Browser Agent is a plugin that uses the Main Model from `_model_config`. **Docker:** the Chromium headless shell is shipped preinstalled (typically under `/a0/tmp/playwright`). **Local development:** if the binary is missing, `ensure_playwright_binary()` in `plugins/_browser_agent/helpers/playwright.py` runs `playwright install chromium --only-shell` into `tmp/playwright` on first Browser Agent use (you may see UI notifications). To install ahead of time, run `PLAYWRIGHT_BROWSERS_PATH=tmp/playwright playwright install chromium --only-shell` after `pip install -r requirements.txt`. If you prefer an external browser stack, use MCP alternatives such as Browser OS, Chrome DevTools, or Playwright MCP. See [MCP Setup](mcp-setup.md).

**9. My secrets disappeared after a backup restore.**
Secrets are stored in `/a0/usr/secrets.env` and are not always included in backup archives. Copy them manually.

**10. Where can I find more documentation or tutorials?**
- Join the Agent Zero [Skool](https://www.skool.com/agent-zero) or [Discord](https://discord.gg/B8KZKNsPpj) community.

**11. How do I adjust API rate limits?**
Use the model rate limit fields in Settings (Main Model and Utility Model sections) to set request/input/output limits. The Browser Agent inherits the Main Model limits. These map to the model config limits (for example `limit_requests`, `limit_input`, `limit_output`).

**12. My `code_execution_tool` doesn't work, what's wrong?**
- Ensure Docker is installed and running.
- On macOS, grant Docker Desktop access to your project files.
- Verify that the Docker image is updated.

**13. Can Agent Zero interact with external APIs or services (e.g., WhatsApp)?**
Yes, by creating custom tools or using MCP servers. See [Extensions](../developer/extensions.md) and [MCP Setup](mcp-setup.md).

## Troubleshooting

**Installation**
- **Docker Issues:** If Docker containers fail to start, consult the Docker documentation and verify your Docker installation and configuration.  On macOS, ensure you've granted Docker access to your project files in Docker Desktop's settings as described in the [Installation guide](../setup/installation.md#4-install-docker-docker-desktop-application). Verify that the Docker image is updated.
- **Web UI not reachable:** Ensure at least one host port is mapped to container port `80`. If you used `0:80`, check the assigned port in Docker Desktop.

**Usage**

- **Terminal commands not executing:** Ensure the Docker container is running and properly configured.  Check SSH settings if applicable. Check if the Docker image is updated by removing it from Docker Desktop app, and subsequently pulling it again.

* **Error Messages:** Pay close attention to the error messages displayed in the Web UI or terminal.  They often provide valuable clues for diagnosing the issue. Refer to the specific error message in online searches or community forums for potential solutions.

* **Performance Issues:** If Agent Zero is slow or unresponsive, it might be due to resource limitations, network latency, or the complexity of your prompts and tasks, especially when using local models.
