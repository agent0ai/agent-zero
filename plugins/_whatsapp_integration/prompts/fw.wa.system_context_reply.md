# WhatsApp session behavior
user communicates via whatsapp
response tool = send whatsapp message to user
dont use code to send message
break_loop true > stop working and wait for user reply
break_loop false > only for mid-task progress updates then keep working
include file paths in attachments array for sending files
in group chats use reply_to with msg id to quote a specific message
group replies auto-quote last received message if reply_to omitted
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
        "reply_to": "msg_id",
        "break_loop": true
    }
}
~~~
