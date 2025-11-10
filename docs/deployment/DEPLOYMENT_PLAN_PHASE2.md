# 🚀 Project WARP Deployment - Phase 2: Testing & Docker

## Current Status
✅ **Full DDoS detection system deployed and running on http://127.0.0.1:8080**

All core services initialized:
- SlidingWindowStore ✅
- FeatureExtractor ✅
- DetectionEngine ✅
- MitigationController ✅
- UpstreamHTTPClient ✅
- TelemetryClient ✅

---

## Phase 1: Live Testing (Current)

### Option A: Quick Manual Tests

**Test 1: Health Check**
```bash
curl http://127.0.0.1:8080/health
```
Expected: `{"status": "healthy", "version": "1.0.0"}`

**Test 2: Dashboard**
```bash
curl http://127.0.0.1:8080/dashboard/login
```
Expected: HTML login page

**Test 3: HTTP Forwarding**
```bash
curl http://127.0.0.1:8080/get?test=1
```
Expected: JSON response from httpbin.org with your query

**Test 4: POST Forwarding**
```bash
curl -X POST http://127.0.0.1:8080/post \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}'
```
Expected: JSON response echoing your data

**Test 5: Metrics**
```bash
curl http://127.0.0.1:8080/metrics
```
Expected: Prometheus metrics in text format

### Option B: Automated Test Script

```powershell
# While proxy is running in another terminal
cd d:\project_warp
d:\project_warp\.venv\Scripts\python.exe quick_test.py
```

Or with batch file:
```cmd
cd d:\project_warp
test.bat
```

---

## Phase 2: DDoS Attack Simulation

### Setup: Generate Test Traffic

**Generate Normal Traffic (Baseline)**
```bash
# Single request every 2 seconds
for i in {1..10}; do 
  curl -s http://127.0.0.1:8080/get?req=$i > /dev/null
  sleep 2
done
```

**Simulate DDoS Attack (Burst)**
```bash
# Rapid requests (~200 per second)
for i in {1..200}; do 
  curl -s http://127.0.0.1:8080/get?attack=$i > /dev/null &
done
wait
```

### Expected Behavior
- ✅ Normal requests: All succeed (200 OK)
- ✅ Attack requests: Should see 429 (Rate Limited) or 403 (Blocked)
- ✅ Dashboard: Should show attack events in metrics
- ✅ Logs: Should see "🛑 Blocking request" messages

### Monitor During Attack
In another terminal, watch the proxy logs:
```bash
# Watch for detection events
tail -f logs/app.log | grep -E "Blocking|attack|detection"
```

---

## Phase 3: Docker Deployment

### Step 1: Build Docker Image

```bash
cd d:\project_warp

# Build the image
docker build -t project-warp:latest .
```

### Step 2: Run with Docker Compose

Start the full monitoring stack:
```bash
# Starts: Proxy, Prometheus, Grafana, Redis
docker-compose -f docker-compose.yml up -d
```

Services:
- **Proxy**: http://localhost:8080
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### Step 3: Deploy to Kubernetes (Optional)

```bash
# Create namespace
kubectl create namespace warp

# Deploy using manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n warp
```

---

## Phase 4: Advanced Features

### Enable Redis Caching
Edit `app/config.py`:
```python
REDIS_ENABLED = True
REDIS_URL = "redis://localhost:6379/0"
```

### Configure Advanced Alerting
Edit `app/config.py`:
```python
ALERT_THRESHOLD = 500  # requests/minute
ALERT_EMAIL = "admin@example.com"
```

### Performance Tuning
```python
# Increase rate limit
MitigationController(
    request_rate_limit=500,  # Up from 100
    sliding_window_seconds=60
)

# Add caching
FeatureExtractor(
    cache_enabled=True,
    cache_ttl=300  # 5 minutes
)
```

---

## Monitoring Dashboard

### Access Grafana
```
http://localhost:3000
User: admin
Password: admin
```

### Key Metrics
- Requests per second (by IP)
- Attack detection rate
- Blocked requests
- Response time p50/p95/p99
- CPU/Memory usage

