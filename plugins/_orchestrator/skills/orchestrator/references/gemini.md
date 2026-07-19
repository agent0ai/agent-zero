# Gemini CLI

Use Gemini CLI for headless Google Gemini coding tasks. Always pass `-p`; bare `gemini` opens the interactive TUI.

## Install And Probe

Check first:

```bash
command -v gemini
```

If missing, install it as one command and wait or poll that same terminal session until it completes. Do not append version, help, or smoke commands to the install call:

```bash
npm install -g @google/gemini-cli --no-progress
```

Then probe it:

```bash
command -v gemini
gemini --version
gemini --help
```

## Smoke Prompt

```bash
cd "$WORKDIR"
gemini -p "Respond exactly: TERMINAL_AGENT_SMOKE_OK" --output-format json --approval-mode=yolo --skip-trust
```

## Login

Headless mode uses existing cached Google credentials, a Gemini API key, or Vertex AI credentials. Do not start bare `gemini` through Agent Zero for login; it opens a TUI. For local browser sign-in, ask the user to run `gemini` in their own terminal, select **Sign in with Google**, finish in the browser, and then retry the smoke prompt.

For container automation, prefer `GEMINI_API_KEY`. Ask the user to add it through **Settings > External Services > Secrets Management**. If `GEMINI_API_KEY` is listed in Agent Zero's available secrets, do not source `/a0/usr/.env`; pass the exact secret alias only to the Gemini process:

```bash
GEMINI_API_KEY='§§secret(GEMINI_API_KEY)' gemini -p "Respond exactly: TERMINAL_AGENT_SMOKE_OK" --output-format json --approval-mode=yolo --skip-trust
```

Vertex AI may instead use `GOOGLE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, or cached Application Default Credentials. It also requires `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`. Never ask the user to paste keys or service-account JSON into chat.

## Real Task

```bash
cd "$WORKDIR"
gemini -p "$TASK" --output-format json --approval-mode=yolo --skip-trust
```

Add `-m "$MODEL"` only when the user or settings provide a model override. Use `--approval-mode=plan` instead of `yolo` when the user explicitly asks for read-only analysis.

When using the saved Gemini secret for a real task, prefix the real-task command with `GEMINI_API_KEY='§§secret(GEMINI_API_KEY)'` in the same way. Never print or probe the expanded value.
