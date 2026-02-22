import os
import json
from datetime import datetime
from python.helpers.tool import Tool, Response
from python.helpers import settings


ENGAGEMENT_BASE = "engagements"


def resolve_engagement_dir(target: str) -> str:
    """Return absolute path to the engagement workspace for a given target name."""
    workdir = settings.get_settings().get("workdir_path", "usr/workdir")
    if not os.path.isabs(workdir):
        workdir = os.path.join("/a0", workdir)
    return os.path.join(workdir, ENGAGEMENT_BASE, target)


class EngagementInit(Tool):
    """
    Initialize or resume a penetration testing engagement workspace.

    Actions:
        init   — create directory structure, write scope and RoE, save to memory
        status — show current active engagement and workspace contents
        list   — list all existing engagements
    """

    async def execute(self, action="init", target="", scope="", roe="", **kwargs):
        action = action.lower().strip()

        if action == "list":
            return self._list_engagements()

        if action == "status":
            return self._status()

        # Default: init
        if not target:
            return Response(
                message="engagement_init requires a 'target' argument (e.g. target name or IP range).",
                break_loop=False,
            )

        eng_dir = resolve_engagement_dir(target)
        already_exists = os.path.isdir(eng_dir)

        # Create directory structure
        for subdir in ["loot", "loot/recon", "screenshots", "reports"]:
            os.makedirs(os.path.join(eng_dir, subdir), exist_ok=True)

        # Write scope.txt
        scope_path = os.path.join(eng_dir, "scope.txt")
        if scope or not os.path.exists(scope_path):
            with open(scope_path, "w") as f:
                f.write(scope if scope else "# Define scope — one entry per line.\n# Formats: IP, CIDR (10.0.0.0/24), domain (example.com), wildcard (*.example.com)\n")

        # Write roe.txt
        roe_path = os.path.join(eng_dir, "roe.txt")
        if roe or not os.path.exists(roe_path):
            with open(roe_path, "w") as f:
                f.write(roe if roe else "# Rules of Engagement\n# Define: allowed techniques, time windows, emergency contact, reporting requirements\n")

        # Initialize findings.json if it doesn't exist
        findings_path = os.path.join(eng_dir, "findings.json")
        if not os.path.exists(findings_path):
            with open(findings_path, "w") as f:
                json.dump([], f, indent=2)

        # Write engagement metadata
        meta_path = os.path.join(eng_dir, "engagement.json")
        if not os.path.exists(meta_path):
            meta = {
                "target": target,
                "created": datetime.utcnow().isoformat(),
                "status": "active",
            }
        else:
            with open(meta_path) as f:
                meta = json.load(f)
            meta["last_accessed"] = datetime.utcnow().isoformat()

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # Save engagement context to agent memory
        memory_entry = (
            f"ACTIVE ENGAGEMENT\n"
            f"Target: {target}\n"
            f"Workspace: {eng_dir}\n"
            f"Scope file: {scope_path}\n"
            f"Findings file: {findings_path}\n"
            f"Created: {meta.get('created', 'unknown')}"
        )
        from python.helpers.memory import Memory
        db = await Memory.get(self.agent)
        await db.insert_text(
            memory_entry,
            {"area": Memory.Area.MAIN.value, "type": "engagement_context", "target": target},
        )

        verb = "Resumed" if already_exists else "Initialized"
        return Response(
            message=(
                f"{verb} engagement workspace for target: {target}\n"
                f"Directory: {eng_dir}\n\n"
                f"Structure:\n"
                f"  {eng_dir}/\n"
                f"  ├── scope.txt        — edit to define IP ranges and domains\n"
                f"  ├── roe.txt          — edit to define rules of engagement\n"
                f"  ├── findings.json    — managed by findings_tracker tool\n"
                f"  ├── engagement.json  — metadata\n"
                f"  ├── loot/            — captured credentials and flags\n"
                f"  │   └── recon/       — raw recon tool output\n"
                f"  ├── screenshots/     — evidence screenshots\n"
                f"  └── reports/         — generated reports\n\n"
                f"Engagement context saved to memory. Next: edit scope.txt then proceed with recon."
            ),
            break_loop=False,
        )

    def _list_engagements(self) -> Response:
        workdir = settings.get_settings().get("workdir_path", "usr/workdir")
        if not os.path.isabs(workdir):
            workdir = os.path.join("/a0", workdir)
        base = os.path.join(workdir, ENGAGEMENT_BASE)

        if not os.path.isdir(base):
            return Response(message="No engagements directory found. Run engagement_init with action=init first.", break_loop=False)

        entries = []
        for name in sorted(os.listdir(base)):
            eng_dir = os.path.join(base, name)
            meta_path = os.path.join(eng_dir, "engagement.json")
            if os.path.isdir(eng_dir) and os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                findings_path = os.path.join(eng_dir, "findings.json")
                finding_count = 0
                if os.path.exists(findings_path):
                    with open(findings_path) as f:
                        finding_count = len(json.load(f))
                entries.append(
                    f"  {name} — created {meta.get('created', '?')[:10]} — {finding_count} findings — status: {meta.get('status', 'unknown')}"
                )

        if not entries:
            return Response(message="No engagements found.", break_loop=False)

        return Response(message="Existing engagements:\n" + "\n".join(entries), break_loop=False)

    def _status(self) -> Response:
        return Response(
            message=(
                "Use 'memory_load' with query 'ACTIVE ENGAGEMENT' to retrieve current engagement context, "
                "or use action='list' to see all engagements."
            ),
            break_loop=False,
        )
