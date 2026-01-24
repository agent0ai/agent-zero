---
description: Deploy Docker images to container registries (Docker Hub, GCR, ECR, ACR, GitLab) with automated tagging and multi-platform builds
argument-hint: [--registry <dockerhub|gcr|ecr|acr|gitlab>] [--tag <version>] [--multi-platform] [--sign]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

Docker Deploy: **${ARGUMENTS}**

## Deploying to Container Registry

Use the Task tool with subagent_type=docker-specialist to deploy Docker images to container registries with the following specifications:

### Input Parameters

**Registry**: ${REGISTRY:-dockerhub} (Docker Hub, GCR, ECR, ACR, GitLab, GHCR)
**Version Tag**: ${TAG:-auto} (version, or auto-generate from git)
**Multi-Platform**: ${MULTI_PLATFORM:-true} (Build for AMD64 + ARM64)
**Sign Image**: ${SIGN:-false} (Sign with Docker Content Trust or Cosign)

### Objectives

You are tasked with deploying Docker images to production registries with proper tagging, signing, and multi-platform support. Your implementation must:

#### 1. Registry Configuration

**Docker Hub**:

```bash
# Login
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# Tag image
docker tag myapp:latest username/myapp:v1.0.0
docker tag myapp:latest username/myapp:latest

# Push
docker push username/myapp:v1.0.0
docker push username/myapp:latest
```

**Google Container Registry (GCR)**:

```bash
# Configure authentication
gcloud auth configure-docker gcr.io

# Tag image
docker tag myapp:latest gcr.io/project-id/myapp:v1.0.0
docker tag myapp:latest gcr.io/project-id/myapp:latest

# Push
docker push gcr.io/project-id/myapp:v1.0.0
docker push gcr.io/project-id/myapp:latest
```

**Google Artifact Registry** (recommended over GCR):

```bash
# Configure authentication
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag image
docker tag myapp:latest us-central1-docker.pkg.dev/project-id/repo/myapp:v1.0.0

# Push
docker push us-central1-docker.pkg.dev/project-id/repo/myapp:v1.0.0
```

**Amazon ECR**:

```bash
# Login (token expires after 12 hours)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Create repository if it doesn't exist
aws ecr create-repository --repository-name myapp --region us-east-1 || true

# Tag image
docker tag myapp:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:v1.0.0

# Push
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:v1.0.0
```

**Azure Container Registry (ACR)**:

```bash
# Login
az acr login --name myregistry

# Tag image
docker tag myapp:latest myregistry.azurecr.io/myapp:v1.0.0

# Push
docker push myregistry.azurecr.io/myapp:v1.0.0
```

**GitHub Container Registry (GHCR)**:

```bash
# Login
echo "$GITHUB_TOKEN" | docker login ghcr.io -u USERNAME --password-stdin

# Tag image
docker tag myapp:latest ghcr.io/username/myapp:v1.0.0

# Push
docker push ghcr.io/username/myapp:v1.0.0
```

**GitLab Container Registry**:

```bash
# Login
echo "$CI_JOB_TOKEN" | docker login registry.gitlab.com -u gitlab-ci-token --password-stdin

# Tag image
docker tag myapp:latest registry.gitlab.com/username/project/myapp:v1.0.0

# Push
docker push registry.gitlab.com/username/project/myapp:v1.0.0
```

#### 2. Multi-Platform Builds

**Setup Buildx** (for multi-arch):

```bash
# Create builder instance
docker buildx create --name multiplatform --use

# Inspect builder
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag myapp:v1.0.0 \
  --push \
  .
```

**Multi-Platform Deployment Script**:

