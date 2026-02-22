import os
import json
import uuid
from datetime import datetime
from python.helpers.tool import Tool, Response
from python.helpers import settings


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}


def _engagement_dir(target: str) -> str:
    workdir = settings.get_settings().get("workdir_path", "usr/workdir")
    if not os.path.isabs(workdir):
        workdir = os.path.join("/a0", workdir)
    return os.path.join(workdir, "engagements", target)


def _load_findings(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def _save_findings(path: str, findings: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(findings, f, indent=2)


class FindingsTracker(Tool):
    """
    CRUD tool for structured penetration test findings.

    Actions:
        add_finding    — add a new vulnerability finding
        list_findings  — list all findings (optionally filtered by severity)
        update_finding — update an existing finding by ID
        get_finding    — get full details of one finding by ID
        export_findings — export findings summary as text for reporting
    """

    async def execute(self, action="list_findings", target="", **kwargs):
        action = action.lower().strip()

        if not target:
            return Response(
                message="findings_tracker requires a 'target' argument matching the engagement name used in engagement_init.",
                break_loop=False,
            )

        eng_dir = _engagement_dir(target)
        findings_path = os.path.join(eng_dir, "findings.json")

        if action == "add_finding":
            return self._add(findings_path, **kwargs)
        if action == "list_findings":
            return self._list(findings_path, **kwargs)
        if action == "update_finding":
            return self._update(findings_path, **kwargs)
        if action == "get_finding":
            return self._get(findings_path, **kwargs)
        if action == "export_findings":
            return self._export(findings_path, target)

        return Response(
            message=f"Unknown action '{action}'. Valid: add_finding, list_findings, update_finding, get_finding, export_findings",
            break_loop=False,
        )

    def _add(self, path: str, title="", severity="medium", cvss_score=0.0,
             host="", port="", service="", cve="", description="",
             steps_to_reproduce="", evidence="", remediation="",
             status="confirmed", **kwargs) -> Response:

        if not title:
            return Response(message="add_finding requires a 'title' argument.", break_loop=False)

        severity = severity.lower()
        if severity not in SEVERITY_ORDER:
            severity = "medium"

        finding = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "severity": severity,
            "cvss_score": float(cvss_score),
            "host": host,
            "port": str(port),
            "service": service,
            "cve": cve,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "evidence": evidence,
            "remediation": remediation,
            "status": status,
            "created": datetime.utcnow().isoformat(),
            "updated": datetime.utcnow().isoformat(),
        }

        findings = _load_findings(path)
        findings.append(finding)
        _save_findings(path, findings)

        return Response(
            message=(
                f"Finding added.\n"
                f"ID: {finding['id']}\n"
                f"Title: {title}\n"
                f"Severity: {severity.upper()} (CVSS {cvss_score})\n"
                f"Host: {host}:{port} — {service}\n"
                f"Total findings: {len(findings)}"
            ),
            break_loop=False,
        )

    def _list(self, path: str, severity_filter="", status_filter="", **kwargs) -> Response:
        findings = _load_findings(path)

        if not findings:
            return Response(message="No findings recorded yet.", break_loop=False)

        if severity_filter:
            findings = [f for f in findings if f.get("severity", "") == severity_filter.lower()]
        if status_filter:
            findings = [f for f in findings if f.get("status", "") == status_filter.lower()]

        # Sort by severity then CVSS descending
        findings = sorted(
            findings,
            key=lambda f: (SEVERITY_ORDER.get(f.get("severity", "low"), 4), -float(f.get("cvss_score", 0)))
        )

        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for f in findings:
            counts[f.get("severity", "low")] = counts.get(f.get("severity", "low"), 0) + 1

        lines = [
            f"Findings summary: {counts['critical']} Critical | {counts['high']} High | "
            f"{counts['medium']} Medium | {counts['low']} Low | {counts['informational']} Info\n"
        ]
        for f in findings:
            lines.append(
                f"[{f['id']}] {f['severity'].upper():13} CVSS {f.get('cvss_score', 0):.1f}  "
                f"{f.get('host', '?')}:{f.get('port', '?')}  {f['title']}"
            )

        return Response(message="\n".join(lines), break_loop=False)

    def _get(self, path: str, finding_id="", **kwargs) -> Response:
        findings = _load_findings(path)
        match = next((f for f in findings if f["id"] == finding_id), None)
        if not match:
            return Response(message=f"No finding with ID '{finding_id}'.", break_loop=False)
        return Response(message=json.dumps(match, indent=2), break_loop=False)

    def _update(self, path: str, finding_id="", **kwargs) -> Response:
        if not finding_id:
            return Response(message="update_finding requires 'finding_id'.", break_loop=False)

        findings = _load_findings(path)
        for f in findings:
            if f["id"] == finding_id:
                updatable = ["title", "severity", "cvss_score", "host", "port", "service",
                             "cve", "description", "steps_to_reproduce", "evidence", "remediation", "status"]
                for field in updatable:
                    if field in kwargs and kwargs[field] != "":
                        f[field] = kwargs[field]
                f["updated"] = datetime.utcnow().isoformat()
                _save_findings(path, findings)
                return Response(message=f"Finding {finding_id} updated.", break_loop=False)

        return Response(message=f"No finding with ID '{finding_id}'.", break_loop=False)

    def _export(self, path: str, target: str) -> Response:
        findings = _load_findings(path)
        if not findings:
            return Response(message="No findings to export.", break_loop=False)

        findings = sorted(
            findings,
            key=lambda f: (SEVERITY_ORDER.get(f.get("severity", "low"), 4), -float(f.get("cvss_score", 0)))
        )

        lines = [f"# Findings Export — {target}\n", f"Generated: {datetime.utcnow().isoformat()}\n"]

        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for f in findings:
            sev = f.get("severity", "low")
            counts[sev] = counts.get(sev, 0) + 1

        lines.append(
            f"Summary: {counts['critical']} Critical, {counts['high']} High, "
            f"{counts['medium']} Medium, {counts['low']} Low, {counts['informational']} Informational\n"
        )

        for i, f in enumerate(findings, 1):
            lines.append(f"\n## {i}. [{f['severity'].upper()}] {f['title']}")
            lines.append(f"- ID: {f['id']}")
            lines.append(f"- CVSS: {f.get('cvss_score', 0)}")
            lines.append(f"- Host: {f.get('host', '')}:{f.get('port', '')} ({f.get('service', '')})")
            if f.get("cve"):
                lines.append(f"- CVE: {f['cve']}")
            if f.get("description"):
                lines.append(f"- Description: {f['description']}")
            if f.get("remediation"):
                lines.append(f"- Remediation: {f['remediation']}")
            if f.get("evidence"):
                lines.append(f"- Evidence: {f['evidence']}")

        return Response(message="\n".join(lines), break_loop=False)
