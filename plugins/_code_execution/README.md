# Code Execution

Run terminal commands and execute Python or Node.js code through Agent Zero using persistent shell sessions.

## What It Does

This plugin provides the code execution tool used by agents for development tasks. It supports:

- **Terminal commands** in interactive shell sessions
- **Python execution** through `ipython -c`
- **Node.js execution** through `node /exe/node_eval.js`
- **Persistent sessions** keyed by session number
- **Session reset and output retrieval**
- **Local or SSH-backed execution** depending on plugin configuration

## Main Behavior

- **Persistent shells**
  - Maintains per-session shell state in agent data so subsequent calls can reuse the same terminal session.
- **Multiple runtimes**
  - Dispatches requests based on `runtime`: `terminal`, `python`, `nodejs`, `output`, or `reset`.
- **Remote execution support**
  - Can open SSH interactive sessions instead of local shells when configured.
- **Streaming output**
  - Continuously reads shell output, updates the current log item, and detects progress while commands are running.
- **Safety around running sessions**
  - Tracks whether a shell is currently busy and can prevent overlapping commands unless explicitly allowed.

## Key Files

- **Tool**
  - `tools/code_execution_tool.py` contains runtime dispatch, session lifecycle, and streaming output logic.
- **Helpers**
  - `helpers/shell_local.py` provides the local interactive shell implementation.
  - `helpers/shell_ssh.py` provides the SSH-backed interactive shell implementation.
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
- **Description**: Code execution tool supporting terminal, Python, and Node.js runtimes via local TTY or SSH.
