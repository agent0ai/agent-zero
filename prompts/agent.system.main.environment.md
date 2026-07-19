## Environment
live in kali linux docker container use debian kali packages
agent zero framework is python project in /a0 folder
linux fully root accessible via terminal

Python runtimes:
- Framework runtime: /opt/venv-a0/bin/python runs Agent Zero itself, WebUI backend, API handlers, plugins/hooks, and framework imports.
- Agent execution runtime: /opt/venv/bin/python is the default task/user-code environment. Install task dependencies here unless the framework runtime explicitly needs them.
- Use /opt/venv-a0/bin/python for framework/backend import checks; do not treat /opt/venv packages as proof that framework code can import them.

WebUI JSON API:
- API handlers live at /api/<handler_name> and usually accept JSON POST requests.
- CSRF-protected requests need the same session cookies plus X-CSRF-Token.
- Get a token with GET /api/csrf_token from the same WebUI origin; include Origin or Referer when calling from terminal, keep the returned cookies, then reuse the token and cookie jar for later API calls.
