# Telegram Send Tool

Send a message to a Telegram chat via bot API.

## Usage

```
{{telegram_send(
  text="Digest content...",
  chat_id="123456789",
  parse_mode="Markdown"
)}}
```

If `chat_id` or `bot_token` are omitted, the tool uses `TELEGRAM_CHAT_ID` and `TELEGRAM_BOT_TOKEN` from the environment.
