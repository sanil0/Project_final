# 📋 Project WARP - Complete Index

**DDoS Protection Proxy with ML Detection, Real-time Dashboard & Kubernetes Ready**

🚀 **START HERE:** Choose what you want to do:

| Goal | File | Time |
|------|------|------|
| 🎬 **See it working NOW** | [`EXECUTE_NOW.md`](EXECUTE_NOW.md) | 2 min read, 1 min run |
| 📖 **Understand the project** | [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) | 5 min |
| 🚀 **Deploy to production** | [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) | 15 min read, 30 min deploy |
| 👥 **Share with a friend** | [`FRIENDS_QUICK_START.md`](FRIENDS_QUICK_START.md) | 3 min |
| 🧪 **Test locally first** | [`LOCAL_TEST_GUIDE.md`](LOCAL_TEST_GUIDE.md) | 8 min |
| ✅ **Pre-deployment checklist** | [`DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md) | 15 min |

## ✨ What You Get

- ✅ ML-powered DDoS detection (real-time threat analysis)
- ✅ Live dashboard for monitoring & control
- ✅ Prometheus + Grafana metrics integration
- ✅ Docker containerization for easy deployment
- ✅ Automated deployment scripts
- ✅ 81 passing tests
- ✅ Comprehensive documentation
- ✅ Works with ANY web application
- ✅ Production-ready & scalable

## 📊 Performance

| Metric | Value |
|--------|-------|
| Throughput | 1000-2000 RPS per instance |
| P95 Latency | < 100ms |
| P99 Latency | < 200ms |
| Memory Usage | 500MB-2GB |
| CPU | 15-25% @ 1000 RPS |
| Availability SLO | 99.9% |

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export UPSTREAM_BASE_URL="http://localhost:3000"
export TARGET_URL="http://localhost:3000"
export ADMIN_API_KEY=$(openssl rand -base64 32)

# Run application
uvicorn app.main:app --reload --port 8080
```

### Docker

```bash
docker build -t project_warp:latest .
docker run -p 8080:8080 \
  -e UPSTREAM_BASE_URL="http://target:8080" \
  -e TARGET_URL="http://target:8080" \
  project_warp:latest
```

### Docker Compose (Full Stack)

Includes app + Prometheus + Grafana:

```bash
docker-compose up -d
```

Access points:
- **Application**: http://localhost:8080
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (admin/admin)

### Kubernetes

```bash
# Deploy to cluster
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify deployment
kubectl get pods -n ddos-protection
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[DOCKER.md](DOCKER.md)** | Docker build, image optimization, local testing |
| **[MONITORING.md](MONITORING.md)** | Prometheus metrics, Grafana dashboards, alerting rules |
| **[docs/KUBERNETES.md](docs/KUBERNETES.md)** | K8s deployment, scaling, HPA, troubleshooting |
| **[docs/SECURITY.md](docs/SECURITY.md)** | Security hardening, TLS, RBAC, compliance |
| **[docs/PERFORMANCE.md](docs/PERFORMANCE.md)** | SLOs, tuning parameters, capacity planning |

## ⚙️ Configuration

### Essential Environment Variables

```env
# Core URLs
UPSTREAM_BASE_URL=http://origin:8080
TARGET_URL=http://origin:8080

# DDoS Protection
SENSITIVITY_LEVEL=medium                  # low | medium | high
REQUEST_RATE_LIMIT=100                    # Req/window
SLIDING_WINDOW_SECONDS=60                 # Window duration
BLOCK_DURATION_MINUTES=30                 # IP block duration

# ML Model Caching
ENABLE_MODEL_CACHE=true
MODEL_CACHE_TTL_SECONDS=300

# Admin API
ADMIN_API_KEY=<secure-key>                # Generate: openssl rand -base64 32
```

See `app/config.py` for complete configuration options.

## 🧪 Testing

```bash
# Run all tests (81 tests, 95%+ coverage)
pytest -v --cov=app

# Load tests
pytest tests/load/ -v

# Security scanning
bandit -r app
safety check -r requirements.txt
```

## 📈 Monitoring & Observability

### Health Endpoint

```bash
curl http://localhost:8080/health
# { "status": "healthy", "version": "1.0.0" }
```

### Metrics Endpoint

```bash
curl http://localhost:8080/metrics
# Prometheus format metrics
```

### Key Metrics

- `ddos_requests_total` - Total requests processed
- `ddos_requests_blocked_total` - Blocked by reason (high_risk, rate_limited)
- `ddos_request_duration_seconds` - Latency histogram
- `ddos_risk_score` - Risk score distribution
- `ddos_model_inference_seconds` - ML model performance
- `ddos_active_blocked_ips` - Currently blocked IPs

### Grafana Dashboards

Pre-built dashboards available in `monitoring/grafana/`.

Import queries:
```promql
# Block rate
rate(ddos_requests_blocked_total[5m]) / rate(ddos_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(ddos_request_duration_seconds_bucket[5m]))

# Requests per second
rate(ddos_requests_total[1m])
```

## 🔐 Security

| Layer | Implementation |
|-------|-----------------|
| **Transport** | HTTPS/TLS 1.3+ with modern ciphers |
| **Auth** | API key validation, RBAC |
| **Secrets** | Encrypted K8s secrets with rotation |
| **Network** | NetworkPolicy isolation, zero-trust |
| **Scanning** | Trivy, bandit in CI/CD |
| **Logging** | Audit logs, structured logging |

See [docs/SECURITY.md](docs/SECURITY.md) for full hardening guide.

## 🏗️ Architecture

```
┌─────────────┐
│   Internet  │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│   Load Balancer (Nginx/ALB) │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────────────┐
│  Project WARP (DDoS Protection)     │
│  ├─ Request Analysis               │
│  ├─ ML-based Detection             │
│  ├─ Rate Limiting                  │
│  └─ IP Blocking & Reputation       │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────┐
│ Target Application  │
│ (Protected Service) │
└─────────────────────┘
```

## 📋 Project Structure

```
app/
  main.py                    # FastAPI entry point
  config.py                  # Pydantic configuration (v2)
  schemas.py                 # Request/response models
  middleware/
    ddos_protection.py       # Main middleware logic
  services/
    detector.py              # ML detection engine
    mitigation.py            # Blocking/rate limiting
    metrics.py               # Prometheus instrumentation
    prediction_service.py    # ML model service
    feature_mapping.py       # Feature extraction
tests/
  app/tests/test_ddos_middleware.py   # 81 tests, >95% coverage
  load/                              # Load testing
monitoring/
  prometheus/prometheus.yml          # Scrape config
  grafana/                           # Dashboard provisioning
k8s/
  deployment.yaml            # Main deployment
  service.yaml               # Kubernetes service
  hpa.yaml                   # Horizontal Pod Autoscaler
  networkpolicy.yaml         # Network isolation
  rbac.yaml                  # Access control
.github/workflows/
  ci.yml                     # GitHub Actions CI/CD
```

## 🚀 Deployment

### Docker

```bash
# Build
docker build -t project_warp:latest .

# Push to registry
docker tag project_warp:latest myregistry.azurecr.io/project_warp:v1.0
docker push myregistry.azurecr.io/project_warp:v1.0
```

### Kubernetes

```bash
# Production deployment
kubectl apply -f k8s/
kubectl rollout status deployment/ddos-protection -n ddos-protection

# Monitor
kubectl port-forward -n ddos-protection svc/prometheus 9090:9090
kubectl port-forward -n ddos-protection svc/grafana 3000:3000
```

### Scaling

```bash
# Horizontal scaling
kubectl scale deployment ddos-protection --replicas=5 -n ddos-protection

# Auto-scaling (configured in hpa.yaml)
kubectl get hpa -n ddos-protection
```

## 📞 Troubleshooting

### High Latency

```bash
# Check resource usage
kubectl top pods -n ddos-protection

# Check metrics
kubectl port-forward svc/prometheus 9091:9090
# View http://localhost:9091

# Scale if needed
kubectl scale deployment ddos-protection --replicas=5 -n ddos-protection
```

### Pod Not Starting

```bash
# Check events
kubectl describe pod <pod-name> -n ddos-protection

# Check logs
kubectl logs -n ddos-protection -l app=ddos-protection --tail=100
```

### Metrics Not Appearing

```bash
# Verify ServiceMonitor
kubectl get servicemonitor -n ddos-protection

# Check Prometheus targets
kubectl port-forward svc/prometheus 9091:9090
# Visit http://localhost:9091/targets
```

## 🧪 CI/CD Pipeline

GitHub Actions workflow (.github/workflows/ci.yml):

✅ **Lint & Type Checks**: flake8, mypy  
✅ **Unit Tests**: 81 tests with coverage  
✅ **Security Scanning**: bandit, trivy  
✅ **Docker Build**: Multi-stage optimized build  
✅ **Registry Push**: Push to GHCR/private registry  

## 📊 Test Results

```
81 passed in 113s (0:01:53)
Coverage: >95%
Zero Pydantic deprecation warnings
All load tests passing
```

## 📝 API Examples

### Health Check

```bash
curl http://localhost:8080/health
```

### Admin: Add to Blocklist

```bash
curl -X POST http://localhost:8080/admin/blocklist \
  -H "X-Admin-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.0.2.1", "reason": "malicious"}'
```

### Metrics

```bash
curl http://localhost:8080/metrics | grep ddos_
```

## 🔄 Updates & Maintenance

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
pytest -v  # Verify compatibility
```

### Rotate Secrets (K8s)

```bash
kubectl delete secret ddos-protection-secrets -n ddos-protection
kubectl create secret generic ddos-protection-secrets \
  -n ddos-protection \
  --from-literal=admin-api-key=$(openssl rand -base64 32)
kubectl rollout restart deployment/ddos-protection -n ddos-protection
```

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

Built with:
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation
- **scikit-learn** - ML detection
- **Prometheus** - Metrics & monitoring
- **Kubernetes** - Container orchestration
- **Starlette** - ASGI middleware

---

**Status**: ✅ **Production Ready**

Version: 1.0.0 | Tests: 81/81 passing | Coverage: >95%
