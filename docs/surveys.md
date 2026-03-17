# Surveys automation (experimental)

This repo includes an experimental **survey-filling agent** designed to work with Agent Zero's built-in Playwright browser.

## What’s included

- `survey_fill` tool: opens a URL (or uses the currently open page), extracts form fields from the cleaned DOM, plans answers using the current **profile** (and optionally a **persona**), then submits/advances through pages.
- Local SQLite database: stores personas, profiles, and survey answers at `memory/<agent_memory_subdir>/survey_profiles.db`.
- Background profile refiner: runs in the background and periodically turns collected survey answers into structured profile updates.

## Demo (local HTML)

There is a local survey at `docs/res/survey_demo.html`.

If you run Agent Zero UI/API and want to test `survey_fill`, open it via a `file://` URL and run:

```json
{
  "tool_name": "survey_fill",
  "tool_args": {
    "url": "file:///a0/docs/res/survey_demo.html",
    "profile_id": "default",
    "max_pages": 3,
    "use_llm": true
  }
}
```

## Personas

Create a persona:

```json
{
  "tool_name": "persona_create",
  "tool_args": {
    "generate": true,
    "seed": "A 32-year-old software engineer in Berlin who prefers Android and avoids alcohol."
  }
}
```

Then pass `persona_id` into `survey_fill`.

By default, persona usage is **restricted to local URLs** unless you set `allow_persona=true`.

