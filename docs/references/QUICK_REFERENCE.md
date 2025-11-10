# ⚡ Quick Reference Card

## 🎬 START HERE (Choose One)

### "Just make it work!" (2 minutes)
```powershell
.\start-local-test.bat
# Open http://localhost:8000/dashboard/login (admin/changeme)
```
👉 **See** [`EXECUTE_NOW.md`](EXECUTE_NOW.md)

### "I want to understand it" (5 minutes)
👉 **Read** [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md)

### "Deploy for my friend" (30 minutes)
👉 **Follow** [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)

---

## 🔥 Most Used Commands

| Task | Command |
|------|---------|
| **Start everything locally** | `.\start-local-test.bat` |
| **Start PDF Library app** | `cd webapp && python main.py` |
| **View live dashboard** | Open `http://localhost:8000/dashboard/login` |
| **View metrics** | Open `http://localhost:9090` |
| **View Grafana** | Open `http://localhost:3000` |
| **Check proxy health** | `curl http://localhost:8080/health` |
| **Simulate DDoS attack** | `wrk -t4 -c500 -d10s http://localhost:8080/` |
| **View Docker logs** | `docker logs ddos-proxy` |
| **Stop everything** | `docker-compose -f docker-compose.production.yml down` |

---

## 📊 Dashboard Login

```
URL:      http://localhost:8000/dashboard/login
Username: admin
Password: changeme
```

**Tabs:**
- 📈 **Metrics** - Real-time traffic counts & blocked requests
- 🔒 **Security** - Malicious IPs, attack patterns
- ⚙️ **Settings** - Sensitivity, rate limits, credentials

---

## 🌐 Service Ports

| Service | Port | URL |
|---------|------|-----|
| **DDoS Proxy** | 8080 | http://localhost:8080 |
| **Dashboard** | 8000 | http://localhost:8000 |
| **Prometheus** | 9090 | http://localhost:9090 |
| **Grafana** | 3000 | http://localhost:3000 |
| **Redis** | 6379 | (internal) |
| **PDF Library** | 8001 | http://localhost:8001 |

---

## 📁 Most Important Files

```
├── EXECUTE_NOW.md              👈 Run this first!
├── LOCAL_TEST_GUIDE.md         For testing locally
├── DEPLOYMENT_GUIDE.md         For production
├── PROJECT_SUMMARY.md          To understand it
├── start-local-test.bat        Quick launcher
├── docker-compose.production.yml   Full stack config
├── .env.production             Configuration template
├── app/main.py                 Core application
├── app/dashboard/routes.py     Web dashboard
├── requirements.txt            Python dependencies
└── tests/                      81 passing tests ✅
```

---

## 🔧 Configuration

### Change Target App URL
Edit `.env.production`:
```env
UPSTREAM_BASE_URL=http://your-app:8080
```
Then restart: `docker-compose -f docker-compose.production.yml restart ddos-proxy`

### Change Dashboard Password
Edit `.env.production`:
```env
ADMIN_PASSWORD=newpassword
```

### Adjust Sensitivity
Edit `.env.production`:
```env
SENSITIVITY_LEVEL=low      # Block less, fewer false positives
SENSITIVITY_LEVEL=medium   # Balanced (default)
SENSITIVITY_LEVEL=high     # Block more, stricter detection
```

### Increase Rate Limit
Edit `.env.production`:
```env
REQUEST_RATE_LIMIT=200     # 200 requests per window
```

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8080 already in use | Change port in docker-compose.production.yml |
| Dashboard won't login | Check admin/changeme creds, restart proxy |
| Proxy not forwarding | Check UPSTREAM_BASE_URL in .env, check target app is running |
| Too many blocks | Lower SENSITIVITY_LEVEL to "low" |
| Attacks getting through | Raise SENSITIVITY_LEVEL to "high" |
| Docker containers fail | Check `docker logs ddos-proxy`, ensure port 8080 free |

---

## 📊 Key Metrics

- **Total Requests**: All HTTP requests received
- **Blocked Requests**: Requests flagged as attacks
- **Block Rate**: Percentage of requests blocked
- **P95 Latency**: 95th percentile response time
- **Backend Errors**: 5xx errors from target app

---

## ✅ Success Checklist

After running `start-local-test.bat`:

- [ ] 4 Docker containers running (`docker ps`)
- [ ] Proxy responding to health check (`curl http://localhost:8080/health`)
- [ ] Dashboard accessible (http://localhost:8000)
- [ ] Can login with admin/changeme
- [ ] PDF Library app running (`cd webapp && python main.py`)
- [ ] Proxy forwards traffic (see counts in dashboard)
- [ ] Prometheus scraping metrics (http://localhost:9090)
- [ ] Can simulate attack (`wrk` command)
- [ ] Dashboard shows blocked requests during attack

---

## 🎓 Test the System

### 1. Generate Normal Traffic
```powershell
# Terminal 3: Send normal requests
for ($i = 1; $i -le 10; $i++) {
    curl http://localhost:8080/
}
```
Expected: Dashboard shows 10 requests, 0 blocked

### 2. Simulate Attack
```powershell
# Install wrk (or use Apache Bench)
# Then run:
wrk -t4 -c500 -d10s http://localhost:8080/
```
Expected: Dashboard shows many requests, high block rate

### 3. Check Blocked IPs
- Dashboard → Security tab
- Should show your IP with high threat score

---

## 📞 Getting Help

| Question | File |
|----------|------|
| How do I deploy to production? | [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) |
| What's the architecture? | [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) |
| How do I test locally? | [`LOCAL_TEST_GUIDE.md`](LOCAL_TEST_GUIDE.md) |
| Am I ready to go live? | [`DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md) |
| I want to share with a friend | [`FRIENDS_QUICK_START.md`](FRIENDS_QUICK_START.md) |
| Technical details? | [`docs/`](docs/) folder |

---

## 🎯 Typical Workflow

```
1. Read: EXECUTE_NOW.md (2 min)
   ↓
2. Run: start-local-test.bat (1 min)
   ↓
3. Start: PDF Library app (1 min)
   ↓
4. Test: Normal & attack traffic (10 min)
   ↓
5. Configure: Sensitivity, rate limits (5 min)
   ↓
6. Deploy: Follow DEPLOYMENT_GUIDE.md (30 min)
   ↓
7. Monitor: Check metrics for 24 hours
   ↓
8. Celebrate: DDoS attacks are now blocked! 🎉
```

---

## 🔐 Security Notes

- Change `ADMIN_PASSWORD` from default "changeme" ⚠️
- Use HTTPS in production (TLS termination recommended)
- Store `.env` file securely (not in git)
- Use strong `ADMIN_API_KEY` (generate: `openssl rand -base64 32`)
- Enable Redis AUTH in production
- Review `docs/SECURITY.md` before deploying

---

## 📈 Performance Expectations

| Metric | Typical | Peak |
|--------|---------|------|
| **Throughput** | 500 RPS | 2000 RPS |
| **Latency P95** | 50ms | 100ms |
| **CPU** | 10-15% | 30-40% |
| **Memory** | 300MB | 800MB |
| **Disk** | ~500MB | ~1GB |

*Per container; scales horizontally with Docker/K8s*

---

## 🚀 Next Steps

1. **NOW**: Run `.\start-local-test.bat`
2. **NEXT**: Read `EXECUTE_NOW.md` while it's starting
3. **THEN**: Test with attack simulation
4. **FINALLY**: Deploy using `DEPLOYMENT_GUIDE.md`

---

**Status**: 🟢 **READY TO USE**

*For detailed info, see [`README.md`](README.md)*
