# ✅ DEPLOYMENT QUICK CHECKLIST

## 🚀 STEP-BY-STEP EXECUTION CHECKLIST

### PHASE 1: GITHUB SETUP (15 minutes)
- [ ] Step 1: Check Git installed (`git --version`)
- [ ] Step 2: Create GitHub repository at https://github.com/new
- [ ] Step 3: Configure Git locally
  ```powershell
  git config --global user.name "Your Name"
  git config --global user.email "your@email.com"
  ```
- [ ] Step 4: Initialize local repo
  ```powershell
  cd d:\project_warp
  git init
  ```
- [ ] Step 5: Add remote
  ```powershell
  git remote add origin https://github.com/YOUR_USERNAME/project_warp.git
  ```
- [ ] Step 6: Commit files
  ```powershell
  git add .
  git commit -m "Initial commit: Project WARP deployment ready"
  git branch -M main
  ```
- [ ] Step 7: Push to GitHub
  ```powershell
  git push -u origin main
  ```

**✅ GITHUB COMPLETE - Proceed to Phase 2**

---

### PHASE 2: AWS PREREQUISITES (30 minutes)

#### AWS Account & IAM Setup
- [ ] Step 8: Create AWS account at https://aws.amazon.com
- [ ] Step 9: Create IAM user `project-warp-deployer`
  - Attach: `AdministratorAccess` policy
  - Create access keys
  - Save: Access Key ID and Secret Access Key

#### AWS CLI Setup
- [ ] Step 10: Install AWS CLI
  ```powershell
  pip install awscli
  ```
- [ ] Step 11: Configure AWS credentials
  ```powershell
  aws configure
  # Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)
  ```
- [ ] Step 12: Verify configuration
  ```powershell
  aws sts get-caller-identity
  ```

#### SSH Key Pair Setup
- [ ] Step 13: Create SSH key pair
  ```powershell
  aws ec2 create-key-pair --key-name project-warp-key --query 'KeyMaterial' --output text > ~/.ssh/project-warp-key.pem
  icacls ~/.ssh/project-warp-key.pem /inheritance:r /grant:r "$env:USERNAME`:(F)"
  ```
- [ ] Step 14: Verify key created
  ```powershell
  Test-Path ~/.ssh/project-warp-key.pem
  ```

#### Optional S3 Setup
- [ ] Step 15: Create S3 bucket
  ```powershell
  aws s3 mb s3://project-warp-artifacts-$(Get-Random 10000 99999)
  ```

**✅ AWS PREREQUISITES COMPLETE - Proceed to Phase 3**

---

### PHASE 3: TERRAFORM INFRASTRUCTURE (20 minutes)

#### Terraform Installation
- [ ] Step 16: Install Terraform
  ```powershell
  # Download from https://www.terraform.io/downloads.html
  # Or: choco install terraform
  terraform --version
  ```

#### Infrastructure Deployment
- [ ] Step 17: Navigate to Terraform directory
  ```powershell
  cd d:\project_warp\aws\terraform
  ```
- [ ] Step 18: Initialize Terraform
  ```powershell
  terraform init
  ```
- [ ] Step 19: Review infrastructure plan
  ```powershell
  terraform plan -out=tfplan
  ```
- [ ] Step 20: Deploy infrastructure
  ```powershell
  terraform apply tfplan
  # Wait 5-10 minutes for resources to create
  ```
- [ ] Step 21: Save outputs
  ```powershell
  terraform output > deployment_outputs.txt
  # Note the: instance_id, instance_ip, alb_dns_name
  ```

**✅ TERRAFORM COMPLETE - Proceed to Phase 4**

---

### PHASE 4: EC2 INSTANCE SETUP (20 minutes)

#### SSH Connection
- [ ] Step 22: Get instance IP from terraform output
- [ ] Step 23: Connect to instance
  ```powershell
  ssh -i ~/.ssh/project-warp-key.pem ubuntu@YOUR_INSTANCE_IP
  ```

#### System Update
- [ ] Step 24: Update system (on EC2 instance)
  ```bash
  sudo apt update
  sudo apt upgrade -y
  ```

#### Docker Installation
- [ ] Step 25: Install Docker
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  newgrp docker
  docker --version
  ```

#### Docker Compose Installation
- [ ] Step 26: Install Docker Compose
  ```bash
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  docker-compose --version
  ```

**✅ EC2 INSTANCE SETUP COMPLETE - Proceed to Phase 5**

---

### PHASE 5: APPLICATION DEPLOYMENT (15 minutes)

#### Repository Clone
- [ ] Step 27: Clone your GitHub repository
  ```bash
  git clone https://github.com/YOUR_USERNAME/project_warp.git
  cd project_warp
  ```

#### Environment Configuration
- [ ] Step 28: Create production environment file
  ```bash
  nano .env.production
  ```
  Add these variables:
  ```bash
  UPSTREAM_BASE_URL=https://your-domain.com
  LISTEN_HOST=0.0.0.0
  LISTEN_PORT=443
  DASHBOARD_USER=secureadmin
  DASHBOARD_PASS=YourStrongPassword123!@#
  REDIS_HOST=redis
  PROMETHEUS_URL=http://prometheus:9090
  PYTHONUNBUFFERED=1
  ```
  Save: `Ctrl+X` → `y` → `Enter`

