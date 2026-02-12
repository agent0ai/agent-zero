import json
import re
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


_CODEX_BIN = "codex"
_CODEX_CONFIG_OVERRIDES = [
    'model_reasoning_effort="high"',
    "mcp_servers={}",
]
_CODEX_MODEL_CANDIDATES = [
    "gpt-5.3-codex",
    "gpt-5.2-codex",
    "gpt-5.1-codex-max",
    "gpt-5.2",
    "gpt-5.1-codex-mini",
    "gpt-5-codex",
]
_MODEL_PROBE_PROMPT = "Reply with exactly: OK"
_MODEL_CACHE_TTL_SECONDS = 30 * 60

_login_lock = threading.RLock()
_login_process: Optional[subprocess.Popen[str]] = None
_login_state: dict[str, Any] = {
    "session_id": "",
    "status": "idle",
    "auth_url": "",
    "message": "",
    "started_at": "",
    "finished_at": "",
    "stdout_tail": [],
    "stderr_tail": [],
}
_model_cache: dict[str, Any] = {
    "timestamp": 0.0,
    "verified": False,
    "models": [],
    "diagnostic": "",
}

_latest_warning: Optional[dict[str, Any]] = None


@dataclass
class CodexExecResult:
    ok: bool
    thread_id: str = ""
    message: str = ""
    reasoning: str = ""
    errors: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    stderr: str = ""
    returncode: int = 0

    @property
    def diagnostic(self) -> str:
        parts: list[str] = []
        if self.errors:
            parts.append("; ".join(self.errors))
        if self.stderr.strip():
            parts.append(self.stderr.strip())
        return " | ".join(p for p in parts if p).strip()


def _base_cmd(model: str) -> list[str]:
    cmd: list[str] = [_CODEX_BIN]
    for override in _CODEX_CONFIG_OVERRIDES:
        cmd.extend(["-c", override])
    cmd.extend(
        [
            "exec",
            "--json",
            "--dangerously-bypass-approvals-and-sandbox",
            "-m",
            model.strip() or "gpt-5-codex",
        ]
    )
    return cmd


