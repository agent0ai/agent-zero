from __future__ import annotations

import json
import os
import shutil
import urllib.request
from dataclasses import dataclass
from typing import Any

import models
from python.helpers import files
from python.helpers.print_style import PrintStyle

LOCAL_PROVIDERS = {"ollama", "huggingface", "local", "lmstudio", "lm_studio"}


@dataclass
class StartupCandidate:
    name: str
    backend: str
    provider: str
    model_name: str
    api_base: str
    agent_profile: str
    source: str


_PRESET_CANDIDATES: dict[str, tuple[str, str, str]] = {
    "claude_local": ("claude_code", "ollama", "qwen2.5-coder:3b"),
    "codex_local": ("codex", "ollama", "qwen2.5-coder:3b"),
    "native_local": ("native", "ollama", "qwen2.5-coder:3b"),
    "native_gemini": ("native", "google", "gemini-2.0-flash"),
}

_STATE: dict[str, Any] = {
    "initialized": False,
    "overrides": {},
    "decision": {
        "enabled": False,
        "selected": None,
        "source": "none",
        "attempts": [],
        "status": "not_run",
        "reason": "",
    },
}


def _is_missing_key(value: str | None) -> bool:
    token = (value or "").strip()
    return token in {"", "None", "NA"}


def _ollama_reachable(api_base: str) -> tuple[bool, str]:
    base = (api_base or "").strip() or "http://localhost:11434"
    url = f"{base.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:  # nosec B310 - local configured endpoint
            status = getattr(resp, "status", 200)
            if 200 <= status < 300:
                return True, f"Ollama reachable at {base}"
            return False, f"Ollama returned HTTP {status}"
    except Exception as e:
        return False, f"Ollama unreachable at {base}: {e}"


def _resolve_external_executable(backend: str) -> str:
    candidates: list[str] = []
    if backend == "claude_code":
        env_path = os.getenv("CLAUDE_CLI_PATH", "").strip()
        if env_path:
            candidates.append(env_path)
        candidates.extend(["claude", "claude-code"])
    elif backend == "codex":
        env_path = os.getenv("CODEX_CLI_PATH", "").strip()
        if env_path:
            candidates.append(env_path)
        candidates.extend(["codex", "codex-cli"])
    else:
        return ""

    for candidate in candidates:
        if os.path.isabs(candidate) and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return ""


def backend_ready(backend: str) -> tuple[bool, str]:
    if backend == "native":
        return True, "Native backend"
    exe = _resolve_external_executable(backend)
    if exe:
        return True, f"{backend} executable found"
    return False, f"{backend} executable not found"


def provider_ready(provider: str, api_base: str) -> tuple[bool, str]:
    p = (provider or "").strip().lower()
    if p == "ollama":
        return _ollama_reachable(api_base)
    if p in LOCAL_PROVIDERS:
        return True, f"Local provider '{p}'"
    key = str(models.get_api_key(p) or "").strip()
    if _is_missing_key(key):
        return False, f"Missing API key for provider '{p}'"
    return True, f"API key configured for provider '{p}'"


def _default_chain(goal: str) -> list[str]:
    if goal == "quality":
        return ["claude_local", "codex_local", "native_gemini", "native_local"]
    if goal == "cost":
        return ["native_local", "claude_local", "codex_local", "native_gemini"]
    return ["claude_local", "codex_local", "native_local", "native_gemini"]


