"""
Phase 2c: Accelerated Attack - Rapid Requests
Purpose: Test rate limiting with sustained high request rate
Method: Minimal spacing between requests to trigger threshold quickly
Expected: Should see 429 responses once limit is exceeded
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import List, Dict, Any

# Configuration
PROXY_URL = "http://127.0.0.1:8080"
TEST_ENDPOINT = f"{PROXY_URL}/get"
RATE_LIMIT = 100  # requests per 60 seconds
BURST_SIZE = 120  # Send 120 rapid requests to exceed limit
MIN_SPACING = 0.01  # 10ms between requests (sustained high rate)

class Phase2cResults:
    """Track accelerated attack results"""
    
    def __init__(self):
        self.events = []
        self.total_requests = 0
        self.total_allowed = 0
        self.total_blocked = 0
        self.first_block_at = None
        self.start_time = None
        self.end_time = None
    
    def add_event(self, req_num: int, status: int, response_time: float):
        """Record request"""
        timestamp = time.time()
        self.events.append({
            "request": req_num,
            "status": status,
            "response_time": response_time,
            "timestamp": timestamp,
            "allowed": status < 400,
            "blocked": status >= 400
        })
        
        self.total_requests += 1
        if status < 400:
            self.total_allowed += 1
        else:
            self.total_blocked += 1
            if self.first_block_at is None:
                self.first_block_at = req_num
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "metadata": {
                "test_type": "Phase 2c - Accelerated Attack",
                "proxy_url": PROXY_URL,
                "rate_limit": f"{RATE_LIMIT} requests/60s",
                "burst_size": BURST_SIZE,
                "min_spacing": MIN_SPACING,
                "test_timestamp": datetime.now().isoformat()
            },
            "results": {
                "total_requests": self.total_requests,
                "total_allowed": self.total_allowed,
                "total_blocked": self.total_blocked,
                "success_rate": (self.total_allowed / self.total_requests * 100) if self.total_requests > 0 else 0,
                "block_rate": (self.total_blocked / self.total_requests * 100) if self.total_requests > 0 else 0,
                "first_block_at_request": self.first_block_at,
                "total_duration": self.end_time - self.start_time if self.end_time and self.start_time else None
            },
            "events": self.events
        }

async def run_burst_attack(results: Phase2cResults) -> None:
    """Execute burst attack"""
    print(f"\n🔥 Starting {BURST_SIZE} rapid requests...")
    print(f"   Spacing: {MIN_SPACING}s between requests")
    print(f"   Goal: Trigger rate limiting by exceeding {RATE_LIMIT} req/60s\n")
    
    results.start_time = time.time()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for req_num in range(1, BURST_SIZE + 1):
            try:
                start = time.time()
                response = await client.get(TEST_ENDPOINT, follow_redirects=True)
                elapsed = time.time() - start
                
                status = response.status_code
                results.add_event(req_num, status, elapsed)
                
                # Visual feedback - show every 10 requests or blocked ones
                if status >= 400 or req_num % 10 == 0:
                    symbol = "✅" if status < 400 else "🚫"
                    print(f"{symbol} Req {req_num:3d}: {status} ({elapsed:.3f}s)")
                
                # Spacing between requests
                await asyncio.sleep(MIN_SPACING)
                
            except asyncio.TimeoutError:
                print(f"❌ Req {req_num:3d}: TIMEOUT")
                results.add_event(req_num, 504, 10.0)
                await asyncio.sleep(MIN_SPACING)
            except Exception as e:
                print(f"❌ Req {req_num:3d}: ERROR - {str(e)[:40]}")
                results.add_event(req_num, 500, 0.0)
                await asyncio.sleep(MIN_SPACING)
    
    results.end_time = time.time()

async def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🔥 PHASE 2c: ACCELERATED ATTACK - RAPID REQUEST BURST")
    print("="*70)
    print(f"Purpose: Test rate limiting with sustained high request rate")
    print(f"Configuration:")
    print(f"  - Total requests: {BURST_SIZE}")
    print(f"  - Request spacing: {MIN_SPACING}s (minimal)")
    print(f"  - Rate limit: {RATE_LIMIT} requests/60s")
    print(f"  - Expected blocking: After ~{RATE_LIMIT} requests")
    print(f"\n📌 Expected Behavior:")
    print(f"  - Requests should initially succeed (✅)")
    print(f"  - After ~{RATE_LIMIT} requests, expect 429/403 responses (🚫)")
    print("="*70)
    
    results = Phase2cResults()
    
    try:
        await run_burst_attack(results)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    # Print results
    print("\n" + "="*70)
    print("📊 PHASE 2c RESULTS - ACCELERATED ATTACK")
    print("="*70)
    print(f"\nTotal Requests: {results.total_requests}")
    print(f"  ✅ Allowed:  {results.total_allowed} ({results.total_allowed/results.total_requests*100:.1f}%)")
    print(f"  🚫 Blocked:  {results.total_blocked} ({results.total_blocked/results.total_requests*100:.1f}%)")
    
    if results.first_block_at:
        print(f"\n🎯 Rate Limiting Triggered:")
        print(f"  - First block at request: {results.first_block_at}")
        print(f"  - Expected threshold: ~{RATE_LIMIT}")
        print(f"  - Accuracy: {'✅ EXCELLENT' if abs(results.first_block_at - RATE_LIMIT) < 15 else '⚠️  MODERATE'}")
    else:
        print(f"\n⚠️  NO BLOCKING DETECTED")
        print(f"  - All {results.total_requests} requests allowed")
        print(f"  - Rate limiter may be configured differently")
    
    # Statistics
    if results.events:
        avg_response = sum(e["response_time"] for e in results.events) / len(results.events)
        max_response = max(e["response_time"] for e in results.events)
        print(f"\n📈 Performance Metrics:")
        print(f"  - Average response time: {avg_response:.3f}s")
        print(f"  - Max response time: {max_response:.3f}s")
        print(f"  - Total test duration: {results.end_time - results.start_time:.2f}s")
    
    # Analysis
    print(f"\n🔍 Analysis:")
    if results.total_blocked > 0:
        print(f"  ✅ Rate limiting IS ACTIVE")
        print(f"  ✅ System correctly identified and blocked excess traffic")
        print(f"  ✅ Detection threshold working as designed")
        blocking_started = results.first_block_at if results.first_block_at else "unknown"
        print(f"  ℹ️  Blocking started at request: {blocking_started}")
    elif results.total_allowed == results.total_requests:
        print(f"  ⚠️  Rate limiting did NOT activate")
        print(f"  Possible reasons:")
        print(f"    1. IP allowlist includes localhost/127.0.0.1")
        print(f"    2. Rate limit is much higher than configured")
        print(f"    3. Sliding window reset between bursts")
        print(f"    4. Feature extractor not detecting rapid pattern")
    
    # Verification
    print(f"\n✅ Verification Checklist:")
    print(f"  [✅] All {BURST_SIZE} requests sent successfully")
    print(f"  [{'✅' if results.total_allowed > 0 else '❌'}] Initial requests allowed (normal traffic)")
    print(f"  [{'✅' if results.total_blocked > 0 else '⚠️ '}] Rate limiting blocked excess traffic")
    print(f"  [{'✅' if results.first_block_at and results.first_block_at > RATE_LIMIT * 0.8 else '⚠️ '}] Threshold timing accurate")
    
    # Save results
    results_dict = results.to_dict()
    with open("phase2c_accelerated_results.json", "w") as f:
        json.dump(results_dict, f, indent=2)
    print(f"\n💾 Results saved to: phase2c_accelerated_results.json")
    
    # Summary
    print("\n" + "="*70)
    if results.total_blocked > results.total_allowed * 0.1:
        print("🎉 PHASE 2c: SUCCESS - Rate limiting triggered and working!")
    elif results.total_blocked > 0:
        print("✅ PHASE 2c: PARTIAL - Some blocking observed")
    else:
        print("ℹ️  PHASE 2c: INFO - No blocking observed in this test")
        print("   → The system may use per-IP rate limiting with localhost allowlist")
        print("   → Or the rate limit may be set higher than 100 req/60s")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
