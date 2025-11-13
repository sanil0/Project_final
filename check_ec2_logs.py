import subprocess

result = subprocess.run(
    [
        "ssh",
        "-i", "DDoS-copilot.pem",
        "-o", "StrictHostKeyChecking=no",
        "ubuntu@98.88.5.133",
        "cd ~/Project_final && docker-compose logs --tail=100 ddos-protection | grep -E 'DDoS|Model loaded|middleware|BLOCKED|ALLOWED'"
    ],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
