# Deploy Target Webapp - EC2 Instance Setup Guide

## 🚀 **Option 1: AWS Console (Easiest for Beginners)**

### **STEP 1: Log into AWS Console**

1. Go to https://console.aws.amazon.com
2. Sign in with your AWS credentials
3. Select **Region: US East (N. Virginia)** (same as your existing instance)
4. Search for **EC2** in the search bar
5. Click on **EC2** service

---

## 📋 **STEP 2: Launch New Instance**

### **2.1 - Navigate to Instances**
1. In the EC2 Dashboard, click **Instances** (left sidebar)
2. Click **Launch Instances** button (blue button, top right)

### **2.2 - Name Your Instance**
1. **Name:** `project-warp-target-app`
2. **Description:** Target webapp for DDoS protection testing

---

## 🖼️ **STEP 3: Select AMI (Operating System)**

### **3.1 - Choose Ubuntu Image**
1. Look for **Ubuntu Server 22.04 LTS free tier eligible**
2. Click to select it
3. Keep default settings

**Key Details:**
- AMI ID: `ami-0c55b159cbfafe1f0` (Ubuntu 22.04 LTS)
- Free tier eligible: ✅ Yes
- Architecture: 64-bit (x86)

---

## 🖥️ **STEP 4: Instance Type**

### **4.1 - Select Instance Type**
1. Choose: **t3.small** (same as your existing instance)
2. Keep default settings
3. Click **Next: Configure Instance Details**

**Specifications:**
- vCPU: 2
- Memory: 2 GB
- Network Performance: Low to Moderate
- Cost: ~$0.0208/hour (within free tier limits with shared resources)

---

## 🔐 **STEP 5: Configure Instance Details**

### **5.1 - Network Settings**
1. **VPC:** Select your existing VPC: `vpc-02cf162f3d8ba8912` (or your WARP VPC)
2. **Subnet:** Select: `subnet-0539f094baa074fa7` (Public Subnet - same as WARP instance)
3. **Auto-assign Public IP:** Enable
4. **IAM instance profile:** Leave as default
5. **Click Next: Add Storage**

---

## 💾 **STEP 6: Storage Configuration**

### **6.1 - EBS Volume**
1. **Size:** 20 GB (sufficient for webapp + PDF storage)
2. **Volume type:** gp3 (General Purpose SSD)
3. **Delete on termination:** ✅ Checked
4. **Encrypted:** Can leave unchecked for testing
5. **Click Next: Add Tags**

---

## 🏷️ **STEP 7: Add Tags**

### **7.1 - Tag Your Instance**
Click **Add tag** and create:

| Key | Value |
|-----|-------|
| Name | project-warp-target-app |
| Project | Project-WARP |
| Environment | production |
| Role | target-webapp |

**Click Next: Configure Security Group**

---

## 🔒 **STEP 8: Security Group Configuration** ⚠️ IMPORTANT

### **8.1 - Create New Security Group**

1. Select: **Create a new security group**
2. **Security group name:** `project-warp-target-sg`
3. **Description:** Security group for WARP target webapp
4. Click **Add rule** for inbound traffic

### **8.2 - Add Inbound Rules**

**Rule 1: Allow WARP Proxy Traffic**
- Type: **Custom TCP**
- Protocol: **TCP**
- Port Range: **8001**
- Source: **Custom** → Enter WARP instance security group ID or IP
  - Option A: Enter security group: `sg-06b9910afd1074d78`
  - Option B: Enter IP: `98.88.5.133/32`
- Description: `Allow from WARP proxy`

**Rule 2: Allow SSH (for you to manage)**
- Type: **SSH**
- Protocol: **TCP**
- Port Range: **22**
- Source: **My IP** (or 0.0.0.0/0 for anywhere)
- Description: `SSH access`

**Outbound Rules:** Leave default (allow all)

---

## 🔑 **STEP 9: Key Pair Selection** ⚠️ IMPORTANT

### **9.1 - Select or Create Key Pair**

1. **Key pair name:** Select existing: **DDoS-copilot**
   - This is the same key you use for WARP instance
   - You already have it at: `C:\Users\Lenovo\Downloads\DDoS-copilot.pem`

2. Click **Launch Instances**

---

## ✅ **STEP 10: Verify Launch**

### **10.1 - Confirmation Page**
1. You should see: "Successfully initiated launch of instance..."
2. Click **View all instances** or **Instances** in sidebar
3. Look for your new instance: `project-warp-target-app`

### **10.2 - Wait for Running State**
| Column | Expected Value |
|--------|----------------|
| **State** | running (green) |
| **Status Checks** | 2/2 passed |
| **Public IPv4** | Will appear (e.g., 54.123.45.67) |
| **Private IPv4** | Will appear (e.g., 10.0.1.50) |

**Wait 2-3 minutes for instance to fully initialize**

---

## 📝 **STEP 11: Note Down Instance Details**

Once running, **save these values:**

```
Instance ID:      [e.g., i-0abc123def456]
Public IP:        [e.g., 54.123.45.67]
Private IP:       [e.g., 10.0.1.50]
Security Group:   [project-warp-target-sg]
Key Pair:         DDoS-copilot.pem
```

