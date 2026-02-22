import os
import ipaddress
import re
from python.helpers.tool import Tool, Response
from python.helpers import settings


def _engagement_dir(target: str) -> str:
    workdir = settings.get_settings().get("workdir_path", "usr/workdir")
    if not os.path.isabs(workdir):
        workdir = os.path.join("/a0", workdir)
    return os.path.join(workdir, "engagements", target)


def load_scope_entries(scope_path: str) -> list[str]:
    """Read scope.txt and return non-empty, non-comment lines."""
    if not os.path.exists(scope_path):
        return []
    entries = []
    with open(scope_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.append(line)
    return entries


def is_in_scope(value: str, scope_entries: list[str]) -> tuple[bool, str]:
    """
    Check if an IP address, CIDR, or domain is within scope entries.
    Returns (in_scope: bool, matched_entry: str).
    """
    value = value.strip().lower()

    # Strip scheme and path for URL inputs
    url_match = re.match(r"(?:https?://)?([^/\s:]+)", value)
    if url_match:
        host = url_match.group(1)
    else:
        host = value

    for entry in scope_entries:
        entry = entry.strip().lower()

        # Try IP/CIDR match
        try:
            target_addr = ipaddress.ip_address(host)
            try:
                network = ipaddress.ip_network(entry, strict=False)
                if target_addr in network:
                    return True, entry
            except ValueError:
                pass
        except ValueError:
            pass

        # Domain exact match
        if host == entry:
            return True, entry

        # Wildcard subdomain: *.example.com
        if entry.startswith("*."):
            parent = entry[2:]
            if host == parent or host.endswith("." + parent):
                return True, entry

        # Subdomain of a base domain in scope
        if host.endswith("." + entry) or host == entry:
            return True, entry

    return False, ""


class ScopeCheck(Tool):
    """
    Verify that a target (IP, CIDR, domain, or URL) is within the defined engagement scope.

    Actions:
        check  — check a specific value against scope
        show   — display current scope entries
    """

    async def execute(self, action="check", target="", value="", **kwargs):
        action = action.lower().strip()

        if action == "show":
            return self._show_scope(target)

        # Default: check
        if not value:
            return Response(
                message="scope_check requires 'value' (IP, domain, or URL to check) and 'target' (engagement name).",
                break_loop=False,
            )

        if not target:
            return Response(
                message="scope_check requires 'target' (engagement name) to locate scope.txt.",
                break_loop=False,
            )

        eng_dir = _engagement_dir(target)
        scope_path = os.path.join(eng_dir, "scope.txt")
        scope_entries = load_scope_entries(scope_path)

        if not scope_entries:
            return Response(
                message=(
                    f"WARNING: No scope entries found in {scope_path}. "
                    "Define scope before proceeding with active testing."
                ),
                break_loop=False,
            )

        in_scope, matched = is_in_scope(value, scope_entries)

        if in_scope:
            return Response(
                message=f"IN SCOPE: '{value}' matches scope entry '{matched}'.",
                break_loop=False,
            )
        else:
            return Response(
                message=(
                    f"OUT OF SCOPE: '{value}' does not match any entry in the engagement scope.\n"
                    f"Scope entries: {scope_entries}\n"
                    f"DO NOT proceed with active testing against this target."
                ),
                break_loop=False,
            )

    def _show_scope(self, target: str) -> Response:
        if not target:
            return Response(message="show requires 'target' (engagement name).", break_loop=False)

        eng_dir = _engagement_dir(target)
        scope_path = os.path.join(eng_dir, "scope.txt")
        entries = load_scope_entries(scope_path)

        if not entries:
            return Response(
                message=f"No scope defined yet. Edit {scope_path} to add targets.",
                break_loop=False,
            )

        return Response(
            message=f"Scope for engagement '{target}':\n" + "\n".join(f"  - {e}" for e in entries),
            break_loop=False,
        )
