# Security Hardening Guide

## Overview

This guide covers security hardening for the DDoS Protection service deployment.

## Application-Level Security

### 1. Input Validation

All inputs are validated via Pydantic models:
- IP address format validation
- URL validation with `AnyHttpUrl`
- Enum validation for sensitivity levels
- String length limits

### 2. Authentication & Authorization

```python
# Admin endpoints require API key
require_admin(admin_api_key: str)

# Set in environment
ADMIN_API_KEY=your-secure-key-here
```

Generate secure key:
```bash
openssl rand -base64 32
```

### 3. Rate Limiting Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633024800
Retry-After: 60
```

### 4. Error Handling

- No sensitive info in error messages
- Exceptions logged server-side only
- Generic 500 response for internal errors

## Transport Security

### HTTPS/TLS

**In Kubernetes (Ingress):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ddos-protection
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - ddos.example.com
    secretName: ddos-tls-cert
```

**Using cert-manager:**
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your@email.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Security Headers

```python
# Add to middleware or ingress
def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # HSTS
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # CSP
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    
    # X-Frame-Options
    response.headers["X-Frame-Options"] = "DENY"
    
    # X-Content-Type-Options
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Referrer-Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

## Infrastructure Security

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ddos-protection-network-policy
  namespace: ddos-protection
spec:
  podSelector:
    matchLabels:
      app: ddos-protection
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53  # DNS
    - protocol: UDP
      port: 53
  - to:
    - podSelector:
        matchLabels:
          app: target-service
    ports:
    - protocol: TCP
      port: 8080
```

Apply:
```bash
kubectl apply -f k8s/networkpolicy.yaml
```

### Pod Security Policies

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: ddos-protection-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'MustRunAs'
    seLinuxOptions:
      level: "s0:c123,c456"
  fsGroup:
    rule: 'MustRunAs'
    fsGroupOptions:
      ranges:
      - min: 1000
        max: 2000
  readOnlyRootFilesystem: false
```

### RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ddos-protection-role
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["ddos-protection-secrets"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ddos-protection-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: ddos-protection-role
subjects:
- kind: ServiceAccount
  name: ddos-protection-sa
  namespace: ddos-protection
```

## Secrets Management

### Never commit secrets:

```bash
# .gitignore
.env
.env.*.local
secrets.yaml
```

### Use Kubernetes Secrets:

```bash
# Create secret
kubectl create secret generic ddos-protection-secrets \
  -n ddos-protection \
  --from-literal=admin-api-key=$(openssl rand -base64 32) \
  --from-literal=db-password=$(openssl rand -base64 32)

# Or use external secret management (HashiCorp Vault)
kubectl apply -f k8s/external-secrets.yaml
```

### Secret Rotation

```bash
# Rotate API key every 90 days
kubectl create secret generic ddos-protection-secrets \
  -n ddos-protection \
  --from-literal=admin-api-key=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Pod restarts automatically
kubectl rollout restart deployment/ddos-protection -n ddos-protection
```

## Vulnerability Scanning

### Container Scanning

```bash
# Using trivy
trivy image project_warp:latest

# Using grype
grype project_warp:latest

# In CI (see .github/workflows/ci.yml)
- name: Scan image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### Dependency Scanning

```bash
# Check Python dependencies
safety check -r requirements.txt

# Update vulnerable packages
pip list --outdated
pip install --upgrade package-name
```

### SAST (Static Application Security Testing)

```bash
# Bandit for Python security issues
bandit -r app

# Semgrep for advanced patterns
semgrep --config=p/security-audit app
```

## Audit Logging

```python
# Log all sensitive operations
logger.info(f"Admin action: {action} by {admin_key}", 
            extra={"admin": True, "action": action})

# Log blocked IPs
logger.warning(f"IP blocked: {ip} - reason: {reason}",
               extra={"blocked_ip": ip})
```

### Centralized Logging

```yaml
# Kubernetes integration with ELK/Loki
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: ddos-protection
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush        5
        Daemon       Off
        Log_Level    info
    
    [INPUT]
        Name              tail
        Path              /var/log/containers/*_ddos-protection_*.log
        Parser            docker
        Tag               kube.*
        Refresh_Interval  5
    
    [OUTPUT]
        Name   loki
        Match  kube.*
        Host   loki.monitoring.svc.cluster.local
        Port   3100
        Labels job=ddos-protection
```

## DDoS Protection Against Admin Endpoints

```python
# Rate limit admin endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/admin/blocklist")
@limiter.limit("10/minute")
async def add_blocklist_entry(request: Request, entry: BlocklistRequest):
    # Verify API key
    if not verify_admin_key(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ...
```

## Compliance

### GDPR Compliance
- No PII logging (remove user identifiers)
- Log retention: max 90 days
- Data encryption at rest and in transit

### HIPAA/PCI-DSS
- Use encrypted secrets
- Enable audit logging
- Regular security scanning
- Penetration testing (annually)

## Security Checklist

- [ ] HTTPS/TLS enabled for all traffic
- [ ] Security headers configured
- [ ] Network policies enforced
- [ ] RBAC properly configured
- [ ] Secrets encrypted and rotated
- [ ] Audit logging enabled and monitored
- [ ] Vulnerability scans in CI/CD
- [ ] Regular dependency updates
- [ ] Penetration testing completed
- [ ] Security incident response plan ready
- [ ] DDoS protection itself protected
- [ ] Firewall rules configured
- [ ] VPN for admin access (optional)

## Incident Response

### If Compromised

1. **Immediate**: Rotate all secrets
   ```bash
   kubectl delete secret ddos-protection-secrets -n ddos-protection
   kubectl create secret generic ddos-protection-secrets ...
   kubectl rollout restart deployment/ddos-protection -n ddos-protection
   ```

2. **Investigate**: Check audit logs
   ```bash
   kubectl logs -n ddos-protection -l app=ddos-protection --all-containers=true | grep -E "WARN|ERROR"
   ```

3. **Patch**: Update vulnerable components
   ```bash
   pip install --upgrade package-name
   docker build -t project_warp:patched .
   kubectl set image deployment/ddos-protection ddos-protection=project_warp:patched -n ddos-protection
   ```

4. **Monitor**: Watch for suspicious activity
   ```bash
   kubectl port-forward -n monitoring svc/prometheus 9090:9090
   # Check metrics for anomalies
   ```

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