---

## 🚀 **STEP 12: Connect to New Instance (SSH)**

### **12.1 - From Windows PowerShell**
```powershell
# Replace with your actual Public IP from Step 11
$target_ip = "54.123.45.67"

# SSH into the instance
ssh -i "C:\Users\Lenovo\Downloads\DDoS-copilot.pem" ubuntu@$target_ip
```

### **12.2 - Accept Host Key**
- Type `yes` when prompted to accept host key
- You should now be connected to the new instance

---

## 🔧 **STEP 13: Setup Webapp on Target Instance**

### **13.1 - Update System**
```bash
sudo apt update
sudo apt upgrade -y
```

### **13.2 - Install Dependencies**
```bash
sudo apt install -y python3 python3-pip git curl wget
```

### **13.3 - Clone Repository**
```bash
git clone https://github.com/sanil0/Project_final.git
cd Project_final
```

### **13.4 - Install Python Dependencies**
```bash
pip install -r requirements.txt
```

### **13.5 - Run the Webapp**
```bash
cd webapp
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

## 📋 **STEP 14: Test Webapp Access**

### **14.1 - Test from Windows**
```powershell
# Test public IP
$target_ip = "54.123.45.67"
curl "http://$target_ip:8001"

# Should return HTML content
```

### **14.2 - View in Browser**
- Go to: `http://54.123.45.67:8001`
- Should see PDF Library interface

---

## 🔗 **STEP 15: Update WARP Proxy to Point to Target**

### **15.1 - Get Target Private IP**
From the AWS Console, note the target instance's **Private IPv4** address
- Example: `10.0.1.50`

### **15.2 - SSH into WARP Instance**
```powershell
ssh -i "C:\Users\Lenovo\Downloads\DDoS-copilot.pem" ubuntu@ec2-98-88-5-133.compute-1.amazonaws.com
```

### **15.3 - Update Configuration**
```bash
cd ~/Project_final

# Edit environment file
nano docker-compose.yml
```

Find the `UPSTREAM_BASE_URL` line and update:

**From:**
```
UPSTREAM_BASE_URL=http://target-app:8080
```

**To:**
```
UPSTREAM_BASE_URL=http://10.0.1.50:8001
```

(Replace 10.0.1.50 with your actual target private IP)

### **15.4 - Save and Exit**
- Press: `Ctrl + X`
- Press: `Y` (yes)
- Press: `Enter`

### **15.5 - Restart WARP Proxy**
```bash
docker-compose down
docker-compose up -d
docker-compose ps
```

---

## ✅ **STEP 16: Verify Traffic Flow**

### **16.1 - Generate Traffic**
```powershell
# From Windows, send requests through WARP proxy
$warp_ip = "98.88.5.133"

# Test 1: Simple request
curl "http://$warp_ip:8080/"

# Test 2: List PDFs
curl "http://$warp_ip:8080/list"

# Test 3: Search
curl "http://$warp_ip:8080/search?query=DDoS"
```

### **16.2 - Check Dashboard**
1. Go to: `http://98.88.5.133:8080/dashboard/login`
2. Login: `secureadmin` / `YourStrongPassword123!`
3. You should now see **traffic metrics and data**! 🎉

---

## 🎯 **Architecture Summary**

```
Internet User
    ↓
WARP Proxy (98.88.5.133:8080)
    ├─ Analyzes traffic
    ├─ Detects DDoS
    └─ Forwards clean traffic ↓
       Target Webapp (10.0.1.50:8001)
           ├─ PDF Library
           ├─ Processes requests
           └─ Returns responses ↓
              Dashboard shows metrics
```

---

## 📊 **Cost Estimate**

| Item | Cost | Notes |
|------|------|-------|
| t3.small instance | ~$0.0208/hour | Free tier eligible |
| EBS storage (20GB) | ~$2/month | Free tier (20GB) |
| Data transfer | Free | Within AWS/same region |
| **Monthly Total** | ~$15 | Or **FREE with free tier** |

---

## 🔄 **Quick Reference Commands**

```bash
# Check if webapp is running
curl http://10.0.1.50:8001

# View logs
docker-compose logs ddos-protection

# Restart WARP
docker-compose restart ddos-protection

# Check container status
docker-compose ps
```

---

## ⚠️ **Troubleshooting**

| Problem | Solution |
|---------|----------|
| Can't SSH | Check security group allows port 22 |
| Webapp not running | Check `python3 -m uvicorn main:app --host 0.0.0.0 --port 8001` output |
| WARP can't reach target | Verify private IP in docker-compose.yml |
| Dashboard shows no traffic | Check both instances are running and connected |

---

## ✅ **Checklist**

- [ ] Instance launched and running
- [ ] Public IP noted
- [ ] Private IP noted
- [ ] SSH connection working
- [ ] Webapp running on port 8001
- [ ] WARP proxy updated with private IP
- [ ] WARP proxy restarted
- [ ] Traffic flowing through proxy
- [ ] Dashboard showing metrics

**Once all checked, you're done!** 🎉

---

**Need help with any step? Let me know!** 🚀
