## tool: telegram_send

Send a message directly to a Telegram chat. Use this when you need to
proactively notify or respond to a user on Telegram.

**Arguments:**
- `chat_id` (required): The Telegram chat ID to send to.
- `message` (required): The message text.

**Example:**
~~~json
{
    "tool_name": "telegram_send",
    "tool_args": {
        "chat_id": "123456789",
        "message": "Your report is ready. I've found 3 issues that need attention."
    }
}
~~~

Only use this tool when you explicitly need to send a message to Telegram.
Normal conversation responses are handled automatically by the bridge.
