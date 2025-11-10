# DDoS Protection Proxy - Deployment Guide

## Overview
This guide walks through deploying the DDoS protection proxy in front of your friend's web application to protect it from DDoS attacks. The proxy analyzes incoming traffic, detects and blocks malicious patterns, and forwards legitimate traffic to the target application.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Internet / Public Traffic                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼───────────┐
        │  DDoS Protection Proxy │
        │  (Port 80/443)         │
        │                        │
        │ - Detect & Block       │
        │ - Rate Limit           │
        │ - ML-based Analysis    │
        └────────────┬───────────┘
                     │
        ┌────────────▼──────────────────────┐
        │  Dashboard & Metrics              │
        │  (Port 8000 - Internal)           │
        │  (Port 9090 - Prometheus)         │
        │  (Port 3000 - Grafana)            │
        └─────────────────────────────────────┘
                     │
        ┌────────────▼────────────────┐
        │  Friend's Web App           │
        │  (Internal/Private Network) │
        │  (e.g., 10.0.1.50:8080)     │
        └─────────────────────────────┘
```

## Prerequisites

- Docker & Docker Compose installed
- Target web app endpoint (URL or IP:port)
- Minimum 2GB RAM for the full stack (proxy + Prometheus + Grafana)
- Network access to the target web app from the proxy

## Step-by-Step Deployment

### Step 1: Prepare Configuration

1. **Copy and edit the production environment file:**
   ```bash
   cp .env.production .env
   ```

2. **Edit `.env` with your specific settings:**
   ```bash
   # Change these to your friend's app details:
   UPSTREAM_BASE_URL=https://friend-app.example.com:443
   # or for internal network:
   UPSTREAM_BASE_URL=http://10.0.1.50:8080
   
   # Change dashboard credentials (IMPORTANT!)
   DASHBOARD_USER=yourusername
   DASHBOARD_PASS=VerySecurePassword123!
   
   # Set admin API key
   ADMIN_API_KEY=your-secure-api-key-$(openssl rand -hex 16)
   
   # Adjust sensitivity if needed (low, medium, high)
   SENSITIVITY_LEVEL=medium
   
   # Set Prometheus URL
   PROMETHEUS_URL=http://prometheus:9090
   ```

### Step 2: Create Required Directories

```bash
mkdir -p {logs,certs,models,grafana-dashboards}
chmod 755 logs
```

### Step 3: Build Docker Image (Optional - if using local Dockerfile)

```bash
docker build -t ddos-protection:latest .
```

Or use the pre-built image if available.

### Step 4: Start the Stack

```bash
# Using production compose file:
docker-compose -f docker-compose.production.yml up -d

# Or with environment file:
docker-compose -f docker-compose.production.yml --env-file .env up -d
```

**Wait 15-30 seconds for all services to start.**

### Step 5: Verify Services are Running

```bash
# Check container status:
docker-compose -f docker-compose.production.yml ps

# Check proxy health:
curl -s http://localhost:8080/health | jq .

# Check dashboard (should require login):
curl -s http://localhost:8000/dashboard/login | grep -i "login"
```

### Step 6: Access Dashboard and Services

Once running, access:
- **Dashboard**: http://localhost:8000/dashboard/login
  - Username: (from DASHBOARD_USER in .env)
  - Password: (from DASHBOARD_PASS in .env)
  - Features: View metrics, traffic analysis, blocked IPs, settings

- **Prometheus**: http://localhost:9090
  - Query raw metrics
  - See scrape status

- **Grafana**: http://localhost:3000
  - Username: admin
  - Password: admin123
  - Setup dashboards with Prometheus data source

### Step 7: Configure DNS/Traffic Routing

**Option A: Direct IP/Domain (Same Network)**
```bash
# Point DNS to the proxy server:
A record: proxy.example.com -> 1.2.3.4  (proxy server IP)

# Then friend's users access proxy instead of their app:
# Before: https://app.example.com
# After:  https://proxy.example.com (routes to the proxy)
```

**Option B: Update Upstream URL (Easier for Testing)**
- The proxy forwards to the UPSTREAM_BASE_URL you set in .env
- Friend's app stays at original URL
- You just point traffic to proxy

**Option C: Load Balancer / ALB**
```bash
# Put the proxy behind an AWS ALB or similar:
ALB -> Proxy (port 80) -> Friend's App
```

### Step 8: Test the Proxy is Working

#### Functional Test (Legitimate Traffic)
```bash
# Test direct proxy:
curl -v http://localhost:8080/

# If UPSTREAM_BASE_URL is httpbin.org, you should get a 200 response
# If it's your friend's app, you should get their app response

# Test dashboard login:
curl -X POST http://localhost:8000/dashboard/login \
  -d "username=yourusername&password=YourPassword123!" \
  -L
```

#### Simulated DDoS Test (Detect & Block)
```bash
# Install wrk (load testing tool):
# Ubuntu/Debian: sudo apt-get install wrk
# macOS: brew install wrk
# Windows: download from https://github.com/wg/wrk/releases

# Simulate attack (rapid requests from single IP):
wrk -t4 -c200 -d10s http://localhost:8080/

