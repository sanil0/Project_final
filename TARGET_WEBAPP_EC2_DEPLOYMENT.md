# Target Webapp - EC2 Deployment (from target-webapp repository)

## 📋 **Quick Deployment Steps**

### **Step 1: Launch EC2 Instance**

Use AWS Console to launch:
- **AMI:** Ubuntu 22.04 LTS
- **Instance Type:** t3.small
- **VPC:** Same as WARP instance
- **Subnet:** Public subnet
- **Security Group:** Create new
  - Inbound: Port 8001 (from WARP security group)
  - Inbound: Port 22 (SSH - from your IP)
- **Key Pair:** DDoS-copilot
- **Storage:** 20GB gp3

**Note down:**
- Public IP: `YOUR_PUBLIC_IP`
- Private IP: `YOUR_PRIVATE_IP`

---

### **Step 2: SSH into Instance**

```powershell
# From Windows
ssh -i "C:\Users\Lenovo\Downloads\DDoS-copilot.pem" ubuntu@YOUR_PUBLIC_IP
```

---

### **Step 3: Install Dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, pip, and git
sudo apt install -y python3 python3-pip git curl
```

---

### **Step 4: Clone Target Webapp Repository**

```bash
# Clone from target-webapp repository (clean, without full Project WARP)
git clone https://github.com/sanil0/target-webapp.git
cd target-webapp

# Install Python dependencies
pip install -r requirements.txt
```

---

### **Step 5: Run the Webapp**

**Option A: Direct Run**
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

**Option B: Background Run (Recommended)**
```bash
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > app.log 2>&1 &
```

**Option C: Using Docker**
```bash
docker build -t target-webapp:latest .
docker run -d -p 8001:8001 -v $(pwd)/pdfs:/app/pdfs target-webapp:latest
```

---

### **Step 6: Test Webapp**

```bash
# From the target instance
curl http://localhost:8001

# From Windows (using public IP)
curl http://YOUR_PUBLIC_IP:8001
```

---

### **Step 7: Update WARP Proxy**

```bash
# SSH into WARP instance
ssh -i "C:\Users\Lenovo\Downloads\DDoS-copilot.pem" ubuntu@ec2-98-88-5-133.compute-1.amazonaws.com

# Update docker-compose.yml
cd ~/Project_final
nano docker-compose.yml
```

Find and update:
```yaml
# From:
UPSTREAM_BASE_URL=http://target-app:8080

# To:
UPSTREAM_BASE_URL=http://YOUR_PRIVATE_IP:8001
```

Save: `Ctrl+X`, `Y`, `Enter`

---

### **Step 8: Restart WARP**

```bash
docker-compose down
docker-compose up -d
docker-compose ps
```

---

### **Step 9: Generate Traffic**

```powershell
# From Windows
# Test the proxy forwarding to target app
curl "http://98.88.5.133:8080/list"
curl "http://98.88.5.133:8080/search?query=DDoS"
```

---

### **Step 10: Verify in Dashboard**

1. Open: `http://98.88.5.133:8080/dashboard/login`
2. Login: `secureadmin` / `YourStrongPassword123!`
3. You should see:
   - ✅ Incoming request count
   - ✅ Traffic metrics
   - ✅ Request patterns
   - ✅ Prometheus data

---

## 🏗️ **Architecture**

```
┌──────────────────────────────────────────────────┐
│              Internet Users                       │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   WARP Proxy Instance      │
        │   98.88.5.133:8080         │
        │ - DDoS Detection           │
        │ - Rate Limiting            │
        │ - Dashboard                │
        └────────────┬────────────────┘
                     │ (clean traffic)
                     ▼
        ┌────────────────────────────┐
        │  Target Webapp Instance    │
        │  YOUR_PRIVATE_IP:8001      │
        │ - PDF Library              │
        │ - Processes requests       │
        │ - Returns data             │
        └────────────────────────────┘
```

---

## 📊 **Files Included in target-webapp Repository**

```
target-webapp/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose config
├── README.md              # Full documentation
├── .gitignore            # Git ignore rules
├── templates/            # HTML templates
│   └── index.html       # Web interface
├── static/              # Static files (CSS, JS)
├── pdfs/                # PDF storage
│   └── .gitkeep        # Keep directory
└── logs/               # Application logs
```

---

## 🚀 **Command Reference**

```bash
# View webapp logs
tail -f app.log

# Check if running
curl http://localhost:8001

# List PDFs
curl http://localhost:8001/list

# Search PDFs
curl "http://localhost:8001/search?query=DDoS"

# Upload PDF
curl -X POST -F "file=@document.pdf" http://localhost:8001/upload

# Stop running process
pkill -f uvicorn

# Check listening ports
netstat -tlnp | grep 8001

# SSH into target instance
ssh -i "path/to/DDoS-copilot.pem" ubuntu@TARGET_PUBLIC_IP

# SSH into WARP instance
ssh -i "path/to/DDoS-copilot.pem" ubuntu@ec2-98-88-5-133.compute-1.amazonaws.com
```

---

## ✅ **Verification Checklist**

- [ ] Target instance launched and running
- [ ] SSH connection working
- [ ] Dependencies installed
- [ ] Webapp cloned from target-webapp repository
- [ ] Webapp running on port 8001
- [ ] Can access http://PRIVATE_IP:8001 from instance
- [ ] Can access http://PUBLIC_IP:8001 from Windows
- [ ] WARP proxy updated with correct private IP
- [ ] WARP proxy restarted
- [ ] Traffic flowing through proxy
- [ ] Dashboard showing metrics

---

## 🔧 **Troubleshooting**

| Issue | Solution |
|-------|----------|
| Can't SSH | Check security group allows port 22 |
| Port 8001 not responding | Check `curl http://localhost:8001` on instance |
| WARP can't reach target | Verify private IP in docker-compose.yml |
| No traffic metrics | Check WARP is forwarding to correct IP:port |
| Permission denied | Use `sudo` or adjust permissions |

---

## 📚 **Additional Resources**

- **Target Webapp Repo:** https://github.com/sanil0/target-webapp
- **Project WARP Repo:** https://github.com/sanil0/Project_final
- **API Documentation:** See README.md in target-webapp repo

---

**Ready to deploy! 🚀**
