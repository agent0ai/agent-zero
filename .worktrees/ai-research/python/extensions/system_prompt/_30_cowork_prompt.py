from typing import Any

from python.helpers.extension import Extension
from python.helpers.settings import get_settings


class CoworkPrompt(Extension):
    async def execute(self, system_prompt: list[str] | None = None, **kwargs: Any):
        if system_prompt is None:
            system_prompt = []
        settings = get_settings()
        if not settings.get("cowork_enabled"):
            return

        allowed_paths = settings.get("cowork_allowed_paths", [])
        require_approvals = bool(settings.get("cowork_require_approvals", True))

        lines = ["Cowork mode is enabled."]
        if allowed_paths:
            lines.append("Allowed folders:")
            lines.extend([f"- {path}" for path in allowed_paths])
        if require_approvals:
            lines.append("Impactful actions require user approval. Ask before proceeding.")

        system_prompt.append("\n".join(lines))
