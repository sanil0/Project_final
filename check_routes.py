#!/usr/bin/env python3
"""Check if routes.py has the new code."""
import subprocess

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"
host = "ubuntu@98.88.5.133"
cmd = "sed -n '230,250p' /home/ubuntu/Project_final/app/dashboard/routes.py"

result = subprocess.run([
    "ssh",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    host,
    cmd
], capture_output=True, text=True, timeout=10)

print("Routes.py lines 230-250 on EC2:")
print(result.stdout)
if "blocked_requests" in result.stdout:
    print("\n✅ NEW CODE FOUND: blocked_requests present")
else:
    print("\n❌ OLD CODE: blocked_requests NOT found")
