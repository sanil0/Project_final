# ⚡ ULTRA-QUICK START (30 Seconds)

## 🚀 Just Run This (5 minutes to see it working)

### Terminal 1:
```powershell
.\start-local-test.bat
```

### Terminal 2:
```powershell
cd webapp
python main.py
```

### Browser:
```
http://localhost:8000/dashboard/login
Username: admin
Password: changeme
```

---

## Done! ✅

You just saw:
- ✅ DDoS proxy running (port 8080)
- ✅ Live dashboard (port 8000)
- ✅ Metrics collection (port 9090)
- ✅ Visualization (port 3000)
- ✅ Protected webapp (port 8001)

**That's it!** Your apps are protected.

---

## 📚 Want to Learn More?

| Time | Read |
|------|------|
| **5 min** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **10 min** | [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) |
| **30 min** | [LOCAL_TEST_GUIDE.md](LOCAL_TEST_GUIDE.md) |
| **1 hour** | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |

---

## 🎯 Next Steps

1. **Test Attack**: `wrk -t4 -c500 -d10s http://localhost:8080/`
2. **Watch Dashboard**: See attacks get blocked
3. **Deploy**: Follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
4. **Done**: You're protected! 🛡️

---

**Need help?** → [START_HERE.md](START_HERE.md)
