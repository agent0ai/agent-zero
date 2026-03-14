# DevOps Deployment Quick Reference Guide

## Quick Start for Kubernetes Deployments

---

## 1. Basic Kubernetes Deployment

### Import the Strategy

```python
from python.tools.deployment_strategies.kubernetes import KubernetesStrategy
from python.helpers.deployment_progress import StreamingProgressReporter

# Create strategy instance
strategy = KubernetesStrategy()

# Optional: Add progress reporting
strategy.set_progress_reporter(StreamingProgressReporter())
```

### Configure Deployment

```python
config = {
    "kubectl_context": "production",      # Kubernetes context from kubeconfig
    "manifest_path": "k8s/manifests/",    # Path to YAML files or directory
    "deployment_name": "api-server",       # Deployment resource name
    "namespace": "default",                # Kubernetes namespace (optional)
}
```

### Execute Deployment

```python
# Validate configuration first
is_valid = await strategy.validate_config(config)
assert is_valid, "Configuration validation failed"

# Execute deployment with streaming updates
async for update in strategy.execute_deployment(config):
    print(f"Status: {update['status']}")
    print(f"Message: {update.get('message', '')}")

    if update['status'] == 'success':
        print(f"Deployed: {update['deployment_name']}")
        print(f"Revision: {update['revision']}")
```

### Run Health Checks

```python
config_with_health = config.copy()
config_with_health["health_endpoint"] = "http://api-server:8080/health"

passed, results = await strategy.run_smoke_tests(config_with_health)

if passed:
    print("✅ All health checks passed")
else:
    print("❌ Health check failed")
    print(results)
```

### Rollback if Needed

```python
async for update in strategy.rollback():
    print(f"Rollback status: {update}")

    if update.get('rollback_successful'):
        print("✅ Successfully rolled back to previous version")
    else:
        print(f"❌ Rollback failed: {update.get('error')}")
```

---

## 2. Deployment Modes

### Rolling Deployment (Default)

```python
# Gradual replacement of old pods with new ones
async for update in strategy.execute_deployment(config, deployment_mode="rolling"):
    print(update)
```

### Blue-Green Deployment

```python
# Run new version alongside old, then switch traffic
async for update in strategy.execute_deployment(config, deployment_mode="blue-green"):
    print(update)
```

### Immediate Deployment

```python
# Replace all pods at once (use with caution)
async for update in strategy.execute_deployment(config, deployment_mode="immediate"):
    print(update)
```

---

## 3. Error Handling

### Understanding Error Types

```python
from python.helpers.deployment_retry import (
    TransientDeploymentError,
    PermanentDeploymentError,
    classify_error
)

try:
    async for update in strategy.execute_deployment(config):
        pass
except TransientDeploymentError as e:
    # Network issue, timeout, or temporary API failure
    # Retry logic already applied
    print(f"Transient error (retried): {e}")
except PermanentDeploymentError as e:
    # Authentication, authorization, or configuration error
    # Won't retry automatically
    print(f"Permanent error (won't retry): {e}")
except Exception as e:
    # Unexpected error
    error_type = classify_error(e, "kubernetes")
    print(f"Classified as: {type(error_type).__name__}")
```

### Manual Retry with Custom Logic

```python
from python.helpers.deployment_retry import with_retry

async def deploy_with_retry():
    return await with_retry(
        strategy.execute_deployment,
        config
    )

async for update in await deploy_with_retry():
    print(update)
```

---

## 4. Progress Tracking

### Streaming Progress Reporter (Real-time)

```python
from python.helpers.deployment_progress import StreamingProgressReporter

reporter = StreamingProgressReporter()
strategy.set_progress_reporter(reporter)

async for update in strategy.execute_deployment(config):
    # Progress is reported automatically during execution
    # Each update is yielded with message and percentage
    if update.get('percent'):
        print(f"Progress: {update['percent']}%")
```

### Logging Progress Reporter (Debug)

