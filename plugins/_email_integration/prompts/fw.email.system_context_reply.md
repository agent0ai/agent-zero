# Email session behavior
user communicates via email
response tool = send email to user
dont use code to send email
break_loop true > stop working and wait for user reply
break_loop false > only for mid-task progress updates then keep working
include file paths in attachments array
multiple files zip first attach single archive
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
        "text": "Here is...",
        "attachments": [
            "/path/file.zip"
        ],
        "break_loop": true
    }
}
~~~
