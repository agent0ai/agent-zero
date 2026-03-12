WARNING: Your response could not be parsed as a valid JSON tool call (attempt {{attempt}}/{{max_attempts}}).

You MUST respond with a single, raw JSON object — no markdown, no code fences, no XML. Example:

{"thoughts": ["your reasoning"], "headline": "Short summary", "tool_name": "response", "tool_args": {"text": "your message"}}

If you want to reply to the user, use tool_name "response" with tool_args.text containing your message.