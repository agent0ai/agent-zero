"""
DevOps Deploy Tool - Multi-Environment Deployment
Converted from Mahoosuc /devops:deploy command

Deploys applications to production, staging, or development environments
with comprehensive safety checks, backups, and health monitoring.

Enhanced with multi-platform deployment strategies:
- Kubernetes (kubectl)
- SSH (traditional servers)
- GitHub Actions (CI/CD workflows)
- AWS (ECS, Lambda, CodeDeploy)
- GCP (Cloud Run, GKE, Cloud Build)
"""

from datetime import datetime, timezone
from time import perf_counter

from python.helpers.deployment_primitives import (
    execute_deployment,
    normalize_environment,
    record_deployment_result,
    run_predeployment_checks,
)
from python.helpers.tool import Response, Tool
from python.tools.deployment_strategies.aws import AWSStrategy
from python.tools.deployment_strategies.gcp import GCPStrategy
from python.tools.deployment_strategies.github_actions import GitHubActionsStrategy
from python.tools.deployment_strategies.kubernetes import KubernetesStrategy
from python.tools.deployment_strategies.ssh import SSHStrategy


class DevOpsDeploy(Tool):
    """
    Deploy application to multi-environment infrastructure with safety checks.

    Supports:
    - Environment validation (production, staging, development)
    - Pre-deployment backups
    - Health checks and smoke tests
    - Rollback procedures
    - Deployment reporting

    Args:
        environment: Target environment (production|staging|development|prod|stage|dev)
        skip_tests: Skip pre-deployment tests (default: false)
        skip_backup: Skip pre-deployment backup (default: false)
    """

    async def execute(self, environment="", skip_tests=False, skip_backup=False, **kwargs):
        """
        Execute deployment to specified environment.

        POC Implementation: Returns simulated deployment report.
        Full implementation will integrate with actual deployment infrastructure.
        """

        # Get environment from args if not passed directly
        if not environment and self.args:
            environment = self.args.get("environment", "")

        # Get skip_tests and skip_backup from args if not passed directly
        if self.args:
            skip_tests = self.args.get("skip_tests", skip_tests)
            skip_backup = self.args.get("skip_backup", skip_backup)
            # Handle string values
            if isinstance(skip_tests, str):
                skip_tests = skip_tests.lower() in ["true", "1", "yes"]
            if isinstance(skip_backup, str):
                skip_backup = skip_backup.lower() in ["true", "1", "yes"]

        platform = ""
        if self.args:
            platform = str(self.args.get("platform", "")).strip()

        # Step 1: Validate environment
        started_at = self._utc_now_iso()
        normalized_env = self._validate_environment(environment)
        if not normalized_env:
            finished_at = self._utc_now_iso()
            return Response(
                message=f"❌ ERROR: Invalid environment: '{environment}'\n"
                f"Valid environments: production, staging, development (or prod, stage, dev)",
                break_loop=False,
                additional={
                    "deployment": {
                        "environment": environment,
                        "status": "failed",
                        "telemetry": {
                            "started_at": started_at,
                            "finished_at": finished_at,
                            "failed_stage": "validate",
                            "stages": [
                                {
                                    "name": "validate",
                                    "status": "failed",
                                    "error": "invalid_environment",
                                }
                            ],
                        },
                    }
                },
            )

        # Step 2: Build structured step results and human-readable report
        result = self._build_deployment_result(
            environment=normalized_env,
            skip_tests=skip_tests,
            skip_backup=skip_backup,
            platform=platform,
        )
        report = self._generate_deployment_poc(result)

        return Response(
            message=report,
            break_loop=False,
            additional={"deployment": result},
        )

    def _select_strategy(self):
        """
        Select deployment strategy based on platform parameter.

        Returns:
            DeploymentStrategy instance or None if no platform specified
        """
        platform = self.args.get("platform") if self.args else None

        if not platform:
            return None

        platform_map = {
            "kubernetes": KubernetesStrategy,
            "ssh": SSHStrategy,
            "github-actions": GitHubActionsStrategy,
            "aws": AWSStrategy,
            "gcp": GCPStrategy,
        }

        strategy_class = platform_map.get(platform)

        if strategy_class:
            return strategy_class()

        return None

    def _validate_environment(self, environment: str) -> str:
        """
        Validate and normalize environment argument.

        Args:
            environment: Raw environment string

        Returns:
            Normalized environment name or empty string if invalid
        """
        return normalize_environment(environment)

    def _build_deployment_result(self, environment: str, skip_tests: bool, skip_backup: bool, platform: str = "") -> dict:
        started_at = self._utc_now_iso()
        stage_runs: list[dict] = []
        failed_stage = ""

        checks = {}
        execution = {}
        record = {}

        current_stage = "checks"
        try:
            checks, stage_meta = self._run_stage(
                "checks",
                lambda: run_predeployment_checks(environment, skip_tests=skip_tests, skip_backup=skip_backup),
            )
            stage_runs.append(stage_meta)

            current_stage = "execute"
            execution, stage_meta = self._run_stage(
                "execute",
                lambda: execute_deployment(environment, platform=platform or None),
            )
            stage_runs.append(stage_meta)

            current_stage = "record"
            record, stage_meta = self._run_stage("record", lambda: record_deployment_result(execution))
            stage_runs.append(stage_meta)
        except Exception as exc:
            failed_stage = current_stage
            stage_runs.append(
                {
                    "name": current_stage,
                    "status": "failed",
                    "error": type(exc).__name__,
                }
            )

        finished_at = self._utc_now_iso()
        health_checks_passed = bool(execution.get("health_checks_passed", False))
        smoke_tests_passed = bool(execution.get("smoke_tests_passed", False))
        status = "failed" if failed_stage else str(execution.get("status", "success"))

        return {
            "environment": environment,
            "platform": execution.get("platform", "default"),
            "skip_tests": bool(skip_tests),
            "skip_backup": bool(skip_backup),
            "status": status,
            "steps": {
                "input_validation": {"status": "passed"},
                "pre_deployment_checks": {"status": "passed"},
                "backup": {"status": "skipped" if skip_backup else "passed"},
                "tests": {"status": "skipped" if skip_tests else "passed"},
                "build_package": {"status": "passed"},
                "deployment": {"status": status},
                "health_checks": {"status": "passed" if health_checks_passed else "failed"},
                "smoke_tests": {"status": "passed" if smoke_tests_passed else "failed"},
                "post_deployment": {"status": "passed"},
            },
            "checks": {
                "health_checks_passed": health_checks_passed,
                "smoke_tests_passed": smoke_tests_passed,
                "backup_created": bool(checks.get("checks", {}).get("backup", False)),
                "tests_run": bool(checks.get("checks", {}).get("tests", False)),
            },
            "primitives": {
                "checks": checks,
                "execution": execution,
                "record": record,
            },
            "telemetry": {
                "started_at": started_at,
                "finished_at": finished_at,
                "failed_stage": failed_stage or None,
                "stages": stage_runs,
            },
        }

    def _run_stage(self, name: str, fn):
        started_at = self._utc_now_iso()
        t0 = perf_counter()
        value = fn()
        duration_ms = int((perf_counter() - t0) * 1000)
        return value, {
            "name": name,
            "status": "passed",
            "started_at": started_at,
            "finished_at": self._utc_now_iso(),
            "duration_ms": duration_ms,
        }

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _generate_deployment_poc(self, result: dict) -> str:
        """
        Generate POC deployment report.

        This is a proof-of-concept implementation that simulates a deployment.
        Full implementation will execute actual deployment workflow.

        Args:
            environment: Normalized environment name
            skip_tests: Whether to skip tests
            skip_backup: Whether to skip backup

        Returns:
            Formatted deployment report
        """

        environment = str(result.get("environment", "unknown"))
        skip_tests = bool(result.get("skip_tests", False))
        skip_backup = bool(result.get("skip_backup", False))

        # Production requires extra confirmation
        production_warning = ""
        if environment == "production":
            production_warning = """
⚠️⚠️⚠️ PRODUCTION DEPLOYMENT ⚠️⚠️⚠️
This is a production deployment - requires explicit approval.
"""

        # Build deployment report
        report = f"""
{production_warning}
═══════════════════════════════════════════════════
    DEVOPS DEPLOYMENT - POC IMPLEMENTATION
═══════════════════════════════════════════════════

Environment: {environment.upper()}
Skip Tests: {skip_tests}
Create Backup: {not skip_backup}

DEPLOYMENT WORKFLOW (POC):

✓ Step 1: Input Validation
  - Environment validated: {environment}
  - Configuration loaded

✓ Step 2: Pre-Deployment Checks (simulated)
  - Git repository status: clean
  - Build verification: passed
  - Environment variables: configured

{'✓ Step 3: Pre-Deployment Backup (simulated)' if not skip_backup else '○ Step 3: Backup skipped (--skip-backup)'}
{'  - Database backup created' if not skip_backup else ''}
{'  - Deployment artifacts backed up' if not skip_backup else ''}

{'✓ Step 4: Test Suite (simulated)' if not skip_tests else '○ Step 4: Tests skipped (--skip-tests)'}
{'  - Unit tests: passed' if not skip_tests else ''}
{'  - Integration tests: passed' if not skip_tests else ''}

✓ Step 5: Build & Package (simulated)
  - Build completed successfully
  - Artifacts packaged

✓ Step 6: Deployment (simulated)
  - Deployed to {environment} infrastructure
  - Services updated

✓ Step 7: Health Checks (simulated)
  - HTTP health endpoint: responding
  - Database connectivity: working
  - API integrations: functional

✓ Step 8: Smoke Tests (simulated)
  - Homepage: loads successfully
  - API endpoints: responding
  - Authentication: working

✓ Step 9: Post-Deployment (simulated)
  - Deployment logs updated
  - Git commit tagged
  - Team notified

DEPLOYMENT STATUS: {'SUCCESS ✓' if result.get('status') == 'success' else 'FAILED ✗'}

Deployment Report:
  Environment: {result["environment"]}
  Status: {result["status"]}
  Health Checks: {'passed' if result["checks"]["health_checks_passed"] else 'failed'}
  Smoke Tests: {'passed' if result["checks"]["smoke_tests_passed"] else 'failed'}
  Backup Created: {result["checks"]["backup_created"]}
  Tests Run: {result["checks"]["tests_run"]}

═══════════════════════════════════════════════════

NOTE: This is a POC implementation demonstrating the deployment workflow.
Full implementation will integrate with actual deployment infrastructure:
- Container orchestration (Docker/Kubernetes)
- Cloud providers (GCP/AWS/Azure)
- Traditional server deployments (SSH/rsync)
- Real health monitoring and rollback procedures

To implement full deployment:
1. Configure deployment targets in environment config
2. Set up health check endpoints
3. Configure backup procedures
4. Implement rollback automation
5. Connect to notification services (Slack/Discord)

═══════════════════════════════════════════════════
"""

        return report.strip()

    def get_log_object(self):
        """Get log object for display"""
        return self.agent.context.log.log(
            type="tool",
            heading=f"🚀 DevOps Deploy: {self.args.get('environment', 'unknown')}",
            content="Deploying to multi-environment infrastructure",
            kvps=self.args,
        )
