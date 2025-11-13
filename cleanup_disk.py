#!/usr/bin/env python3
"""Clean up disk space and restart."""
import subprocess
import sys

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"
host = "ubuntu@98.88.5.133"
cmd = "docker system prune -f && docker volume prune -f && cd /home/ubuntu/Project_final && docker-compose restart ddos-protection && sleep 4"

result = subprocess.run([
    "ssh",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    host,
    cmd
], capture_output=True, text=True, timeout=300)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
