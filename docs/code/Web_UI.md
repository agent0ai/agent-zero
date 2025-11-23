---
tags: [component, ui, frontend]
---

# Web UI

The interface for interacting with Agent Zero.

## Stack

- **HTML/CSS/JS**: Pure vanilla implementation in `webui/`.
- **Backend**: Python server (likely Flask or similar in `run_ui.py` or `agent.py` extensions).

## Components

- **Chat**: Main interface.
- **Settings**: Configuration.
- **Log View**: Real-time execution logs.

## Relations

- Communicates with [[Agent Core]] via API/WebSockets.

