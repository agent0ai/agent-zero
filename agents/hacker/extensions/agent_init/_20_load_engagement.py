"""
Load Engagement Extension
Runs once when the hacker agent is initialized.
Looks for an active engagement workspace and injects context into the agent's
initial prompt so it starts each session aware of the current engagement state.
"""

import os
import json
from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import settings, log


def _get_engagement_summary(eng_dir: str, target: str) -> str:
    """Build a brief engagement status summary string."""
    scope_path = os.path.join(eng_dir, "scope.txt")
    findings_path = os.path.join(eng_dir, "findings.json")
    roe_path = os.path.join(eng_dir, "roe.txt")

    scope_entries = []
    if os.path.exists(scope_path):
        with open(scope_path) as f:
            scope_entries = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    findings = []
    if os.path.exists(findings_path):
        with open(findings_path) as f:
            findings = json.load(f)

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
    for finding in findings:
        sev = finding.get("severity", "low")
        counts[sev] = counts.get(sev, 0) + 1

    roe_preview = ""
    if os.path.exists(roe_path):
        with open(roe_path) as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            roe_preview = "; ".join(lines[:3])

    summary_parts = [
        f"ACTIVE ENGAGEMENT: {target}",
        f"Workspace: {eng_dir}",
        f"Scope ({len(scope_entries)} entries): {', '.join(scope_entries[:5])}{'...' if len(scope_entries) > 5 else ''}",
        f"Findings: {counts['critical']} Critical | {counts['high']} High | {counts['medium']} Medium | {counts['low']} Low | {counts['informational']} Info",
    ]
    if roe_preview:
        summary_parts.append(f"RoE: {roe_preview}")

    return "\n".join(summary_parts)


class LoadEngagement(Extension):
    """
    On hacker agent init: scan engagement workspaces for an active engagement
    and inject a brief context summary into the agent's initial message.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        workdir = settings.get_settings().get("workdir_path", "usr/workdir")
        if not os.path.isabs(workdir):
            workdir = os.path.join("/a0", workdir)
        engagements_dir = os.path.join(workdir, "engagements")

        if not os.path.isdir(engagements_dir):
            return

        # Find the most recently accessed engagement
        best_target = ""
        best_mtime = 0
        for name in os.listdir(engagements_dir):
            meta_path = os.path.join(engagements_dir, name, "engagement.json")
            if os.path.exists(meta_path):
                try:
                    mtime = os.path.getmtime(meta_path)
                    if mtime > best_mtime:
                        best_mtime = mtime
                        best_target = name
                except OSError:
                    pass

        if not best_target:
            return

        eng_dir = os.path.join(engagements_dir, best_target)
        try:
            summary = _get_engagement_summary(eng_dir, best_target)
        except Exception:
            return

        self.agent.context.log.log(
            type="info",
            heading="Engagement Context Loaded",
            content=summary,
        )

        # Inject into extras so it appears in the initial system prompt context
        loop_data.extras_persistent["engagement_context"] = (
            f"\n## Active Engagement\n{summary}\n"
        )
