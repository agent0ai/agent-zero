### code_execution_tool
run terminal, python, or nodejs commands
args:
- `runtime`: `terminal`, `python`, `nodejs`, or `output`
- `code`: command or script code
- `session`: terminal session id; default `0`
- `reset`: kill a session before running; `true` or `false`
rules:
- place the command or script in `code`
- use `runtime=output` to poll running work
- use `input` for interactive terminal prompts
- if a session is stuck, call again with the same `session` and `reset=true`
- check dependencies before running code
- replace placeholder or demo data with real values before execution
- use `print()` or `console.log()` when you need explicit output
- do not interleave other tools while waiting
- treat trailing framework `[SYSTEM: ...]` info as execution status, not command output; use it to decide whether to wait, reset, rerun, or continue
- probe cwd files tools and dependencies before expensive commands
- split long work into small commands: inspect, prepare, run, verify
- for builds installs servers training and long tests, redirect logs and poll with `runtime=output`
- after timeout or pause, inspect logs and processes before deciding wait reset or stop
- never claim success from timeout partial output or a still-running command
- stop stale background processes you started before final response
- when exact output matters, verify file path line count bytes and content with commands
examples:
1 terminal command
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

2 python snippet
~~~json
{
  "thoughts": ["A short Python check is faster than using the shell."],
  "headline": "Running Python snippet",
  "tool_name": "code_execution_tool",
  "tool_args": {
    "runtime": "python",
    "session": 0,
    "reset": false,
    "code": "import os\nprint(os.getcwd())"
  }
}
~~~

3 wait for running output
~~~json
{
  "thoughts": ["The previous command is still running, so I should poll for output."],
  "headline": "Waiting for command output",
  "tool_name": "code_execution_tool",
  "tool_args": {
    "runtime": "output",
    "session": 0
  }
}
~~~