```python
from python.helpers.deployment_progress import LoggingProgressReporter
import json

reporter = LoggingProgressReporter()
strategy.set_progress_reporter(reporter)

async for update in strategy.execute_deployment(config):
    # Progress is logged as JSON
    # Useful for debugging and audit trails
    print(json.dumps(update, indent=2))
```

---

## 5. Health Checking

### HTTP Endpoint Check

```python
from python.helpers.deployment_health import check_http_endpoint

# Basic health check
success, details = await check_http_endpoint("http://localhost:8080/health")

if success:
    print(f"✅ Healthy (response time: {details['response_time_ms']}ms)")
else:
    print(f"❌ Unhealthy: {details}")
```

### Custom Configuration

```python
# Longer timeout for slow services
success, details = await check_http_endpoint(
    "http://slow-service:8080/health",
    timeout=60,  # 60 second timeout
    expected_status=200,
    headers={"Authorization": "Bearer TOKEN"}
)
```

---

## 6. Common Workflows

### Complete Deploy → Validate → Rollback Flow

```python
async def safe_deploy(config):
    # Step 1: Validate configuration
    if not await strategy.validate_config(config):
        return {"success": False, "error": "Invalid configuration"}

    # Step 2: Execute deployment
    deployment_result = None
    async for update in strategy.execute_deployment(config):
        deployment_result = update

    if deployment_result['status'] != 'success':
        return deployment_result

    # Step 3: Run health checks
    health_config = config.copy()
    health_config['health_endpoint'] = 'http://api:8080/health'
    passed, results = await strategy.run_smoke_tests(health_config)

    if not passed:
        # Step 4: Rollback on health check failure
        print("Health checks failed, rolling back...")
        async for rollback_update in strategy.rollback():
            print(f"Rollback: {rollback_update}")

        return {
            "success": False,
            "error": "Health checks failed, rolled back",
            "details": results
        }

    return {
        "success": True,
        "deployment": deployment_result,
        "health_check": results
    }

# Execute the workflow
result = await safe_deploy(config)
print(json.dumps(result, indent=2))
```

### Multi-Namespace Deployment

```python
async def deploy_to_namespaces(manifest_path, namespaces):
    results = {}

    for namespace in namespaces:
        config = {
            "kubectl_context": "production",
            "manifest_path": manifest_path,
            "namespace": namespace,
            "deployment_name": "api-server",
        }

        result = None
        async for update in strategy.execute_deployment(config):
            result = update

        results[namespace] = result

    return results

# Deploy to multiple namespaces
namespaces = ["staging", "production"]
results = await deploy_to_namespaces("k8s/manifests/", namespaces)
```

---

## 7. Configuration Examples

### Minimal Configuration

```python
config = {
    "kubectl_context": "default",
    "manifest_path": "k8s/",
}
```

### Complete Configuration with Health Checks

```python
config = {
    # Required
    "kubectl_context": "production-us-east",
    "manifest_path": "/home/user/k8s/manifests",

    # Optional
    "namespace": "production",
    "deployment_name": "api-server",
    "health_endpoint": "http://api-server:8080/health",
    "deployment_mode": "rolling",
    "skip_tests": False,
}
```

---

## 8. Testing Your Deployment Code

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_deployment():
    strategy = KubernetesStrategy()
    config = {
        "kubectl_context": "test",
        "manifest_path": "k8s/test/",
    }

    with patch("python.tools.deployment_strategies.kubernetes.config"):
        with patch("python.tools.deployment_strategies.kubernetes.client") as mock_client:
            # Mock kubernetes API
            mock_deployment = MagicMock()
            mock_deployment.metadata.generation = 1

            mock_api = MagicMock()
            mock_api.read_namespaced_deployment.return_value = mock_deployment
            mock_client.AppsV1Api.return_value = mock_api

            with patch.object(strategy, "_parse_manifests") as mock_parse:
                with patch.object(strategy, "_apply_manifests") as mock_apply:
                    with patch.object(strategy, "_wait_for_rollout"):
                        mock_parse.return_value = [{"kind": "Deployment"}]
                        mock_apply.return_value = ["Deployment/api"]

                        # Test deployment
                        result = None
                        async for update in strategy.execute_deployment(config):
                            result = update

                        assert result["status"] == "success"
