"""
Auto-Save Findings Extension
Runs at the end of each monologue for the hacker agent.
Scans the assistant's most recent output for patterns that suggest a new
vulnerability was discovered (CVE IDs, version + "vulnerable", exploit success).
Logs a reminder if a finding looks like it should be recorded but wasn't.
"""

import re
from python.helpers.extension import Extension
from agent import LoopData


# Patterns that suggest a new finding was identified in the response
FINDING_SIGNALS = [
    re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE),
    re.compile(r"\bvulnerable\b", re.IGNORECASE),
    re.compile(r"\bexploited?\b", re.IGNORECASE),
    re.compile(r"\bremote code execution\b", re.IGNORECASE),
    re.compile(r"\bprivilege escalation\b", re.IGNORECASE),
    re.compile(r"\bsql injection\b", re.IGNORECASE),
    re.compile(r"\bcredentials?\s+found\b", re.IGNORECASE),
    re.compile(r"\bpassword\s+cracked\b", re.IGNORECASE),
    re.compile(r"\bshell\s+obtained\b", re.IGNORECASE),
    re.compile(r"\baccess\s+granted\b", re.IGNORECASE),
    re.compile(r"\buid=0\b", re.IGNORECASE),  # root shell proof
    re.compile(r"\bwhoami.*root\b", re.IGNORECASE),
]

# If agent already called findings_tracker in this monologue, skip
TRACKER_CALL_PATTERN = re.compile(r"findings_tracker", re.IGNORECASE)


class AutoSaveFindings(Extension):
    """
    Post-monologue reminder: if the response contains vulnerability indicators
    but findings_tracker was not called, nudge the agent to log the finding.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Get the last assistant message text
        if not self.agent.history:
            return

        # Look at last few messages for assistant output
        recent_text = ""
        for msg in reversed(self.agent.history[-5:]):
            if hasattr(msg, "output_text"):
                recent_text += msg.output_text()
            elif hasattr(msg, "content"):
                content = msg.content
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            recent_text += part.get("text", "")
                elif isinstance(content, str):
                    recent_text += content

        if not recent_text:
            return

        # If findings_tracker was already called, no need to remind
        if TRACKER_CALL_PATTERN.search(recent_text):
            return

        # Check for finding signals
        triggered = [p.pattern for p in FINDING_SIGNALS if p.search(recent_text)]
        if not triggered:
            return

        # Extract CVE IDs if present for a more specific reminder
        cves = re.findall(r"CVE-\d{4}-\d{4,}", recent_text, re.IGNORECASE)
        cve_note = f" (CVEs detected: {', '.join(set(cves))})" if cves else ""

        reminder = (
            f"\n---\n"
            f"**REMINDER:** This response contains vulnerability indicators{cve_note}. "
            f"If a new finding was confirmed, log it now with `findings_tracker` (action=add_finding) "
            f"before proceeding. Include: title, severity, cvss_score, host, port, service, description, "
            f"steps_to_reproduce, evidence path, remediation.\n"
            f"---"
        )

        # Inject as a temporary prompt addition so agent sees it next iteration
        existing = loop_data.extras_temporary.get("finding_reminder", "")
        loop_data.extras_temporary["finding_reminder"] = existing + reminder
