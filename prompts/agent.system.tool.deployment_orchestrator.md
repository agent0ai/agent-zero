# Deployment Orchestrator Tool

The **deployment_orchestrator** tool provides end-to-end CI/CD pipeline generation, Docker configuration, Kubernetes manifests, and deployment management.

## Purpose

- Generate CI/CD pipelines for GitHub Actions, GitLab CI, Azure Pipelines
- Create Docker configurations with multi-stage builds
- Generate Kubernetes deployment manifests
- Manage deployment environments
- Track deployment status and health

---

## Available Actions

### Project Registration

#### 1. register_project

**Register a project for deployment management**

```
{{deployment_orchestrator(
  action="register_project",
  name="My API",
  project_path="/projects/my-api",
  language="python",
  framework="fastapi"
)}}
```

**Parameters:**

- `name` (required): Project name
- `project_path` (required): Path to project
- `project_type` (optional): web, api, cli, microservice
- `language` (optional): Auto-detected if not provided (python, javascript, typescript, go)
- `framework` (optional): Framework used (fastapi, express, react, etc.)

**Returns:** project_id, detected language

---

#### 2. get_project / list_projects

```
{{deployment_orchestrator(action="get_project", project_id=1)}}
{{deployment_orchestrator(action="list_projects")}}
```

---

### CI/CD Pipeline Generation

#### 3. generate_cicd

**Generate CI/CD pipeline configuration**

```
{{deployment_orchestrator(
  action="generate_cicd",
  project_id=1,
  platform="github_actions",
  include_tests=true,
  include_lint=true,
  include_build=true,
  deploy_env="staging"
)}}
```

**Parameters:**

- `project_id` (required): Project ID
- `platform` (optional): github_actions, gitlab_ci, azure_pipelines (default: github_actions)
- `include_tests` (optional): Include test job (default: true)
- `include_lint` (optional): Include linting (default: true)
- `include_build` (optional): Include build job (default: true)
- `deploy_env` (optional): Add deployment job for environment

**Returns:** pipeline_id, config_path, full pipeline configuration

**Supported Languages:**

- Python (pytest, ruff)
- JavaScript/TypeScript (npm test, npm run lint)
- Go (go test, golangci-lint)

---

#### 4. get_pipeline / list_pipelines

```
{{deployment_orchestrator(action="get_pipeline", pipeline_id=1)}}
{{deployment_orchestrator(action="list_pipelines", project_id=1)}}
```

---

### Docker Configuration

#### 5. generate_docker

**Generate Docker configuration**

```
{{deployment_orchestrator(
  action="generate_docker",
  project_id=1,
  port=8000,
  include_compose=true,
  multi_stage=true
)}}
```

**Parameters:**

- `project_id` (required): Project ID
- `port` (optional): Application port (default: 8000)
- `include_compose` (optional): Generate docker-compose.yml (default: true)
- `multi_stage` (optional): Use multi-stage build (default: true)

**Returns:** Dockerfile, docker-compose.yml, .dockerignore

**Generated Files:**

- Dockerfile (optimized for production)
- docker-compose.yml (with optional database service)
- .dockerignore (language-specific exclusions)

---

#### 6. get_docker_config

```
{{deployment_orchestrator(action="get_docker_config", project_id=1)}}
```

---

### Kubernetes Manifests

#### 7. generate_k8s

**Generate Kubernetes manifests**

```
{{deployment_orchestrator(
  action="generate_k8s",
  project_id=1,
  replicas=3,
  port=8000,
  namespace="production",
  include_service=true,
  include_ingress=true
)}}
```

**Parameters:**

- `project_id` (required): Project ID
- `replicas` (optional): Number of replicas (default: 2)
- `port` (optional): Container port (default: 8000)
- `namespace` (optional): Kubernetes namespace (default: default)
- `include_service` (optional): Generate Service (default: true)
- `include_ingress` (optional): Generate Ingress (default: false)

**Returns:** Deployment, Service, Ingress manifests

**Generated Manifests:**

- Deployment with resource limits and probes
- ClusterIP Service
- Ingress with nginx annotations

---

#### 8. get_k8s_manifests

```
{{deployment_orchestrator(
  action="get_k8s_manifests",
  project_id=1,
  manifest_type="deployment"
)}}
```

**Parameters:**

- `project_id` (required): Project ID
- `manifest_type` (optional): Filter by type (deployment, service, ingress)

