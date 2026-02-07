---
name: "docker-devops"
description: "Docker and DevOps best practices for containerization, orchestration, and CI/CD pipelines. Use when working with containers, deployments, or infrastructure."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["docker", "devops", "containers", "kubernetes", "ci-cd", "infrastructure"]
trigger_patterns:
  - "docker"
  - "container"
  - "kubernetes"
  - "k8s"
  - "deploy"
  - "ci/cd"
  - "pipeline"
---

# Docker & DevOps Skill

Best practices for containerization, orchestration, and deployment pipelines.

## Docker Fundamentals

### Dockerfile Best Practices

```dockerfile
# Use specific version tags
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency files first (layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Use exec form for CMD
CMD ["python", "app.py"]
```

### Multi-Stage Builds

```dockerfile
# Build stage
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./app:/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## Kubernetes Basics

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:1.0.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-service
            port:
              number: 80
```

## CI/CD Pipelines

### GitHub Actions

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Login to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Push image
        run: |
          docker tag myapp:${{ github.sha }} ghcr.io/${{ github.repository }}:${{ github.sha }}
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying ${{ github.sha }}"
          # kubectl set image deployment/myapp myapp=ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### GitLab CI

```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pytest

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $DOCKER_IMAGE .
    - docker push $DOCKER_IMAGE

deploy:
  stage: deploy
  only:
    - main
  script:
    - kubectl set image deployment/myapp myapp=$DOCKER_IMAGE
```

## Useful Commands

### Docker

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -d -p 8000:8000 --name myapp myapp:latest

# View logs
docker logs -f myapp

# Execute in container
docker exec -it myapp /bin/sh

# Clean up
docker system prune -a

# List resources
docker ps -a
docker images
docker volume ls
docker network ls
```

### Kubernetes

```bash
# Get resources
kubectl get pods
kubectl get services
kubectl get deployments

# Describe resource
kubectl describe pod <pod-name>

# Logs
kubectl logs -f <pod-name>

# Execute in pod
kubectl exec -it <pod-name> -- /bin/sh

# Apply configuration
kubectl apply -f deployment.yaml

# Scale deployment
kubectl scale deployment myapp --replicas=5

# Rollback
kubectl rollout undo deployment/myapp
```

## Security Checklist

```markdown
- [ ] Use specific image tags, not 'latest'
- [ ] Run as non-root user
- [ ] Scan images for vulnerabilities
- [ ] Use secrets management (not env vars for sensitive data)
- [ ] Limit container resources
- [ ] Enable network policies
- [ ] Use read-only file systems where possible
- [ ] Implement pod security policies
- [ ] Rotate credentials regularly
```

## Monitoring & Logging

```yaml
# Prometheus ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: metrics
    interval: 30s
```

```yaml
# Fluentd sidecar for logging
containers:
- name: myapp
  image: myapp:latest
- name: fluentd
  image: fluent/fluentd:latest
  volumeMounts:
  - name: logs
    mountPath: /var/log/app
```