```

---

## 9. Troubleshooting

### Issue: Configuration Validation Fails

```python
try:
    await strategy.validate_config(config)
except ValueError as e:
    print(f"❌ Config validation error: {e}")
    # Common issues:
    # - Missing kubectl_context
    # - Missing manifest_path
    # - Invalid manifest_path (file/directory doesn't exist)
```

### Issue: Kubeconfig Not Found

```python
# Ensure kubeconfig is accessible
import os

kubeconfig = os.getenv("KUBECONFIG", os.path.expanduser("~/.kube/config"))
print(f"Using kubeconfig: {kubeconfig}")

if not os.path.exists(kubeconfig):
    print("❌ Kubeconfig not found!")
```

### Issue: Health Check Timeout

```python
# Increase timeout for slow services
success, details = await check_http_endpoint(
    endpoint,
    timeout=120  # Increase from default 30s
)

if not success:
    print(f"Health check failed: {details['error']}")
```

### Issue: Deployment Hangs

```python
# Check pod status manually
# kubectl get pods -n namespace
# kubectl describe pod <pod-name> -n namespace
# kubectl logs <pod-name> -n namespace
```

---

## 10. API Reference

### KubernetesStrategy Class

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `validate_config()` | `async def validate_config(config: dict) -> bool` | bool | Validates Kubernetes configuration |
| `execute_deployment()` | `async def execute_deployment(config: dict, deployment_mode: str = "rolling") -> AsyncGenerator` | AsyncGenerator | Executes deployment with progress |
| `run_smoke_tests()` | `async def run_smoke_tests(config: dict) -> tuple[bool, dict]` | (bool, dict) | Runs post-deployment validation |
| `rollback()` | `async def rollback() -> AsyncGenerator` | AsyncGenerator | Rolls back to previous version |
| `set_progress_reporter()` | `def set_progress_reporter(reporter)` | None | Injects progress reporter |

### Error Classification

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `classify_error()` | `def classify_error(error: Exception, platform: str) -> Exception` | Exception | Classifies error as transient or permanent |
| `with_retry()` | `async def with_retry(func, *args, **kwargs) -> Any` | Any | Executes function with retry logic |

### Health Checking

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `check_http_endpoint()` | `async def check_http_endpoint(url: str, timeout: int = 30, expected_status: int = 200, headers: dict = None) -> tuple[bool, dict]` | (bool, dict) | Checks HTTP endpoint health |

### Progress Reporting

| Class | Method | Description |
|-------|--------|-------------|
| `StreamingProgressReporter` | `async def report(message: str, percent: int = None) -> AsyncGenerator` | Yields progress updates as async generator |
| `LoggingProgressReporter` | `async def report(message: str, percent: int = None) -> AsyncGenerator` | Logs progress updates for debugging |

---

## 11. Best Practices

### ✅ DO's

- ✅ Always validate configuration before deploying
- ✅ Use progress reporters for visibility
- ✅ Run health checks after deployment
- ✅ Store deployment metadata for rollback
- ✅ Use rolling deployments for zero-downtime updates
- ✅ Test deployments in staging before production
- ✅ Monitor health endpoints during deployment
- ✅ Set appropriate timeouts for your infrastructure

### ❌ DON'Ts

- ❌ Don't skip health checks in production
- ❌ Don't use immediate deployments without good reason
- ❌ Don't deploy without rollback capability
- ❌ Don't ignore network timeouts
- ❌ Don't hardcode credentials in config
- ❌ Don't deploy during critical business hours without monitoring
- ❌ Don't skip manifest validation before deployment

---

## 12. Environment Setup

### Required Environment Variables

```bash
# Kubernetes configuration
export KUBECONFIG=~/.kube/config

