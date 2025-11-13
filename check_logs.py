import subprocess

key_path = r"C:\Users\Lenovo\Downloads\DDoS-copilot.pem"

result = subprocess.run(
    [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "ubuntu@98.88.5.133",
        "cd ~/Project_final && docker-compose logs --tail=50 ddos-protection 2>&1"
    ],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr and "Warning" not in result.stderr:
    print("STDERR:", result.stderr)

