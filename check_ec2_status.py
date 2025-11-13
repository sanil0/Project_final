#!/usr/bin/env python3
"""Check container restart time."""
import subprocess
from datetime import datetime

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"
host = "ubuntu@98.88.5.133"
cmd = "docker inspect ddos-protection --format='{{.State.StartedAt}}'"

result = subprocess.run([
    "ssh",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    host,
    cmd
], capture_output=True, text=True, timeout=10)

start_time = result.stdout.strip().strip("'\"")
print(f"Container started at: {start_time}")
print("\nAlso check the git log:")

# Check git log
cmd2 = "cd /home/ubuntu/Project_final && git log --oneline -5"
result2 = subprocess.run([
    "ssh",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    host,
    cmd2
], capture_output=True, text=True, timeout=10)

print(result2.stdout)
