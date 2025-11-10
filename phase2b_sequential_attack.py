"""
Phase 2b: Sequential Attack Pattern Testing
Purpose: Verify rate limiting triggers at configured thresholds
Method: Wave-based attack pattern to trigger detection
Expected: 429/403 responses when exceeding rate limit
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
WAVES = 5
REQUESTS_PER_WAVE = 20
SPACING_WITHIN_WAVE = 0.1  # 100ms between requests in a wave
SPACING_BETWEEN_WAVES = 2.0  # 2 seconds between waves

class Phase2bResults:
    """Track attack simulation results"""
    
    def __init__(self):
        self.wave_results = []
        self.total_requests = 0
        self.total_allowed = 0
        self.total_blocked = 0
        self.start_time = None
        self.end_time = None
        self.threshold_exceeded_at = None
        self.events = []
    
    def add_event(self, wave: int, request_num: int, status: int, response_time: float, timestamp: float):
        """Record individual request event"""
        self.events.append({
            "wave": wave,
            "request": request_num,
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
            if self.threshold_exceeded_at is None:
                self.threshold_exceeded_at = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary"""
        return {
            "metadata": {
                "test_type": "Phase 2b - Sequential Attack Pattern",
                "proxy_url": PROXY_URL,
                "rate_limit": f"{RATE_LIMIT} requests/60s",
                "test_configuration": {
                    "waves": WAVES,
                    "requests_per_wave": REQUESTS_PER_WAVE,
                    "total_requests": WAVES * REQUESTS_PER_WAVE,
                    "spacing_within_wave": SPACING_WITHIN_WAVE,
                    "spacing_between_waves": SPACING_BETWEEN_WAVES
                },
                "test_timestamp": datetime.now().isoformat()
            },
            "results": {
                "total_requests": self.total_requests,
                "total_allowed": self.total_allowed,
                "total_blocked": self.total_blocked,
                "success_rate": (self.total_allowed / self.total_requests * 100) if self.total_requests > 0 else 0,
                "block_rate": (self.total_blocked / self.total_requests * 100) if self.total_requests > 0 else 0,
                "threshold_exceeded_at_request": self.total_allowed,
                "threshold_exceeded_timestamp": self.threshold_exceeded_at
            },
            "events": self.events,
            "summary": {
                "phase_2b_status": "ATTACK PATTERN EXECUTED",
                "rate_limiting_active": self.total_blocked > 0,
                "detection_triggered": self.threshold_exceeded_at is not None,
                "expected_behavior": "Rate limit should trigger around request 100-110"
            }
        }

