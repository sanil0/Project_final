import subprocess

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"

print("=== Restarting container ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "cd ~/Project_final && docker-compose restart ddos-protection"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=60
)
print(result.stdout)

import time
time.sleep(5)

print("\n=== Verifying middleware code in container ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "docker exec ddos-protection cat /app/app/main.py | head -60 | tail -20"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30
)
print(result.stdout)

print("\n=== Checking logs for middleware module load ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "docker logs --since 1m ddos-protection 2>&1 | grep -E 'MODULE|DDoS Protection initialized|middleware' | head -10"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30
)
print(result.stdout if result.stdout else "No middleware logs yet")

print("\n=== Sending test request ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "curl -s http://localhost:8080/health"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=10
)
print(result.stdout)

print("\n=== Checking for middleware processing log ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "docker logs --since 30s ddos-protection 2>&1 | grep 'Middleware processing' | head -5"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30
)
print(result.stdout if result.stdout else "❌ STILL NO MIDDLEWARE PROCESSING!")
