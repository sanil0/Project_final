# 🚀 Project WARP - Complete Deployment Guide

**Date**: November 6, 2025  
**Status**: ✅ Ready to Deploy  
**Version**: 1.0.0

---

## 📋 Deployment Options

You have 3 deployment paths:

### **Option 1: Docker Compose** ⭐ (EASIEST - Recommended)
- **Time**: 5-10 minutes
- **Complexity**: Low
- **Best For**: Testing, staging, local deployment
- **Includes**: App + Prometheus + Grafana + Redis + AlertManager

### **Option 2: Docker** (Single Server Production)
- **Time**: 10-15 minutes
- **Complexity**: Medium
- **Best For**: Single server deployment, small-medium workloads
- **Includes**: Container-based isolation, resource limits

### **Option 3: Kubernetes** (Enterprise Production)
- **Time**: 20-30 minutes
- **Complexity**: High
- **Best For**: Cloud, high availability, auto-scaling, large workloads
- **Includes**: Auto-scaling, load balancing, self-healing, monitoring

---

## 🎯 Phase 1: Pre-Deployment Setup

### Step 1: Verify Application Status
```powershell
# Check all tests pass
python -m pytest app/tests/ -v --cov=app
# Expected: ✅ 55/55 PASS

# Verify imports
python test_import.py
# Expected: ✅ All imports successful

# Check startup
python test_startup.py
# Expected: ✅ Application initializes
```

### Step 2: Update Configuration for Production

Edit `app/config.py` to update production settings:

```python
# CRITICAL: Change these for production!
DASHBOARD_USER = "your_secure_username"  # Change from "admin"
DASHBOARD_PASS = "your_secure_password"  # Change from "changeme"
DASHBOARD_HTTPS_ONLY = True             # Enable HTTPS only
DASHBOARD_SECURE_COOKIES = True         # Secure session cookies
```

### Step 3: Update Environment Variables