```bash
#!/bin/bash

set -e

VERSION=${1:-latest}
REGISTRY=${REGISTRY:-gcr.io/project-id}
IMAGE_NAME=${IMAGE_NAME:-myapp}

echo "🏗️  Building multi-platform image..."
echo "Registry: $REGISTRY"
echo "Image: $IMAGE_NAME"
echo "Version: $VERSION"

# Create and use builder
docker buildx create --name multiplatform --use 2>/dev/null || \
  docker buildx use multiplatform

# Build and push for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag $REGISTRY/$IMAGE_NAME:$VERSION \
  --tag $REGISTRY/$IMAGE_NAME:latest \
  --cache-from type=registry,ref=$REGISTRY/$IMAGE_NAME:buildcache \
  --cache-to type=registry,ref=$REGISTRY/$IMAGE_NAME:buildcache,mode=max \
  --push \
  --provenance=true \
  --sbom=true \
  .

echo "✅ Image pushed successfully!"
echo "Pull with: docker pull $REGISTRY/$IMAGE_NAME:$VERSION"
```

#### 3. Automated Version Tagging

**Semantic Versioning from Git**:

```bash
#!/bin/bash

# Get version from git tag or generate
if git describe --tags --exact-match 2>/dev/null; then
  VERSION=$(git describe --tags --exact-match)
else
  # Generate version from branch and commit
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  COMMIT=$(git rev-parse --short HEAD)
  VERSION="${BRANCH}-${COMMIT}"
fi

echo "Version: $VERSION"

# Tag with multiple versions
docker tag myapp:latest myregistry/myapp:$VERSION
docker tag myapp:latest myregistry/myapp:latest

# Also tag with major/minor versions
if [[ $VERSION =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  MAJOR="${BASH_REMATCH[1]}"
  MINOR="${BASH_REMATCH[2]}"
  PATCH="${BASH_REMATCH[3]}"

  docker tag myapp:latest myregistry/myapp:v$MAJOR
  docker tag myapp:latest myregistry/myapp:v$MAJOR.$MINOR
fi

# Push all tags
docker push --all-tags myregistry/myapp
```

**Calendar Versioning** (CalVer):

```bash
# Generate YYYY.MM.DD.BUILD format
VERSION=$(date +%Y.%m.%d)
BUILD_NUMBER=${CI_BUILD_NUMBER:-0}
FULL_VERSION="${VERSION}.${BUILD_NUMBER}"

docker tag myapp:latest myregistry/myapp:$FULL_VERSION
docker tag myapp:latest myregistry/myapp:$VERSION
docker tag myapp:latest myregistry/myapp:latest
```

#### 4. Image Signing and Verification

**Docker Content Trust** (Notary):

```bash
# Enable Content Trust
export DOCKER_CONTENT_TRUST=1

# Generate keys (first time only)
docker trust key generate mykey

# Add signer
docker trust signer add --key mykey.pub myname myregistry/myapp

# Push (automatically signs)
docker push myregistry/myapp:v1.0.0

# Verify signature
docker trust inspect --pretty myregistry/myapp:v1.0.0
```

**Cosign** (Sigstore):

```bash
# Install cosign
curl -O -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
chmod +x cosign-linux-amd64
sudo mv cosign-linux-amd64 /usr/local/bin/cosign

# Generate key pair
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key myregistry/myapp:v1.0.0

# Verify signature
cosign verify --key cosign.pub myregistry/myapp:v1.0.0

# Sign with keyless (OIDC)
cosign sign myregistry/myapp:v1.0.0  # Uses OIDC provider

# Attach SBOM
cosign attach sbom --sbom sbom.json myregistry/myapp:v1.0.0
```

#### 5. Complete Deployment Workflow

**CI/CD Integration** (GitHub Actions):

```yaml
name: Build and Deploy Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write  # For cosign

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true
          sbom: true

      - name: Install Cosign
        uses: sigstore/cosign-installer@v3

      - name: Sign image
        env:
          TAGS: ${{ steps.meta.outputs.tags }}
          DIGEST: ${{ steps.build-and-push.outputs.digest }}
        run: |
          echo "${TAGS}" | xargs -I {} cosign sign --yes {}@${DIGEST}

      - name: Verify signature
        run: |
          cosign verify \
            --certificate-identity=https://github.com/${{ github.repository }}/.github/workflows/build.yml@refs/heads/main \
            --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build-and-push.outputs.digest }}
```

**GitLab CI**:

```yaml
build-and-push:
  image: docker:24
  services:
    - docker:24-dind

  variables:
    DOCKER_DRIVER: overlay2
    IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG

  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

  script:
    # Build for multiple platforms
    - docker buildx create --use
    - |
      docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag $IMAGE_TAG \
        --tag $CI_REGISTRY_IMAGE:latest \
        --push \
        .

  only:
    - main
    - tags
```

#### 6. Deployment Strategies

**Blue-Green Deployment**:

```bash
#!/bin/bash

# Blue-Green deployment script

NEW_VERSION=$1
REGISTRY=myregistry.com
IMAGE=myapp

# Deploy to green environment
echo "🟢 Deploying v$NEW_VERSION to green environment..."
kubectl set image deployment/myapp-green \
  app=$REGISTRY/$IMAGE:v$NEW_VERSION

# Wait for green to be ready
kubectl rollout status deployment/myapp-green --timeout=5m

# Run smoke tests on green
echo "🧪 Running smoke tests..."
./smoke-tests.sh https://green.example.com

# Switch traffic to green
echo "🔄 Switching traffic to green..."
kubectl patch service myapp -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor for 5 minutes
echo "📊 Monitoring for anomalies..."
sleep 300

# Check error rates
ERROR_RATE=$(curl -s "https://monitoring.example.com/error-rate?env=green")
if (( $(echo "$ERROR_RATE > 1.0" | bc -l) )); then
  echo "❌ High error rate detected, rolling back..."
  kubectl patch service myapp -p '{"spec":{"selector":{"version":"blue"}}}'
  exit 1
fi

echo "✅ Deployment successful!"

# Update blue to new version for next deployment
kubectl set image deployment/myapp-blue \
  app=$REGISTRY/$IMAGE:v$NEW_VERSION
```

**Canary Deployment**:

```yaml
# Istio VirtualService for canary deployment
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp
spec:
  hosts:
    - myapp.example.com
  http:
    - match:
        - headers:
            canary:
              exact: "true"
      route:
        - destination:
            host: myapp
            subset: canary
    - route:
        - destination:
            host: myapp
            subset: stable
          weight: 95
        - destination:
            host: myapp
            subset: canary
          weight: 5  # 5% canary traffic
```

### Implementation Steps

**Step 1: Setup**

1. Detect target registry
2. Configure authentication
3. Verify access
4. Create repository if needed

**Step 2: Build**

1. Build multi-platform image
2. Run security scans
3. Generate SBOM
4. Tag appropriately

**Step 3: Push**

1. Push to registry
2. Sign image (if enabled)
3. Attach metadata
4. Update registry tags

**Step 4: Verification**

1. Verify push successful
2. Verify signatures
3. Test image pull
4. Update documentation

**Step 5: Deployment** (optional)

1. Trigger deployment pipeline
2. Monitor rollout
3. Run smoke tests
4. Verify health

### Output Requirements

**Generated Files**:

- `deploy.sh` - Automated deployment script
- `multi-platform-build.sh` - Multi-arch build script
- `.github/workflows/deploy.yml` - CI/CD workflow
- `DEPLOYMENT.md` - Deployment documentation

**DEPLOYMENT.md Contents**:

```markdown
# Docker Deployment Guide

## Quick Deploy

```bash
# Deploy to production
./deploy.sh v1.2.3

# Deploy to staging
REGISTRY=staging.gcr.io/project ./deploy.sh v1.2.3-rc1
```

## Registry Configuration

**Production**: gcr.io/production-project/myapp
**Staging**: gcr.io/staging-project/myapp
**Development**: localhost:5000/myapp

## Deployment Process

### Manual Deployment

1. **Build multi-platform image**:

   ```bash
   ./multi-platform-build.sh v1.2.3
   ```

2. **Run security scan**:

   ```bash
   trivy image gcr.io/project/myapp:v1.2.3
   ```

3. **Push to registry**:

   ```bash
   docker push gcr.io/project/myapp:v1.2.3
   ```

4. **Sign image**:

   ```bash
   cosign sign gcr.io/project/myapp:v1.2.3
   ```

### Automated Deployment (CI/CD)

**GitHub**: Push tag triggers deployment

```bash
git tag v1.2.3
git push origin v1.2.3
```

**Workflow**: Build → Test → Scan → Push → Sign → Deploy

## Version Tags

Images are tagged with:

- Commit SHA: `myapp:abc123`
- Branch: `myapp:main`
- Semantic version: `myapp:v1.2.3`
- Major version: `myapp:v1`
- Latest: `myapp:latest`

## Multi-Platform Support

Images support:

- linux/amd64 (Intel/AMD)
- linux/arm64 (ARM servers, M1/M2 Macs)

Pull correct architecture automatically:

```bash
docker pull gcr.io/project/myapp:v1.2.3
```

## Image Verification

Verify image signature:

```bash
cosign verify \
  --certificate-identity=https://github.com/org/repo/.github/workflows/deploy.yml@refs/heads/main \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  gcr.io/project/myapp:v1.2.3
