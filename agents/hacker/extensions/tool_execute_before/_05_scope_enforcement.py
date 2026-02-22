"""
Scope Enforcement Extension
Runs before every tool call for the hacker agent.
Extracts any IP/domain/URL from tool arguments and verifies it is within
the active engagement scope. Blocks and warns if out of scope.
"""

import os
import re
from python.helpers.extension import Extension
from python.tools.scope_check import is_in_scope, load_scope_entries, _engagement_dir
from agent import LoopData
from python.helpers import settings, log


# Tools that involve network targets and need scope checking
NETWORK_TOOLS = {
    "code_execution_tool",
    "browser_agent",
    "search_engine",
}

# Regex to extract IPs and domains from arbitrary strings
IP_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
DOMAIN_PATTERN = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
)
URL_PATTERN = re.compile(
    r"https?://([^\s/\"']+)"
)

# These hostnames are always allowed (internal container, localhost)
ALWAYS_ALLOWED = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _extract_targets(args: dict) -> list[str]:
    """Extract all potential network targets from tool arguments."""
    targets = set()
    text = str(args)

    for match in IP_PATTERN.finditer(text):
        targets.add(match.group())

    for match in URL_PATTERN.finditer(text):
        host = match.group(1).split(":")[0]  # strip port
        targets.add(host)

    for match in DOMAIN_PATTERN.finditer(text):
        candidate = match.group()
        # Skip obvious file extensions and single-segment names
        if "." in candidate and not candidate.endswith((".py", ".txt", ".json", ".md", ".sh")):
            targets.add(candidate)

    return [t for t in targets if t not in ALWAYS_ALLOWED]


def _find_active_engagement() -> tuple[str, list[str]]:
    """
    Look for an active engagement workspace and return (target_name, scope_entries).
    Returns ("", []) if none found.
    """
    workdir = settings.get_settings().get("workdir_path", "usr/workdir")
    if not os.path.isabs(workdir):
        workdir = os.path.join("/a0", workdir)
    engagements_dir = os.path.join(workdir, "engagements")

    if not os.path.isdir(engagements_dir):
        return "", []

    # Find the most recently accessed engagement
    best_target = ""
    best_mtime = 0
    for name in os.listdir(engagements_dir):
        meta_path = os.path.join(engagements_dir, name, "engagement.json")
        scope_path = os.path.join(engagements_dir, name, "scope.txt")
        if os.path.exists(meta_path) and os.path.exists(scope_path):
            mtime = os.path.getmtime(meta_path)
            if mtime > best_mtime:
                best_mtime = mtime
                best_target = name

    if not best_target:
        return "", []

    scope_path = os.path.join(engagements_dir, best_target, "scope.txt")
    entries = load_scope_entries(scope_path)
    return best_target, entries


class ScopeEnforcement(Extension):
    """
    Pre-tool-execution scope check for the hacker agent.
    Warns if a tool call targets an out-of-scope host.
    Does NOT hard-block (the agent may have legitimate reasons, e.g. researching
    a vulnerability on a public CVE database). Instead, logs a clear warning
    so the agent can make an informed decision.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        tool_name = kwargs.get("tool_name", "")
        tool_args = kwargs.get("tool_args", {})

        if not tool_args or not isinstance(tool_args, dict):
            return

        # Only check tools that involve network targets
        if tool_name not in NETWORK_TOOLS:
            return

        targets = _extract_targets(tool_args)
        if not targets:
            return

        engagement_target, scope_entries = _find_active_engagement()
        if not scope_entries:
            # No scope defined — warn but allow (engagement may not be initialized)
            self.agent.context.log.log(
                type="warning",
                heading="Scope Enforcement: No scope defined",
                content=(
                    f"Tool '{tool_name}' targets {targets} but no engagement scope is loaded. "
                    "Run engagement_init to define scope before active testing."
                ),
            )
            return

        out_of_scope = []
        for t in targets:
            in_scope, matched = is_in_scope(t, scope_entries)
            if not in_scope:
                out_of_scope.append(t)

        if out_of_scope:
            warning = (
                f"SCOPE WARNING: The following targets appear to be outside the engagement scope "
                f"for '{engagement_target}': {out_of_scope}\n"
                f"Defined scope: {scope_entries}\n"
                f"Verify this is intentional before proceeding. If this target should be in scope, "
                f"add it to scope.txt or update the engagement."
            )
            self.agent.context.log.log(
                type="warning",
                heading="Scope Enforcement: Out-of-scope target detected",
                content=warning,
            )
            # Append warning to agent history so it sees it before acting
            loop_data.extras_temporary["scope_warning"] = warning