def _parse_event(line: str) -> Optional[dict[str, Any]]:
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def run_codex_exec(
    prompt: str,
    model: str = "gpt-5-codex",
    resume_thread_id: str = "",
    cwd: Optional[str] = None,
    timeout_seconds: int = 300,
) -> CodexExecResult:
    cmd = _base_cmd(model)
    if resume_thread_id:
        cmd.extend(["resume", resume_thread_id])

    result = CodexExecResult(ok=False)
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return CodexExecResult(
            ok=False,
            errors=["codex executable not found on PATH"],
            returncode=127,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else ""
        return CodexExecResult(
            ok=False,
            errors=[f"codex exec timed out after {timeout_seconds}s"],
            stderr=stderr,
            returncode=124,
        )
    except Exception as exc:
        return CodexExecResult(
            ok=False,
            errors=[f"failed to execute codex: {type(exc).__name__}: {exc}"],
            returncode=1,
        )

    result.returncode = completed.returncode
    result.stderr = completed.stderr or ""

    for line in (completed.stdout or "").splitlines():
        event = _parse_event(line.strip())
        if not event:
            continue
        result.events.append(event)

        event_type = str(event.get("type", ""))
        if event_type == "thread.started":
            result.thread_id = str(event.get("thread_id", "")) or result.thread_id
            continue
        if event_type == "item.completed":
            item = event.get("item", {})
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type", ""))
            text = str(item.get("text", "") or "")
            if item_type == "agent_message" and text:
                result.message = text
            elif item_type == "reasoning" and text:
                result.reasoning = (result.reasoning + "\n" + text).strip()
            continue
        if event_type == "error":
            message = str(event.get("message", "")).strip()
            if message:
                result.errors.append(message)
            continue
        if event_type == "turn.failed":
            err_obj = event.get("error", {})
            if isinstance(err_obj, dict):
                msg = str(err_obj.get("message", "")).strip()
                if msg:
                    result.errors.append(msg)

    if completed.returncode == 0 and result.message:
        result.ok = True
        return result

    if completed.returncode != 0 and not result.errors:
        result.errors.append(f"codex exited with status {completed.returncode}")
    if not result.message and not result.errors:
        result.errors.append("codex returned no assistant message")
    return result


def get_codex_status(timeout_seconds: int = 8) -> dict[str, Any]:
    status = {
        "installed": False,
        "version": "",
        "logged_in": False,
        "auth_mode": "unknown",
        "diagnostic": "",
    }

    if not shutil.which(_CODEX_BIN):
        status["diagnostic"] = "codex-cli not found on PATH"
        return status

    status["installed"] = True
    try:
        version_cmd = [_CODEX_BIN, "--version"]
        version_cp = subprocess.run(
            version_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        version_line = (version_cp.stdout or "").strip().splitlines()
        if version_line:
            status["version"] = version_line[0].strip()
    except Exception as exc:
        status["diagnostic"] = f"failed to read codex version: {exc}"
        return status

    cmd: list[str] = [_CODEX_BIN]
    for override in _CODEX_CONFIG_OVERRIDES:
        cmd.extend(["-c", override])
    cmd.extend(["login", "status"])
    try:
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except Exception as exc:
        status["diagnostic"] = f"failed to check codex auth: {exc}"
        return status

    text = "\n".join(
        [line for line in [(cp.stdout or "").strip(), (cp.stderr or "").strip()] if line]
    ).strip()
    lowered = text.lower()

    if cp.returncode == 0:
        status["logged_in"] = True
        if "chatgpt" in lowered:
            status["auth_mode"] = "chatgpt"
        elif "api key" in lowered:
            status["auth_mode"] = "api_key"
        else:
            status["auth_mode"] = "unknown"
        status["diagnostic"] = ""
    else:
        status["logged_in"] = False
        status["auth_mode"] = "none"
        status["diagnostic"] = text or f"codex login status exited with {cp.returncode}"

    return status


def set_latest_warning(
    role: str,
    message: str,
    fallback_provider: str = "",
    fallback_model: str = "",
    diagnostic: str = "",
) -> None:
    global _latest_warning
    _latest_warning = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "message": message,
        "fallback_provider": fallback_provider,
        "fallback_model": fallback_model,
        "diagnostic": diagnostic,
    }


def get_latest_warning() -> Optional[dict[str, Any]]:
    if not _latest_warning:
        return None
    return dict(_latest_warning)


def _format_model_label(model_id: str) -> str:
    parts: list[str] = []
    for part in model_id.split("-"):
        token = part.strip().lower()
        if token == "gpt":
            parts.append("GPT")
        elif token == "codex":
            parts.append("Codex")
        elif token == "max":
            parts.append("Max")
        elif token == "mini":
            parts.append("Mini")
        elif token.replace(".", "", 1).isdigit():
            parts.append(part)
        else:
            parts.append(part.capitalize())
    return "-".join(parts)


def _default_codex_models() -> list[dict[str, Any]]:
    return [
        {"value": model, "label": _format_model_label(model), "available": None}
        for model in _CODEX_MODEL_CANDIDATES
    ]


def get_cached_codex_models() -> dict[str, Any]:
    with _login_lock:
        if _model_cache.get("models"):
            return {
                "models": list(_model_cache.get("models", [])),
                "verified": bool(_model_cache.get("verified", False)),
                "diagnostic": str(_model_cache.get("diagnostic", "")),
            }
    return {"models": _default_codex_models(), "verified": False, "diagnostic": ""}


def get_codex_models(force_refresh: bool = False) -> dict[str, Any]:
    now = time.time()
    with _login_lock:
        cache_age = now - float(_model_cache.get("timestamp", 0.0))
        if (
            not force_refresh
            and _model_cache.get("models")
            and cache_age < _MODEL_CACHE_TTL_SECONDS
        ):
            return {
                "models": list(_model_cache.get("models", [])),
                "verified": bool(_model_cache.get("verified", False)),
                "diagnostic": str(_model_cache.get("diagnostic", "")),
            }

    status = get_codex_status()
    if not status.get("logged_in"):
        result = {
            "models": _default_codex_models(),
            "verified": False,
            "diagnostic": "Log in to ChatGPT subscription to verify available Codex models.",
        }
        with _login_lock:
            _model_cache["timestamp"] = now
            _model_cache["verified"] = False
            _model_cache["models"] = list(result["models"])
            _model_cache["diagnostic"] = result["diagnostic"]
        return result

    available: list[dict[str, Any]] = []
    unavailable: list[str] = []
    diagnostics: list[str] = []
    for model in _CODEX_MODEL_CANDIDATES:
        probe = run_codex_exec(
            prompt=_MODEL_PROBE_PROMPT,
            model=model,
            timeout_seconds=25,
        )
        if probe.ok:
            available.append(
                {"value": model, "label": _format_model_label(model), "available": True}
            )
        else:
            unavailable.append(model)
            if probe.errors:
                err = "; ".join(probe.errors[:2])
                diagnostics.append(f"{model}: {err[:220]}")
            elif probe.diagnostic:
                diagnostics.append(f"{model}: {probe.diagnostic[:220]}")

    models = available[:]
    if not models:
        models = _default_codex_models()
        for item in models:
            item["available"] = None
        diagnostic = (
            "Could not verify Codex model availability. Showing fallback model list."
        )
    else:
        for model in unavailable:
            models.append(
                {"value": model, "label": _format_model_label(model), "available": False}
            )
        diagnostic = (
            "Unavailable: " + ", ".join(unavailable)
            if unavailable
            else "Model availability verified."
        )
    if diagnostics:
        diagnostic = f"{diagnostic} Details: {' | '.join(diagnostics[:3])}"

    result = {
        "models": models,
        "verified": True,
        "diagnostic": diagnostic,
    }
    with _login_lock:
        _model_cache["timestamp"] = now
        _model_cache["verified"] = True
        _model_cache["models"] = list(models)
        _model_cache["diagnostic"] = diagnostic
    return result


def _append_tail(buffer: list[str], line: str, max_len: int = 20) -> list[str]:
    line = line.strip()
    if not line:
        return buffer
    buffer.append(line)
    if len(buffer) > max_len:
        buffer = buffer[-max_len:]
    return buffer


def _extract_auth_url(text: str) -> str:
    matches = re.findall(r"https://auth\.openai\.com/\S+", text)
    return matches[0].strip() if matches else ""


def _snapshot_login_state() -> dict[str, Any]:
    with _login_lock:
        snapshot = {
            "session_id": str(_login_state.get("session_id", "")),
            "status": str(_login_state.get("status", "idle")),
            "auth_url": str(_login_state.get("auth_url", "")),
            "message": str(_login_state.get("message", "")),
            "started_at": str(_login_state.get("started_at", "")),
            "finished_at": str(_login_state.get("finished_at", "")),
            "stdout_tail": list(_login_state.get("stdout_tail", [])),
            "stderr_tail": list(_login_state.get("stderr_tail", [])),
        }
        process = _login_process
    if process and process.poll() is None:
        snapshot["running"] = True
    else:
        snapshot["running"] = False
    return snapshot


def _read_login_stream(stream_name: str, pipe: Any) -> None:
    if pipe is None:
        return
    try:
        for raw_line in iter(pipe.readline, ""):
            line = raw_line.strip()
            if not line:
                continue
            with _login_lock:
                tail_key = "stdout_tail" if stream_name == "stdout" else "stderr_tail"
                tail = list(_login_state.get(tail_key, []))
                _login_state[tail_key] = _append_tail(tail, line)
                url = _extract_auth_url(line)
                if url and not _login_state.get("auth_url"):
                    _login_state["auth_url"] = url
                    if _login_state.get("status") in ("starting", "idle"):
                        _login_state["status"] = "waiting_browser"
                        _login_state["message"] = "Open the login page and complete authorization."
    except Exception:
        return
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def _wait_login_process(proc: subprocess.Popen[str], session_id: str) -> None:
    returncode = proc.wait()
    status = get_codex_status()
    with _login_lock:
        if _login_state.get("session_id") != session_id:
            return
        _login_state["finished_at"] = datetime.now(timezone.utc).isoformat()
        if returncode == 0 and status.get("logged_in"):
            _login_state["status"] = "completed"
            _login_state["message"] = "ChatGPT subscription connected."
        elif _login_state.get("status") == "cancelled":
            _login_state["message"] = "Login cancelled."
        else:
            _login_state["status"] = "failed"
            tail = _login_state.get("stderr_tail") or _login_state.get("stdout_tail") or []
            if tail:
                _login_state["message"] = str(tail[-1])
            elif returncode != 0:
                _login_state["message"] = f"codex login exited with status {returncode}"
            else:
                _login_state["message"] = "ChatGPT login failed."

        global _login_process
        _login_process = None


def start_codex_login() -> dict[str, Any]:
    with _login_lock:
        global _login_process
        if _login_process and _login_process.poll() is None:
            current = _snapshot_login_state()
            current["already_running"] = True
            return current

    cmd: list[str] = [_CODEX_BIN]
    for override in _CODEX_CONFIG_OVERRIDES:
        cmd.extend(["-c", override])
    cmd.append("login")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
    except FileNotFoundError:
        return {
            "session_id": "",
            "status": "failed",
            "auth_url": "",
            "message": "codex executable not found on PATH",
            "running": False,
        }
    except Exception as exc:
        return {
            "session_id": "",
            "status": "failed",
            "auth_url": "",
            "message": f"failed to start codex login: {exc}",
            "running": False,
        }

    session_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    with _login_lock:
        _login_process = proc
        _login_state["session_id"] = session_id
        _login_state["status"] = "starting"
        _login_state["auth_url"] = ""
        _login_state["message"] = "Starting browser login..."
        _login_state["started_at"] = started_at
        _login_state["finished_at"] = ""
        _login_state["stdout_tail"] = []
        _login_state["stderr_tail"] = []

    threading.Thread(
        target=_read_login_stream, args=("stdout", proc.stdout), daemon=True
    ).start()
    threading.Thread(
        target=_read_login_stream, args=("stderr", proc.stderr), daemon=True
    ).start()
    threading.Thread(
        target=_wait_login_process, args=(proc, session_id), daemon=True
    ).start()

    deadline = time.time() + 2.5
    while time.time() < deadline:
        snapshot = _snapshot_login_state()
        if snapshot.get("auth_url"):
            break
        if not snapshot.get("running"):
            break
        time.sleep(0.05)
    return _snapshot_login_state()


def cancel_codex_login() -> dict[str, Any]:
    with _login_lock:
        proc = _login_process
        if not proc or proc.poll() is not None:
            state = _snapshot_login_state()
            state["message"] = state.get("message") or "No active login session."
            return state
        _login_state["status"] = "cancelled"
        _login_state["message"] = "Cancelling login..."
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    return _snapshot_login_state()


def logout_codex() -> dict[str, Any]:
    cmd: list[str] = [_CODEX_BIN]
    for override in _CODEX_CONFIG_OVERRIDES:
        cmd.extend(["-c", override])
    cmd.append("logout")
    try:
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "message": "codex executable not found on PATH",
            "status": get_codex_status(),
        }
    except Exception as exc:
        return {"ok": False, "message": str(exc), "status": get_codex_status()}

    output = "\n".join(
        [line for line in [(cp.stdout or "").strip(), (cp.stderr or "").strip()] if line]
    ).strip()
    with _login_lock:
        _model_cache["timestamp"] = 0.0
        _model_cache["verified"] = False
        _model_cache["models"] = []
        _model_cache["diagnostic"] = ""
    return {
        "ok": cp.returncode == 0,
        "message": output or ("Logged out." if cp.returncode == 0 else "Logout failed."),
        "status": get_codex_status(),
    }


def get_codex_login_state() -> dict[str, Any]:
    state = _snapshot_login_state()
    if not state.get("running"):
        status = get_codex_status()
        if status.get("logged_in"):
            if state.get("status") in ("idle", "starting", "waiting_browser", "failed"):
                state["status"] = "completed"
            if not state.get("message"):
                state["message"] = "ChatGPT subscription connected."
        elif state.get("status") == "completed":
            state["status"] = "idle"
            state["message"] = "Not logged in."
    return state
