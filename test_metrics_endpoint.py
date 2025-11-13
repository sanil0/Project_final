#!/usr/bin/env python3
"""Quick test to verify the metrics endpoint works without SSH deployment."""

import asyncio
import httpx
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_metrics():
    """Test querying the metrics endpoint and parsing it."""
    try:
        async with httpx.AsyncClient() as client:
            # This simulates what the dashboard endpoint will do
            print("\n1. Querying /metrics endpoint from 98.88.5.133:8080...")
            response = await client.get('http://98.88.5.133:8080/metrics', timeout=5)
            metrics_text = response.text
            print(f"   ✓ Got metrics text ({len(metrics_text)} bytes)")
            
            total_requests = 0
            total_blocked = 0
            active_ips = 0
            
            # Parse the Prometheus text format
            found_count = 0
            for line in metrics_text.split('\n'):
                # ddos_requests_total{method="GET",status="allowed"} 60.0
                if line.startswith('ddos_requests_total{') and '_created' not in line:
                    found_count += 1
                    try:
                        match = re.search(r'\}\s+([\d.eE+-]+)$', line)
                        if match:
                            total_requests += float(match.group(1))
                            print(f"   ✓ Found request metric: {line[:60]}... = {float(match.group(1))}")
                    except (ValueError, AttributeError):
                        pass
                
                # ddos_requests_blocked_total{reason="..."} value
                elif line.startswith('ddos_requests_blocked_total{') and '_created' not in line:
                    found_count += 1
                    try:
                        match = re.search(r'\}\s+([\d.eE+-]+)$', line)
                        if match:
                            total_blocked += float(match.group(1))
                            print(f"   ✓ Found blocked metric: {line[:60]}... = {float(match.group(1))}")
                    except (ValueError, AttributeError):
                        pass
                
                # ddos_active_blocked_ips value
                elif line.startswith('ddos_active_blocked_ips '):
                    found_count += 1
                    try:
                        val_str = line.split()[-1]
                        active_ips = float(val_str)
                        print(f"   ✓ Found active IPs metric: {line} = {active_ips}")
                    except (ValueError, IndexError):
                        pass
            
            print(f"\n2. Parsing results (found {found_count} metrics):")
            print(f"   - total_requests: {int(total_requests)}")
            print(f"   - total_blocked: {int(total_blocked)}")
            print(f"   - active_ips: {int(active_ips)}")
            
            block_rate = (total_blocked / total_requests * 100) if total_requests > 0 else 0
            print(f"   - block_rate: {block_rate:.2f}%")
            
            if found_count >= 1:
                print(f"\n✅ SUCCESS: Parsing logic works correctly!")
                print(f"   The dashboard endpoint should return these values once deployed.")
                return True
            else:
                print(f"\n❌ FAILED: No metrics found in /metrics output")
                return False
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_metrics())
    exit(0 if success else 1)
