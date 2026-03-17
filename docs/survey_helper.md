# Survey Helper (Human-in-the-loop)

This feature helps you **review** a survey page, **extract** form questions, and optionally **generate suggested answers** from a **user-owned profile**.

It is intentionally designed to be human-in-the-loop:
- It **does not** automatically submit surveys.
- It **does not** fabricate personal details; if your profile doesn’t contain needed info, suggestions should return **UNKNOWN**.

## How it works

- **1) Load a URL**
  - The app renders the URL with Playwright (Chromium) and captures:
    - page HTML
    - page title + final URL (after redirects)
    - a screenshot preview

- **2) Extract questions**
  - The HTML is parsed and likely form controls are detected:
    - inputs (including grouped radio/checkbox questions)
    - selects
    - textareas
  - Each question includes a best-effort label + options (when available).

- **3) Suggest answers (optional)**
  - If you have **Ollama** running locally, the tool can generate answer suggestions using your saved profile.
  - Suggestions are only a draft for you to copy/paste and review.

## Profile storage

- Stored at `memory/survey_profile.json`
- You can edit it in the GUI under **“Profile (editable JSON)”**.

## Ways to use it

### A) Desktop GUI (recommended)

Run:

```bash
bash scripts/start_survey_helper.sh
```

This script sets up a local `.venv/` and installs only the **minimal** packages needed for the Survey Helper (BeautifulSoup + Playwright), then installs Playwright’s Chromium browser.

If the script reports `tkinter` is missing, install it:
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y python3-tk`

Then in the window:
- Paste URL → **Load (render + screenshot)**
- **Extract questions**
- (Optional) start Ollama and click **Suggest answers**

### A2) CLI mode (no GUI)

If you don’t have a GUI environment (or don’t want one), run:

```bash
SURVEY_HELPER_MODE=cli bash scripts/start_survey_helper.sh "https://example.com/survey"
```

Or directly:

```bash
python3 run_survey_helper_cli.py "https://example.com/survey" --json
```

### B) Inside Agent Zero (tool mode)

If you are running the Agent Zero Web UI, you can ask the agent to use `survey_helper`.

Example request:
- “Use `survey_helper` on this URL and show me the extracted fields. Don’t submit anything.”

The tool returns JSON with `fields[]`, and optionally `suggestions` if enabled.

Note: installing/running the full Agent Zero stack may be easiest via the project’s Docker workflow (see `README.md` / `docs/installation.md`).