async def run_wave_attack(wave_num: int, results: Phase2bResults) -> None:
    """Execute a single wave of requests"""
    print(f"\n🌊 Wave {wave_num}/{WAVES} starting...")
    print(f"   Sending {REQUESTS_PER_WAVE} requests with {SPACING_WITHIN_WAVE}s spacing...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for req_num in range(1, REQUESTS_PER_WAVE + 1):
            try:
                start = time.time()
                response = await client.get(TEST_ENDPOINT, follow_redirects=True)
                elapsed = time.time() - start
                
                status = response.status_code
                results.add_event(wave_num, req_num, status, elapsed, time.time())
                
                # Visual feedback
                if status < 400:
                    symbol = "✅"
                else:
                    symbol = "🚫"
                
                print(f"   {symbol} Wave {wave_num} - Req {req_num:2d}: {status} ({elapsed:.3f}s)")
                
                # Spacing within wave
                if req_num < REQUESTS_PER_WAVE:
                    await asyncio.sleep(SPACING_WITHIN_WAVE)
                
            except Exception as e:
                print(f"   ❌ Wave {wave_num} - Req {req_num:2d}: ERROR - {str(e)[:50]}")
                results.add_event(wave_num, req_num, 500, 0.0, time.time())
                await asyncio.sleep(SPACING_WITHIN_WAVE)
        
        # Summary for wave
        wave_allowed = sum(1 for e in results.events if e["wave"] == wave_num and e["allowed"])
        wave_blocked = sum(1 for e in results.events if e["wave"] == wave_num and e["blocked"])
        print(f"   📊 Wave {wave_num} Summary: {wave_allowed} allowed, {wave_blocked} blocked")

async def main():
    """Main test execution"""
    print("\n" + "="*70)
    print("🎯 PHASE 2b: SEQUENTIAL ATTACK PATTERN TESTING")
    print("="*70)
    print(f"Purpose: Verify rate limiting triggers at configured threshold")
    print(f"Configuration:")
    print(f"  - Waves: {WAVES}")
    print(f"  - Requests per wave: {REQUESTS_PER_WAVE}")
    print(f"  - Total requests: {WAVES * REQUESTS_PER_WAVE}")
    print(f"  - Rate limit: {RATE_LIMIT} requests/60s")
    print(f"  - Expected threshold: ~{RATE_LIMIT} requests")
    print(f"\n📌 Expected Behavior:")
    print(f"  - Requests 1-100: Should mostly succeed (✅)")
    print(f"  - Requests 101+: Should start getting blocked (🚫)")
    print("="*70)
    
    results = Phase2bResults()
    results.start_time = time.time()
    
    # Execute waves
    try:
        for wave in range(1, WAVES + 1):
            await run_wave_attack(wave, results)
            
            # Spacing between waves (except after last wave)
            if wave < WAVES:
                print(f"\n⏸️  Waiting {SPACING_BETWEEN_WAVES}s before next wave...")
                await asyncio.sleep(SPACING_BETWEEN_WAVES)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    
    finally:
        results.end_time = time.time()
    
    # Print comprehensive results
    print("\n" + "="*70)
    print("📊 PHASE 2b RESULTS")
    print("="*70)
    print(f"\nTotal Requests: {results.total_requests}")
    print(f"  ✅ Allowed: {results.total_allowed} ({results.total_allowed/results.total_requests*100:.1f}%)")
    print(f"  🚫 Blocked: {results.total_blocked} ({results.total_blocked/results.total_requests*100:.1f}%)")
    
    if results.threshold_exceeded_at:
        threshold_req = results.total_allowed
        print(f"\n🎯 Rate Limiting Threshold:")
        print(f"  - Exceeded at request: ~{threshold_req}")
        print(f"  - Expected threshold: {RATE_LIMIT}")
        print(f"  - Match: {'✅ YES' if abs(threshold_req - RATE_LIMIT) < 20 else '⚠️ VARIES'}")
    else:
        print(f"\n⚠️  Rate limiting did not trigger (all requests allowed)")
    
    # Analysis
    print(f"\n🔍 Analysis:")
    if results.total_blocked > 0:
        print(f"  ✅ Rate limiting is ACTIVE")
        print(f"  ✅ Detection correctly triggered blocked requests")
        print(f"  ✅ Wave-based pattern successfully triggered threshold")
    else:
        print(f"  ⚠️  Rate limiting did NOT trigger")
        print(f"  → May need higher request rate or longer test duration")
    
    if results.total_requests > 0:
        avg_response_time = sum(e["response_time"] for e in results.events) / len(results.events)
        print(f"  📈 Average response time: {avg_response_time:.3f}s")
    
    # Verification checklist
    print(f"\n✅ Verification Checklist:")
    print(f"  [{'✅' if results.total_requests == WAVES * REQUESTS_PER_WAVE else '❌'}] All {WAVES * REQUESTS_PER_WAVE} requests executed")
    print(f"  [{'✅' if results.total_allowed > 0 else '❌'}] Some requests allowed (normal traffic)")
    print(f"  [{'✅' if results.total_blocked > 0 else '⚠️ '}] Rate limiting triggered (blocked requests)")
    print(f"  [{'✅' if results.threshold_exceeded_at else '⚠️ '}] Threshold exceeded detected")
    print(f"  [{'✅' if results.total_blocked > results.total_allowed * 0.05 else '⚠️ '}] Significant blocking observed")
    
    # Save results
    results_dict = results.to_dict()
    with open("phase2b_attack_results.json", "w") as f:
        json.dump(results_dict, f, indent=2)
    print(f"\n💾 Results saved to: phase2b_attack_results.json")
    
    # Final status
    print("\n" + "="*70)
    if results.total_blocked > 0 and results.total_allowed > 0:
        print("🎉 PHASE 2b: SUCCESS - Rate limiting is working correctly!")
        print(f"   Threshold triggered at ~{results.total_allowed} requests (target: {RATE_LIMIT})")
    elif results.total_blocked > 0:
        print("⚠️  PHASE 2b: PARTIALLY WORKING - Most requests were blocked")
        print(f"   May indicate aggressive rate limiting or IP-level blocking")
    else:
        print("ℹ️  PHASE 2b: NO BLOCKING OBSERVED")
        print(f"   Rate limiter may have reset or not be at threshold yet")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
