import requests

# Send some requests
print("Sending 10 requests to generate traffic...")
for i in range(10):
    try:
        r = requests.get("http://98.88.5.133:8080/health", timeout=5)
        print(f"Request {i+1}: {r.status_code}")
    except Exception as e:
        print(f"Request {i+1}: Error - {e}")

print("\nChecking metrics...")
try:
    r = requests.get("http://98.88.5.133:8080/metrics", timeout=10)
    lines = r.text.split('\n')
    
    print("\n📊 DDoS Metrics:")
    for line in lines:
        if 'ddos_requests' in line and not line.startswith('#'):
            print(f"  {line}")
        if 'ddos_risk_score' in line and not line.startswith('#'):
            print(f"  {line}")
except Exception as e:
    print(f"Error getting metrics: {e}")

print("\nNow open dashboard at: http://98.88.5.133:8080/dashboard")
print("Login: admin / SecureP@ssw0rd123!")
