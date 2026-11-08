## Environment
live in an official Python docker image based on Debian Trixie slim and use Debian packages
agent zero framework is python project in /a0 folder
linux fully root accessible via terminal

Python runtime:
- /usr/local/bin/python is the global environment for Agent Zero, WebUI/API handlers, plugins/hooks, and local task/user code.
- Install Python dependencies into the global environment unless the work explicitly targets an isolated sandbox image or the operating system.

WebUI JSON API:
- API handlers live at /api/<handler_name> and usually accept JSON POST requests.
- CSRF-protected requests need the same session cookies plus X-CSRF-Token.
- Get a token with GET /api/csrf_token from the same WebUI origin; include Origin or Referer when calling from terminal, keep the returned cookies, then reuse the token and cookie jar for later API calls.
before Agent Zero framework development or WebUI API calls, load a0-development and read relevant references
