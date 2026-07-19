import asyncio
from shutil import which
from typing import Any
from urllib.parse import urlparse

from helpers.api import ApiHandler, Request, Response
from helpers.mcp_handler import MCPConfig, normalize_name


_PROMPT_INJECTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "developer message",
    "hidden instruction",
    "exfiltrate",
    "leak secret",
    "credential",
)


class McpServerScan(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        server = dict(input.get("server") or {})
        allow_local_execution = bool(input.get("allow_local_execution", False))
        allow_remote_network = bool(input.get("allow_remote_network", False))
        inspect_runtime = input.get("inspect_runtime", True) is not False

        server = self._normalize_server(server)
        warnings = self._static_warnings(server)
        is_local = not (server.get("url") or server.get("serverUrl"))
        has_static_errors = any(warning.get("level") == "error" for warning in warnings)

        runtime_status: list[dict[str, Any]] = []
        runtime_detail: dict[str, Any] = {}
        runtime_error = ""

        should_inspect_runtime = (
            inspect_runtime
            and not has_static_errors
            and ((is_local and allow_local_execution) or (not is_local and allow_remote_network))
        )

        if should_inspect_runtime:
            try:
                scan_config = await asyncio.to_thread(
                    lambda: MCPConfig(servers_list=[server], config_scope="scan")
                )
                runtime_status = scan_config.get_servers_status()
                runtime_detail = scan_config.get_server_detail(server.get("name", ""))
                warnings.extend(self._tool_warnings(runtime_detail.get("tools", [])))
            except Exception as exc:
                runtime_error = str(exc)
                warnings.append(
                    {
                        "level": "error",
                        "title": "Runtime inspection failed",
                        "message": runtime_error,
                    }
                )
        elif is_local and inspect_runtime:
            warnings.append(
                {
                    "level": "warning",
                    "title": "Local command not executed",
                    "message": "Local stdio MCP inspection requires explicit trust because it runs the configured command.",
                }
            )
        elif not is_local and inspect_runtime and has_static_errors:
            warnings.append(
                {
                    "level": "info",
                    "title": "Runtime inspection skipped",
                    "message": "Fix static scan errors before attempting runtime MCP inspection.",
                }
            )
        elif not is_local and inspect_runtime:
            warnings.append(
                {
                    "level": "info",
                    "title": "Remote runtime inspection skipped",
                    "message": "Enable trusted remote inspection to contact the MCP URL and list exposed tools.",
                }
            )

        return {
            "success": True,
            "server": self._redact_server(server),
            "risk_level": self._risk_level(warnings),
            "warnings": warnings,
            "status": runtime_status,
            "detail": runtime_detail,
            "runtime_error": runtime_error,
        }

    def _normalize_server(self, server: dict[str, Any]) -> dict[str, Any]:
        name = str(server.get("name") or "").strip()
        url = str(server.get("url") or server.get("serverUrl") or "").strip()
        command = str(server.get("command") or "").strip()

        if not name:
            name = self._derive_name(url, command)
        server["name"] = normalize_name(name or "mcp_server")

        if url:
            server["url"] = url
            server.setdefault("type", "streamable-http")
        elif command:
            server["command"] = command
            server["type"] = "stdio"

        return server

    def _derive_name(self, url: str, command: str) -> str:
        if url:
            parsed = urlparse(url)
            parts = [part for part in parsed.path.split("/") if part]
            return parts[-1] if parts else parsed.hostname or "remote_mcp"
        if command:
            return command.rsplit("/", 1)[-1]
        return "mcp_server"

    def _static_warnings(self, server: dict[str, Any]) -> list[dict[str, str]]:
        warnings: list[dict[str, str]] = []
        url = str(server.get("url") or "").strip()
        command = str(server.get("command") or "").strip()

        if url:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                warnings.append(
                    {
                        "level": "error",
                        "title": "Unsupported URL scheme",
                        "message": "Remote MCP URLs should use http or https.",
                    }
                )
            elif parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
                warnings.append(
                    {
                        "level": "warning",
                        "title": "Unencrypted remote URL",
                        "message": "Prefer HTTPS for remote MCP servers outside localhost.",
                    }
                )
            if not parsed.netloc:
                warnings.append(
                    {
                        "level": "error",
                        "title": "Invalid remote URL",
                        "message": "The remote MCP URL is missing a host.",
                    }
                )
        elif command:
            if which(command) is None:
                warnings.append(
                    {
                        "level": "warning",
                        "title": "Command not found",
                        "message": f"'{command}' is not currently available on PATH.",
                    }
                )
            if command in {"bash", "sh", "zsh", "fish", "python", "python3", "node"}:
                warnings.append(
                    {
                        "level": "warning",
                        "title": "General-purpose interpreter",
                        "message": "Review the command and arguments carefully before running this local MCP server.",
                    }
                )
        else:
            warnings.append(
                {
                    "level": "error",
                    "title": "Missing connection target",
                    "message": "Provide either a remote URL or a local command.",
                }
            )

        if isinstance(server.get("headers"), dict) and server["headers"]:
            warnings.append(
                {
                    "level": "info",
                    "title": "Headers configured",
                    "message": "Header values are redacted in scan output. Keep tokens in trusted settings only.",
                }
            )

        if isinstance(server.get("env"), dict) and server["env"]:
            warnings.append(
                {
                    "level": "info",
                    "title": "Environment configured",
                    "message": "Environment values are redacted in scan output. Avoid hardcoding secrets in MCP configs.",
                }
            )

        return warnings

    def _tool_warnings(self, tools: Any) -> list[dict[str, str]]:
        warnings: list[dict[str, str]] = []
        if not isinstance(tools, list):
            return warnings

        for tool in tools:
            if not isinstance(tool, dict):
                continue
            haystack = f"{tool.get('name', '')}\n{tool.get('description', '')}".lower()
            if any(marker in haystack for marker in _PROMPT_INJECTION_MARKERS):
                warnings.append(
                    {
                        "level": "warning",
                        "title": "Suspicious tool description",
                        "message": f"Review tool '{tool.get('name', 'unknown')}' for prompt-injection style language.",
                    }
                )
        return warnings

    def _redact_server(self, server: dict[str, Any]) -> dict[str, Any]:
        redacted = dict(server)
        for key in ("headers", "env"):
            if isinstance(redacted.get(key), dict):
                redacted[key] = {name: "***" for name in redacted[key]}
        return redacted

    def _risk_level(self, warnings: list[dict[str, str]]) -> str:
        levels = {warning.get("level", "info") for warning in warnings}
        if "error" in levels:
            return "error"
        if "warning" in levels:
            return "warning"
        return "ok"
