# 🚀 AWS DEPLOYMENT - COMPLETE STEP-BY-STEP GUIDE

**Project**: Project WARP - DDoS Protection Proxy  
**Date**: November 10, 2025  
**Status**: Ready for Deployment  
**Estimated Time**: 6 hours total  
**Project Size**: 321 MB (after dataset removal)

---

## 📋 TABLE OF CONTENTS

1. [GitHub Setup](#github-setup)
2. [AWS Account Prerequisites](#aws-account-prerequisites)
3. [Local Preparation](#local-preparation)
4. [GitHub Push](#github-push)
5. [AWS Deployment](#aws-deployment)
6. [Verification](#verification)

---

## 🔧 GITHUB SETUP

### Step 1: Check if Git is Installed

```powershell
git --version
```

**Expected Output**: `git version 2.x.x` or higher

**If NOT installed:**
- Download: https://git-scm.com/download/win
- Run installer
- Accept defaults
- Restart PowerShell

---

### Step 2: Create GitHub Repository

**Option A: Create via Web**

1. Go to https://github.com/new
2. Repository name: `project_warp`
3. Description: `DDoS Protection Proxy with ML Detection`
4. Visibility: Public or Private (your choice)
5. ✅ Initialize with README? **NO** (we have one)
6. Click: **Create repository**
7. Copy the repository URL (e.g., `https://github.com/yourname/project_warp.git`)

**Option B: Via GitHub CLI**

```bash
gh auth login
gh repo create project_warp --public --source=. --remote=origin --push
```

---

### Step 3: Configure Git (First Time Only)

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Example:**
```powershell
git config --global user.name "John Developer"
git config --global user.email "john@example.com"
```

---

## 📦 LOCAL PREPARATION

### Step 4: Navigate to Project

```powershell
cd d:\project_warp
```

---

### Step 5: Initialize Git Repository

```powershell
git init
```

**Output**: `Initialized empty Git repository in D:\project_warp\.git\`

---

### Step 6: Add Remote Repository

Replace `YOUR_USERNAME` with your GitHub username:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/project_warp.git
```

**Verify:**
```powershell
git remote -v
```

**Expected Output:**
```
origin  https://github.com/YOUR_USERNAME/project_warp.git (fetch)
origin  https://github.com/YOUR_USERNAME/project_warp.git (push)
```

---

### Step 7: Add All Files to Git

```powershell
git add .
```

**Verify what will be committed:**
```powershell
git status
```

**Expected Output**: Shows all files ready to commit (green text)

---

### Step 8: Create Initial Commit

```powershell
git commit -m "Initial commit: Project WARP deployment ready"
```

**Expected Output**: Shows files added/changed

---

### Step 9: Rename Branch to Main

```powershell
git branch -M main
```

---

## 🚀 GITHUB PUSH

### Step 10: Push to GitHub (First Time)

```powershell
git push -u origin main
```

**First time might ask for credentials:**
- GitHub username: Your username
- Password/Token: Use Personal Access Token (recommended)

**Creating Personal Access Token:**

1. Go to: https://github.com/settings/tokens
2. Click: **Generate new token (classic)**
3. Note: `GitHub PAT`
4. Scopes needed:
   - ✅ `repo` (full control of private repositories)
   - ✅ `workflow` (update GitHub workflows)
5. Click: **Generate token**
6. **COPY the token** (you won't see it again!)
7. Use as password when pushing

**After push completes:**
```
✅ All files pushed to GitHub
✅ Repository at: https://github.com/YOUR_USERNAME/project_warp
```

---

### Step 11: Verify GitHub Push

```powershell
git log --oneline
```

**Expected Output**: Shows your commit

**Also verify on GitHub**: https://github.com/YOUR_USERNAME/project_warp

---

## ✅ GITHUB COMPLETE

**Summary of GitHub Setup:**
- ✅ Git repository initialized locally
- ✅ Remote repository created on GitHub
- ✅ All files committed and pushed
- ✅ Project available at GitHub URL
- ✅ Ready for AWS deployment

---

---

## 🏢 AWS ACCOUNT PREREQUISITES

### Step 12: Create AWS Account (If Not Exists)

1. Go to: https://aws.amazon.com
2. Click: **Create an AWS Account**
3. Enter email, password, and AWS account name
4. Enter payment method (required for verification)
5. Verify phone number
6. Choose **Basic** support plan
7. Account created ✅

**⏱️ Estimated Time**: 5-10 minutes

---

### Step 13: Set Up AWS IAM User

**⚠️ Security Best Practice**: Never use root account for deployments!

1. **Log in to AWS Console**
   - URL: https://console.aws.amazon.com
   - Email: Your AWS email
   - Password: Your AWS password

2. **Create IAM User**
   - Click: **IAM** in services
   - Left menu: **Users** → **Create user**
   - User name: `project-warp-deployer`
   - Click: **Next**

3. **Add Permissions**
   - Click: **Attach policies directly**
   - Search: `AdministratorAccess`
   - Check: `AdministratorAccess`
   - Click: **Next** → **Create user**

4. **Create Access Keys**
   - Click: **Security credentials** tab
   - Scroll: **Access keys** section
   - Click: **Create access key**
   - Choose: **Command Line Interface (CLI)**
   - Acknowledge: ✅ Check box
   - Click: **Create access key**
   - **SAVE these credentials somewhere safe!**
     - Access Key ID: `AKIA...`
     - Secret Access Key: `wJalr...`

**⏱️ Estimated Time**: 10 minutes

---

### Step 14: Install AWS CLI

```powershell
# Check if installed
aws --version
```

**If NOT installed:**

```powershell
# Option A: Using pip (if Python installed)
pip install awscli

# Option B: Using installer
# Download: https://awscli.amazonaws.com/AWSCLIV2.msi
# Run installer, accept defaults
```

**Verify installation:**
```powershell
aws --version
```

**Expected Output**: `aws-cli/2.x.x ...`

---

### Step 15: Configure AWS CLI Credentials

```powershell
aws configure
```

**When prompted, enter:**

```
AWS Access Key ID [None]: AKIA... (from Step 13)
AWS Secret Access Key [None]: wJalr... (from Step 13)
Default region name [None]: us-east-1
Default output format [None]: json
```

**Verify configuration:**
```powershell
aws sts get-caller-identity
```

**Expected Output**: Shows your AWS account ID

---

### Step 16: Create SSH Key Pair

You'll need this to connect to EC2 instances:

```powershell
# Create directory for keys
mkdir ~/.ssh

# Create key pair (choose one method)
```

**Option A: Create via AWS Console**

1. Go to: AWS Console → EC2 → Key Pairs
2. Click: **Create key pair**
3. Name: `project-warp-key`
4. Format: **pem** (for Linux/Mac/Windows)
5. Click: **Create key pair**
6. File downloads: `project-warp-key.pem`
7. Save to: `~/.ssh/project-warp-key.pem`
8. Set permissions:
   ```powershell
   icacls ~/.ssh/project-warp-key.pem /inheritance:r /grant:r "$env:USERNAME`:(F)"
   ```

**Option B: Create via AWS CLI**

```powershell
aws ec2 create-key-pair --key-name project-warp-key --query 'KeyMaterial' --output text > ~/.ssh/project-warp-key.pem

# Set permissions (Windows)
icacls ~/.ssh/project-warp-key.pem /inheritance:r /grant:r "$env:USERNAME`:(F)"

# Set permissions (Linux/Mac)
chmod 400 ~/.ssh/project-warp-key.pem
```

**Verify:**
```powershell
Test-Path ~/.ssh/project-warp-key.pem
```

**Expected Output**: `True`

---

### Step 17: Create S3 Bucket for Artifacts (Optional)

```powershell
aws s3 mb s3://project-warp-artifacts-$(Get-Random 10000 99999)
```

**Example:**
```powershell
aws s3 mb s3://project-warp-artifacts-42837
```

**Verify:**
```powershell
aws s3 ls
```

---

## ✅ AWS PREREQUISITES COMPLETE

**Summary:**
- ✅ AWS account created
- ✅ IAM user created with credentials
- ✅ AWS CLI installed and configured
- ✅ SSH key pair created
- ✅ S3 bucket created (optional)
- ✅ Ready for infrastructure deployment

---

---

## 🚀 AWS DEPLOYMENT - TERRAFORM METHOD (RECOMMENDED)

### Step 18: Install Terraform

```powershell
# Check if installed
terraform --version
```

**If NOT installed:**

```powershell
# Option A: Using Chocolatey
choco install terraform

# Option B: Manual download
# Download: https://www.terraform.io/downloads.html
# Extract to: C:\terraform
# Add to PATH
```

**Verify:**
```powershell
terraform --version
```

---

### Step 19: Create Terraform Configuration

Navigate to project:
```powershell
cd d:\project_warp\aws\terraform
```

**File: `main.tf`** (Already exists, verify contents)

Key sections to review:
- VPC Configuration
- EC2 Instance Type
- Security Groups
- Load Balancer
- Auto Scaling

---

### Step 20: Initialize Terraform

```powershell
cd d:\project_warp\aws\terraform
terraform init
```

**Expected Output**: 
```
Terraform has been successfully configured!
```

---

### Step 21: Plan Deployment

```powershell
terraform plan -out=tfplan
```

**Review output:**
- Shows resources to create
- Shows estimated costs
- Verify configuration is correct

**Expected to create:**
- 1 VPC
- 2 Subnets
- 1 Internet Gateway
- 1 Security Group
- 1 EC2 Instance
- 1 Application Load Balancer
- DNS records
- ~15 resources total

---

### Step 22: Apply Terraform Configuration

```powershell
terraform apply tfplan
```

**When prompted:** `Do you want to perform these actions?`
- Type: `yes`
- Press: `Enter`

**Estimated Time**: 5-10 minutes

**Expected Output**: Shows created resources and outputs like:
```
Outputs:
instance_id = "i-0123456789abcdef0"
instance_ip = "54.123.45.67"
alb_dns_name = "project-warp-alb-123.us-east-1.elb.amazonaws.com"
```

**Save these outputs!** You'll need them.

---

### Step 23: Verify Infrastructure Created

```powershell
# View Terraform state
terraform show

# Or check AWS Console
# Go to: AWS Console → EC2 → Instances
# Should see: 1 running instance
```

---

## 🐳 DOCKER & APPLICATION DEPLOYMENT

### Step 24: Connect to EC2 Instance

```powershell
# Get instance IP from terraform outputs or AWS Console
$instance_ip = "54.123.45.67"  # Replace with actual IP

# Connect via SSH
ssh -i ~/.ssh/project-warp-key.pem ubuntu@$instance_ip
```

**Expected Output**: 
```
ubuntu@ip-10-0-1-100:~$
```

You're now connected to your EC2 instance!

---

### Step 25: Update System

```bash
# On the EC2 instance
sudo apt update
sudo apt upgrade -y
```

---

### Step 26: Install Docker

```bash
# On the EC2 instance
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

---

### Step 27: Install Docker Compose

```bash
# On the EC2 instance
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

### Step 28: Clone Your GitHub Repository

```bash
# On the EC2 instance
git clone https://github.com/YOUR_USERNAME/project_warp.git
cd project_warp
```

---

### Step 29: Create Production Environment File

```bash
# On the EC2 instance
nano .env.production
```

**Add these contents:**
```bash
# Application
UPSTREAM_BASE_URL=https://your-domain.com
LISTEN_HOST=0.0.0.0
LISTEN_PORT=443
PYTHONUNBUFFERED=1

# Dashboard
DASHBOARD_USER=secureadmin
DASHBOARD_PASS=YourStrongPassword123!@#

# Database (if using RDS)
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=YourDatabasePassword123!
DB_NAME=project_warp

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Monitoring
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_PASSWORD=YourGrafanaPassword123!
```

**To save:**
- Press: `Ctrl + X`
- Type: `y`
- Press: `Enter`

---

### Step 30: Start Docker Services

```bash
# On the EC2 instance
docker-compose up -d
```

**Verify services are running:**
```bash
docker-compose ps
```

**Expected Output:**
```
NAME                STATUS
project_warp        Up 2 minutes
prometheus          Up 2 minutes
grafana             Up 2 minutes
redis               Up 2 minutes
```

---

### Step 31: Verify Application Health

```bash
# On the EC2 instance
curl -k https://localhost/health
```

**Expected Output:**
```json
{"status": "healthy", "version": "1.0.0"}
```

---

## 📊 MONITORING & TESTING

### Step 32: Access Dashboard

1. **Get ALB DNS name:**
   ```powershell
   terraform output alb_dns_name
   ```

2. **Access dashboard:**
   - URL: `https://your-alb-dns.elb.amazonaws.com/dashboard/login`
   - Username: `secureadmin`
   - Password: `YourStrongPassword123!@#`

3. **Access Prometheus:**
   - URL: `https://your-alb-dns.elb.amazonaws.com:9090`

4. **Access Grafana:**
   - URL: `https://your-alb-dns.elb.amazonaws.com:3000`
   - Username: `admin`
   - Password: `YourGrafanaPassword123!`

---

### Step 33: Configure CloudWatch Monitoring

```powershell
# From your local machine
aws cloudwatch put-metric-alarm \
  --alarm-name project-warp-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

---

### Step 34: Run Health Tests

```bash
# On the EC2 instance
cd project_warp

# Run Phase 1 tests
python phase1_tests.py

# Run attack simulation (optional)
python phase2_attack.py
```

---

## 🔒 SECURITY CONFIGURATION

### Step 35: Configure SSL/TLS Certificate

**Option A: Use Let's Encrypt (Free)**

```bash
# On the EC2 instance
sudo apt install certbot -y
sudo certbot certonly --standalone -d your-domain.com
```

**Option B: Use AWS ACM Certificate**

```powershell
# From local machine
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS
```

---

### Step 36: Harden Security

```bash
# On the EC2 instance

# Disable SSH root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Enable firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Update system
sudo apt autoremove -y
```

---

## ✅ FINAL VERIFICATION CHECKLIST

### Step 37: Complete Verification

- [ ] GitHub repository created and pushed
- [ ] AWS account and IAM user configured
- [ ] AWS CLI installed and credentials set
- [ ] SSH key pair created
- [ ] Terraform infrastructure deployed
- [ ] EC2 instance running and healthy
- [ ] Docker services running (4/4)
- [ ] Application responding to health checks
- [ ] Dashboard accessible
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards displaying
- [ ] SSL/TLS certificate installed
- [ ] Security groups configured
- [ ] Monitoring alarms set up
- [ ] Tests passing on deployment

---

## 📋 DEPLOYMENT SUMMARY

| Phase | Task | Status | Time |
|-------|------|--------|------|
| 1 | GitHub Setup | ✅ | 15 min |
| 2 | AWS Prerequisites | ✅ | 30 min |
| 3 | Terraform Deployment | ✅ | 15 min |
| 4 | Docker Setup | ✅ | 20 min |
| 5 | Application Deploy | ✅ | 15 min |
| 6 | Configuration | ✅ | 10 min |
| 7 | Security Setup | ✅ | 10 min |
| 8 | Verification | ✅ | 10 min |
| | **TOTAL** | **✅** | **2.5 hours** |

---

## 🚀 YOU'RE LIVE!

**Your Project WARP is now running on AWS!**

```
✅ Application deployed
✅ Monitoring active
✅ Dashboards accessible
✅ Security configured
✅ Tests passing
✅ Production ready
```

---

## 📞 TROUBLESHOOTING

### Common Issues

**Issue: Cannot connect to instance**
```powershell
# Verify security group allows SSH
aws ec2 describe-security-groups --query 'SecurityGroups[0].IpPermissions'

# Verify key permissions
icacls ~/.ssh/project-warp-key.pem
```

**Issue: Docker services not running**
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

**Issue: Application not responding**
```bash
# Check application logs
docker logs project_warp

# Check port is open
sudo netstat -tlpn | grep 443
```

---

## ✨ NEXT STEPS

1. **Monitor your deployment** - Check CloudWatch dashboards
2. **Set up backups** - Configure RDS backups
3. **Enable auto-scaling** - Configure ASG policies
4. **Add custom domains** - Configure Route 53
5. **Set up CI/CD** - GitHub Actions for deployments

---

**Deployment Complete! 🎉**
