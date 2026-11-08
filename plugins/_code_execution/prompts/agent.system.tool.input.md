### input:
send keyboard input to an interactive terminal program
use keyboard arg for terminal program input
use session arg for terminal session number
use the same destination as the terminal session; default is `default`
answer dialogues enter passwords etc
not for browser
usage:
~~~json
{
    "thoughts": [
        "The program asks for Y/N..."
    ],
    "headline": "Responding to terminal program prompt",
    "tool_name": "input",
    "tool_args": {
        "keyboard": "Y",
        "session": 0,
        "destination": "default"
    }
}
~~~
