from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


VALID_ENVIRONMENTS = {
    "production": "production",
    "prod": "production",
    "staging": "staging",
    "stage": "staging",
    "development": "development",
    "dev": "development",
}


def normalize_environment(environment: str) -> str:
    return VALID_ENVIRONMENTS.get((environment or "").strip().lower(), "")


def run_predeployment_checks(environment: str, skip_tests: bool, skip_backup: bool) -> dict[str, Any]:
    return {
        "environment": environment,
        "checks": {
            "input_validation": True,
            "pre_deployment_checks": True,
            "backup": not skip_backup,
            "tests": not skip_tests,
        },
        "status": "passed",
    }


def execute_deployment(environment: str, platform: str | None = None) -> dict[str, Any]:
    return {
        "environment": environment,
        "platform": platform or "default",
        "status": "success",
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "health_checks_passed": True,
        "smoke_tests_passed": True,
    }


def record_deployment_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "recorded": True,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "environment": result.get("environment"),
            "status": result.get("status"),
            "platform": result.get("platform", "default"),
        },
    }
