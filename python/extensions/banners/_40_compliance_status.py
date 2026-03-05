from python.helpers.extension import Extension
from python.helpers.compliance import ComplianceConfig, get_compliance_status


class ComplianceStatusBanner(Extension):
    """Display compliance level and classification banner on the welcome screen."""

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        config = ComplianceConfig.get_instance()
        status = get_compliance_status()

        # Classification banner (if configured)
        classification_text = config.get_classification_banner()
        if classification_text:
            banners.append({
                "id": "classification-banner",
                "type": "warning",
                "priority": 200,
                "title": classification_text,
                "html": "This system is subject to monitoring and compliance controls.",
                "dismissible": False,
                "source": "backend",
            })

        # Compliance status info banner
        level_display = status["level"].upper()
        controls_summary = []
        if status["audit_enabled"]:
            controls_summary.append("Audit Logging")
        if status["restrict_external_urls"]:
            controls_summary.append("URL Restriction")
        if status["requires_auth"]:
            controls_summary.append("Auth Required")
        if status["log_tool_usage"]:
            controls_summary.append("Tool Use Logging")
        if status["data_marking"] != "None":
            controls_summary.append(f"Marking: {status['data_marking']}")

        controls_html = " &bull; ".join(controls_summary) if controls_summary else "Minimal controls active"

        banners.append({
            "id": "compliance-status",
            "type": "info",
            "priority": 15,
            "title": f"JSIG/RMF Compliance: {level_display}",
            "html": (
                f"<strong>Active Controls:</strong> {controls_html}<br>"
                f"Session timeout: {status['session_timeout_minutes']} min &bull; "
                f"Configure via <code>A007_*</code> environment variables."
            ),
            "dismissible": True,
            "source": "backend",
        })
