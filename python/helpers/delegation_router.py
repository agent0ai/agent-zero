"""Auto-delegation routing based on agent manifest rules.

Inspects the current agent's ``behavior.auto_delegate`` mapping and
matches incoming task descriptions against declared task categories
to suggest which profile should handle the work.
"""

from __future__ import annotations

import re
from typing import Any

from python.helpers.agent_composer import AgentComposer, get_composer

# ---------------------------------------------------------------------------
# Keyword patterns for built-in task categories
# ---------------------------------------------------------------------------

_CATEGORY_PATTERNS: dict[str, re.Pattern[str]] = {
    "research_tasks": re.compile(
        r"\b(research|investigate|find\s+(?:out|info)|look\s+up|analyze\s+data|"
        r"survey|literature|sources|evidence|study)\b",
        re.IGNORECASE,
    ),
    "content_tasks": re.compile(
        r"\b(write|draft|compose|blog|article|newsletter|copy|"
        r"editorial|storytelling|ghost[\s-]?writ|content\s+creat)\b",
        re.IGNORECASE,
    ),
    "security_tasks": re.compile(
        r"\b(security|pentest|penetration|vulnerability|exploit|" r"audit\s+security|hack|cve|owasp)\b",
        re.IGNORECASE,
    ),
    "devops_tasks": re.compile(
        r"\b(deploy|ci[\s/]?cd|docker|kubernetes|k8s|infrastructure|"
        r"terraform|ansible|monitoring|uptime|pipeline)\b",
        re.IGNORECASE,
    ),
    "development_tasks": re.compile(
        r"\b(implement|code|program|develop|refactor|debug|"
        r"build\s+(?:a|the)\s+\w+|fix\s+(?:the\s+)?bug|pull\s+request|"
        r"unit\s+test|integration\s+test)\b",
        re.IGNORECASE,
    ),
    "operations_tasks": re.compile(
        r"\b(schedule|automate|integrate|cron|webhook|" r"orchestrat|workflow\s+(?:run|trigger))\b",
        re.IGNORECASE,
    ),
}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


class DelegationRouter:
    """Decides whether a task should be delegated to another profile."""

    def __init__(self, composer: AgentComposer | None = None) -> None:
        self.composer = composer or get_composer()

    def get_delegation_rules(self, profile: str) -> dict[str, str]:
        """Return the ``auto_delegate`` mapping for *profile*.

        Returns an empty dict when the profile has no manifest or no
        delegation rules.
        """
        manifest = self.composer.load_manifest(profile)
        behavior: dict[str, Any] = manifest.get("behavior", {})
        return dict(behavior.get("auto_delegate", {}) or {})

    async def should_delegate(self, task: str, current_profile: str) -> str | None:
        """Return the target profile name if *task* should be delegated,
        or ``None`` to keep it on the current profile.

        Matching is done by scanning the task text for keywords that
        correspond to each declared delegation category.
        """
        rules = self.get_delegation_rules(current_profile)
        if not rules:
            return None

        # Score each category by how many keyword hits it has
        best_target: str | None = None
        best_score: int = 0

        for category, target_profile in rules.items():
            pattern = _CATEGORY_PATTERNS.get(category)
            if pattern is None:
                continue
            hits = len(pattern.findall(task))
            if hits > best_score:
                best_score = hits
                best_target = target_profile

        # Avoid delegating to self
        if best_target == current_profile:
            return None

        return best_target


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_router: DelegationRouter | None = None


def get_router() -> DelegationRouter:
    """Return (and lazily create) the singleton :class:`DelegationRouter`."""
    global _default_router
    if _default_router is None:
        _default_router = DelegationRouter()
    return _default_router
