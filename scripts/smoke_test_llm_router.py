#!/usr/bin/env python3
"""
LLM Router API Smoke Test Script

Hits all 11 LLM Router endpoints on a running instance and validates
response structure, key casing, and HTTP-level success.

Usage:
    python scripts/smoke_test_llm_router.py                           # default localhost:50080
    python scripts/smoke_test_llm_router.py --base-url http://host:port
    python scripts/smoke_test_llm_router.py --skip-state-changing      # skip SET/SWITCH calls
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package not found. Install with: pip install requests")
    sys.exit(1)


# ── Config ───────────────────────────────────────────────────────────────────


@dataclass
class TestResult:
    endpoint: str
    passed: bool
    status_code: int = 0
    response_time_ms: float = 0
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ── CSRF & Session ──────────────────────────────────────────────────────────


def get_session(base_url: str) -> requests.Session:
    """Create a session with CSRF token."""
    session = requests.Session()

    # Try to get CSRF token
    try:
        resp = session.get(
            f"{base_url}/csrf_token",
            headers={"Origin": base_url},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token", "")
            if token:
                session.headers.update({"X-CSRF-Token": token})
                print(f"  CSRF token acquired: {token[:20]}...")
            else:
                print("  CSRF token empty (auth may be disabled)")
        else:
            print(f"  CSRF endpoint returned {resp.status_code} (may not require CSRF)")
    except Exception as e:
        print(f"  CSRF token fetch failed: {e} (continuing without CSRF)")

    session.headers.update(
        {
            "Content-Type": "application/json",
            "Origin": base_url,
        }
    )
    return session


# ── Key Validators ──────────────────────────────────────────────────────────


def assert_keys(data: dict, required_keys: list[str], path: str = "") -> list[str]:
    """Check that all required keys exist. Returns list of error messages."""
    errors = []
    for key in required_keys:
        parts = key.split(".")
        obj = data
        for i, part in enumerate(parts):
            if not isinstance(obj, dict):
                errors.append(f"{path}{'.'.join(parts[:i])} is not a dict (can't access .{part})")
                break
            if part not in obj:
                errors.append(f"Missing key: {path}{key}")
                break
            obj = obj[part]
    return errors


def assert_no_snake_keys(data: dict, keys: list[str], path: str = "") -> list[str]:
    """Verify snake_case keys are NOT present (should be camelCase).

    Supports dotted paths through dicts. For arrays, use '[]' to check
    the first element, e.g. 'models.[].display_name'.
    """
    errors = []
    for key in keys:
        parts = key.split(".")
        obj = data
        found = True
        for part in parts:
            if part == "[]":
                if isinstance(obj, list) and len(obj) > 0:
                    obj = obj[0]
                else:
                    found = False
                    break
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                found = False
                break
        if found:
            errors.append(f"Found snake_case key that should be camelCase: {path}{key}")
    return errors


# ── Endpoint Definitions ────────────────────────────────────────────────────


ENDPOINTS = [
    {
        "name": "llm_router_dashboard",
        "payload": {},
        "required_keys": [
            "success",
            "models",
            "models.byProvider",
            "models.totalCount",
            "models.localCount",
            "models.cloudCount",
            "defaults",
            "usage",
            "usage.lastHour",
            "usage.last24h",
            "usage.lastHour.calls",
            "usage.lastHour.costUsd",
            "usage.last24h.calls",
            "usage.last24h.costUsd",
        ],
        "forbidden_snake_keys": [
            "models.by_provider",
            "models.total_count",
            "models.local_count",
            "models.cloud_count",
            "usage.last_hour",
            "usage.last_24h",
            "usage.lastHour.cost_usd",
            "usage.last24h.cost_usd",
            "usage.last24h.by_model",
        ],
        "state_changing": False,
    },
    {
        "name": "llm_router_models",
        "payload": {},
        "required_keys": ["success", "models", "count"],
        "forbidden_snake_keys": [
            "models.[].display_name",
            "models.[].is_local",
            "models.[].context_length",
            "models.[].cost_per_1k_input",
            "models.[].cost_per_1k_output",
            "models.[].size_gb",
            "models.[].avg_latency_ms",
            "models.[].is_available",
            "models.[].priority_score",
        ],
        "state_changing": False,
    },
    {
        "name": "llm_router_get_defaults",
        "payload": {},
        "required_keys": ["success", "defaults"],
        "forbidden_snake_keys": [
            "defaults.chat.model_name",
        ],
        "state_changing": False,
    },
    {
        "name": "llm_router_usage",
        "payload": {"hours": 24},
        "required_keys": ["success", "stats"],
        "forbidden_snake_keys": [
            "stats.total_calls",
            "stats.total_cost",
            "stats.by_model",
            "stats.period_hours",
        ],
        "state_changing": False,
    },
    {
        "name": "llm_router_rules",
        "payload": {"action": "list"},
        "required_keys": ["success", "rules"],
        "state_changing": False,
    },
    {
        "name": "llm_router_select",
        "payload": {"role": "chat", "priority": "quality"},
        "required_keys": ["success"],
        "notes": ["May return success=False if no models registered (expected)"],
        "allow_failure": True,
        "state_changing": False,
    },
    {
        "name": "llm_router_fallback",
        "payload": {"role": "chat"},
        "required_keys": ["success"],
        "notes": ["May return success=False if no models registered (expected)"],
        "allow_failure": True,
        "state_changing": False,
    },
    {
        "name": "llm_router_discover",
        "payload": {},
        "required_keys": ["success", "models", "count", "providers"],
        "state_changing": True,
        "notes": ["Discovers models from Ollama/cloud — may take a few seconds"],
    },
    {
        "name": "llm_router_auto_configure",
        "payload": {},
        "required_keys": ["success"],
        "forbidden_snake_keys": [
            "discovered_models",
            "configured_defaults",
        ],
        "state_changing": True,
        "notes": ["Runs full discovery + default assignment"],
    },
    {
        "name": "llm_router_set_default",
        "payload": {"role": "chat", "provider": "ollama", "modelName": "qwen2.5-coder:3b"},
        "required_keys": ["success"],
        "allow_failure": True,
        "notes": ["Will fail if model not in registry (expected before discover)"],
        "state_changing": True,
    },
    {
        "name": "model_selector_quick_switch",
        "payload": {"provider": "ollama", "modelName": "qwen2.5-coder:3b"},
        "required_keys": ["success"],
        "allow_failure": True,
        "notes": ["Updates settings + router default"],
        "state_changing": True,
    },
    {
        "name": "llm_router_select",
        "payload": {"role": "chat", "priority": "INVALID_JUNK_VALUE"},
        "required_keys": ["success"],
        "allow_failure": True,
        "notes": ["Invalid priority should fallback to BALANCED, not crash"],
        "state_changing": False,
        "custom_name": "llm_router_select (invalid priority)",
    },
    {
        "name": "llm_router_fallback",
        "payload": {"role": "chat", "priority": "NOT_A_REAL_PRIORITY"},
        "required_keys": ["success"],
        "allow_failure": True,
        "notes": ["Invalid priority should fallback to BALANCED, not crash"],
        "state_changing": False,
        "custom_name": "llm_router_fallback (invalid priority)",
    },
    {
        "name": "llm_router_rules",
        "payload": {"action": "add", "rule": {"name": "_smoke_test_rule", "priority": 1, "enabled": True}},
        "required_keys": ["success"],
        "state_changing": True,
        "custom_name": "llm_router_rules (add)",
    },
    {
        "name": "llm_router_rules",
        "payload": {"action": "toggle", "name": "_smoke_test_rule", "enabled": False},
        "required_keys": ["success"],
        "state_changing": True,
        "custom_name": "llm_router_rules (toggle)",
    },
    {
        "name": "llm_router_rules",
        "payload": {"action": "delete", "name": "_smoke_test_rule"},
        "required_keys": ["success"],
        "state_changing": True,
        "custom_name": "llm_router_rules (delete)",
    },
]


# ── Test Runner ─────────────────────────────────────────────────────────────


def test_endpoint(session: requests.Session, base_url: str, endpoint: dict) -> TestResult:
    """Test a single endpoint and return results."""
    name = endpoint["name"]
    display_name = endpoint.get("custom_name", name)
    result = TestResult(endpoint=display_name, passed=False)

    try:
        start = time.monotonic()
        resp = session.post(
            f"{base_url}/{name}",
            json=endpoint["payload"],
            timeout=30,
        )
        result.response_time_ms = (time.monotonic() - start) * 1000
        result.status_code = resp.status_code

        if resp.status_code != 200:
            result.errors.append(f"HTTP {resp.status_code}: {resp.text[:200]}")
            return result

        data = resp.json()

        # Check required keys
        errors = assert_keys(data, endpoint["required_keys"])
        result.errors.extend(errors)

        # Check forbidden snake_case keys (for dashboard)
        forbidden = endpoint.get("forbidden_snake_keys", [])
        snake_errors = assert_no_snake_keys(data, forbidden)
        result.errors.extend(snake_errors)

        # Check success field
        if not data.get("success") and not endpoint.get("allow_failure"):
            result.errors.append(f"success=False: {data.get('error', 'unknown')}")

        # Add notes
        result.notes = endpoint.get("notes", [])

        result.passed = len(result.errors) == 0

    except requests.ConnectionError:
        result.errors.append(f"Connection refused — is the server running at {base_url}?")
    except requests.Timeout:
        result.errors.append("Request timed out (30s)")
    except json.JSONDecodeError:
        result.errors.append(f"Response is not valid JSON: {resp.text[:200]}")
    except Exception as e:
        result.errors.append(f"Unexpected error: {e}")

    return result


def run_all_tests(base_url: str, skip_state: bool = False) -> list[TestResult]:
    """Run all endpoint tests."""
    print(f"\n{'='*60}")
    print("  LLM Router API Smoke Tests")
    print(f"  Base URL: {base_url}")
    print(f"  Skip state-changing: {skip_state}")
    print(f"{'='*60}\n")

    print("Setting up session...")
    session = get_session(base_url)
    print()

    results = []
    endpoints = ENDPOINTS
    if skip_state:
        endpoints = [e for e in ENDPOINTS if not e.get("state_changing")]

    for i, endpoint in enumerate(endpoints, 1):
        display_name = endpoint.get("custom_name", endpoint["name"])
        print(f"[{i}/{len(endpoints)}] {display_name}...", end=" ", flush=True)

        result = test_endpoint(session, base_url, endpoint)
        results.append(result)

        if result.passed:
            print(f"PASS ({result.response_time_ms:.0f}ms)")
        else:
            print("FAIL")
            for err in result.errors:
                print(f"      {err}")

        if result.notes:
            for note in result.notes:
                print(f"      Note: {note}")

    return results


def print_summary(results: list[TestResult]):
    """Print test summary."""
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")

    if failed > 0:
        print("\nFailed endpoints:")
        for r in results:
            if not r.passed:
                print(f"  - {r.endpoint}")
                for err in r.errors:
                    print(f"      {err}")

    avg_time = sum(r.response_time_ms for r in results if r.status_code > 0) / max(
        1, sum(1 for r in results if r.status_code > 0)
    )
    print(f"\nAvg response time: {avg_time:.0f}ms")
    print()

    return failed == 0


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="LLM Router API Smoke Tests")
    parser.add_argument(
        "--base-url",
        default="http://localhost:50080",
        help="Base URL of the running instance (default: http://localhost:50080)",
    )
    parser.add_argument(
        "--skip-state-changing",
        action="store_true",
        help="Skip endpoints that modify state (discover, set_default, quick_switch)",
    )
    args = parser.parse_args()

    results = run_all_tests(args.base_url, args.skip_state_changing)
    all_passed = print_summary(results)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