#### Docker Services Startup
- [ ] Step 29: Start Docker Compose
  ```bash
  docker-compose up -d
  ```
- [ ] Step 30: Verify services running
  ```bash
  docker-compose ps
  # Should show 4 services: Up
  ```

#### Health Check
- [ ] Step 31: Verify application health
  ```bash
  curl -k https://localhost/health
  # Should return: {"status": "healthy"}
  ```

**✅ APPLICATION DEPLOYMENT COMPLETE - Proceed to Phase 6**

---

### PHASE 6: MONITORING & SECURITY (20 minutes)

#### Dashboard Access
- [ ] Step 32: Get ALB DNS name
  ```powershell
  # From local machine
  terraform output alb_dns_name
  ```
- [ ] Step 33: Access dashboards
  - Dashboard: `https://YOUR_ALB_DNS/dashboard/login`
  - Prometheus: `https://YOUR_ALB_DNS:9090`
  - Grafana: `https://YOUR_ALB_DNS:3000`

#### Testing
- [ ] Step 34: Run Phase 1 tests
  ```bash
  # On EC2 instance
  python phase1_tests.py
  # Should show: 9/9 PASSING
  ```

#### Security Hardening
- [ ] Step 35: Disable SSH root login
  ```bash
  sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config
  sudo systemctl restart ssh
  ```
- [ ] Step 36: Enable firewall
  ```bash
  sudo ufw enable
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  ```

#### Monitoring Setup
- [ ] Step 37: Configure CloudWatch alarms
  ```powershell
  aws cloudwatch put-metric-alarm \
    --alarm-name project-warp-high-cpu \
    --alarm-description "Alert when CPU > 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1
  ```

**✅ MONITORING & SECURITY COMPLETE**

---

## 📊 DEPLOYMENT VERIFICATION

### Final Checklist

**Infrastructure:**
- [ ] EC2 instance running
- [ ] Load balancer created
- [ ] Security groups configured
- [ ] SSH key pair working

**Application:**
- [ ] Docker services running (4/4)
- [ ] Application responding to health checks
- [ ] Dashboard accessible and login working
- [ ] Prometheus collecting metrics
- [ ] Grafana displaying dashboards

**Testing:**
- [ ] Phase 1 tests: 9/9 PASSING
- [ ] Can forward requests through proxy
- [ ] DDoS detection working
- [ ] Metrics being collected

**Security:**
- [ ] SSL/TLS enabled
- [ ] SSH hardened
- [ ] Firewall enabled
- [ ] No default passwords
- [ ] IAM permissions least privilege

**Monitoring:**
- [ ] CloudWatch metrics visible
- [ ] Alarms configured
- [ ] Logs aggregated
- [ ] Dashboards populated

---

## 🎯 QUICK REFERENCE COMMANDS

### Local Machine (PowerShell)

**GitHub:**
```powershell
git status
git add .
git commit -m "message"
git push
```

**AWS CLI:**
```powershell
aws configure
aws ec2 describe-instances
aws s3 ls
terraform init
terraform plan
terraform apply
```

**SSH to Instance:**
```powershell
ssh -i ~/.ssh/project-warp-key.pem ubuntu@YOUR_IP
```

### EC2 Instance (Bash)

**Docker:**
```bash
docker ps
docker logs service_name
docker-compose up -d
docker-compose down
docker-compose ps
```

**Application:**
```bash
curl -k https://localhost/health
python phase1_tests.py
python phase2_attack.py
```

**System:**
```bash
sudo systemctl status service_name
tail -f /var/log/syslog
df -h
free -m
top
```

---

## ⏱️ ESTIMATED TIMELINE

| Phase | Tasks | Time | Status |
|-------|-------|------|--------|
| 1 | GitHub Setup | 15 min | ⏳ |
| 2 | AWS Prerequisites | 30 min | ⏳ |
| 3 | Terraform Infrastructure | 20 min | ⏳ |
| 4 | EC2 Instance Setup | 20 min | ⏳ |
| 5 | Application Deployment | 15 min | ⏳ |
| 6 | Monitoring & Security | 20 min | ⏳ |
| **TOTAL** | **37 steps** | **120 min** | **⏳** |

---

## ❌ TROUBLESHOOTING

### Issue: Cannot connect to EC2
```powershell
# Verify security group
aws ec2 describe-security-groups --query 'SecurityGroups[0]'

# Verify instance is running
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
```

### Issue: Docker services not starting
```bash
# Check logs
docker-compose logs -f

# Restart
docker-compose restart

# Check port usage
sudo netstat -tlpn | grep 443
```

### Issue: Application not responding
```bash
# Check application logs
docker logs project_warp

# Check health endpoint
curl -k https://localhost/health

# Check environment variables
cat .env.production
```

### Issue: Terraform destroy to clean up
```powershell
# WARNING: This deletes all AWS resources
cd d:\project_warp\aws\terraform
terraform destroy
```

---

## ✅ COMPLETION

**When all steps are complete:**

1. ✅ GitHub repository is updated
2. ✅ AWS infrastructure deployed
3. ✅ Application running on EC2
4. ✅ Services accessible via dashboards
5. ✅ Tests passing in production
6. ✅ Monitoring and alerts configured
7. ✅ Security hardened

**You're ready for production!** 🎉

---

**Need help?** Check `DEPLOYMENT_COMPLETE_GUIDE.md` for detailed explanations of each step.
