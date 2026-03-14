# Installation Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Methods

### Option 1: PyPI (Recommended)

Once published to PyPI:

```bash
pip install agent-jumbo-devops
```

### Option 2: Development Installation (From Source)

```bash
# Clone repository
git clone https://github.com/agent-jumbo-deploy/agent-jumbo-devops.git
cd agent-jumbo-devops

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Option 3: Docker

Build from source:

```bash
docker build -t agent-jumbo-devops:latest .
docker run -it agent-jumbo-devops:latest
```

## Verification

Verify installation:

```bash
python -c "from agent_jumbo.tools.devops_deploy import deploy_to_kubernetes; print('✅ Installation successful')"
```

## Platform-Specific Setup

### For Kubernetes Deployments

Install Kubernetes Python client:

```bash
pip install kubernetes
```

Ensure you have:

- Kubernetes cluster running
- kubectl configured with access
- kubeconfig in standard location (~/.kube/config)

Verify:

```bash
python -c "import kubernetes; print('✅ Kubernetes SDK ready')"
```

### For SSH Deployments (Coming Soon)

Will require:

```bash
pip install paramiko  # or fabric
```

### For AWS Deployments (Coming Soon)

Will require:

```bash
pip install boto3
pip install botocore
```

AWS credentials must be configured via:

- Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- AWS credentials file (~/.aws/credentials)
- IAM role (if running on EC2)

### For GCP Deployments (Coming Soon)

Will require:

```bash
pip install google-cloud-core
pip install google-cloud-compute
```

GCP credentials via:

- Service account JSON file
- Application Default Credentials

## Troubleshooting

### Import Errors

If you get "ModuleNotFoundError: No module named 'agent_jumbo'":

```bash
# Ensure you've installed the package
pip install agent-jumbo-devops

# Or from source
pip install -e .
```

### Kubernetes Connection Errors

If you can't connect to Kubernetes:

```bash
# Verify kubeconfig
echo $KUBECONFIG
cat ~/.kube/config

# Test connection
kubectl cluster-info

# Verify Python client can connect
python -c "from kubernetes import client, config; config.load_kube_config(); print('✅ Connected')"
```

### Permission Errors

If you get permission errors:

```bash
# Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install agent-jumbo-devops

# Or use --user flag
pip install --user agent-jumbo-devops
```

## Next Steps

- [Quick Start](README.md#quick-start) - Get deploying in 5 minutes
- [Full Documentation](docs/DEVOPS_DEPLOYMENT_README.md) - Comprehensive guide
- [Contributing](CONTRIBUTING.md) - Help us improve

## Getting Help

- Documentation: [docs/](docs/)
- Report Issues: [https://github.com/agent-jumbo-deploy/agent-jumbo-devops/issues](https://github.com/agent-jumbo-deploy/agent-jumbo-devops/issues)
- Discussions: [https://github.com/agent-jumbo-deploy/agent-jumbo-devops/discussions](https://github.com/agent-jumbo-deploy/agent-jumbo-devops/discussions)