# Monitor in dashboard:
# - Should see "Blocked" requests increase
# - Request rate graph should spike
# - Check "Security" tab for detected threats
```

#### Check Metrics in Prometheus
```bash
# Visit: http://localhost:9090
# In "Graph" tab, search for:
# - ddos_requests_total (total requests)
# - ddos_blocked_requests (blocked count)
# - ddos_detection_rate (detection accuracy)
```

### Step 9: Configure Grafana Dashboards

1. **Log in to Grafana:** http://localhost:3000 (admin/admin123)
2. **Add Prometheus Data Source:**
   - Settings > Data Sources > Add
   - Name: Prometheus
   - URL: http://prometheus:9090
   - Save & Test

3. **Create Dashboard:**
   - Create > Dashboard > Add Panel
   - Query: Select Prometheus data source
   - Use metrics like:
     ```
     rate(ddos_requests_total[5m])
     rate(ddos_blocked_requests[5m])
     ```

4. **Set Alerts (Optional):**
   - Go to Alerting > Alert Rules
   - Create rule: Alert if blocked_rate > 5% for 2 minutes

### Step 10: Monitor Logs

```bash
# View proxy logs:
docker-compose -f docker-compose.production.yml logs -f ddos-proxy

# View all services logs:
docker-compose -f docker-compose.production.yml logs -f

# Or check log file in ./logs/ directory
tail -f logs/*.log
```

### Step 11: Production Hardening Checklist

- [ ] Change dashboard credentials (strong password)
- [ ] Change admin API key
- [ ] Set UPSTREAM_BASE_URL to your friend's actual app
- [ ] Review SENSITIVITY_LEVEL and adjust if needed (too many false positives? → lower)
- [ ] Enable TLS/HTTPS if public internet:
  - Place behind AWS ALB with TLS termination
  - Or configure TLS certs in proxy (TLS_CERT_PATH, TLS_KEY_PATH)
- [ ] Restrict security groups to allowed source IPs
- [ ] Enable logging to centralized log store (ELK, CloudWatch, etc.)
- [ ] Set up alerts for:
  - High blocked request rate (> 10% for 5 min)
  - Backend health failures (5xx errors)
  - Sudden traffic spike
- [ ] Test backup/restore process
- [ ] Document runbook for operations team

## Troubleshooting

### Issue: Proxy Can't Reach Target App
```bash
# Check connectivity:
docker exec ddos-proxy ping 10.0.1.50

# Check logs for connection errors:
docker-compose -f docker-compose.production.yml logs ddos-proxy | grep -i "error\|timeout"

# Verify UPSTREAM_BASE_URL is correct:
docker exec ddos-proxy env | grep UPSTREAM
```

### Issue: Dashboard Login Not Working
```bash
# Check dashboard logs:
docker-compose -f docker-compose.production.yml logs ddos-proxy | grep -i "login"

# Verify credentials in .env:
cat .env | grep DASHBOARD
```

### Issue: High Latency
```bash
# Check proxy resource usage:
docker stats ddos-proxy

# Lower sensitivity if too many checks causing delays:
# Edit .env: SENSITIVITY_LEVEL=low
# Restart: docker-compose -f docker-compose.production.yml restart ddos-proxy
```

### Issue: Services Won't Start
```bash
# Check for port conflicts:
netstat -an | grep -E "8080|8000|9090|3000"

# Check Docker logs:
docker logs ddos-proxy

# Try stopping all and restarting:
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

## Scaling & High Availability

For production with high traffic:

1. **Run multiple proxy instances behind a load balancer**
   ```yaml
   # Add to docker-compose:
   ddos-proxy-1:
     ...
     ports:
       - "8001:8080"
   ddos-proxy-2:
     ...
     ports:
       - "8002:8080"
   
   # Then ALB/LB routes to both
   ```

2. **Use managed services:**
   - AWS ECS / EKS for container orchestration
   - AWS ALB for load balancing
   - AWS CloudWatch for logging
   - AWS SNS for alerts

3. **Persist metrics:**
   - Move Prometheus data to external storage
   - Use RDS or managed Prometheus
   - Archive dashboards to S3

## Rollback Procedure

If issues occur:

```bash
# 1. Stop the proxy:
docker-compose -f docker-compose.production.yml stop ddos-proxy

# 2. Point traffic back to original target (update DNS or ALB)

# 3. Check what went wrong:
docker logs ddos-proxy | tail -100

# 4. Fix (update .env, rebuild, etc.)

# 5. Restart:
docker-compose -f docker-compose.production.yml up -d ddos-proxy

# 6. Validate before pointing traffic back
```

## Next Steps

1. **Customize sensitivity:** Run with real traffic, monitor false positive rate, tune SENSITIVITY_LEVEL
2. **Add custom rules:** Update detection thresholds in `app/config.py`
3. **Integrate with SIEM:** Send logs to Splunk, ELK, or cloud provider
4. **Test failover:** Simulate proxy failure, ensure traffic can failover
5. **Performance test:** Use `wrk`, `hey`, or `siege` to measure baseline latency and throughput

## Support & Further Reading

- Dashboard guides: `docs/README.md`
- Configuration reference: `docs/configuration.md`
- Security hardening: `docs/SECURITY.md`
- Performance tuning: `docs/PERFORMANCE.md`
- Monitoring setup: `docs/MONITORING.md`
- Kubernetes deployment: `docs/KUBERNETES.md`

---

**Last Updated:** November 7, 2025
**Status:** Production-Ready
