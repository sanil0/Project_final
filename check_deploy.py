#!/usr/bin/env python3
"""Check if the deployed code has the right changes."""
import subprocess
import sys

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"
host = "ubuntu@98.88.5.133"

# Read lines 168-175 from the deployed file
cmd = "sed -n '168,175p' /home/ubuntu/Project_final/app/dashboard/routes.py"

result = subprocess.run([
    "ssh",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    host,
    cmd
], capture_output=True, text=True)

print("Deployed code (lines 168-175):")
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
