# Code Execution

Run terminal commands and execute Python or Node.js code through Agent Zero using persistent shell sessions.

## What It Does

This plugin provides the code execution tool used by agents for development tasks. It supports:

- **Terminal commands** in interactive shell sessions
- **Python execution** through `ipython -c`
- **Node.js execution** through `node /exe/node_eval.js`
- **Persistent sessions** keyed by destination and session number
- **Session reset and output retrieval**
- **Execution destinations** for the default sandbox, a named sandbox, the Agent Zero machine (`local`), or an authenticated Connector (`host`)

## Main Behavior

- **Persistent shells**
  - Maintains per-session shell state in agent data so subsequent calls can reuse the same terminal session.
  - Groups multi-line terminal input in the current shell so only the final prompt marks the command complete.
- **Multiple runtimes**
  - Dispatches requests based on `runtime`: `terminal`, `python`, `nodejs`, `output`, or `reset`.
- **Streaming output**
  - Continuously reads shell output, updates the current log item, and detects progress while commands are running.
  - Detects shell exit even when a command ends the shell before it prints a final prompt.
- **Long-running work**
  - Keeps normal command execution responsive while giving the `output` runtime longer polling windows for builds, installs, servers, tests, and training jobs.
- **Safety around running sessions**
  - Tracks whether a shell is currently busy and can prevent overlapping commands unless explicitly allowed.

## Key Files

- **Tool**
  - `tools/code_execution_tool.py` contains runtime dispatch, session lifecycle, and streaming output logic.
- **Helpers**
  - `helpers/shell_local.py` provides the local interactive shell implementation.
- **Configuration**
  - `default_config.yaml` defines execution, prompt, and timeout settings.
- **Prompts**
  - `prompts/` contains the response templates shown to the agent.

## Configuration Scope

- **Settings section**: `agent`
- **Per-project config**: `true`
- **Per-agent config**: `true`
- **Always enabled**: `false`

## Plugin Metadata

- **Name**: `_code_execution`
- **Title**: `Code Execution`
- **Description**: Run terminal, Python, and Node.js commands in a sandbox, on the Agent Zero machine, or on a connected host.
