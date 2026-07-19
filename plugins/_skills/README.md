# Skills

Skills is a built-in Agent Zero plugin that manages active skills across scope defaults and the current chat.

## What It Does

- pins default skills for the current plugin scope
- injects the effective active skills into prompt extras on every turn
- extends the same config screen with a current-chat mode so users can activate or hide skills live per conversation
- supports global and project scoped configurations without agent-profile variants
- links directly to the built-in Skills list
- links directly to the active project's Skills section when a project is active

## Why This Exists

Agent Zero already supports loading skills dynamically with `skills_tool`, and already has great built-in skill management surfaces. What it did not have was a lightweight way to make a few skills feel "always on" for a specific scope without modifying the core prompt system.

Skills fills that gap as a bundled built-in plugin.
The shared active-skill state and prompt-resolution logic live in `helpers/skills.py`, and this plugin focuses on configuration, UI, and prompt injection.

## Notes

- keep the active list short because every active skill is injected into prompt extras every turn
- the framework-wide cap is 20 active skills
- selected skills are stored in normalized `/a0/...` form so configs stay portable across development and Docker-style layouts
- scope defaults can be hidden or supplemented per chat without creating a new conversation
- if a configured skill is not visible in the current agent scope, it is skipped quietly instead of breaking the prompt build
