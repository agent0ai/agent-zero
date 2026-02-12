from python.helpers.extension import Extension
from python.helpers import codex_exec


class CodexHealthBanner(Extension):
    """Show latest Codex fallback/failure warning."""

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        warning = codex_exec.get_latest_warning()
        if not warning:
            return

        role = str(warning.get("role", "chat")).strip() or "chat"
        message = str(warning.get("message", "")).strip() or "Codex backend warning."
        fallback_provider = str(warning.get("fallback_provider", "")).strip()
        fallback_model = str(warning.get("fallback_model", "")).strip()
        diagnostic = str(warning.get("diagnostic", "")).strip()

        fallback_part = ""
        if fallback_provider:
            fallback_part = f"Fallback used: <code>{fallback_provider}</code>"
            if fallback_model:
                fallback_part += f" / <code>{fallback_model}</code>"
            fallback_part += ".<br>"

        diagnostic_part = ""
        if diagnostic:
            diagnostic_part = f"<details><summary>Diagnostic</summary><pre>{diagnostic}</pre></details>"

        banners.append(
            {
                "id": "codex-health-warning",
                "type": "warning",
                "priority": 95,
                "title": f"Codex warning ({role})",
                "html": (
                    f"{message}<br>"
                    f"{fallback_part}"
                    "Open <a href=\"#\" onclick=\"document.getElementById('settings').click(); return false;\">Settings</a> "
                    "to verify Codex login/model configuration.<br>"
                    f"{diagnostic_part}"
                ),
                "dismissible": True,
                "source": "backend",
            }
        )
