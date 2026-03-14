"""
Deployment Orchestrator Tool for Agent Jumbo
CI/CD pipeline generation, Docker configuration, and Kubernetes manifests
"""

import asyncio

from python.helpers import files
from python.helpers.tool import Response, Tool


class DeploymentOrchestrator(Tool):
    """
    Agent Jumbo tool for deployment automation.
    Generates CI/CD pipelines, Docker configurations, and Kubernetes manifests.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.deployment_orchestrator.deployment_manager import DeploymentOrchestratorManager

        # Initialize manager
        db_path = files.get_abs_path("./instruments/custom/deployment_orchestrator/data/deployment_orchestrator.db")
        self.manager = DeploymentOrchestratorManager(db_path)

    async def execute(self, **kwargs):
        """Execute deployment orchestrator action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        action_handlers = {
            # Project registration
            "register_project": self._register_project,
            "get_project": self._get_project,
            "list_projects": self._list_projects,
            # CI/CD generation
            "generate_cicd": self._generate_cicd,
            "get_pipeline": self._get_pipeline,
            "list_pipelines": self._list_pipelines,
            # Docker generation
            "generate_docker": self._generate_docker,
            "get_docker_config": self._get_docker_config,
            # Kubernetes generation
            "generate_k8s": self._generate_k8s,
            "get_k8s_manifests": self._get_k8s_manifests,
            # Environment management
            "setup_environment": self._setup_environment,
            "get_environment": self._get_environment,
            "list_environments": self._list_environments,
            # Deployment status
            "get_deployment_dashboard": self._get_deployment_dashboard,
            "health_check": self._health_check,
            "list_deployments": self._list_deployments,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}", break_loop=False
        )

    # ========== Project Registration ==========

    async def _register_project(self):
        """Register a project for deployment management"""
        name = self.args.get("name")
        project_path = self.args.get("project_path")
        project_type = self.args.get("project_type")
        language = self.args.get("language")
        framework = self.args.get("framework")

        if not name or not project_path:
            return Response(message="Error: name and project_path are required", break_loop=False)

        result = self.manager.register_project(
            name=name, project_path=project_path, project_type=project_type, language=language, framework=framework
        )

        lines = ["## Project Registered\n"]
        lines.append(f"**Project ID:** {result['project_id']}")
        lines.append(f"**Name:** {result['name']}")
        lines.append(f"**Path:** {result['project_path']}")
        lines.append(f"**Language:** {result['language']}")
        if result.get("framework"):
            lines.append(f"**Framework:** {result['framework']}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_project(self):
        """Get project details"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.get_project(project_id)

        if not result:
            return Response(message=f"Project not found: {project_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Project: {result['name']}"), break_loop=False)

    async def _list_projects(self):
        """List all registered projects"""
        projects = self.manager.list_projects()

        if not projects:
            return Response(message="No projects registered.", break_loop=False)

        lines = ["## Registered Projects\n"]
        for p in projects:
            lines.append(f"- **{p['name']}** (ID: {p['project_id']})")
            lines.append(f"  Language: {p.get('language', 'N/A')}, Path: {p['project_path']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== CI/CD Generation ==========

    async def _generate_cicd(self):
        """Generate CI/CD pipeline configuration"""
        project_id = self.args.get("project_id")
        platform = self.args.get("platform", "github_actions")
        include_tests = self.args.get("include_tests", True)
        include_lint = self.args.get("include_lint", True)
        include_build = self.args.get("include_build", True)
        deploy_env = self.args.get("deploy_env")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.generate_cicd(
            project_id=project_id,
            platform=platform,
            include_tests=include_tests,
            include_lint=include_lint,
            include_build=include_build,
            deploy_env=deploy_env,
        )

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## CI/CD Pipeline Generated\n"]
        lines.append(f"**Pipeline ID:** {result['pipeline_id']}")
        lines.append(f"**Platform:** {result['platform']}")
        lines.append(f"**Config Path:** {result['config_path']}")
        lines.append("")
        lines.append("### Configuration")
        lines.append("```yaml")
        lines.append(result["config_content"])
        lines.append("```")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_pipeline(self):
        """Get pipeline details"""
        pipeline_id = self.args.get("pipeline_id")

        if not pipeline_id:
            return Response(message="Error: pipeline_id is required", break_loop=False)

        result = self.manager.get_pipeline(pipeline_id)

        if not result:
            return Response(message=f"Pipeline not found: {pipeline_id}", break_loop=False)

        lines = [f"## Pipeline: {result['name']}\n"]
        lines.append(f"**Platform:** {result['platform']}")
        lines.append(f"**Config Path:** {result['config_path']}")
        lines.append("")
        lines.append("### Configuration")
        lines.append("```yaml")
        lines.append(result["config_content"])
        lines.append("```")

        return Response(message="\n".join(lines), break_loop=False)

    async def _list_pipelines(self):
        """List pipelines for a project"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        pipelines = self.manager.list_pipelines(project_id)

        if not pipelines:
            return Response(message="No pipelines found for this project.", break_loop=False)

        lines = ["## CI/CD Pipelines\n"]
        for p in pipelines:
            lines.append(f"- **{p['name']}** (ID: {p['pipeline_id']})")
            lines.append(f"  Platform: {p['platform']}, Status: {p['status']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Docker Generation ==========

    async def _generate_docker(self):
        """Generate Docker configuration"""
        project_id = self.args.get("project_id")
        port = self.args.get("port", 8000)
        include_compose = self.args.get("include_compose", True)
        multi_stage = self.args.get("multi_stage", True)

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.generate_docker(
            project_id=project_id, port=port, include_compose=include_compose, multi_stage=multi_stage
        )

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## Docker Configuration Generated\n"]
        lines.append(f"**Config ID:** {result['config_id']}")
        lines.append("")

        lines.append("### Dockerfile")
        lines.append("```dockerfile")
        lines.append(result["dockerfile"])
        lines.append("```")

        if result.get("docker_compose"):
            lines.append("")
            lines.append("### docker-compose.yml")
            lines.append("```yaml")
            lines.append(result["docker_compose"])
            lines.append("```")

        if result.get("dockerignore"):
            lines.append("")
            lines.append("### .dockerignore")
            lines.append("```")
            lines.append(result["dockerignore"])
            lines.append("```")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_docker_config(self):
        """Get Docker configuration for a project"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.get_docker_config(project_id)

        if not result:
            return Response(message="No Docker configuration found for this project.", break_loop=False)

        lines = ["## Docker Configuration\n"]

        if result.get("dockerfile_content"):
            lines.append("### Dockerfile")
            lines.append("```dockerfile")
            lines.append(result["dockerfile_content"])
            lines.append("```")

        if result.get("compose_content"):
            lines.append("")
            lines.append("### docker-compose.yml")
            lines.append("```yaml")
            lines.append(result["compose_content"])
            lines.append("```")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Kubernetes Generation ==========

    async def _generate_k8s(self):
        """Generate Kubernetes manifests"""
        project_id = self.args.get("project_id")
        replicas = self.args.get("replicas", 2)
        port = self.args.get("port", 8000)
        namespace = self.args.get("namespace", "default")
        include_service = self.args.get("include_service", True)
        include_ingress = self.args.get("include_ingress", False)

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.generate_k8s(
            project_id=project_id,
            replicas=replicas,
            port=port,
            namespace=namespace,
            include_service=include_service,
            include_ingress=include_ingress,
        )

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## Kubernetes Manifests Generated\n"]
        lines.append(f"**Namespace:** {result['namespace']}")
        lines.append(f"**Manifests:** {len(result['manifests'])}")
        lines.append("")

        for manifest in result["manifests"]:
            lines.append(f"### {manifest['type'].title()}")
            lines.append("```yaml")
            lines.append(manifest["content"])
            lines.append("```")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_k8s_manifests(self):
        """Get Kubernetes manifests for a project"""
        project_id = self.args.get("project_id")
        manifest_type = self.args.get("manifest_type")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        manifests = self.manager.get_k8s_manifests(project_id, manifest_type)

        if not manifests:
            return Response(message="No Kubernetes manifests found.", break_loop=False)

        lines = ["## Kubernetes Manifests\n"]
        for m in manifests:
            lines.append(f"### {m['name']} ({m['manifest_type']})")
            lines.append("```yaml")
            lines.append(m["content"])
            lines.append("```")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Environment Management ==========

    async def _setup_environment(self):
        """Set up a deployment environment"""
        project_id = self.args.get("project_id")
        name = self.args.get("name")
        env_type = self.args.get("env_type", "staging")
        config = self.args.get("config", {})

        if not project_id or not name:
            return Response(message="Error: project_id and name are required", break_loop=False)

        result = self.manager.setup_environment(project_id=project_id, name=name, env_type=env_type, config=config)

        lines = ["## Environment Created\n"]
        lines.append(f"**Environment ID:** {result['environment_id']}")
        lines.append(f"**Name:** {result['name']}")
        lines.append(f"**Type:** {result['env_type']}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_environment(self):
        """Get environment details"""
        environment_id = self.args.get("environment_id")

        if not environment_id:
            return Response(message="Error: environment_id is required", break_loop=False)

        result = self.manager.get_environment(environment_id)

        if not result:
            return Response(message=f"Environment not found: {environment_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Environment: {result['name']}"), break_loop=False)

    async def _list_environments(self):
        """List environments for a project"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        environments = self.manager.list_environments(project_id)

        if not environments:
            return Response(message="No environments configured.", break_loop=False)

        lines = ["## Environments\n"]
        for e in environments:
            lines.append(f"- **{e['name']}** (ID: {e['environment_id']})")
            lines.append(f"  Type: {e['env_type']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Deployment Status ==========

    async def _get_deployment_dashboard(self):
        """Get deployment dashboard for a project"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.get_deployment_dashboard(project_id)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = [f"## Deployment Dashboard: {result['project_name']}\n"]
        lines.append(f"**Language:** {result.get('language', 'N/A')}")
        lines.append(f"**Pipelines:** {result['pipelines']}")
        lines.append("")

        lines.append("### Environment Status")
        for env in result["environments"]:
            status_icon = (
                "✅"
                if env["status"] == "completed"
                else "⏳"
                if env["status"] == "pending"
                else "❌"
                if env["status"] == "failed"
                else "⬜"
            )
            lines.append(f"- {status_icon} **{env['environment']}** ({env['env_type']})")
            lines.append(f"  Version: {env.get('latest_version', 'N/A')}, Status: {env['status']}")

        if result["recent_deployments"]:
            lines.append("")
            lines.append("### Recent Deployments")
            for d in result["recent_deployments"][:5]:
                lines.append(f"- {d.get('version', 'N/A')} - {d['status']} ({d['started_at']})")

        return Response(message="\n".join(lines), break_loop=False)

    async def _health_check(self):
        """Check health status of deployments"""
        project_id = self.args.get("project_id")
        environment_id = self.args.get("environment_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.health_check(project_id, environment_id)

        if result.get("status") == "no_deployments":
            return Response(message="No deployments found.", break_loop=False)

        # MOS hook: notify Linear on successful deployment
        if result.get("healthy") and result.get("status") == "completed":
            try:
                from python.helpers.mos_orchestrator import MOSOrchestrator

                asyncio.create_task(
                    MOSOrchestrator.on_deployment_success(
                        project_name=self.args.get("project_id", ""),
                    )
                )
            except Exception:
                pass

        status_icon = "✅" if result.get("healthy") else "❌"
        lines = [f"## Health Check {status_icon}\n"]
        lines.append(f"**Deployment ID:** {result.get('deployment_id')}")
        lines.append(f"**Version:** {result.get('version', 'N/A')}")
        lines.append(f"**Status:** {result['status']}")
        lines.append(f"**Started:** {result.get('started_at')}")
        if result.get("completed_at"):
            lines.append(f"**Completed:** {result['completed_at']}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _list_deployments(self):
        """List recent deployments"""
        project_id = self.args.get("project_id")
        limit = self.args.get("limit", 10)

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        deployments = self.manager.list_deployments(project_id, limit)

        if not deployments:
            return Response(message="No deployments found.", break_loop=False)

        lines = ["## Recent Deployments\n"]
        for d in deployments:
            status_icon = "✅" if d["status"] == "completed" else "⏳" if d["status"] == "pending" else "❌"
            lines.append(f"- {status_icon} **{d.get('version', 'N/A')}** (ID: {d['deployment_id']})")
            lines.append(f"  Status: {d['status']}, Started: {d['started_at']}")
            if d.get("environment_name"):
                lines.append(f"  Environment: {d['environment_name']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Helpers ==========

    def _format_result(self, data: dict, title: str) -> str:
        """Format result dictionary as readable output"""
        lines = [f"## {title}\n"]

        for key, value in data.items():
            if key in ["config_content", "dockerfile_content", "compose_content", "content"]:
                continue  # Skip large content fields in summary
            elif isinstance(value, dict):
                lines.append(f"**{key}:**")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"**{key}:** ({len(value)} items)")
            else:
                lines.append(f"**{key}:** {value}")

        return "\n".join(lines)
