#!/usr/bin/env python3
"""SSH deployment helper."""
import subprocess
import sys

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"
host = "ubuntu@98.88.5.133"
cmd = """cd /home/ubuntu/Project_final && git pull && docker-compose build --no-cache ddos-protection 2>&1 | tail -1 && docker-compose restart ddos-protection && sleep 4"""

try:
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
    sys.exit(result.returncode)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
