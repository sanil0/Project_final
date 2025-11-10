# Docker & Deployment Guide

## Building the Docker Image

Build locally:
```bash
docker build -t project_warp:latest .
```

Build with custom tag for registry:
```bash
docker build -t myregistry.azurecr.io/project_warp:v1.0 .
```

## Running Locally

```bash
docker run -d \
  -p 8080:8080 \
  -e UPSTREAM_BASE_URL="http://target-app:8080" \
  -e TARGET_URL="http://target-app:8080" \
  -e SENSITIVITY_LEVEL="medium" \
  --name ddos_guard \
  project_warp:latest
```

Check health:
```bash
docker logs ddos_guard
curl http://localhost:8080/health
```

## Environment Variables

Required:
- `UPSTREAM_BASE_URL`: Base URL of the upstream service (e.g., http://localhost:3000)
- `TARGET_URL`: Target URL to protect (e.g., http://localhost:3000)

Optional (with defaults):
- `SENSITIVITY_LEVEL`: low / medium / high (default: medium)
- `REQUEST_RATE_LIMIT`: Max requests per window (default: 5)
- `SLIDING_WINDOW_SECONDS`: Time window in seconds (default: 60)
- `BLOCK_DURATION_MINUTES`: How long to block IPs (default: 30)

## Docker Compose

Run with docker-compose (see `docker-compose.yml`):
```bash
docker-compose up -d
```

## Kubernetes Deployment

See `k8s/` directory for manifests:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Image Details

- **Base**: `python:3.11-slim` (minimal runtime footprint)
- **Size**: ~300MB (optimized multi-stage build)
- **User**: Non-root `appuser` for security
- **Port**: 8080
- **Health Check**: curl-based, 30s interval
- **Volumes**: `/app/logs`, `/app/models`
