import os
import json
from datetime import datetime
from python.helpers.tool import Tool, Response
from python.helpers import settings


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
SEVERITY_CVSS = {
    "critical": "9.0–10.0",
    "high": "7.0–8.9",
    "medium": "4.0–6.9",
    "low": "0.1–3.9",
    "informational": "0.0",
}


def _engagement_dir(target: str) -> str:
    workdir = settings.get_settings().get("workdir_path", "usr/workdir")
    if not os.path.isabs(workdir):
        workdir = os.path.join("/a0", workdir)
    return os.path.join(workdir, "engagements", target)


class ReportGenerator(Tool):
    """
    Generate a penetration test report from findings.json.

    Actions:
        generate — produce report in requested format (markdown, html, or pdf)
        preview  — show executive summary only
    """

    async def execute(self, action="generate", target="", format="markdown",
                      title="Penetration Test Report", client="[Client Name]",
                      tester="Agent Zero Security Assessment", **kwargs):
        action = action.lower().strip()
        fmt = format.lower().strip()

        if not target:
            return Response(
                message="report_generator requires 'target' (engagement name).",
                break_loop=False,
            )

        eng_dir = _engagement_dir(target)
        findings_path = os.path.join(eng_dir, "findings.json")

        if not os.path.exists(findings_path):
            return Response(
                message=f"No findings.json found at {findings_path}. Initialize engagement first.",
                break_loop=False,
            )

        with open(findings_path) as f:
            findings = json.load(f)

        findings = sorted(
            findings,
            key=lambda f: (SEVERITY_ORDER.get(f.get("severity", "low"), 4), -float(f.get("cvss_score", 0)))
        )

        if action == "preview":
            return Response(message=self._executive_summary(findings, target, title, client), break_loop=False)

        # Generate full report
        md = self._build_markdown(findings, target, title, client, tester)

        reports_dir = os.path.join(eng_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        if fmt == "markdown":
            path = os.path.join(reports_dir, "report.md")
            with open(path, "w") as f:
                f.write(md)
            return Response(message=f"Markdown report generated: {path}", break_loop=False)

        if fmt in ("html", "pdf"):
            html = self._md_to_html(md, title)
            html_path = os.path.join(reports_dir, "report.html")
            with open(html_path, "w") as f:
                f.write(html)

            if fmt == "html":
                return Response(message=f"HTML report generated: {html_path}", break_loop=False)

            # PDF via weasyprint
            pdf_path = os.path.join(reports_dir, "report.pdf")
            try:
                from weasyprint import HTML  # type: ignore
                HTML(string=html).write_pdf(pdf_path)
                return Response(message=f"PDF report generated: {pdf_path}", break_loop=False)
            except ImportError:
                return Response(
                    message=(
                        f"HTML report saved to {html_path}.\n"
                        "PDF generation requires weasyprint: pip install weasyprint\n"
                        "Convert manually: weasyprint report.html report.pdf"
                    ),
                    break_loop=False,
                )

        return Response(
            message=f"Unknown format '{fmt}'. Use: markdown, html, or pdf.",
            break_loop=False,
        )

    def _count_by_severity(self, findings: list) -> dict:
        counts = {s: 0 for s in SEVERITY_ORDER}
        for f in findings:
            sev = f.get("severity", "low")
            counts[sev] = counts.get(sev, 0) + 1
        return counts

    def _overall_rating(self, counts: dict) -> str:
        for sev in ["critical", "high", "medium", "low"]:
            if counts.get(sev, 0) > 0:
                return sev.upper()
        return "INFORMATIONAL"

    def _executive_summary(self, findings: list, target: str, title: str, client: str) -> str:
        counts = self._count_by_severity(findings)
        rating = self._overall_rating(counts)
        top3 = findings[:3]

        lines = [
            f"## Executive Summary — {title}",
            f"**Client:** {client}  |  **Target:** {target}  |  **Date:** {datetime.utcnow().strftime('%Y-%m-%d')}",
            f"**Overall Risk Rating:** {rating}",
            "",
            f"**Findings:** {counts['critical']} Critical | {counts['high']} High | "
            f"{counts['medium']} Medium | {counts['low']} Low | {counts['informational']} Informational",
            "",
            "**Key Findings:**",
        ]
        for f in top3:
            lines.append(f"- [{f['severity'].upper()}] {f['title']} — {f.get('host', '?')}:{f.get('port', '?')}")

        return "\n".join(lines)

    def _build_markdown(self, findings: list, target: str, title: str, client: str, tester: str) -> str:
        counts = self._count_by_severity(findings)
        rating = self._overall_rating(counts)
        date = datetime.utcnow().strftime("%Y-%m-%d")
        top3 = findings[:3]

        sections = []

        # Cover
        sections.append(
            f"# {title}\n\n"
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| Client | {client} |\n"
            f"| Target | {target} |\n"
            f"| Prepared by | {tester} |\n"
            f"| Date | {date} |\n"
            f"| Classification | CONFIDENTIAL |\n"
            f"| Overall Risk | **{rating}** |\n"
        )

        # Executive Summary
        top3_bullets = "\n".join(
            f"- **[{f['severity'].upper()}]** {f['title']} on `{f.get('host', '?')}:{f.get('port', '?')}`"
            for f in top3
        )
        sections.append(
            f"## Executive Summary\n\n"
            f"This report presents the results of an authorized penetration test against **{target}**. "
            f"A total of **{len(findings)} vulnerabilities** were identified.\n\n"
            f"**Risk Distribution:** {counts['critical']} Critical | {counts['high']} High | "
            f"{counts['medium']} Medium | {counts['low']} Low | {counts['informational']} Informational\n\n"
            f"**Top Findings:**\n{top3_bullets}\n\n"
            f"**Overall Risk Rating: {rating}**\n"
        )

        # Risk Matrix
        sections.append(
            "## Risk Rating Matrix\n\n"
            "| Severity | CVSS Range | Description |\n"
            "|----------|------------|-------------|\n"
            "| **Critical** | 9.0–10.0 | Immediate exploitation risk; full system compromise possible |\n"
            "| **High** | 7.0–8.9 | Significant risk; likely exploited in targeted attacks |\n"
            "| **Medium** | 4.0–6.9 | Moderate risk; requires specific conditions or chaining |\n"
            "| **Low** | 0.1–3.9 | Minimal direct impact; contributes to attack chains |\n"
            "| **Informational** | 0.0 | Best practice violation; no direct exploit path |\n"
        )

        # Findings
        findings_md = ["## Findings\n"]
        for i, f in enumerate(findings, 1):
            sev = f.get("severity", "low").upper()
            title_f = f.get("title", "Untitled")
            findings_md.append(f"### {i}. [{sev}] — {title_f}\n")
            findings_md.append(
                f"| Field | Value |\n"
                f"|-------|-------|\n"
                f"| CVSS Score | {f.get('cvss_score', 0)} |\n"
                f"| Affected Host | `{f.get('host', '?')}:{f.get('port', '?')}` |\n"
                f"| Service | {f.get('service', '?')} |\n"
                f"| CVE | {f.get('cve', 'N/A')} |\n"
                f"| Status | {f.get('status', 'confirmed')} |\n"
                f"| Finding ID | {f.get('id', '?')} |\n"
            )
            if f.get("description"):
                findings_md.append(f"**Description:** {f['description']}\n")
            if f.get("steps_to_reproduce"):
                findings_md.append(f"**Steps to Reproduce:**\n{f['steps_to_reproduce']}\n")
            if f.get("evidence"):
                findings_md.append(f"**Evidence:** `{f['evidence']}`\n")
            if f.get("remediation"):
                findings_md.append(f"**Remediation:** {f['remediation']}\n")
            findings_md.append("---\n")

        sections.append("\n".join(findings_md))

        return "\n\n".join(sections)

    def _md_to_html(self, md: str, title: str) -> str:
        try:
            import markdown  # type: ignore
            body = markdown.markdown(md, extensions=["tables", "fenced_code"])
        except ImportError:
            # Fallback: wrap in pre tag
            body = f"<pre>{md}</pre>"

        return (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>"
            "<style>"
            "body{font-family:Arial,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#333}"
            "h1{color:#1a1a2e}h2{color:#16213e;border-bottom:2px solid #e94560;padding-bottom:6px}"
            "h3{color:#0f3460}"
            "table{border-collapse:collapse;width:100%;margin:16px 0}"
            "th,td{border:1px solid #ddd;padding:8px;text-align:left}"
            "th{background:#0f3460;color:white}"
            "tr:nth-child(even){background:#f9f9f9}"
            "code{background:#f4f4f4;padding:2px 6px;border-radius:3px}"
            "pre{background:#1a1a2e;color:#e0e0e0;padding:16px;border-radius:6px;overflow-x:auto}"
            "hr{border:none;border-top:1px solid #eee;margin:24px 0}"
            "</style></head>"
            f"<body>{body}</body></html>"
        )
