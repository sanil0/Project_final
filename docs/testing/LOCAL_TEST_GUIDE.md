# Local Testing: Deploying DDoS Proxy for Our Webapp

This guide shows how to protect our own PDF Library webapp with the DDoS protection proxy.

## Architecture for Local Testing

```
┌──────────────────────────────────────┐
│  Your Browser / Load Test Tool       │
└──────────────────────┬───────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  DDoS Protection Proxy      │
        │  (Port 8080)                │
        │  Listens for attacks        │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  PDF Library Webapp         │
        │  (Port 8001)                │
        │  Protected!                 │
        └─────────────────────────────┘

Dashboard & Monitoring:
  - Dashboard: http://localhost:8000
  - Prometheus: http://localhost:9090
  - Grafana: http://localhost:3000
```

## Step 1: Configure the Proxy

Edit `.env` to forward to our local webapp:

```bash
cp .env.production .env
```

Edit the file:
```
UPSTREAM_BASE_URL=http://localhost:8001
DASHBOARD_USER=admin
DASHBOARD_PASS=changeme
LISTEN_HOST=0.0.0.0
LISTEN_PORT=8080
SENSITIVITY_LEVEL=medium
PROMETHEUS_URL=http://prometheus:9090
```

## Step 2: Start the PDF Library Webapp

In one terminal (from project root):

```bash
cd webapp
pip install -r requirements.txt
python main.py
# Should start on: http://localhost:8001
```

Or in another PowerShell window:
```powershell
cd D:\project_warp\webapp
python main.py
```

Wait for startup: `Uvicorn running on http://127.0.0.1:8001`

## Step 3: Start the DDoS Protection Proxy

From another terminal (project root):

**Option A - Windows (Easiest):**
```powershell
.\deploy.bat start
```

**Option B - Manual:**
```powershell
docker-compose -f docker-compose.production.yml up -d
```

Wait 30 seconds for all services to start.

## Step 4: Verify Everything is Working

### Test 1: Direct Access to Webapp (Without Proxy)
```bash
curl http://localhost:8001/
# Should return PDF Library HTML
```

### Test 2: Access Through Proxy
```bash
curl http://localhost:8080/
# Should also return PDF Library HTML (proxied)
```

### Test 3: Dashboard Access
Open in browser: http://localhost:8000/dashboard/login
- Login: admin / changeme
- Should see empty metrics (ready to capture traffic)

### Test 4: Send Some Legitimate Traffic
```bash
# From PowerShell:
for ($i = 0; $i -lt 10; $i++) {
    curl http://localhost:8080/ > $null
}

# Check dashboard - should see 10 requests
```

## Step 5: Simulate a DDoS Attack

Install load testing tool:
```bash
# Windows: Use this or download from https://github.com/wg/wrk/releases
# Or use Apache Bench (comes with Apache):
# Or use hey: go install github.com/rakyll/hey@latest
```

Simulate attack (from PowerShell):
```powershell
# If you have wrk installed:
wrk -t4 -c500 -d10s http://localhost:8080/

# Or use hey (simple):
# hey -n 1000 -c 100 http://localhost:8080/

# Or use simple loop (slower):
for ($i = 0; $i -lt 100; $i++) {
    curl http://localhost:8080/ -s > $null &
}
```

Watch the dashboard while traffic flows:
- http://localhost:8000/dashboard/login
- Should see "Blocked" count increase if attack pattern detected
- "Traffic" tab shows request spikes
- "Security" tab shows detected threats

## Step 6: View Metrics in Prometheus

Open: http://localhost:9090

Search for:
```
ddos_requests_total
ddos_blocked_requests
ddos_block_rate
```

Should show metrics from the traffic you just sent.

## Step 7: View Dashboards in Grafana

Open: http://localhost:3000
- Username: admin
- Password: admin123

Create a simple graph:
1. Click "+" → Dashboard
2. Add Panel
3. Query: `rate(ddos_requests_total[5m])`
4. Should show request rate graph

## What You Should See

### During Normal Traffic (Legitimate Users)
```
Dashboard:
  ✅ Requests: Increasing (matched to your traffic)
  ✅ Blocked: 0 or very low
  ✅ Block Rate: < 1%
  ✅ Status: All green
```

### During Simulated Attack
```
Dashboard:
  ✅ Requests: Spiking high
  ✅ Blocked: Increasing rapidly
  ✅ Block Rate: > 5-10%
  ✅ Security Tab: Shows detected threats
  ✅ Latency: May increase slightly
```

## Monitoring the Proxy

### View Live Logs
```bash
docker-compose -f docker-compose.production.yml logs -f ddos-proxy
```

Should show:
```
INFO - DDoS Protection initialized
INFO - Model loaded from models
INFO - {"client_ip": "127.0.0.1", "action": "allow", "severity": "low", ...}
```

### Check Proxy Health
```bash
curl http://localhost:8080/health
# Should return: {"status":"ok"}
```

## Troubleshooting

### Proxy Can't Connect to Webapp
```bash
# Check if webapp is running:
netstat -an | findstr 8001

# Try direct connection to webapp:
curl http://localhost:8001/

# If that works, check .env UPSTREAM_BASE_URL is correct
```

### Dashboard Not Loading
```bash
# Check if all containers are running:
docker ps

# Restart:
docker-compose -f docker-compose.production.yml restart
```

### High Latency Through Proxy
- Sensitivity too high? Lower it: SENSITIVITY_LEVEL=low
- Proxy running out of resources? Check: docker stats ddos-proxy

## Cleanup

When done testing:

```bash
# Stop proxy and monitoring:
docker-compose -f docker-compose.production.yml down

# Stop webapp:
# (Press Ctrl+C in the webapp terminal)
```

## What This Demonstrates

✅ **Real DDoS Detection:** Proxy analyzes actual traffic patterns  
✅ **Attack Blocking:** Malicious traffic is blocked, legitimate allowed  
✅ **Live Dashboard:** Real-time monitoring of attacks  
✅ **Metrics & Alerts:** Prometheus + Grafana integration  
✅ **Production Ready:** Same setup works for friend's webapp later  

## Next Steps

After testing locally:
1. Adjust SENSITIVITY_LEVEL based on false positive rate
2. Review metrics to understand traffic patterns
3. Setup alerts in Grafana for high blocked rate
4. Document findings
5. Deploy to friend's infrastructure when ready

---

**You now have:**
- ✅ DDoS proxy protecting the webapp
- ✅ Live dashboard showing attacks
- ✅ Prometheus metrics for analysis
- ✅ Grafana dashboards for visualization
- ✅ All logs available for review

The same setup works for protecting any web application!