Create `.env` file (don't commit to git!):

```bash
# Production Settings
ENVIRONMENT=production
DEBUG=false

# Dashboard
DASHBOARD_USER=your_username
DASHBOARD_PASS=your_secure_password
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000

# DDoS Settings
DDOS_THRESHOLD=100
DDOS_WINDOW_SECONDS=60

# Database
DATABASE_URL=postgresql://user:pass@host:5432/project_warp

# Redis (if using)
REDIS_URL=redis://localhost:6379

# Upstream Target
UPSTREAM_TARGET=https://your-api.example.com
```

### Step 4: Security Hardening Checklist

- [ ] Change default credentials
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up VPN/bastion host access
- [ ] Enable audit logging
- [ ] Configure backup strategy
- [ ] Set up monitoring/alerting
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Rotate API keys

---

## 📦 Phase 2: Choose Deployment Option

### **🐳 Option 1: Docker Compose (EASIEST - Recommended First)**

```powershell
# 1. Build the image
docker build -t project_warp:v1.0.0 .

# 2. Start all services
docker-compose up -d

# 3. Verify services running
docker-compose ps

# 4. Check logs
docker-compose logs -f app

# 5. Access dashboard
# Browser: http://localhost:8000/dashboard/login

# 6. Monitor with Prometheus
# Browser: http://localhost:9091

# 7. View Grafana dashboards
# Browser: http://localhost:3000 (admin/admin)
```

**What Gets Deployed:**
- ✅ Project WARP app (port 8000)
- ✅ Prometheus (port 9091)
- ✅ Grafana (port 3000)
- ✅ Redis (port 6379) - optional
- ✅ AlertManager (port 9093)

**Files Used:**
- `docker-compose.yml`
- `Dockerfile`
- `docker-entrypoint.sh`

---

### **🐋 Option 2: Docker (Single Server Production)**

```powershell
# 1. Build production image
docker build -t project_warp:v1.0.0 .

# 2. Run container with environment
docker run -d `
  --name project_warp `
  --restart unless-stopped `
  -p 8000:8000 `
  -e ENVIRONMENT=production `
  -e DEBUG=false `
  -e DASHBOARD_USER="secure_user" `
  -e DASHBOARD_PASS="secure_pass" `
  -v /data/project_warp:/app/data `
  -v /etc/ssl/certs:/etc/ssl/certs:ro `
  project_warp:v1.0.0

# 3. Verify running
docker ps
docker logs project_warp

# 4. Health check
Invoke-WebRequest http://localhost:8000/health

# 5. Setup reverse proxy (nginx/Apache)
# Point nginx to http://localhost:8000
```

**What You Need:**
- Docker engine
- Reverse proxy (nginx/Apache) for HTTPS
- SSL certificates
- Volume for data persistence
- Monitoring solution (optional)

---

### **☸️ Option 3: Kubernetes (Enterprise Production)**

```powershell
# 1. Create namespace
kubectl create namespace ddos-protection

# 2. Apply RBAC
kubectl apply -f k8s/rbac.yaml -n ddos-protection

# 3. Create secrets
kubectl create secret generic ddos-secrets `
  --from-literal=admin-user="secure_user" `
  --from-literal=admin-pass="secure_pass" `
  -n ddos-protection

# 4. Apply ConfigMaps
kubectl apply -f k8s/configmap.yaml -n ddos-protection

# 5. Deploy application
kubectl apply -f k8s/deployment.yaml -n ddos-protection

# 6. Create service
kubectl apply -f k8s/service.yaml -n ddos-protection

# 7. Setup ingress
kubectl apply -f k8s/ingress.yaml -n ddos-protection

# 8. Configure auto-scaling
kubectl apply -f k8s/hpa.yaml -n ddos-protection

# 9. Setup monitoring
kubectl apply -f k8s/servicemonitor.yaml -n ddos-protection

# 10. Verify deployment
kubectl rollout status deployment/ddos-protection -n ddos-protection
kubectl get pods -n ddos-protection
```

**What You Get:**
- ✅ Auto-scaling (2-10 pods)
- ✅ Load balancing
- ✅ Self-healing
- ✅ Rolling updates
- ✅ Resource management
- ✅ Network policies
- ✅ Pod disruption budgets
- ✅ Prometheus integration

**Requirements:**
- Kubernetes cluster (1.20+)
- kubectl configured
- Persistent storage (PV/PVC)
- Ingress controller
- Prometheus Operator (optional)

---

## 🔍 Phase 3: Post-Deployment Verification

### Health Checks

```powershell
# 1. Service Health
Invoke-WebRequest http://localhost:8000/health

# 2. Metrics Endpoint
Invoke-WebRequest http://localhost:8000/metrics

# 3. Dashboard Access
# Open: http://localhost:8000/dashboard/login
# Login: admin / changeme

# 4. API Endpoints
curl http://localhost:8000/api/dashboard/metrics
curl http://localhost:8000/api/dashboard/traffic
curl http://localhost:8000/api/dashboard/events
```

### Verification Checklist

- [ ] Application starts without errors
- [ ] Dashboard login works
- [ ] Charts display data
- [ ] Metrics endpoint returns data
- [ ] Health check passes
- [ ] Logs show no errors
- [ ] Prometheus scrapes metrics
- [ ] Grafana dashboards populate
- [ ] Alerts trigger correctly
- [ ] All tests still pass

---

## 📊 Phase 4: Monitoring Setup

### Prometheus Metrics

Available metrics at: `http://localhost:8000/metrics`

```
ddos_requests_total             # Total requests
ddos_blocked_total              # Blocked requests
ddos_detection_confidence       # Detection confidence
ddos_response_time_seconds      # Response time
ddos_active_threats             # Current threats
```

### Grafana Dashboards

**Default Access:**
- URL: `http://localhost:3000`
- Username: `admin`
- Password: `admin` (change in production!)

**Pre-built Dashboards:**
1. Overview - Key metrics
2. Traffic Analysis - Request patterns
3. Security Threats - Attack detection
4. Performance - Latency & throughput
5. System Resources - CPU, Memory, Disk

### Alerting Rules

Configured alerts:

```
- High request rate (>10k/min)
- High detection rate (>5%)
- Response time spike (>500ms)
- Memory usage >80%
- CPU usage >80%
- Service unavailable
```

---

## 🔒 Phase 5: Security Hardening

### SSL/TLS Setup

```powershell
# Generate self-signed cert (testing only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Or use Let's Encrypt (production)
certbot certonly --standalone -d your.domain.com
```

### Firewall Rules

```
Port 8000   - Application (restrict to load balancer only)
Port 9090   - Prometheus (restrict to ops team)
Port 3000   - Grafana (restrict to ops team)
Port 443    - HTTPS (public if needed)
```

### Environment Variables

Set these before deployment:

```bash
ENVIRONMENT=production
DEBUG=false
DASHBOARD_HTTPS_ONLY=true
DASHBOARD_SECURE_COOKIES=true
CORS_ORIGINS=["https://your-domain.com"]
```

---

## 📈 Phase 6: Performance Tuning

### Uvicorn Settings

```python
# app/main.py - Update before deployment
app = FastAPI(...)

# Run with:
# python -m uvicorn app.main:app \
#   --workers 4 \
#   --worker-class uvicorn.workers.UvicornWorker \
#   --bind 0.0.0.0:8000
```

### Recommended Resources

```
CPU:    2-4 cores
Memory: 2-4 GB
Disk:   20-50 GB
Network: 1 Gbps +
```

---

## ✅ Deployment Timeline

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Pre-deployment setup | 5 min | 📋 Ready |
| 2 | Update credentials | 5 min | 📋 Ready |
| 3 | Deploy (choose option) | 10-30 min | 🚀 Next |
| 4 | Verification | 10 min | 📋 Ready |
| 5 | Monitoring setup | 15 min | 📋 Ready |
| 6 | Security hardening | 20 min | 📋 Ready |
| **Total** | | **60-75 min** | |

---

## 🎯 Recommended Deployment Path

### **For Testing/Staging:**
1. ✅ Update credentials (Phase 2)
2. ✅ Run `docker-compose up -d` (Option 1)
3. ✅ Verify health checks (Phase 3)
4. ✅ Access dashboard at http://localhost:8000/dashboard/login

**Time: ~20 minutes**

### **For Production (Single Server):**
1. ✅ Update credentials (Phase 2)
2. ✅ Build Docker image (Option 2)
3. ✅ Run with Docker
4. ✅ Setup nginx reverse proxy with SSL
5. ✅ Configure monitoring

**Time: ~45 minutes**

### **For Production (Enterprise):**
1. ✅ Update credentials (Phase 2)
2. ✅ Push image to registry (Option 3)
3. ✅ Deploy to Kubernetes cluster
4. ✅ Setup ingress & SSL
5. ✅ Configure monitoring & alerting

**Time: ~60-75 minutes**

---

## 🆘 Troubleshooting

### Docker won't start?
```powershell
docker logs project_warp
# Check docker-entrypoint.sh permissions
```

### Port already in use?
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Permission denied errors?
```powershell
# Run with elevated privileges
docker run --privileged ...
```

### Logs not showing?
```powershell
docker-compose logs -f app
kubectl logs -f deployment/ddos-protection
```

---

## 📚 See Also

- **[docs/DOCKER.md](DOCKER.md)** - Docker-specific documentation
- **[docs/KUBERNETES.md](KUBERNETES.md)** - Kubernetes deployment guide
- **[docs/MONITORING.md](MONITORING.md)** - Monitoring & alerting setup
- **[docs/SECURITY.md](SECURITY.md)** - Security hardening guide
- **[docs/PERFORMANCE.md](PERFORMANCE.md)** - Performance tuning guide
- **[docs/CHECKLIST.md](CHECKLIST.md)** - Pre-deployment checklist

---

**Status**: ✅ **READY TO DEPLOY**  
**Next**: Choose deployment option and update credentials
