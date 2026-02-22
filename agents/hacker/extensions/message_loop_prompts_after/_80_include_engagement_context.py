"""
Engagement Context Injection Extension
Injects the current engagement status (target, scope summary, finding counts)
into every message loop prompt. Keeps the hacker agent aware of its engagement
state even deep in a conversation without requiring explicit memory recalls.
"""

import os
import json
from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import settings


SEVERITY_ORDER = ["critical", "high", "medium", "low", "informational"]


def _load_engagement_context() -> str:
    """Find the active engagement and return a one-line context summary."""
    workdir = settings.get_settings().get("workdir_path", "usr/workdir")
    if not os.path.isabs(workdir):
        workdir = os.path.join("/a0", workdir)
    engagements_dir = os.path.join(workdir, "engagements")

    if not os.path.isdir(engagements_dir):
        return ""

    # Find most recently touched engagement
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
        return ""

    eng_dir = os.path.join(engagements_dir, best_target)

    # Scope entry count
    scope_path = os.path.join(eng_dir, "scope.txt")
    scope_count = 0
    scope_preview = ""
    if os.path.exists(scope_path):
        with open(scope_path) as f:
            entries = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            scope_count = len(entries)
            scope_preview = ", ".join(entries[:3])
            if len(entries) > 3:
                scope_preview += f" (+{len(entries) - 3} more)"

    # Finding counts
    findings_path = os.path.join(eng_dir, "findings.json")
    counts = {s: 0 for s in SEVERITY_ORDER}
    if os.path.exists(findings_path):
        try:
            with open(findings_path) as f:
                findings = json.load(f)
            for finding in findings:
                sev = finding.get("severity", "low")
                counts[sev] = counts.get(sev, 0) + 1
        except (json.JSONDecodeError, OSError):
            pass

    total_findings = sum(counts.values())
    finding_summary = " | ".join(
        f"{counts[s]} {s.title()}" for s in SEVERITY_ORDER if counts[s] > 0
    ) or "No findings yet"

    return (
        f"## Current Engagement\n"
        f"**Target:** {best_target} | "
        f"**Scope:** {scope_count} entries ({scope_preview}) | "
        f"**Findings:** {total_findings} total — {finding_summary}\n"
        f"**Workspace:** {eng_dir}\n"
    )


class IncludeEngagementContext(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        context = _load_engagement_context()
        if context:
            loop_data.extras_temporary["engagement_context"] = context