def _load_project_startup_overrides(project_name: str) -> dict[str, Any]:
    if not project_name:
        return {}
    try:
        from python.helpers import projects

        lifecycle_path = projects.get_project_lifecycle_folder(project_name, "lifecycle.json")
        if not os.path.exists(lifecycle_path):
            return {}
        lifecycle = json.loads(files.read_file(lifecycle_path))
        if not isinstance(lifecycle, dict):
            return {}

        patch: dict[str, Any] = {}
        startup = lifecycle.get("startup")
        if isinstance(startup, dict):
            patch.update(startup)

        phase = str(lifecycle.get("current_phase", "")).strip()
        bindings = lifecycle.get("phase_bindings")
        if phase and isinstance(bindings, dict):
            binding = bindings.get(phase)
            if isinstance(binding, dict):
                profile = binding.get("agent_profile")
                if isinstance(profile, str) and profile.strip():
                    patch["agent_profile"] = profile.strip()
                startup_profile = binding.get("startup_profile")
                if isinstance(startup_profile, dict):
                    patch.update(startup_profile)

        if "agent_profile" not in patch:
            phase_profile_defaults = {
                "design": "researcher",
                "development": "developer",
                "testing": "researcher",
                "validation": "researcher",
                "ai_agent_evaluation": "researcher",
            }
            if phase in phase_profile_defaults:
                patch["agent_profile"] = phase_profile_defaults[phase]
        return patch
    except Exception:
        return {}


def _build_candidate_from_settings(settings: dict[str, Any], source: str, name: str = "current") -> StartupCandidate:
    return StartupCandidate(
        name=name,
        backend=str(settings.get("chat_execution_backend", "native") or "native").strip().lower(),
        provider=str(settings.get("chat_model_provider", "ollama") or "ollama").strip().lower(),
        model_name=str(settings.get("chat_model_name", "qwen2.5-coder:3b") or "qwen2.5-coder:3b").strip(),
        api_base=str(settings.get("chat_model_api_base", "") or "").strip(),
        agent_profile=str(settings.get("agent_profile", "agent0") or "agent0").strip(),
        source=source,
    )


def _build_preset_candidate(preset_name: str, base_settings: dict[str, Any], source: str) -> StartupCandidate | None:
    preset = _PRESET_CANDIDATES.get(preset_name)
    if not preset:
        return None
    backend, provider, model_name = preset
    api_base = str(base_settings.get("chat_model_api_base", "") or "").strip()
    if provider == "ollama":
        api_base = (
            str(base_settings.get("util_model_api_base", "") or "").strip()
            or str(base_settings.get("browser_model_api_base", "") or "").strip()
            or str(base_settings.get("chat_model_api_base", "") or "").strip()
        )
    else:
        api_base = ""
    return StartupCandidate(
        name=preset_name,
        backend=backend,
        provider=provider,
        model_name=model_name,
        api_base=api_base,
        agent_profile=str(base_settings.get("agent_profile", "agent0") or "agent0").strip(),
        source=source,
    )


def _candidate_ready(candidate: StartupCandidate) -> tuple[bool, str]:
    ok_backend, msg_backend = backend_ready(candidate.backend)
    if not ok_backend:
        return False, msg_backend
    ok_provider, msg_provider = provider_ready(candidate.provider, candidate.api_base)
    if not ok_provider:
        return False, msg_provider
    return True, "ready"


def _candidate_to_overrides(candidate: StartupCandidate) -> dict[str, Any]:
    return {
        "chat_execution_backend": candidate.backend,
        "chat_model_provider": candidate.provider,
        "chat_model_name": candidate.model_name,
        "chat_model_api_base": candidate.api_base,
        "util_model_provider": candidate.provider,
        "util_model_name": candidate.model_name,
        "util_model_api_base": candidate.api_base,
        "browser_model_provider": candidate.provider,
        "browser_model_name": candidate.model_name,
        "browser_model_api_base": candidate.api_base,
        "agent_profile": candidate.agent_profile,
    }


