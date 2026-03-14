"""
settings_validation.py — Pydantic models for runtime validation of settings.

This module was extracted from settings.py as part of OPA-5 (Settings Architecture Refactor).
It provides:
  - Pydantic BaseModel validators for critical settings sections
  - A SettingsValidator class with validate(raw) -> (validated, warnings)
  - Validation for ctx_length > 0, rate limits >= 0, required fields present
"""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, field_validator, model_validator

    _HAS_PYDANTIC = True
except ImportError:  # pragma: no cover — graceful fallback
    _HAS_PYDANTIC = False
    BaseModel = object  # type: ignore[assignment,misc]

    def field_validator(*_a, **_kw):  # type: ignore[misc]
        def _noop(fn):
            return fn

        return _noop

    def model_validator(*_a, **_kw):  # type: ignore[misc]
        def _noop(fn):
            return fn

        return _noop


# ---------------------------------------------------------------------------
# Pydantic validator models for critical sections
# ---------------------------------------------------------------------------

if _HAS_PYDANTIC:

    class ModelConfigValidator(BaseModel):
        """Validates a single model configuration block (chat, util, browser, embed)."""

        provider: str = ""
        name: str = ""
        api_base: str = ""
        ctx_length: int | None = None
        rl_requests: int = 0
        rl_input: int = 0
        rl_output: int = 0

        @field_validator("ctx_length")
        @classmethod
        def ctx_length_positive(cls, v: int | None) -> int | None:
            if v is not None and v <= 0:
                raise ValueError("ctx_length must be > 0")
            return v

        @field_validator("rl_requests", "rl_input", "rl_output")
        @classmethod
        def rate_limits_non_negative(cls, v: int) -> int:
            if v < 0:
                raise ValueError("rate limit values must be >= 0")
            return v

    class AuthConfigValidator(BaseModel):
        """Validates authentication settings."""

        auth_login: str = ""
        auth_password: str = ""

    class DeploymentConfigValidator(BaseModel):
        """Validates deployment / RFC settings."""

        rfc_url: str = ""
        rfc_password: str = ""
        rfc_port_http: int = 55080
        rfc_port_ssh: int = 55022

        @field_validator("rfc_port_http", "rfc_port_ssh")
        @classmethod
        def port_range(cls, v: int) -> int:
            if v < 0 or v > 65535:
                raise ValueError("port must be between 0 and 65535")
            return v

    class MemoryConfigValidator(BaseModel):
        """Validates memory subsystem settings."""

        memory_recall_interval: int = 3
        memory_recall_history_len: int = 10000
        memory_recall_similarity_threshold: float = 0.7

        @field_validator("memory_recall_interval")
        @classmethod
        def interval_positive(cls, v: int) -> int:
            if v < 1:
                raise ValueError("memory_recall_interval must be >= 1")
            return v

        @field_validator("memory_recall_similarity_threshold")
        @classmethod
        def threshold_range(cls, v: float) -> float:
            if v < 0 or v > 1:
                raise ValueError("memory_recall_similarity_threshold must be between 0 and 1")
            return v

    class TierConfigValidator(BaseModel):
        """Validates free/pro tier performance config."""

        deployment_tier: str = "free"
        perf_slo_profile: str = "free"
        max_concurrent_sessions: int = 25

        @field_validator("deployment_tier", "perf_slo_profile")
        @classmethod
        def valid_profile(cls, v: str) -> str:
            normalized = v.strip().lower()
            if normalized not in {"free", "pro"}:
                raise ValueError("must be one of: free, pro")
            return normalized

        @field_validator("max_concurrent_sessions")
        @classmethod
        def positive_sessions(cls, v: int) -> int:
            if v < 1:
                raise ValueError("max_concurrent_sessions must be >= 1")
            return v

    class LlmRoutingConfigValidator(BaseModel):
        """Validates LLM routing and local/cloud policy flags."""

        llm_router_enabled: bool = True
        llm_router_auto_configure: bool = True
        llm_local_only_mode: bool = True
        llm_cloud_fallback_enabled: bool = False

    class StartupSelectionValidator(BaseModel):
        """Validates startup auto-selection policy."""

        startup_auto_select_enabled: bool = True
        startup_selection_goal: str = "reliability"
        startup_context_priority: str = "project"
        startup_fallback_policy: str = "chain"
        startup_fallback_chain: list[str] = ["claude_local", "codex_local", "native_local", "native_gemini"]

        @field_validator("startup_selection_goal")
        @classmethod
        def valid_goal(cls, v: str) -> str:
            normalized = v.strip().lower()
            if normalized not in {"reliability", "quality", "cost"}:
                raise ValueError("startup_selection_goal must be one of: reliability, quality, cost")
            return normalized

        @field_validator("startup_context_priority")
        @classmethod
        def valid_context_priority(cls, v: str) -> str:
            normalized = v.strip().lower()
            if normalized not in {"project", "user", "system"}:
                raise ValueError("startup_context_priority must be one of: project, user, system")
            return normalized

        @field_validator("startup_fallback_policy")
        @classmethod
        def valid_fallback_policy(cls, v: str) -> str:
            normalized = v.strip().lower()
            if normalized not in {"chain", "hard_fail", "retry"}:
                raise ValueError("startup_fallback_policy must be one of: chain, hard_fail, retry")
            return normalized


