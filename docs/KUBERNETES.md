# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster 1.24+
- kubectl configured
- Container registry access (if using private registry)
- Prometheus operator (optional, for metrics)

## Quick Deploy

### 1. Create namespace and secrets

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (update values first!)
kubectl create secret generic ddos-protection-secrets \
  -n ddos-protection \
  --from-literal=admin-api-key=YOUR_SECRET_KEY
```

### 2. Create ConfigMap

```bash
# Update k8s/configmap.yaml with your environment variables
kubectl apply -f k8s/configmap.yaml
```

### 3. Deploy application

```bash
# Deploy with RBAC, storage, and networking
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### 4. Verify deployment

```bash
# Check pod status
kubectl get pods -n ddos-protection

# Check service
kubectl get svc -n ddos-protection

# View logs
kubectl logs -n ddos-protection -l app=ddos-protection -f
```

## Manifests Overview

### Core Manifests
- **namespace.yaml**: Creates isolated namespace
- **deployment.yaml**: Main application with 3 replicas
- **service.yaml**: ClusterIP service for internal access
- **ingress.yaml**: External HTTP/HTTPS access

### Configuration
- **configmap.yaml**: Non-sensitive config (log level, rate limits, etc.)
- **secrets.yaml**: Sensitive values (API keys, passwords)
- **rbac.yaml**: Service account and RBAC roles

### Advanced
- **hpa.yaml**: Horizontal Pod Autoscaler (scales 2-10 replicas)
- **pdb.yaml**: Pod Disruption Budget (ensures availability)
- **networkpolicy.yaml**: Network isolation (optional)
- **storage.yaml**: PersistentVolumes for logs/models

### Monitoring
- **servicemonitor.yaml**: Prometheus monitoring endpoint
- **alertmanager.yaml**: Alert rules for critical events

### Infrastructure
- **cluster-autoscaler.yaml**: Scales nodes based on demand
- **vpa.yaml**: Vertical Pod Autoscaler (right-size resources)

## Production Checklist

- [ ] Update image to production registry
- [ ] Set realistic resource requests/limits
- [ ] Configure ingress with SSL/TLS certificates
- [ ] Set up Prometheus/Grafana for monitoring
- [ ] Create alerting rules for critical issues
- [ ] Configure persistent volumes for logs/models
- [ ] Set up backup/restore procedures
- [ ] Enable network policies for security
- [ ] Configure RBAC with minimal permissions
- [ ] Set up pod security policies

## Environment Variables

```yaml
# Core settings (in ConfigMap)
LOG_LEVEL: INFO
WORKERS: 4
SENSITIVITY_LEVEL: medium
UPSTREAM_BASE_URL: http://target-service:8080
TARGET_URL: http://target-service:8080

# Rate limiting
REQUEST_RATE_LIMIT: 100
SLIDING_WINDOW_SECONDS: 60
BLOCK_DURATION_MINUTES: 30

# ML/Features
ENABLE_MODEL_CACHE: "true"
MODEL_CACHE_TTL_SECONDS: "300"
BATCH_PREDICTION_SIZE: "100"

# Secrets (in Secrets)
ADMIN_API_KEY: <your-secret>
```

## Scaling

### Horizontal Scaling (HPA)

The `hpa.yaml` automatically scales based on CPU:

```yaml
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

View HPA status:
```bash
kubectl get hpa -n ddos-protection
kubectl describe hpa ddos-protection -n ddos-protection
```

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment ddos-protection -n ddos-protection --replicas=5

# Watch scaling in progress
kubectl rollout status deployment/ddos-protection -n ddos-protection
```

## Monitoring

### Prometheus Integration

Prometheus scrapes metrics from `/metrics` endpoint automatically via ServiceMonitor.

Check scrape targets:
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Visit http://localhost:9090/targets
```

### View Logs

```bash
# All pods
kubectl logs -n ddos-protection -l app=ddos-protection --all-containers=true -f

# Specific pod
kubectl logs -n ddos-protection ddos-protection-xxxxx

# Last 100 lines
kubectl logs -n ddos-protection -l app=ddos-protection --tail=100
```

## Troubleshooting

### Pod won't start

```bash
# Check pod events
kubectl describe pod -n ddos-protection ddos-protection-xxxxx

# Check image pull
kubectl get events -n ddos-protection --sort-by='.lastTimestamp'
```

### High latency

```bash
# Check resource usage
kubectl top pods -n ddos-protection

# Check HPA status
kubectl get hpa -n ddos-protection

# Scale up if needed
kubectl scale deployment ddos-protection -n ddos-protection --replicas=5
```

### Metrics not appearing

```bash
# Check ServiceMonitor
kubectl get servicemonitor -n ddos-protection

# Verify Prometheus scrape config
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Check http://localhost:9090/targets
```

## Rollout & Updates

### Rolling Update

```bash
# Update image
kubectl set image deployment/ddos-protection \
  -n ddos-protection \
  ddos-protection=myregistry.azurecr.io/ddos-protection:v1.1

# Watch rollout
kubectl rollout status deployment/ddos-protection -n ddos-protection

# Rollback if needed
kubectl rollout undo deployment/ddos-protection -n ddos-protection
```

### Zero-downtime Deployment

The deployment uses:
- `RollingUpdate` strategy
- `maxSurge: 1`, `maxUnavailable: 0`
- Health probes to verify readiness

## Resource Cleanup

```bash
# Delete entire deployment
kubectl delete namespace ddos-protection

# Or delete individual resources
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml
```

## Example: Full Production Deploy

```bash
#!/bin/bash
set -e

NAMESPACE=ddos-protection
IMAGE=myregistry.azurecr.io/ddos-protection:v1.0

# Create namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic ddos-protection-secrets \
  -n $NAMESPACE \
  --from-literal=admin-api-key=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply configs
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/storage.yaml

# Update image and deploy
sed "s|ddos-protection:latest|$IMAGE|g" k8s/deployment.yaml | kubectl apply -f -
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Set up monitoring
kubectl apply -f k8s/servicemonitor.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml

echo "✅ Deployment complete!"
kubectl get all -n $NAMESPACE
```