### Create Custom Dashboard
1. Open Grafana
2. Click "New Dashboard"
3. Add Prometheus data source: `http://prometheus:9090`
4. Create panels:
   - `rate(requests_total[1m])` - Request rate
   - `rate(blocked_requests_total[1m])` - Block rate
   - `detection_engine_verdict{action="block"}` - Blocks
   - `rate(response_time_seconds_sum[1m])` - Response time

---

## Testing Commands Summary

### Quick Health Check
```bash
curl http://127.0.0.1:8080/health
```

### Test Forwarding
```bash
# GET
curl http://127.0.0.1:8080/get
curl http://127.0.0.1:8080/post

# PUT
curl -X PUT http://127.0.0.1:8080/put -d "test"

# DELETE
curl -X DELETE http://127.0.0.1:8080/delete
```

### Load Test with Apache Bench
```bash
# Normal load
ab -n 100 -c 10 http://127.0.0.1:8080/get

# High load (attack simulation)
ab -n 1000 -c 50 http://127.0.0.1:8080/get
```

### Load Test with wrk
```bash
# 4 threads, 100 connections, 30 seconds
wrk -t4 -c100 -d30s http://127.0.0.1:8080/get
```

---

## File Structure

```
d:\project_warp\
├── app/
│   ├── main.py              # 🔧 Main FastAPI app (UPDATED)
│   ├── config.py            # Configuration
│   ├── services/
│   │   ├── detector.py      # ML detection
│   │   ├── mitigation.py    # Rate limiting
│   │   ├── http_client.py   # 🔧 Forwarding (UPDATED)
│   │   └── ...
│   └── dashboard/
│       └── routes.py        # Dashboard endpoints
├── models/
│   ├── ddos_model.joblib    # Trained ML model
│   └── features.joblib      # Feature encoder
├── docker-compose.yml       # Docker stack
├── k8s/                     # Kubernetes manifests
├── start_simple.py          # 🚀 Start script
├── test_deployment.py       # Comprehensive tests
├── quick_test.py            # Quick tests
├── test.bat                 # Batch test script
├── DEPLOYMENT_STATUS.md     # 📊 Current status
└── DEPLOYMENT_PLAN_PHASE2.md # This file
```

---

## Troubleshooting

### Proxy Won't Start
```bash
# Check if port 8080 is in use
netstat -ano | findstr :8080

# Kill process using port
taskkill /PID <PID> /F
```

### Detection Not Working
```bash
# Check model files exist
ls -la models/ddos_model.joblib
ls -la models/features.joblib

# Verify initialization in logs
tail -20 logs/app.log | grep "All DDoS"
```

### Slow Response Time
```bash
# Check CPU/Memory
Get-Process python | Select-Object Name, CPU, Memory

# Enable debug logging
export LOG_LEVEL=DEBUG

# Restart proxy
python start_simple.py
```

---

## Success Criteria

### ✅ Phase 1 Complete When
- [ ] All 5 manual tests passing
- [ ] Health endpoint returns 200
- [ ] Dashboard loads login page
- [ ] Forwarding echoes back request data
- [ ] Metrics endpoint returns data

### ✅ Phase 2 Complete When
- [ ] Normal traffic shows 200 OK
- [ ] Attack traffic shows 429/403
- [ ] Dashboard shows attack metrics
- [ ] Logs show detection events
- [ ] Rate limiting triggered correctly

### ✅ Phase 3 Complete When
- [ ] Docker image builds successfully
- [ ] Docker Compose starts all services
- [ ] Proxy accessible at http://localhost:8080
- [ ] Grafana dashboard working
- [ ] Prometheus collecting metrics

### ✅ Phase 4 Complete When
- [ ] Redis caching working
- [ ] Advanced alerts configured
- [ ] Performance optimized
- [ ] Full test suite passing (158/158)
- [ ] Ready for production

---

## Next Steps

1. **Immediate** (5 min): Run quick tests to verify deployment
2. **Short-term** (15 min): Simulate DDoS attack and monitor detection
3. **Medium-term** (30 min): Deploy Docker and test monitoring
4. **Long-term**: Optimize, secure, and deploy to production

---

**Status**: 🟢 READY FOR TESTING
**Last Updated**: 2025-11-07
**Next Phase**: Live Testing & Attack Simulation
