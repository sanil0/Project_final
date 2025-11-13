#!/usr/bin/env python3
"""Check if EC2 has the latest HTML changes."""
import subprocess
import sys

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"
host = "ubuntu@98.88.5.133"
cmd = "head -80 /home/ubuntu/Project_final/templates/dashboard.html | tail -20"

result = subprocess.run([
    "ssh",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    host,
    cmd
], capture_output=True, text=True, timeout=10)

print("HTML content from EC2 (lines 60-80):")
print(result.stdout)
if "totalRequests" in result.stdout:
    print("\n✅ GOOD: HTML has correct IDs (totalRequests found)")
elif "metric-total" in result.stdout:
    print("\n❌ BAD: HTML still has old IDs (metric-total found)")
else:
    print("\n? UNKNOWN: Could not determine")
