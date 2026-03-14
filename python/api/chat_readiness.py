import urllib.request
from urllib.error import URLError

import models
from python.helpers import settings, startup_selector
from python.helpers.api import ApiHandler, Request, Response


class ChatReadiness(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    def _check_ollama(self, api_base: str) -> tuple[bool, str]:
        base = (api_base or "").strip() or "http://localhost:11434"
        url = f"{base.rstrip('/')}/api/tags"
        try:
            with urllib.request.urlopen(url, timeout=2.5) as resp:  # nosec B310 - configured local provider URL
                if 200 <= getattr(resp, "status", 200) < 300:
                    return True, f"Ollama reachable at {base}"
                return False, f"Ollama check returned HTTP {getattr(resp, 'status', 'unknown')}"
        except URLError as e:
            return False, f"Ollama unreachable at {base}: {e}"
        except Exception as e:
            return False, f"Ollama health check failed: {e}"

    async def process(self, input: dict, request: Request) -> dict | Response:
        cfg = settings.get_settings()

        provider = str(cfg.get("chat_model_provider", "") or "").strip().lower()
        model_name = str(cfg.get("chat_model_name", "") or "").strip()
        api_base = str(cfg.get("chat_model_api_base", "") or "").strip()
        backend = str(cfg.get("chat_execution_backend", "native") or "native").strip().lower()

        checks: list[dict[str, str | bool]] = []

        checks.append(
            {
                "id": "chat_provider",
                "ok": bool(provider),
                "detail": f"provider={provider or 'unset'}",
            }
        )
        checks.append(
            {
                "id": "chat_model",
                "ok": bool(model_name),
                "detail": f"model={model_name or 'unset'}",
            }
        )

        local_providers = {"ollama", "huggingface", "local", "lmstudio", "lm_studio"}
        requires_key = provider not in local_providers
        if requires_key:
            key = str(models.get_api_key(provider) or "").strip()
            ok = key not in {"", "None", "NA"}
            checks.append(
                {
                    "id": "provider_api_key",
                    "ok": ok,
                    "detail": "API key configured" if ok else f"Missing API key for provider '{provider}'",
                }
            )

        if provider == "ollama":
            ok, detail = self._check_ollama(api_base)
            checks.append({"id": "ollama_connectivity", "ok": ok, "detail": detail})

        if backend in {"codex", "claude_code"}:
            ok_backend, detail_backend = startup_selector.backend_ready(backend)
            checks.append(
                {
                    "id": "execution_backend",
                    "ok": ok_backend,
                    "detail": detail_backend,
                }
            )
        else:
            checks.append(
                {
                    "id": "execution_backend",
                    "ok": True,
                    "detail": "Native backend active",
                }
            )

        ready = all(bool(c.get("ok")) for c in checks)
        if ready:
            message = "Chat runtime is ready."
        else:
            failures = [str(c.get("detail", "")) for c in checks if not bool(c.get("ok"))]
            message = "Chat runtime is not ready: " + "; ".join(failures)

        return {
            "ready": ready,
            "message": message,
            "checks": checks,
            "provider": provider,
            "model": model_name,
            "backend": backend,
            "startup_selection": startup_selector.get_startup_selection_state(),
        }
