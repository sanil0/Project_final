# Deployment Checklist for DDoS Protection Proxy

## Pre-Deployment Planning

- [ ] **Target Application Details**
  - [ ] Web app URL/IP and port (e.g., http://10.0.1.50:8080)
  - [ ] Expected traffic volume (requests/sec)
  - [ ] Peak traffic time windows
  - [ ] Backend health check endpoint (e.g., /health, /status)
  - [ ] Required headers/cookies to preserve (User-Agent, Authorization, etc.)

- [ ] **Network & Security**
  - [ ] Proxy server IP/hostname assigned
  - [ ] DNS records prepared (or will update after proxy runs)
  - [ ] Security group rules drafted (allow ports 80/443 inbound, allow outbound to target)
  - [ ] TLS certificates obtained or generated (if terminating TLS on proxy)
  - [ ] Firewall rules allowed between proxy and target

- [ ] **Monitoring & Alerting**
  - [ ] Alert recipients identified (email, Slack, PagerDuty, etc.)
  - [ ] Alerting thresholds decided (blocked rate %, latency threshold, etc.)
  - [ ] Log destination chosen (local files, CloudWatch, ELK, Splunk, etc.)

- [ ] **Backup & Disaster Recovery**
  - [ ] Rollback procedure documented
  - [ ] Original DNS/ALB configuration saved
  - [ ] Health check procedure defined

## Environment Setup

- [ ] **Install Prerequisites**
  - [ ] Docker installed (v20+)
  - [ ] Docker Compose installed (v1.29+)
  - [ ] Linux/macOS or Windows with WSL2/Hyper-V

- [ ] **Create Required Directories**
  ```bash
  mkdir -p logs certs models grafana-dashboards
  chmod 755 logs
  ```

- [ ] **Configure .env File**
  - [ ] Copy `.env.production` to `.env`
  - [ ] Edit UPSTREAM_BASE_URL (target app address)
  - [ ] Change DASHBOARD_USER and DASHBOARD_PASS (strong credentials)
  - [ ] Set ADMIN_API_KEY (random secure string)
  - [ ] Verify SENSITIVITY_LEVEL (start with 'medium')
  - [ ] Review all settings and document any customizations

- [ ] **Prepare TLS Certificates (if needed)**
  - [ ] Place TLS cert in `./certs/tls.crt`
  - [ ] Place TLS key in `./certs/tls.key`
  - [ ] Set TLS_CERT_PATH and TLS_KEY_PATH in .env

## Build & Start

- [ ] **Build Docker Image**
  ```bash
  docker build -t ddos-protection:latest .
  ```
  Or skip if using pre-built image.

- [ ] **Start Services**
  ```bash
  # Option 1: Using deploy script
  ./deploy.sh start  # macOS/Linux
  deploy.bat start   # Windows
  
  # Option 2: Manual Docker Compose
  docker-compose -f docker-compose.production.yml up -d
  ```

- [ ] **Wait for Startup**
  - [ ] All containers running (`docker ps` shows 4 services: proxy, prometheus, grafana, redis)
  - [ ] No ERROR logs in `docker logs ddos-proxy`
  - [ ] Health check passes: `curl http://localhost:8080/health`

## Functional Testing

- [ ] **Proxy Connectivity**
  - [ ] Test proxy to target: `curl -v http://localhost:8080/`
  - [ ] Expected: Response from target app (or error if target unreachable)
  - [ ] Check latency: should be < 100ms if local network

- [ ] **Dashboard Access**
  - [ ] Open http://localhost:8000/dashboard/login
  - [ ] Login with DASHBOARD_USER credentials
  - [ ] Dashboard loads with no errors
  - [ ] Metrics tab shows data

- [ ] **Prometheus Metrics**
  - [ ] Open http://localhost:9090
  - [ ] Query: `ddos_requests_total` (should show metric)
  - [ ] Query: `ddos_blocked_requests` (should show 0 or low values)

- [ ] **Grafana Visualization**
  - [ ] Open http://localhost:3000 (admin/admin123)
  - [ ] Verify Prometheus data source is connected
  - [ ] Create basic dashboard showing request rates

## Load & Attack Testing

- [ ] **Generate Legitimate Traffic**
  - [ ] Use tool like `wrk`, `hey`, or `ab`
  - [ ] Example (10 sec, 50 concurrent):
    ```bash
    wrk -t2 -c50 -d10s http://localhost:8080/
    ```
  - [ ] Observe: Requests counted in dashboard (should mostly be "allowed")

- [ ] **Simulate DDoS Attack**
  - [ ] From external machine (different IP/network), run aggressive requests:
    ```bash
    wrk -t4 -c500 -d30s http://localhost:8080/
    ```
  - [ ] Observe: Blocked requests increase in dashboard
  - [ ] Logs show detection of attack patterns
  - [ ] Verify attack detection accuracy (low false positive rate)

- [ ] **Monitor Under Load**
  - [ ] Dashboard updates in real-time (or near real-time)
  - [ ] Prometheus scrapes metrics successfully
  - [ ] No out-of-memory or CPU 100% issues
  - [ ] Latency remains acceptable (< 500ms)

## Pre-Production Hardening

- [ ] **Security**
  - [ ] Change all default passwords
  - [ ] Restrict dashboard access (port 8000) to admin IPs only via firewall
  - [ ] Restrict Prometheus/Grafana ports to internal network only
  - [ ] Enable TLS if exposing publicly (use ALB + TLS or proxy-side TLS)
  - [ ] Review security group rules for principle of least privilege

- [ ] **Secrets Management**
  - [ ] Move credentials to secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
  - [ ] Don't commit .env to version control
  - [ ] Rotate API keys periodically

- [ ] **Logging & Monitoring**
  - [ ] Set up log shipping (e.g., to CloudWatch, ELK, Splunk)
  - [ ] Configure Prometheus data retention (30+ days)
  - [ ] Set up alerting rules:
    - High blocked rate (e.g., > 5% for 2 min)
    - Backend health failures (5xx errors > 1%)
    - Metrics export failure

- [ ] **Backup & Disaster Recovery**
  - [ ] Document restore procedure
  - [ ] Test backup of Prometheus/Grafana data
  - [ ] Have rollback plan ready (switch DNS back to original target)

## Production Deployment

- [ ] **Update DNS / Traffic Routing**
  - [ ] Option A: Update DNS A record to proxy server IP
  - [ ] Option B: If behind ALB, update ALB target
  - [ ] Option C: If friend updates client config, point to proxy URL
  - [ ] Verify DNS propagation: `nslookup proxy.example.com`

- [ ] **Monitor First 1 Hour**
  - [ ] Watch dashboard for normal traffic patterns
  - [ ] Check logs for errors or unexpected blocks
  - [ ] Verify latency acceptable (compare before/after if possible)
  - [ ] Validate backend responses (status codes, headers, body)

- [ ] **Adjust Sensitivity if Needed**
  - [ ] If too many false positives: lower SENSITIVITY_LEVEL to "low"
  - [ ] If too lenient: raise to "high"
  - [ ] Restart proxy after changing: `docker-compose restart ddos-proxy`

- [ ] **Enable Backups (if persistent storage needed)**
  - [ ] Configure Prometheus backup
  - [ ] Backup Grafana dashboards (export JSON)
  - [ ] Automate backups (cron job or cloud provider backup)

## Post-Deployment Validation

- [ ] **24-Hour Stability Check**
  - [ ] All services running without restart
  - [ ] Dashboard shows continuous data (no gaps)
  - [ ] No alert spam
  - [ ] Legitimate requests passing through (low block rate)

- [ ] **Incident Simulation**
  - [ ] Simulate proxy failure: stop container, verify failover or alert
  - [ ] Simulate backend failure: stop target app, verify error handling
  - [ ] Verify graceful degradation

- [ ] **Documentation**
  - [ ] Document final configuration (scrubbed of secrets)
  - [ ] Create runbook for on-call team
  - [ ] Document escalation procedures
  - [ ] Create troubleshooting guide

## Ongoing Operations (Monthly/Quarterly)

- [ ] **Review Metrics & Logs**
  - [ ] Check false positive rate
  - [ ] Review blocked attacks (are they real threats?)
  - [ ] Identify trends (attack patterns, peak times)

- [ ] **Update & Patch**
  - [ ] Pull latest Docker images for security patches
  - [ ] Test in staging first
  - [ ] Apply patches during maintenance window

- [ ] **Rotate Credentials**
  - [ ] Rotate dashboard password
  - [ ] Rotate API keys
  - [ ] Rotate TLS certificates (before expiration)

- [ ] **Capacity Planning**
  - [ ] Review resource usage (CPU, memory, disk)
  - [ ] Identify if scaling needed
  - [ ] Plan for growth

---

## Quick Reference

### Start Deployment
```bash
# macOS/Linux
./deploy.sh start

# Windows
deploy.bat start
```

### Check Status
```bash
docker-compose -f docker-compose.production.yml ps
```

### View Logs
```bash
docker-compose -f docker-compose.production.yml logs -f ddos-proxy
```

### Stop & Rollback
```bash
docker-compose -f docker-compose.production.yml down
# Revert DNS/ALB to original target
```

### Common Metrics to Monitor
- `ddos_requests_total` - Total requests processed
- `ddos_blocked_requests` - Total blocked requests
- `ddos_block_rate` - Blocked / Total ratio
- Request latency (p50, p95, p99)
- Backend error rate (5xx responses)

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Approval:** _______________
**Notes:** _______________