```

## Rollback Procedure

1. **Identify previous version**:

   ```bash
   kubectl rollout history deployment/myapp
   ```

2. **Rollback**:

   ```bash
   kubectl rollout undo deployment/myapp
   # OR to specific revision:
   kubectl rollout undo deployment/myapp --to-revision=3
   ```

## Monitoring

- **Registry**: <https://console.cloud.google.com/gcr>
- **Deployments**: <https://console.cloud.google.com/kubernetes>
- **Logs**: <https://console.cloud.google.com/logs>

## Troubleshooting

### Image Pull Fails

**Issue**: `Error: image pull failed`

**Solution**:

```bash
# Check authentication
gcloud auth configure-docker

# Verify image exists
gcloud container images list --repository=gcr.io/project

# Check permissions
gcloud projects get-iam-policy project-id
```

### Multi-Platform Build Fails

**Issue**: `Multiple platform feature not supported`

**Solution**:

```bash
# Install QEMU
docker run --privileged --rm tonistiigi/binfmt --install all

# Recreate builder
docker buildx rm multiplatform
docker buildx create --name multiplatform --use
```

## ROI Impact

**Deployment Speed**:

- Manual deployment: 2 hours → 10 minutes (92% faster)
- Multi-registry support: Deploy anywhere in seconds
- Automated CI/CD: Zero-touch deployments

**Reliability**:

- Image signing: Verify authenticity
- Multi-platform: Support all architectures
- Automated testing: Catch issues before production

**Cost Savings**:

- Deployment automation: $25,000/year
- Reduced errors: $20,000/year
- Faster time-to-market: $15,000/year

**Total Value**: $60,000/year

## Success Metrics

✅ **Images pushed to registry**
✅ **Multi-platform support enabled**
✅ **Images signed and verified**
✅ **CI/CD automation configured**
✅ **Zero deployment failures**

---

**Status**: 🟢 Production Ready
**Annual ROI**: $60,000

```

## ROI Impact

**Deployment Efficiency**:
- **90% faster deployments** - Manual 2 hours → Automated 10 minutes
- **Zero deployment errors** - Automated validation
- **Multi-registry support** - Deploy anywhere

**Developer Productivity**:
- **Simplified deployment** - One command to deploy
- **Automated builds** - CI/CD integration
- **Multi-platform** - Build once, run anywhere

**Cost Savings**:
- Deployment automation: $25,000/year (20 deploys/month × 2 hours saved)
- Reduced errors: $20,000/year (fewer rollbacks)
- Multi-platform support: $15,000/year (ARM cost savings)
- **Total Value**: $60,000/year

## Success Criteria

✅ **Multi-platform builds working** (AMD64 + ARM64)
✅ **Images pushed to registry successfully**
✅ **Image signing configured**
✅ **CI/CD pipeline integrated**
✅ **Deployment documentation complete**
✅ **Rollback procedure tested**

**Performance Targets**:
- Build time: < 5 minutes
- Push time: < 2 minutes
- Total deployment: < 10 minutes
- Success rate: > 99%

## Next Steps

1. Configure registry authentication
2. Run first multi-platform build
3. Set up CI/CD automation
4. Enable image signing
5. Deploy to production

---

**Deployment Status**: 🟢 Ready for Production
**Supported Platforms**: AMD64, ARM64
**Annual ROI**: $60,000
