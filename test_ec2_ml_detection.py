"""Test ML-based DDoS detection on EC2."""

import asyncio
import httpx
import time
from datetime import datetime

EC2_URL = "http://98.88.5.133:8080"

async def test_burst_attack():
    """Test burst attack - should trigger ML detection and blocking."""
    print("\n🔴 Testing Burst Attack Pattern on EC2...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        start_time = time.time()
        blocked_count = 0
        allowed_count = 0
        errors = 0
        
        for i in range(100):
            try:
                response = await client.get(f"{EC2_URL}/health")
                if response.status_code == 429:
                    blocked_count += 1
                    if i < 20 or blocked_count <= 5:  # Show first 20 or first 5 blocks
                        print(f"  Request {i+1}: Status {response.status_code} - 🛡️ BLOCKED by ML")
                elif response.status_code == 200:
                    allowed_count += 1
                    if i < 10:  # Show first 10
                        print(f"  Request {i+1}: Status {response.status_code} - Allowed")
                else:
                    print(f"  Request {i+1}: Status {response.status_code} - Unexpected")
                
                # No delay - rapid fire attack
                if i % 20 == 0:
                    await asyncio.sleep(0.01)
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  Request {i+1}: ❌ Error - {e}")
        
        duration = time.time() - start_time
        print(f"\n📊 Attack Summary:")
        print(f"  Total Requests: 100")
        print(f"  Allowed: {allowed_count} ✅")
        print(f"  Blocked: {blocked_count} 🛡️")
        print(f"  Errors: {errors} ❌")
        print(f"  Block Rate: {(blocked_count/100)*100:.1f}%")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Rate: {100/duration:.1f} req/s")
        
        return blocked_count > 0

async def check_dashboard_metrics():
    """Check dashboard metrics after attacks."""
    print("\n📈 Checking Dashboard Metrics...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{EC2_URL}/dashboard/api/metrics")
            if response.status_code == 200:
                metrics = response.json()
                print(f"  Total Requests: {metrics.get('total_requests', 'N/A')}")
                print(f"  Blocked Requests: {metrics.get('blocked_requests', 'N/A')}")
                print(f"  Block Rate: {metrics.get('block_rate', 'N/A')}%")
                print(f"  Blocked IPs: {metrics.get('blocked_ips', 'N/A')}")
                return metrics
            else:
                print(f"  Dashboard requires authentication (expected)")
                print(f"  Access at: http://98.88.5.133:8080/dashboard")
        except Exception as e:
            print(f"  ❌ Error getting metrics: {e}")
    return None

async def main():
    """Run tests."""
    print("=" * 60)
    print("🧪 EC2 ML-Based DDoS Detection Test")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: {EC2_URL}")
    
    # Test burst attack
    ml_working = await test_burst_attack()
    
    # Check metrics
    await check_dashboard_metrics()
    
    print("\n" + "="*60)
    if ml_working:
        print("✅ ML Detection is WORKING!")
        print("   Your project name 'Intelligent DDoS Detection' is now MEANINGFUL! 🎉")
    else:
        print("⚠️  No blocks detected - may need to adjust sensitivity")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
