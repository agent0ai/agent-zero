## Environment
live in kali linux docker container use debian kali packages
agent zero framework is python project in /a0 folder
linux fully root accessible via terminal

Python runtimes:
- /opt/venv/bin/python: task code and task dependencies
- /opt/venv-a0/bin/python: Agent Zero framework, backend, plugins/hooks and import checks
do not use one runtime as proof for the other
before Agent Zero framework development or WebUI API calls, load a0-development and read relevant references
