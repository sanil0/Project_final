"""Test ML-based DDoS detection system."""

import asyncio
import httpx
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

async def test_normal_traffic():
    """Test normal traffic - should be allowed."""
    print("\n🔵 Testing Normal Traffic Pattern...")
    async with httpx.AsyncClient() as client:
        for i in range(5):
            try:
                response = await client.get(f"{BASE_URL}/health")
                print(f"  Request {i+1}: Status {response.status_code} - {'✅ Allowed' if response.status_code == 200 else '❌ Blocked'}")
                await asyncio.sleep(2)  # 2 second delay between requests
            except Exception as e:
                print(f"  Request {i+1}: ❌ Error - {e}")

async def test_burst_attack():
    """Test burst attack - should trigger ML detection and blocking."""
    print("\n🔴 Testing Burst Attack Pattern...")
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        blocked_count = 0
        allowed_count = 0
        
        for i in range(50):
            try:
                response = await client.get(f"{BASE_URL}/health")
                if response.status_code == 429:
                    blocked_count += 1
                    print(f"  Request {i+1}: Status {response.status_code} - 🛡️ BLOCKED by ML")
                else:
                    allowed_count += 1
                    print(f"  Request {i+1}: Status {response.status_code} - Allowed")
                
                # No delay - rapid fire attack
                if i % 10 == 0:
                    await asyncio.sleep(0.01)  # Tiny delay every 10 requests
            except Exception as e:
                print(f"  Request {i+1}: ❌ Error - {e}")
        
        duration = time.time() - start_time
        print(f"\n📊 Attack Summary:")
        print(f"  Total Requests: {50}")
        print(f"  Allowed: {allowed_count} ✅")
        print(f"  Blocked: {blocked_count} 🛡️")
        print(f"  Block Rate: {(blocked_count/50)*100:.1f}%")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Rate: {50/duration:.1f} req/s")

async def test_sustained_attack():
    """Test sustained high-rate attack."""
    print("\n🔴 Testing Sustained Attack Pattern...")
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(30):
            tasks.append(client.get(f"{BASE_URL}/health"))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        blocked = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 429)
        allowed = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        errors = sum(1 for r in responses if isinstance(r, Exception))
        
        print(f"\n📊 Concurrent Attack Summary:")
        print(f"  Total Requests: {len(tasks)}")
        print(f"  Allowed: {allowed} ✅")
        print(f"  Blocked: {blocked} 🛡️")
        print(f"  Errors: {errors} ❌")
        print(f"  Block Rate: {(blocked/len(tasks))*100:.1f}%")

async def check_dashboard_metrics():
    """Check dashboard metrics after attacks."""
    print("\n📈 Checking Dashboard Metrics...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/dashboard/api/metrics")
            if response.status_code == 200:
                metrics = response.json()
                print(f"  Total Requests: {metrics.get('total_requests', 'N/A')}")
                print(f"  Blocked Requests: {metrics.get('blocked_requests', 'N/A')}")
                print(f"  Block Rate: {metrics.get('block_rate', 'N/A')}%")
                print(f"  Blocked IPs: {metrics.get('blocked_ips', 'N/A')}")
                return metrics
            else:
                print(f"  ❌ Failed to get metrics: Status {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error getting metrics: {e}")
    return None

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 ML-Based DDoS Detection System Test")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Normal traffic (should be allowed)
    await test_normal_traffic()
    
    # Check metrics after normal traffic
    metrics_before = await check_dashboard_metrics()
    
    print("\n" + "="*60)
    print("⏳ Waiting 5 seconds before attack tests...")
    await asyncio.sleep(5)
    
    # Test 2: Burst attack (should be detected and blocked)
    await test_burst_attack()
    
    print("\n" + "="*60)
    print("⏳ Waiting 3 seconds...")
    await asyncio.sleep(3)
    
    # Test 3: Sustained concurrent attack
    await test_sustained_attack()
    
    # Final metrics check
    print("\n" + "="*60)
    metrics_after = await check_dashboard_metrics()
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
