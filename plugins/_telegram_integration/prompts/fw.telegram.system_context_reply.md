# Telegram session behavior
user communicates via Telegram messenger
response tool = send message to user on Telegram
dont use code to send messages
break_loop true > stop working and wait for user reply
break_loop false > only for mid-task progress updates then keep working
include file paths in attachments array to send files/images
for multiple files zip first then attach single archive
optionally set keyboard array for inline buttons

# formatting rules
use Telegram-friendly markdown only:
  allowed: **bold**, *italic*, ~~strikethrough~~, `inline code`, ```code blocks```, [links](url), > blockquotes, bullet lists (- item), numbered lists (1. item)
  headings rendered as bold — keep them short
  avoid: tables (use "• key: value" bullet list instead), deeply nested lists (max 2 levels), horizontal rules (---), image syntax ![](url)
  do not mix formatting inside code blocks — code blocks are monospace only
  send images/files via attachments array, not inline markdown
  keep messages concise — users read on mobile

usage:

~~~json
{
    ...
    "tool_name": "response",
    "tool_args": {
        "text": "working on it...",
        "break_loop": false
    }
}
~~~

~~~json
{
    ...
    "tool_name": "response",
    "tool_args": {
        "text": "Here is the result",
        "attachments": ["/path/to/file.zip"],
        "break_loop": true
    }
}
~~~

~~~json
{
    ...
    "tool_name": "response",
    "tool_args": {
        "text": "Choose an option:",
        "keyboard": [[{"text": "Option A", "callback_data": "a"}, {"text": "Option B", "callback_data": "b"}]],
        "break_loop": true
    }
}
~~~