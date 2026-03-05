## Cursor Cloud specific instructions

### Project overview

Agent Zero is a Python-based AI agent framework with a Flask web UI. See `README.md` and `docs/` for full documentation.

### Running the application

- Activate the venv: `source /workspace/.venv/bin/activate`
- Start the dev server: `python run_ui.py` (serves on `http://localhost:5000` by default; configurable via `WEB_UI_PORT` in `.env`)
- The web UI is a static frontend served by Flask from `webui/`.

### Gotchas

- `openai-whisper` requires `setuptools<81` (older versions with `pkg_resources`). When installing dependencies, install whisper first with `--no-build-isolation`, then install the rest: `pip install openai-whisper==20240930 --no-build-isolation && pip install -r requirements.txt`
- `flask-socketio` is required at runtime but is not listed in `requirements.txt`. It is installed as an extra dependency.
- The app requires at least one LLM API key (e.g. `API_KEY_OPENAI`) configured in `.env` or via the Settings UI for the agent to function. The web UI itself starts without API keys.
- No formal test suite or linting config exists in the repo. `ruff` is available as a transitive dependency and can be used for basic linting: `ruff check .`
- Settings are persisted in `tmp/settings.json`; API keys are stored in `.env`.
- The two satellite microservices under `services/` (autonomous_listing, collab_doc) are optional and not required for the core agent to function.