# ---------------------------------------------------------------------------
# Unified validator
# ---------------------------------------------------------------------------


class SettingsValidator:
    """
    Validate a raw settings dict.

    Returns:
        tuple[dict, list[str]]: (validated_settings, list_of_warnings)

    If pydantic is unavailable the raw dict is returned unchanged with a
    single warning noting that validation was skipped.
    """

    # Model prefixes we validate with ModelConfigValidator
    _MODEL_PREFIXES = ("chat_model", "util_model", "browser_model", "embed_model")

    @classmethod
    def validate(cls, raw: dict) -> tuple[dict, list[str]]:
        warnings: list[str] = []

        if not _HAS_PYDANTIC:
            warnings.append("pydantic not installed; settings validation skipped")
            return raw, warnings

        validated = dict(raw)  # shallow copy

        # --- model sections ---
        for prefix in cls._MODEL_PREFIXES:
            model_data: dict[str, Any] = {}
            model_data["provider"] = raw.get(f"{prefix}_provider", "")
            model_data["name"] = raw.get(f"{prefix}_name", "")
            model_data["api_base"] = raw.get(f"{prefix}_api_base", "")
            if f"{prefix}_ctx_length" in raw:
                model_data["ctx_length"] = raw[f"{prefix}_ctx_length"]
            model_data["rl_requests"] = raw.get(f"{prefix}_rl_requests", 0)
            model_data["rl_input"] = raw.get(f"{prefix}_rl_input", 0)
            model_data["rl_output"] = raw.get(f"{prefix}_rl_output", 0)

            try:
                obj = ModelConfigValidator(**model_data)
                # write validated values back
                validated[f"{prefix}_provider"] = obj.provider
                validated[f"{prefix}_name"] = obj.name
                validated[f"{prefix}_api_base"] = obj.api_base
                if obj.ctx_length is not None:
                    validated[f"{prefix}_ctx_length"] = obj.ctx_length
                validated[f"{prefix}_rl_requests"] = obj.rl_requests
                validated[f"{prefix}_rl_input"] = obj.rl_input
                validated[f"{prefix}_rl_output"] = obj.rl_output
            except Exception as exc:
                warnings.append(f"{prefix}: {exc}")

        # --- auth ---
        try:
            AuthConfigValidator(
                auth_login=raw.get("auth_login", ""),
                auth_password=raw.get("auth_password", ""),
            )
        except Exception as exc:
            warnings.append(f"auth: {exc}")

        # --- deployment ---
        try:
            dep = DeploymentConfigValidator(
                rfc_url=raw.get("rfc_url", ""),
                rfc_password=raw.get("rfc_password", ""),
                rfc_port_http=raw.get("rfc_port_http", 55080),
                rfc_port_ssh=raw.get("rfc_port_ssh", 55022),
            )
            validated["rfc_port_http"] = dep.rfc_port_http
            validated["rfc_port_ssh"] = dep.rfc_port_ssh
        except Exception as exc:
            warnings.append(f"deployment: {exc}")

        # --- memory ---
        try:
            mem = MemoryConfigValidator(
                memory_recall_interval=raw.get("memory_recall_interval", 3),
                memory_recall_history_len=raw.get("memory_recall_history_len", 10000),
                memory_recall_similarity_threshold=raw.get("memory_recall_similarity_threshold", 0.7),
            )
            validated["memory_recall_interval"] = mem.memory_recall_interval
            validated["memory_recall_history_len"] = mem.memory_recall_history_len
            validated["memory_recall_similarity_threshold"] = mem.memory_recall_similarity_threshold
        except Exception as exc:
            warnings.append(f"memory: {exc}")

        # --- required fields check ---
        required = ("chat_model_provider", "chat_model_name", "embed_model_provider", "embed_model_name")
        for field in required:
            val = validated.get(field)
            if not val or (isinstance(val, str) and not val.strip()):
                warnings.append(f"required field '{field}' is missing or empty")

        # --- tier/perf profile ---
        try:
            tier = TierConfigValidator(
                deployment_tier=raw.get("deployment_tier", "free"),
                perf_slo_profile=raw.get("perf_slo_profile", "free"),
                max_concurrent_sessions=raw.get("max_concurrent_sessions", 25),
            )
            validated["deployment_tier"] = tier.deployment_tier
            validated["perf_slo_profile"] = tier.perf_slo_profile
            validated["max_concurrent_sessions"] = tier.max_concurrent_sessions
        except Exception as exc:
            warnings.append(f"tier: {exc}")

        # --- llm routing profile ---
        try:
            llm = LlmRoutingConfigValidator(
                llm_router_enabled=raw.get("llm_router_enabled", True),
                llm_router_auto_configure=raw.get("llm_router_auto_configure", True),
                llm_local_only_mode=raw.get("llm_local_only_mode", True),
                llm_cloud_fallback_enabled=raw.get("llm_cloud_fallback_enabled", False),
            )
            validated["llm_router_enabled"] = llm.llm_router_enabled
            validated["llm_router_auto_configure"] = llm.llm_router_auto_configure
            validated["llm_local_only_mode"] = llm.llm_local_only_mode
            validated["llm_cloud_fallback_enabled"] = llm.llm_cloud_fallback_enabled
        except Exception as exc:
            warnings.append(f"llm-routing: {exc}")

        # --- startup auto-selection ---
        try:
            startup = StartupSelectionValidator(
                startup_auto_select_enabled=raw.get("startup_auto_select_enabled", True),
                startup_selection_goal=raw.get("startup_selection_goal", "reliability"),
                startup_context_priority=raw.get("startup_context_priority", "project"),
                startup_fallback_policy=raw.get("startup_fallback_policy", "chain"),
                startup_fallback_chain=raw.get(
                    "startup_fallback_chain",
                    ["claude_local", "codex_local", "native_local", "native_gemini"],
                ),
            )
            validated["startup_auto_select_enabled"] = startup.startup_auto_select_enabled
            validated["startup_selection_goal"] = startup.startup_selection_goal
            validated["startup_context_priority"] = startup.startup_context_priority
            validated["startup_fallback_policy"] = startup.startup_fallback_policy
            validated["startup_fallback_chain"] = startup.startup_fallback_chain
        except Exception as exc:
            warnings.append(f"startup-selection: {exc}")

        return validated, warnings
