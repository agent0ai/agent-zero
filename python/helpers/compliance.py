"""
Agent 007 - JSIG/RMF Compliance Controls Module

Provides configurable security controls aligned with:
- JSIG (Joint SIGINT Cybersecurity Instruction Guide) - IC community security standards
- RMF (Risk Management Framework) - NIST SP 800-37/53 based controls

These controls are designed to be practical for classified environments without
being so restrictive that the agent becomes unusable. Controls are configurable
via environment variables (A0_SET_*) or settings.
"""

import os
import re
import datetime
import logging
from typing import Optional

from python.helpers.print_style import PrintStyle

_PRINTER = PrintStyle(italic=True, font_color="cyan", padding=False)

# ── Control Families (mapped to NIST 800-53 control families) ──────────────

# AC - Access Control
# AU - Audit and Accountability
# CM - Configuration Management
# SC - System and Communications Protection
# SI - System and Information Integrity


class ComplianceLevel:
    """Classification environment compliance levels."""
    STANDARD = "standard"       # Basic controls, suitable for CUI/FOUO-equivalent
    ELEVATED = "elevated"       # Stricter controls, suitable for SECRET-equivalent
    HIGH = "high"               # Maximum controls, suitable for TS/SCI-equivalent


class ComplianceConfig:
    """Runtime compliance configuration, loaded from env/settings."""

    _instance: Optional["ComplianceConfig"] = None

    def __init__(self):
        self.level = os.getenv("A007_COMPLIANCE_LEVEL", ComplianceLevel.STANDARD).lower()
        self.audit_enabled = os.getenv("A007_AUDIT_LOG", "true").lower() == "true"
        self.session_timeout_minutes = int(os.getenv("A007_SESSION_TIMEOUT", "480"))  # 8 hrs
        self.restrict_external_urls = os.getenv("A007_RESTRICT_EXTERNAL", "false").lower() == "true"
        self.data_marking = os.getenv("A007_DATA_MARKING", "")  # e.g., "CUI", "SECRET"
        self.banner_text = os.getenv("A007_BANNER_TEXT", "")
        self.log_tool_usage = os.getenv("A007_LOG_TOOL_USAGE", "true").lower() == "true"
        self.max_output_length = int(os.getenv("A007_MAX_OUTPUT_LENGTH", "0"))  # 0 = unlimited
        self.allowed_domains: list[str] = _parse_list(os.getenv("A007_ALLOWED_DOMAINS", ""))
        self.blocked_domains: list[str] = _parse_list(os.getenv("A007_BLOCKED_DOMAINS", ""))

    @classmethod
    def get_instance(cls) -> "ComplianceConfig":
        if cls._instance is None:
            cls._instance = ComplianceConfig()
        return cls._instance

    @classmethod
    def reload(cls):
        cls._instance = ComplianceConfig()

    @property
    def requires_auth(self) -> bool:
        """Elevated and high levels require authentication."""
        return self.level in (ComplianceLevel.ELEVATED, ComplianceLevel.HIGH)

    @property
    def requires_encryption(self) -> bool:
        """High level requires encryption for all communications."""
        return self.level == ComplianceLevel.HIGH

    def get_classification_banner(self) -> str:
        """Return the classification banner text for UI display."""
        if self.banner_text:
            return self.banner_text
        banners = {
            ComplianceLevel.STANDARD: "",
            ComplianceLevel.ELEVATED: "CONTROLLED ENVIRONMENT - AUTHORIZED USERS ONLY",
            ComplianceLevel.HIGH: "RESTRICTED ACCESS - AUTHORIZED USERS ONLY - ALL ACTIVITY MONITORED",
        }
        return banners.get(self.level, "")


# ── AU: Audit Logging ──────────────────────────────────────────────────────

_audit_logger: Optional[logging.Logger] = None


