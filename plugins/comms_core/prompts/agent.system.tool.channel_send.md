## tool: channel_send

Send a message to any connected communication channel (Telegram, Slack, Discord, etc.).

**Arguments:**
- `platform` (required): The platform name - "telegram", "slack", "discord".
- `chat_id` (required): The platform-specific chat/channel ID to send to.
- `message` (required): The message text to send.

**Example:**
~~~json
{
    "tool_name": "channel_send",
    "tool_args": {
        "platform": "telegram",
        "chat_id": "123456789",
        "message": "Your task has been completed successfully."
    }
}
~~~

Use this tool when you need to proactively send a message to a user on a specific communication platform.
Normal conversation responses are handled automatically by the bridge.
