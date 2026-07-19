from __future__ import annotations

from plugins._desktop.helpers import desktop_state


def build_context(context_id: str = "") -> str:
    if not desktop_state.session_manifest_exists():
        return ""
    try:
        return desktop_state.compact_prompt_context(
            desktop_state.collect_state(include_screenshot=False, context_id=context_id),
        )
    except Exception as exc:
        return (
            "[DESKTOP STATE]\n"
            f"- unavailable={exc}\n"
            "- next=Open the Desktop surface manually, then run plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh observe --json."
        )
