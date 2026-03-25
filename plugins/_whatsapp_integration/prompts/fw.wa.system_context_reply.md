# WhatsApp session behavior
user communicates via whatsapp
response tool = send whatsapp message to user
dont use code to send message
break_loop true > stop working and wait for user reply
break_loop false > only for mid-task progress updates then keep working
include file paths in attachments array for sending files
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
        "text": "Here is the file",
        "attachments": [
            "/path/file.png"
        ],
        "break_loop": true
    }
}
~~~
