import subprocess

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"

print("=== Checking if Middleware is Loaded ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "docker logs ddos-protection 2>&1 | grep 'Model loaded' | head -5"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore'
)
print(result.stdout if result.stdout else "No model load logs")

print("\n=== Checking Middleware Init ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "docker logs ddos-protection 2>&1 | grep 'initialized' | head -5"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore'
)
print(result.stdout if result.stdout else "No init logs")

print("\n=== Checking for Processing Logs ===")
result = subprocess.run(
    ["ssh", "-i", key_path, "-o", "StrictHostKeyChecking=no", "ubuntu@98.88.5.133",
     "docker logs ddos-protection 2>&1 | grep -i middleware | head -10"],
    capture_output=True, text=True, encoding='utf-8', errors='ignore'
)
print(result.stdout if result.stdout else "❌ NO MIDDLEWARE LOGS!")
