#!/usr/bin/env python3
"""Force rebuild and restart."""
import subprocess
import sys

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"
host = "ubuntu@98.88.5.133"
cmd = "cd /home/ubuntu/Project_final && docker-compose down ddos-protection && sleep 2 && docker-compose build --no-cache --force-rm ddos-protection && docker-compose up -d ddos-protection && sleep 5"

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