def _compute_selection(current_settings: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    enabled = bool(current_settings.get("startup_auto_select_enabled", True))
    goal = str(current_settings.get("startup_selection_goal", "reliability") or "reliability").strip().lower()
    context_priority = str(current_settings.get("startup_context_priority", "project") or "project").strip().lower()
    fallback_policy = str(current_settings.get("startup_fallback_policy", "chain") or "chain").strip().lower()

    decision: dict[str, Any] = {
        "enabled": enabled,
        "status": "not_run",
        "goal": goal,
        "context_priority": context_priority,
        "fallback_policy": fallback_policy,
        "selected": None,
        "source": "none",
        "attempts": [],
        "reason": "",
    }
    if not enabled:
        decision["status"] = "disabled"
        decision["reason"] = "startup_auto_select_enabled=false"
        return {}, decision

    base = dict(current_settings)
    defaults: dict[str, Any] = {}
    try:
        from python.helpers.settings_core import get_default_settings

        defaults = get_default_settings()
    except Exception:
        defaults = {}

    active_project = str(
        current_settings.get("startup_active_project", "") or os.getenv("AGENT_ZERO_ACTIVE_PROJECT", "")
    ).strip()
    project_patch = _load_project_startup_overrides(active_project)

    preferred = _build_candidate_from_settings(base, source="user", name="preferred")
    if context_priority == "system":
        preferred = _build_candidate_from_settings(defaults or base, source="system", name="preferred")
    elif context_priority == "project" and project_patch:
        project_base = dict(base)
        project_base.update(project_patch)
        preferred = _build_candidate_from_settings(project_base, source="project", name="preferred")

    raw_chain = current_settings.get("startup_fallback_chain")
    if isinstance(raw_chain, list):
        chain_names = [str(x).strip() for x in raw_chain if str(x).strip()]
    else:
        chain_names = []
    if not chain_names:
        chain_names = _default_chain(goal)

    candidates: list[StartupCandidate] = [preferred]
    for item in chain_names:
        cand = _build_preset_candidate(item, base, source="chain")
        if cand:
            candidates.append(cand)

    deduped: list[StartupCandidate] = []
    seen: set[tuple[str, str, str, str]] = set()
    for candidate in candidates:
        key = (candidate.backend, candidate.provider, candidate.model_name, candidate.agent_profile)
        if key not in seen:
            deduped.append(candidate)
            seen.add(key)

    selected: StartupCandidate | None = None
    for idx, candidate in enumerate(deduped):
        ok, reason = _candidate_ready(candidate)
        decision["attempts"].append(
            {
                "index": idx,
                "candidate": candidate.name,
                "backend": candidate.backend,
                "provider": candidate.provider,
                "model_name": candidate.model_name,
                "agent_profile": candidate.agent_profile,
                "ok": ok,
                "reason": reason,
            }
        )
        if ok:
            selected = candidate
            break
        if fallback_policy == "hard_fail":
            break
        if fallback_policy == "retry":
            # Retry policy means only preferred candidate is attempted.
            break

    if not selected:
        decision["status"] = "failed"
        decision["reason"] = "no ready startup candidate"
        return {}, decision

    overrides = _candidate_to_overrides(selected)
    decision["status"] = "selected"
    decision["selected"] = {
        "backend": selected.backend,
        "provider": selected.provider,
        "model_name": selected.model_name,
        "api_base": selected.api_base,
        "agent_profile": selected.agent_profile,
    }
    decision["source"] = selected.source
    decision["reason"] = "ready candidate selected"
    if active_project:
        decision["active_project"] = active_project
    return overrides, decision


def apply_startup_selection(current_settings: dict[str, Any]) -> dict[str, Any]:
    global _STATE
    if _STATE["initialized"]:
        merged = dict(current_settings)
        merged.update(_STATE.get("overrides") or {})
        return merged

    overrides, decision = _compute_selection(current_settings)
    _STATE["initialized"] = True
    _STATE["overrides"] = overrides
    _STATE["decision"] = decision

    if overrides:
        selected = decision.get("selected") or {}
        PrintStyle().print(
            "Startup selector chose "
            f"backend={selected.get('backend')} provider={selected.get('provider')} "
            f"model={selected.get('model_name')} profile={selected.get('agent_profile')}"
        )
    else:
        PrintStyle.warning(f"Startup selector kept existing settings: {decision.get('reason', 'unknown')}")

    merged = dict(current_settings)
    merged.update(overrides)
    return merged


def get_startup_selection_state() -> dict[str, Any]:
    return dict(_STATE.get("decision") or {})


def reset_startup_selection_state() -> None:
    global _STATE
    _STATE = {
        "initialized": False,
        "overrides": {},
        "decision": {
            "enabled": False,
            "selected": None,
            "source": "none",
            "attempts": [],
            "status": "not_run",
            "reason": "",
        },
    }
