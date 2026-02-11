### code_execution_tool

execute terminal commands python nodejs code for computation or software tasks
place code in "code" arg; escape carefully and indent properly
select "runtime" arg: "terminal" "python" "nodejs" "output"
select "session" number, 0 default, others for multitasking
if code runs long, use runtime "output" to wait
use argument reset true on next call to kill previous process when stuck default false
use "pip" "npm" "apt-get" in "terminal" to install package
to output, use print() or console.log()
if tool outputs error, adjust code before retrying;
important: check code for placeholders or demo data; replace with real variables; don't reuse snippets
don't use with other tools except thoughts; wait for response before using others
check dependencies before running code
output may end with [SYSTEM: ...] information comming from framework, not terminal
usage:

1 execute terminal command

~~~json
{
    "thoughts": [
        "Need to do...",
        "Need to install...",
    ],
    "headline": "Installing zip package via terminal",
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "terminal",
        "session": 0,
        "reset": false,
        "code": "apt-get install zip",
    }
}
~~~

2 execute python code

~~~json
{
    "thoughts": [
        "Need to do...",
        "I can use...",
        "Then I can...",
    ],
    "headline": "Executing Python code to check current directory",
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "python",
        "session": 0,
        "reset": false,
        "code": "import os\nprint(os.getcwd())",
    }
}
~~~

3 execute nodejs code

~~~json
{
    "thoughts": [
        "Need to do...",
        "I can use...",
        "Then I can...",
    ],
    "headline": "Executing Javascript code to check current directory",
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "nodejs",
        "session": 0,
        "reset": false,
        "code": "console.log(process.cwd());",
    }
}
~~~

4 wait for output with long-running scripts

~~~json
{
    "thoughts": [
        "Waiting for program to finish...",
    ],
    "headline": "Waiting for long-running program to complete",
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "output",
        "session": 0,
    }
}
~~~
