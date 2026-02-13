### input:
use keyboard arg for terminal program input
use session arg for terminal session number
answer dialogues enter passwords etc
not for browser
control signals:
- <ctrl+c> interrupt 
- <ctrl+d> EOF
usage:

~~~json
{
    "thoughts": [
        "The program asks for Y/N...",
    ],
    "headline": "...",
    "tool_name": "input",
    "tool_args": {
        "keyboard": "Y",
        "session": 0
    }
}
~~~

~~~json
{
    "thoughts": [
        "The program is hanging..."
    ],
    "headline": "...",
    "tool_name": "input",
    "tool_args": {
        "keyboard": "<ctrl+c>",
        "session": 0
    }
}
~~~