# Optional: Context override
export KUBERNETES_CONTEXT=production
```

### Python Dependencies

```bash
# Core dependencies
pip install kubernetes>=34.1.0
pip install pyyaml>=6.0
pip install tenacity>=8.0.0

# For async support
pip install asyncio-contextmanager>=1.0.0
```

### Kubeconfig Setup

```bash
# List available contexts
kubectl config get-contexts

# Switch context
kubectl config use-context production

# View current context
kubectl config current-context
```

---

## 13. Complete Example: Production Deployment

```python
import json
import asyncio
from python.tools.deployment_strategies.kubernetes import KubernetesStrategy
from python.helpers.deployment_progress import StreamingProgressReporter

async def main():
    # Initialize strategy with progress reporting
    strategy = KubernetesStrategy()
    strategy.set_progress_reporter(StreamingProgressReporter())

    # Configuration
    config = {
        "kubectl_context": "production",
        "manifest_path": "/app/k8s/manifests",
        "namespace": "production",
        "deployment_name": "api-server",
        "health_endpoint": "https://api.example.com/health",
    }

    try:
        # Step 1: Validate
        print("📋 Validating configuration...")
        if not await strategy.validate_config(config):
            print("❌ Configuration validation failed")
            return

        # Step 2: Deploy
        print("🚀 Starting deployment...")
        deployment_result = None
        async for update in strategy.execute_deployment(config, deployment_mode="rolling"):
            deployment_result = update

        if deployment_result['status'] != 'success':
            print(f"❌ Deployment failed: {deployment_result}")
            return

        print(f"✅ Deployment successful: {deployment_result['message']}")

        # Step 3: Health check
        print("🏥 Running health checks...")
        passed, results = await strategy.run_smoke_tests(config)

        if passed:
            print("✅ All health checks passed")
            print(f"📊 Results: {json.dumps(results, indent=2)}")
        else:
            print("❌ Health checks failed, initiating rollback...")
            async for rollback_update in strategy.rollback():
                print(f"↩️  {rollback_update}")
            return

        print("🎉 Deployment complete and healthy!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Rolling back...")
        async for rollback_update in strategy.rollback():
            print(f"↩️  {rollback_update}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 14. Quick Troubleshooting Checklist

| Issue | Check | Solution |
|-------|-------|----------|
| Config validation fails | Required fields | Ensure `kubectl_context` and `manifest_path` present |
| Kubeconfig not found | `KUBECONFIG` env var | Set `KUBECONFIG` or place in `~/.kube/config` |
| Context not found | Available contexts | Run `kubectl config get-contexts` |
| Manifest not found | File path | Verify path is absolute or relative to correct directory |
| Health check timeout | Network connectivity | Increase timeout or check service is responding |
| Rollout timeout | Pod readiness | Check `kubectl get pods`, review pod logs |
| API authentication error | Credentials | Verify kubeconfig and context permissions |
| Health endpoint 404 | Service configuration | Verify service and port in health_endpoint URL |

---

## 15. Next Steps

1. **Try a test deployment** in your staging cluster
2. **Configure health endpoints** for your services
3. **Set up progress monitoring** in your dashboards
4. **Test rollback procedures** in non-production first
5. **Document your deployment procedures** for your team
6. **Integrate with CI/CD pipeline** (GitHub Actions, etc.)
7. **Monitor deployment metrics** (duration, success rate)

---

**For More Information**:

- Full implementation: `DEVOPS_DEPLOYMENT_COMPLETION_SUMMARY.md`
- Testing guide: `DEVOPS_DEPLOY_TESTING_PLAN.md`
- Source code: `python/tools/deployment_strategies/kubernetes.py`

**Repository**: <https://github.com/agent-jumbo-deploy/agent-jumbo-devops>

**Status**: Production Ready ✅