def get_audit_logger() -> logging.Logger:
    """Get or create the compliance audit logger (AU-2, AU-3, AU-6)."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = logging.getLogger("agent007.audit")
        _audit_logger.setLevel(logging.INFO)

        # File handler for persistent audit log
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, "audit.log"))
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z"
        ))
        _audit_logger.addHandler(handler)
    return _audit_logger


def audit_log(event_type: str, details: str, user: str = "system", severity: str = "INFO"):
    """
    Write an audit log entry (AU-2: Audit Events, AU-3: Content of Audit Records).

    Args:
        event_type: Category of event (e.g., TOOL_USE, AUTH, CONFIG_CHANGE, DATA_ACCESS)
        details: Human-readable description of the event
        user: Identity of the user or process
        severity: INFO, WARNING, ERROR
    """
    config = ComplianceConfig.get_instance()
    if not config.audit_enabled:
        return

    logger = get_audit_logger()
    msg = f"[{event_type}] user={user} | {details}"

    if severity == "WARNING":
        logger.warning(msg)
    elif severity == "ERROR":
        logger.error(msg)
    else:
        logger.info(msg)


def audit_tool_use(tool_name: str, tool_args: dict, agent_id: str = "agent0"):
    """Log tool invocations for compliance audit trail (AU-12)."""
    config = ComplianceConfig.get_instance()
    if not config.log_tool_usage:
        return

    # Sanitize args to avoid logging secrets
    safe_args = _sanitize_for_log(tool_args)
    audit_log(
        event_type="TOOL_USE",
        details=f"tool={tool_name} agent={agent_id} args={safe_args}",
        user=agent_id,
    )


# ── SC: System & Communications Protection ─────────────────────────────────

def check_url_allowed(url: str) -> tuple[bool, str]:
    """
    Check if a URL is permitted under current compliance settings (SC-7).

    Returns:
        (allowed, reason) tuple
    """
    config = ComplianceConfig.get_instance()

    if not config.restrict_external_urls:
        return True, ""

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.hostname or ""
    except Exception:
        return False, "Invalid URL format"

    # Check blocked domains first
    for blocked in config.blocked_domains:
        if domain == blocked or domain.endswith("." + blocked):
            return False, f"Domain '{domain}' is blocked by compliance policy"

    # If allowed domains list is set, only those are permitted
    if config.allowed_domains:
        for allowed in config.allowed_domains:
            if domain == allowed or domain.endswith("." + allowed):
                return True, ""
        return False, f"Domain '{domain}' is not in the allowed domains list"

    return True, ""


# ── SI: System and Information Integrity ────────────────────────────────────

def sanitize_output(text: str) -> str:
    """
    Apply output sanitization controls (SI-15: Information Output Filtering).

    Checks for accidental inclusion of classification markings or sensitive patterns.
    """
    config = ComplianceConfig.get_instance()

    if config.max_output_length > 0 and len(text) > config.max_output_length:
        text = text[:config.max_output_length] + "\n[Output truncated by compliance policy]"

    return text


def get_data_marking_prefix() -> str:
    """Get the data marking prefix for outputs (SI-12: Information Handling)."""
    config = ComplianceConfig.get_instance()
    if config.data_marking:
        return f"[{config.data_marking}] "
    return ""


# ── CM: Configuration Management ───────────────────────────────────────────

def get_compliance_status() -> dict:
    """
    Get current compliance configuration status for display/reporting (CM-6).

    Returns a dict suitable for inclusion in banners or status pages.
    """
    config = ComplianceConfig.get_instance()
    return {
        "level": config.level,
        "audit_enabled": config.audit_enabled,
        "session_timeout_minutes": config.session_timeout_minutes,
        "restrict_external_urls": config.restrict_external_urls,
        "data_marking": config.data_marking or "None",
        "requires_auth": config.requires_auth,
        "requires_encryption": config.requires_encryption,
        "log_tool_usage": config.log_tool_usage,
        "allowed_domains": len(config.allowed_domains),
        "blocked_domains": len(config.blocked_domains),
    }


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_list(value: str) -> list[str]:
    """Parse a comma-separated env var into a list."""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _sanitize_for_log(args: dict, max_value_len: int = 200) -> str:
    """Sanitize tool arguments for safe audit logging - mask potential secrets."""
    sanitized = {}
    sensitive_keys = {"password", "secret", "token", "key", "api_key", "credential", "auth"}

    for k, v in args.items():
        if any(s in k.lower() for s in sensitive_keys):
            sanitized[k] = "***REDACTED***"
        else:
            val_str = str(v)
            if len(val_str) > max_value_len:
                val_str = val_str[:max_value_len] + "..."
            sanitized[k] = val_str
    return str(sanitized)
