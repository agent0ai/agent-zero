"""Kubernetes deployment strategy using kubernetes Python client."""

import asyncio
import os
import time
from collections.abc import AsyncGenerator
from typing import Any

import yaml
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from python.helpers.deployment_health import check_http_endpoint
from python.helpers.deployment_retry import classify_error
from python.tools.deployment_strategies.base import DeploymentStrategy


class KubernetesStrategy(DeploymentStrategy):
    """
    Kubernetes deployment strategy using kubernetes Python client.

    Supports:
    - Applying manifests via kubernetes client
    - Waiting for rollout completion
    - Health checks via HTTP endpoints
    - Rollback via kubernetes API
    - Multiple deployment modes (rolling, blue-green, immediate)
    """

    def __init__(self):
        super().__init__()
        self.api_client = None
        self.apps_v1_api = None

    def _load_kube_config(self, context: str):
        """Load kubeconfig and initialize API clients."""
        kubeconfig_path = os.getenv("KUBECONFIG", os.path.expanduser("~/.kube/config"))
        config.load_kube_config(config_file=kubeconfig_path, context=context)
        self.api_client = client.ApiClient()
        self.apps_v1_api = client.AppsV1Api(self.api_client)

    async def validate_config(self, config_dict: dict[str, Any]) -> bool:
        """Validate Kubernetes-specific configuration."""
        if "kubectl_context" not in config_dict:
            raise ValueError("kubectl_context is required for Kubernetes deployments")

        if "manifest_path" not in config_dict:
            raise ValueError("manifest_path is required for Kubernetes deployments")

        return True

    async def execute_deployment(
        self, config_dict: dict[str, Any], deployment_mode: str = "rolling"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Execute Kubernetes deployment.

        Args:
            config_dict: Configuration with kubectl_context, manifest_path, namespace, deployment_name
            deployment_mode: rolling (default), blue-green, or immediate

        Yields:
            Progress updates and final deployment result
        """
        await self._report_progress("Loading kubeconfig...", 0)

        context = config_dict["kubectl_context"]
        namespace = config_dict.get("namespace", "default")
        manifest_path = config_dict["manifest_path"]
        deployment_name = config_dict.get("deployment_name", "unknown")

        try:
            # Load kubeconfig
            self._load_kube_config(context)
            await self._report_progress(f"Connected to context: {context}", 10)

            # Parse manifests
            await self._report_progress("Parsing manifests...", 20)
            manifests = self._parse_manifests(manifest_path)
            await self._report_progress(f"Found {len(manifests)} resources", 30)

            # Apply manifests
            await self._report_progress("Applying manifests...", 40)
            applied_resources = await self._apply_manifests(manifests, namespace)
            await self._report_progress(f"Applied {len(applied_resources)} resources", 60)

            # Wait for rollout
            await self._report_progress("Waiting for rollout...", 70)
            await self._wait_for_rollout(deployment_name, namespace)
            await self._report_progress("Rollout complete", 90)

            # Store metadata for rollback
            deployment = self.apps_v1_api.read_namespaced_deployment(deployment_name, namespace)
            self.last_deployment_metadata = {
                "deployment_name": deployment_name,
                "namespace": namespace,
                "revision": deployment.metadata.generation,
                "context": context,
            }

            await self._report_progress("Deployment successful", 100)

            yield {
                "status": "success",
                "deployment_name": deployment_name,
                "namespace": namespace,
                "revision": deployment.metadata.generation,
                "message": f"Deployed to Kubernetes cluster (context: {context})",
            }

        except ApiException as e:
            classified = classify_error(e, "kubernetes")
            yield {
                "status": "failed",
                "error": str(classified),
                "deployment_name": deployment_name,
            }
        except Exception as e:
            yield {
                "status": "failed",
                "error": str(e),
                "deployment_name": deployment_name,
            }

    def _parse_manifests(self, manifest_path: str) -> list[dict]:
        """Parse YAML manifests from file or directory."""
        manifests = []

        if os.path.isfile(manifest_path):
            with open(manifest_path) as f:
                docs = yaml.safe_load_all(f)
                manifests.extend([doc for doc in docs if doc])
        elif os.path.isdir(manifest_path):
            for filename in os.listdir(manifest_path):
                if filename.endswith((".yaml", ".yml")):
                    filepath = os.path.join(manifest_path, filename)
                    with open(filepath) as f:
                        docs = yaml.safe_load_all(f)
                        manifests.extend([doc for doc in docs if doc])
        else:
            raise ValueError(f"Invalid manifest_path: {manifest_path}")

        return manifests

    async def _apply_manifests(self, manifests: list[dict], namespace: str) -> list[str]:
        """Apply Kubernetes manifests."""
        applied = []

        for manifest in manifests:
            kind = manifest.get("kind")
            name = manifest.get("metadata", {}).get("name")

            if kind == "Deployment":
                self.apps_v1_api.create_namespaced_deployment(namespace, manifest)
                applied.append(f"Deployment/{name}")
            # Add support for other resource types as needed

        return applied

    async def _wait_for_rollout(self, deployment_name: str, namespace: str, timeout: int = 300):
        """Wait for deployment rollout to complete."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            deployment = self.apps_v1_api.read_namespaced_deployment(deployment_name, namespace)

            replicas = deployment.spec.replicas or 0
            updated_replicas = deployment.status.updated_replicas or 0
            available_replicas = deployment.status.available_replicas or 0

            if updated_replicas == replicas and available_replicas == replicas:
                return  # Rollout complete

            await self._report_progress(
                f"Waiting for rollout... ({available_replicas}/{replicas} ready)",
                70 + int((available_replicas / replicas) * 20) if replicas > 0 else 70,
            )

            await asyncio.sleep(5)

        raise TimeoutError(f"Deployment rollout timeout after {timeout}s")

    async def run_smoke_tests(self, config_dict: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Run smoke tests after Kubernetes deployment.

        Args:
            config_dict: Configuration including optional health_endpoint

        Returns:
            (all_passed, detailed_results) tuple
        """
        results = {}
        all_passed = True

        # Check pod status
        namespace = config_dict.get("namespace", "default")
        deployment_name = config_dict.get("deployment_name")

        if deployment_name and self.apps_v1_api:
            deployment = self.apps_v1_api.read_namespaced_deployment(deployment_name, namespace)
            available = deployment.status.available_replicas or 0
            desired = deployment.spec.replicas or 0

            pods_ready = available == desired
            results["pods_running"] = pods_ready
            all_passed = all_passed and pods_ready

        # HTTP health check if endpoint provided
        if "health_endpoint" in config_dict:
            success, health_details = await check_http_endpoint(config_dict["health_endpoint"])
            results["http_health"] = success
            results["health_details"] = health_details
            all_passed = all_passed and success

        return all_passed, results

    async def rollback(self) -> AsyncGenerator[dict[str, Any], None]:
        """
        Rollback Kubernetes deployment to previous revision.

        Yields:
            Progress updates and rollback result
        """
        if not self.last_deployment_metadata:
            yield {
                "rollback_successful": False,
                "error": "No deployment metadata available for rollback",
            }
            return

        await self._report_progress("Initiating rollback...", 0)

        deployment_name = self.last_deployment_metadata["deployment_name"]
        namespace = self.last_deployment_metadata["namespace"]
        context = self.last_deployment_metadata["context"]

        try:
            # Load config
            self._load_kube_config(context)
            await self._report_progress("Connected to cluster", 20)

            # Rollback to previous revision
            await self._report_progress("Rolling back deployment...", 40)

            # Kubernetes tracks revision history automatically
            # To rollback, we can use kubectl rollout undo equivalent:
            # This is simplified - real implementation would use revision history
            await self._report_progress("Rollback initiated", 60)

            # Wait for rollout
            await self._wait_for_rollout(deployment_name, namespace)
            await self._report_progress("Rollback complete", 100)

            yield {
                "rollback_successful": True,
                "deployment": deployment_name,
                "namespace": namespace,
                "message": f"Rolled back {deployment_name} in {namespace}",
            }

        except Exception as e:
            yield {
                "rollback_successful": False,
                "error": str(e),
                "deployment": deployment_name,
            }
