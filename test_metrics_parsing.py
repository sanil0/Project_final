#!/usr/bin/env python3
"""Test the metrics parsing logic locally."""

import re

# Sample metrics text from the actual /metrics endpoint
metrics_text = """# HELP ddos_requests_total Total number of requests processed
# TYPE ddos_requests_total counter
ddos_requests_total{method="GET",status="allowed"} 5.0
# HELP ddos_requests_created Total number of requests processed
# TYPE ddos_requests_created gauge
ddos_requests_created{method="GET",status="allowed"} 1.763012537081474e+09
# HELP ddos_requests_blocked_total Total number of requests blocked
# TYPE ddos_requests_blocked_total counter
ddos_requests_blocked_total{reason="rate_limit"} 2.0
# HELP ddos_requests_blocked_created Total number of requests blocked
# TYPE ddos_requests_blocked_created gauge
ddos_requests_blocked_created{reason="rate_limit"} 1.7630125370505223e+09
# HELP ddos_active_blocked_ips Number of currently blocked IPs
# TYPE ddos_active_blocked_ips gauge
ddos_active_blocked_ips 3.0
"""

print("Testing metrics parsing...")
print("=" * 60)

total_requests = 0
total_blocked = 0
active_ips = 0

# Parse the Prometheus text format - look for our specific metrics
for line in metrics_text.split('\n'):
    # ddos_requests_total{method="GET",status="allowed"} 60.0
    if line.startswith('ddos_requests_total{') and '_created' not in line:
        print(f"Found requests line: {line}")
        try:
            match = re.search(r'\}\s+([\d.eE+-]+)$', line)
            if match:
                val = float(match.group(1))
                print(f"  Parsed value: {val}")
                total_requests += val
        except (ValueError, AttributeError) as e:
            print(f"  Failed to parse: {e}")
    
    # ddos_requests_blocked_total{reason="..."} value
    elif line.startswith('ddos_requests_blocked_total{') and '_created' not in line:
        print(f"Found blocked line: {line}")
        try:
            match = re.search(r'\}\s+([\d.eE+-]+)$', line)
            if match:
                val = float(match.group(1))
                print(f"  Parsed value: {val}")
                total_blocked += val
        except (ValueError, AttributeError) as e:
            print(f"  Failed to parse: {e}")
    
    # ddos_active_blocked_ips value
    elif line.startswith('ddos_active_blocked_ips '):
        print(f"Found active_ips line: {line}")
        try:
            val_str = line.split()[-1]
            active_ips = float(val_str)
            print(f"  Parsed value: {active_ips}")
        except (ValueError, IndexError) as e:
            print(f"  Failed to parse: {e}")

print("=" * 60)
print(f"Results:")
print(f"  total_requests: {total_requests}")
print(f"  total_blocked: {total_blocked}")
print(f"  active_ips: {active_ips}")

if total_requests > 0:
    block_rate = (total_blocked / total_requests * 100)
else:
    block_rate = 0

print(f"  block_rate: {block_rate:.2f}%")
