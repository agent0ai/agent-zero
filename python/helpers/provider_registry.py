import hashlib
import json
import os
import tempfile
from typing import Any, Dict, Optional
import urllib.error
import urllib.parse
import urllib.request

from python.helpers import files
from python.helpers.print_style import PrintStyle


REGISTRY_URL = os.environ.get(
    "A0_PROVIDER_REGISTRY_URL",
    "https://raw.githubusercontent.com/agent0ai/a0-providers/main/registry.json",
)
REGISTRY_CACHE_PATH = "conf/provider_registry_cache.json"
PROVIDERS_CONFIG_PATH = "conf/model_providers.yaml"
REQUEST_TIMEOUT = 10
USER_AGENT = "agent-zero-provider-registry"


def update_model_providers() -> None:
    try:
        _update_model_providers()
    except Exception as exc:
        PrintStyle.warning(f"Provider registry update failed: {exc}")


def _update_model_providers() -> None:
    cache = _load_cache()
    registry_payload, etag = _fetch_registry(cache, use_etag=True)

    if registry_payload is None:
        if files.exists(PROVIDERS_CONFIG_PATH):
            return
        registry_payload, etag = _fetch_registry(cache, use_etag=False)
        if registry_payload is None:
            return

    registry = _parse_registry(registry_payload)
    if registry is None:
        return

    files = registry.get("files", [])
    if not files or not isinstance(files, list):
        return
    
    provider_file = files[0]
    registry_sha = provider_file.get("sha256")
    registry_path = provider_file.get("path")
    if not registry_sha or not registry_path:
        return

    local_sha = _hash_local_file(PROVIDERS_CONFIG_PATH)
    if local_sha and local_sha == registry_sha:
        _save_cache(
            {
                **cache,
                "etag": etag or cache.get("etag"),
                "sha256": registry_sha,
                "path": registry_path,
            }
        )
        return

    download_url = _resolve_download_url(registry_path)
    provider_payload = _fetch_payload(download_url)
    if provider_payload is None:
        return

    downloaded_sha = _hash_bytes(provider_payload)
    if downloaded_sha != registry_sha:
        PrintStyle.warning(
            "Provider registry hash mismatch; skipping update to model_providers.yaml."
        )
        return

    _write_providers_config(provider_payload)
    _save_cache(
        {
            **cache,
            "etag": etag or cache.get("etag"),
            "sha256": registry_sha,
            "path": registry_path,
        }
    )


def _fetch_registry(cache: Dict[str, Any], use_etag: bool) -> tuple[Optional[bytes], Optional[str]]:
    headers = {"User-Agent": USER_AGENT}
    if use_etag and cache.get("etag"):
        headers["If-None-Match"] = cache["etag"]

    request = urllib.request.Request(REGISTRY_URL, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = response.read()
            etag = response.headers.get("ETag")
            return payload, etag
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return None, cache.get("etag")
        return None, cache.get("etag")
    except urllib.error.URLError:
        return None, cache.get("etag")


def _fetch_payload(url: str) -> Optional[bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return response.read()
    except urllib.error.URLError:
        return None


def _parse_registry(payload: bytes) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _resolve_download_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = REGISTRY_URL.rsplit("/", 1)[0] + "/"
    return urllib.parse.urljoin(base, path)


def _hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _hash_local_file(relative_path: str) -> Optional[str]:
    if not files.exists(relative_path):
        return None
    abs_path = files.get_abs_path(relative_path)
    hasher = hashlib.sha256()
    with open(abs_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_providers_config(payload: bytes) -> None:
    files.make_dirs(PROVIDERS_CONFIG_PATH)
    target_path = files.get_abs_path(PROVIDERS_CONFIG_PATH)
    target_dir = os.path.dirname(target_path)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=target_dir) as handle:
        handle.write(payload)
        temp_name = handle.name
    os.replace(temp_name, target_path)


def _load_cache() -> Dict[str, Any]:
    cache_path = files.get_abs_path(REGISTRY_CACHE_PATH)
    try:
        with open(cache_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    files.make_dirs(REGISTRY_CACHE_PATH)
    cache_path = files.get_abs_path(REGISTRY_CACHE_PATH)
    with open(cache_path, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=2, sort_keys=True)
        handle.write("\n")