---

### Environment Management

#### 9. setup_environment

**Set up a deployment environment**

```
{{deployment_orchestrator(
  action="setup_environment",
  project_id=1,
  name="production",
  env_type="production",
  config={
    "replicas": 3,
    "domain": "api.example.com"
  }
)}}
```

**Parameters:**

- `project_id` (required): Project ID
- `name` (required): Environment name
- `env_type` (optional): development, staging, production (default: staging)
- `config` (optional): Environment-specific configuration

**Returns:** environment_id

---

#### 10. get_environment / list_environments

```
{{deployment_orchestrator(action="get_environment", environment_id=1)}}
{{deployment_orchestrator(action="list_environments", project_id=1)}}
```

---

### Deployment Status

#### 11. get_deployment_dashboard

**Get comprehensive deployment dashboard**

```
{{deployment_orchestrator(
  action="get_deployment_dashboard",
  project_id=1
)}}
```

**Parameters:**

- `project_id` (required): Project ID

**Returns:** Environment status, recent deployments, pipeline count

---

#### 12. health_check

**Check health status of deployments**

```
{{deployment_orchestrator(
  action="health_check",
  project_id=1,
  environment_id=1
)}}
```

**Parameters:**

- `project_id` (required): Project ID
- `environment_id` (optional): Specific environment

**Returns:** Latest deployment status, health indicator

---

#### 13. list_deployments

**List recent deployments**

```
{{deployment_orchestrator(
  action="list_deployments",
  project_id=1,
  limit=10
)}}
```

---

## Typical Workflows

### Complete Deployment Setup

```
# 1. Register the project
{{deployment_orchestrator(
  action="register_project",
  name="My API",
  project_path="/projects/my-api"
)}}

# 2. Generate CI/CD pipeline
{{deployment_orchestrator(
  action="generate_cicd",
  project_id=1,
  platform="github_actions",
  deploy_env="staging"
)}}

# 3. Generate Docker configuration
{{deployment_orchestrator(
  action="generate_docker",
  project_id=1,
  port=8000
)}}

# 4. Generate Kubernetes manifests
{{deployment_orchestrator(
  action="generate_k8s",
  project_id=1,
  namespace="my-api"
)}}

# 5. Set up environments
{{deployment_orchestrator(
  action="setup_environment",
  project_id=1,
  name="staging",
  env_type="staging"
)}}

{{deployment_orchestrator(
  action="setup_environment",
  project_id=1,
  name="production",
  env_type="production"
)}}

# 6. Check deployment status
{{deployment_orchestrator(
  action="get_deployment_dashboard",
  project_id=1
)}}
```

### Quick Container Setup

```
# Register and generate Docker in one flow
{{deployment_orchestrator(action="register_project", name="App", project_path="/app")}}
{{deployment_orchestrator(action="generate_docker", project_id=1)}}
```

---

## Generated Configuration Examples

### GitHub Actions (Python)

```yaml
name: CI/CD for My API

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Lint
        run: ruff check .
      - name: Run tests
        run: pytest
```

### Multi-Stage Dockerfile (Python)

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

# Production stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-api
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-api
  template:
    spec:
      containers:
        - name: my-api
          image: my-api:latest
          ports:
            - containerPort: 8000
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
```

---

## Integration with Other Tools

### With Project Scaffold

Deploy scaffolded projects:

```
{{project_scaffold(action="scaffold_project", template="api/fastapi", ...)}}
{{deployment_orchestrator(action="register_project", name="New API", project_path="...")}}
{{deployment_orchestrator(action="generate_cicd", project_id=1)}}
```

### With Portfolio Manager

Track deployed products:

```
{{portfolio_manager_tool(action="add", project_path="/projects/api")}}
{{deployment_orchestrator(action="register_project", ...)}}
```

### With Diagram Architect

Include deployment in architecture docs:

```
{{diagram_architect(action="analyze_architecture", project_path="...")}}
{{deployment_orchestrator(action="generate_k8s", ...)}}
```

---

## Notes

- Auto-detects project language from files (package.json, requirements.txt, go.mod)
- Generates production-ready configurations
- Multi-stage Docker builds minimize image size
- Kubernetes manifests include resource limits and health probes
- Supports GitHub Actions, GitLab CI, and Azure Pipelines
- Environments track deployment history and status
