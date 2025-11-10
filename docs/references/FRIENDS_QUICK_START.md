# 🛡️ Quick Start Guide for Your Friend

## Your Friend's Perspective: "I Need to Protect My Web App"

This guide explains what your friend needs to know to protect their web application using the DDoS protection proxy.

---

## What This Does

You run a **reverse proxy** in front of your friend's web app. It:
- ✅ Detects incoming DDoS attacks in real-time
- ✅ Blocks malicious traffic automatically
- ✅ Allows legitimate users through
- ✅ Shows live dashboards with attack status
- ✅ Alerts when attacks occur

```
Internet Traffic
       ↓
   [DDoS Proxy] ← Analyzes & blocks attacks
       ↓
[Friend's Web App] ← Only legitimate traffic
```

---

## Setup Overview

### What You Need
1. Server/VM to run the proxy (2GB RAM, 1 CPU minimum)
2. Docker installed on that server
3. Friend's app URL/IP and port

### Time Required
- First-time setup: **10-15 minutes**
- Testing: **10 minutes**
- Going live: **5 minutes**

### Cost
- Infrastructure: Same as before (proxy runs on existing VM/server)
- No additional licensing needed

---

## Simple 3-Step Deployment

### Step 1: Prepare Configuration (5 min)

```bash
# On the proxy server, run:
cp .env.production .env
```

Edit the `.env` file:
```bash
# Set your friend's app URL
UPSTREAM_BASE_URL=https://friend-app.example.com:443

# Set strong dashboard password (change this!)
DASHBOARD_PASS=MySecurePassword123!

# Set admin API key (make it random and long)
ADMIN_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Step 2: Start the Proxy (3 min)

#### Option A: Automatic (Recommended)

**macOS/Linux:**
```bash
./deploy.sh start
```

**Windows:**
```cmd
deploy.bat start
```

#### Option B: Manual

```bash
docker-compose -f docker-compose.production.yml up -d
```

Wait 30 seconds for all services to start.

### Step 3: Update DNS / Traffic Routing (2 min)

Tell everyone to use the proxy instead of the app directly.

**Option A: Update DNS** (Easiest)
```
Old:  app.example.com → 1.2.3.4 (Friend's app)
New:  app.example.com → 5.6.7.8 (Proxy server)
```

**Option B: Use Load Balancer**
```
ALB (facing internet) → Proxy (port 80) → Friend's App (internal)
```

---

## After Deployment: Access Points

Once running, access:

| What | URL | Login |
|------|-----|-------|
| **Dashboard** | http://proxy-server:8000/dashboard/login | Username from .env / Password from .env |
| **Prometheus** | http://proxy-server:9090 | (No login) |
| **Grafana** | http://proxy-server:3000 | admin / admin123 |
| **Proxy API** | http://proxy-server:8080 | Your app traffic |

### Dashboard Features
- 📊 **Overview:** Real-time request & block counts
- 📈 **Traffic:** Graphs of requests over time
- 🚨 **Security:** Active threats & blocked IPs
- ⚙️ **Settings:** Configuration & sensitivity

---

## How to Know It's Working

### Check 1: Proxy Health
```bash
curl http://localhost:8080/health
# Should return: {"status": "healthy"}
```

### Check 2: Traffic is Flowing
```bash
curl http://localhost:8080/
# Should get response from friend's app
```

### Check 3: Dashboard Shows Activity
- Open http://localhost:8000/dashboard/login
- Login with your credentials
- Should see metrics (request count, latency, etc.)

### Check 4: Attack Detection Works
```bash
# From another computer/network, send aggressive traffic:
wrk -t4 -c500 -d10s http://proxy-server:8080/

# Then check dashboard:
# Should see "Blocked" count increase
# Dashboard shows attack detection
```

---

## If Something Goes Wrong

### Proxy Not Responding
```bash
# Check if containers are running:
docker ps

# Check logs for errors:
docker logs ddos-proxy

# Restart:
docker-compose -f docker-compose.production.yml restart ddos-proxy
```

### Can't Reach Friend's App Through Proxy
```bash
# Verify target is correct:
grep UPSTREAM_BASE_URL .env

# Test direct connection to target:
curl UPSTREAM_BASE_URL_VALUE

# Check security groups/firewall allows proxy → target
```

### Dashboard Shows Errors
```bash
# Restart all services:
docker-compose -f docker-compose.production.yml restart

# Wait 30 seconds and try again
```

---

## Regular Monitoring

### Daily
- ✅ Check dashboard shows activity (no all-zeros)
- ✅ Verify no error logs: `docker logs ddos-proxy | grep ERROR`

### Weekly
- ✅ Review blocked requests (normal for attacks)
- ✅ Check Prometheus graphs for trends

### Monthly
- ✅ Review false positive rate
- ✅ Adjust sensitivity if needed (in .env)
- ✅ Rotate dashboard password

---

## Tuning for Your Friend's App

### Too Many False Positives? (Legitimate Users Blocked)
Reduce sensitivity:
```bash
# Edit .env:
SENSITIVITY_LEVEL=low

# Restart:
docker-compose -f docker-compose.production.yml restart ddos-proxy
```

### Attacks Getting Through? (Blocked Rate Too Low)
Increase sensitivity:
```bash
# Edit .env:
SENSITIVITY_LEVEL=high

# Restart:
docker-compose -f docker-compose.production.yml restart ddos-proxy
```

---

## Common Questions

### Q: Will this slow down my app?
**A:** Minimal impact. Proxy adds ~10-50ms latency depending on network. Most apps won't notice.

### Q: What if the proxy goes down?
**A:** Temporarily, users can't reach the app. Keep proxy running 24/7. Have a rollback plan.

### Q: Does it cost money?
**A:** No additional cost. Uses same infrastructure. Prometheus/Grafana are free.

### Q: Can I scale this?
**A:** Yes! Run multiple proxy instances behind a load balancer.

### Q: Does it work with HTTPS?
**A:** Yes! Set `UPSTREAM_BASE_URL=https://...` if target is HTTPS.

### Q: What attacks does it block?
**A:** Volumetric (flooding), TCP flag manipulation, protocol-level, slow attacks, and more via ML model.

---

## Rollback Procedure (Go Back to Normal)

If you want to stop using the proxy:

```bash
# 1. Stop the proxy:
docker-compose -f docker-compose.production.yml down

# 2. Update DNS/ALB back to friend's app (revert Step 3)
#    Old:  app.example.com → 1.2.3.4 (Friend's app)

# 3. Verify traffic is flowing normally
curl https://friend-app.example.com

# Done! Proxy is now offline
```

---

## Emergency Contact / Support

For issues:
1. Check logs: `docker logs ddos-proxy | tail -50`
2. Check dashboard for error messages
3. Try restarting: `docker-compose -f docker-compose.production.yml restart`
4. If stuck, review full guide: `DEPLOYMENT_GUIDE.md`

---

## Advanced Topics (Optional)

- **Kubernetes deployment:** See `docs/KUBERNETES.md`
- **Custom rules:** See `docs/CONFIGURATION.md`
- **Performance tuning:** See `docs/PERFORMANCE.md`
- **Security hardening:** See `docs/SECURITY.md`

---

## Summary

```
✅ Configure .env with friend's app URL
✅ Run ./deploy.sh start (or deploy.bat start)
✅ Update DNS to point to proxy
✅ Verify in dashboard
✅ Monitor for attacks
✅ Adjust sensitivity if needed
✅ Done! App is now protected
```

---

**Status:** 🟢 Ready to Protect Your Friend's App  
**Next Step:** Edit `.env` and run deploy script
