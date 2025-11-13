"""Generate continuous traffic to see dashboard update live."""
import requests
import time
from datetime import datetime

EC2_URL = "http://98.88.5.133:8080"

print("=" * 60)
print("🚀 Generating Continuous Traffic for Dashboard")
print("=" * 60)
print(f"Open Dashboard: http://98.88.5.133:8080/dashboard")
print(f"Login: admin / SecureP@ssw0rd123!")
print("Watch the graphs update in real-time!")
print("=" * 60)
print()

request_count = 0
while True:
    try:
        start = time.time()
        # Send requests at varying rates to create graph fluctuation
        batch_size = 5 if request_count % 3 == 0 else 2  # Vary batch size
        
        for i in range(batch_size):
            r = requests.get(f"{EC2_URL}/health", timeout=5)
            request_count += 1
            
        elapsed = time.time() - start
        rate = batch_size / elapsed if elapsed > 0 else 0
        
        print(f"\r📊 Total Requests: {request_count} | Last batch: {batch_size} requests in {elapsed:.2f}s ({rate:.1f} req/s)", end="", flush=True)
        
        # Vary delay to create fluctuation in graphs
        if request_count % 10 == 0:
            time.sleep(2)  # Slow period
        elif request_count % 5 == 0:
            time.sleep(0.5)  # Medium period
        else:
            time.sleep(0.1)  # Fast period
            
    except KeyboardInterrupt:
        print(f"\n\n✅ Stopped. Sent {request_count} total requests.")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        time.sleep(1)
