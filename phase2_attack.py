#!/usr/bin/env python3
"""
Phase 2: DDoS Attack Simulation & Detection Verification
This script simulates a realistic DDoS attack and monitors the proxy's response.
"""

import asyncio
import httpx
import time
import json
from datetime import datetime
from typing import Dict, List


class Phase2AttackSimulator:
    def __init__(self, proxy_url="http://127.0.0.1:8080", target_path="/get"):
        self.proxy_url = proxy_url
        self.target_path = target_path
        self.baseline_results = []
        self.attack_results = []
        self.summary = {}
        
    async def run_simulation(self):
        """Run complete Phase 2 attack simulation"""
        print("\n" + "="*70)
        print("🔥 PHASE 2: DDoS ATTACK SIMULATION & DETECTION")
        print("="*70 + "\n")
        
        # Step 1: Baseline traffic
        print("📍 Step 1: Generating Baseline Traffic (Normal Usage)")
        print("-" * 70)
        await self.generate_baseline_traffic()
        
        # Wait between phases
        await asyncio.sleep(3)
        
        # Step 2: Attack simulation
        print("\n📍 Step 2: Simulating DDoS Attack (Burst Traffic)")
        print("-" * 70)
        await self.simulate_attack()
        
        # Wait for results to settle
        await asyncio.sleep(2)
        
        # Step 3: Analysis
        print("\n📍 Step 3: Analyzing Results")
        print("-" * 70)
        self.analyze_results()
        
        # Step 4: Verification
        print("\n📍 Step 4: Detection Verification")
        print("-" * 70)
        self.verify_detection()
    
    async def generate_baseline_traffic(self):
        """Generate normal baseline traffic (low rate)"""
        print("Sending 10 requests with 0.5s delay (normal usage pattern)...\n")
        
        async with httpx.AsyncClient(timeout=10) as client:
            for i in range(10):
                try:
                    start = time.time()
                    response = await client.get(
                        f"{self.proxy_url}{self.target_path}?req={i}&phase=baseline"
                    )
                    elapsed = time.time() - start
                    
                    result = {
                        "request_id": i,
                        "status_code": response.status_code,
                        "response_time": elapsed,
                        "timestamp": datetime.now().isoformat(),
                        "phase": "baseline",
                        "allowed": response.status_code == 200
                    }
                    self.baseline_results.append(result)
                    
                    icon = "✅" if response.status_code == 200 else "❌"
                    print(f"  {icon} Request {i+1}: Status {response.status_code}, "
                          f"Time: {elapsed:.3f}s")
                    
                except Exception as e:
                    print(f"  ❌ Request {i+1}: Error - {str(e)}")
                    self.baseline_results.append({
                        "request_id": i,
                        "status_code": 0,
                        "response_time": 0,
                        "timestamp": datetime.now().isoformat(),
                        "phase": "baseline",
                        "allowed": False,
                        "error": str(e)
                    })
                
                # Normal pacing (0.5 seconds between requests)
                await asyncio.sleep(0.5)
        
        # Calculate baseline stats
        successful = sum(1 for r in self.baseline_results if r.get("allowed"))
        avg_time = sum(r["response_time"] for r in self.baseline_results) / len(self.baseline_results)
        
        print(f"\n📊 Baseline Stats:")
        print(f"   - Successful: {successful}/{len(self.baseline_results)}")
        print(f"   - Average response time: {avg_time:.3f}s")
    
    async def simulate_attack(self):
        """Simulate a DDoS attack (high rate concurrent requests)"""
        print("Simulating DDoS attack: 50 concurrent requests...")
        print("(This should trigger rate limiting/blocking)")
        print()
        
        async with httpx.AsyncClient(timeout=10) as client:
            # Create 50 concurrent requests
            tasks = []
            for i in range(50):
                tasks.append(
                    self._attack_request(client, i)
                )
            
            # Execute all simultaneously
            start = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            attack_duration = time.time() - start
            
            # Process results
            for i, response in enumerate(responses):
                if isinstance(response, dict):
                    self.attack_results.append(response)
                    status = response.get("status_code", "ERROR")
                    
                    if status == 200:
                        icon = "✅"
                        result = "ALLOWED"
                    elif status == 429:
                        icon = "⚠️ "
                        result = "RATE LIMITED"
                    elif status == 403:
                        icon = "🛑"
                        result = "BLOCKED"
                    else:
                        icon = "❌"
                        result = f"STATUS {status}"
                    
                    print(f"  {icon} Request {i+1}: {result}")
        
        # Calculate attack stats
        allowed = sum(1 for r in self.attack_results if r.get("status_code") == 200)
        rate_limited = sum(1 for r in self.attack_results if r.get("status_code") == 429)
        blocked = sum(1 for r in self.attack_results if r.get("status_code") == 403)
        errors = sum(1 for r in self.attack_results if r.get("status_code", 0) not in [200, 429, 403])
        
        print(f"\n📊 Attack Stats:")
        print(f"   - Allowed: {allowed}/50")
        print(f"   - Rate Limited (429): {rate_limited}/50")
        print(f"   - Blocked (403): {blocked}/50")
        print(f"   - Errors: {errors}/50")
        print(f"   - Duration: {attack_duration:.2f}s")
        print(f"   - Request rate: {50/attack_duration:.1f} req/s")
    
    async def _attack_request(self, client: httpx.AsyncClient, request_id: int):
        """Single attack request"""
        try:
            start = time.time()
            response = await client.get(
                f"{self.proxy_url}{self.target_path}?attack={request_id}&phase=attack",
                follow_redirects=False
            )
            elapsed = time.time() - start
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": elapsed,
                "timestamp": datetime.now().isoformat(),
                "phase": "attack"
            }
        except Exception as e:
            return {
                "request_id": request_id,
                "status_code": 0,
                "response_time": 0,
                "timestamp": datetime.now().isoformat(),
                "phase": "attack",
                "error": str(e)
            }
    
    def analyze_results(self):
        """Analyze baseline vs attack results"""
        print("Comparing baseline vs attack behavior...\n")
        
        # Baseline analysis
        baseline_allowed = sum(1 for r in self.baseline_results if r.get("allowed"))
        baseline_blocked = len(self.baseline_results) - baseline_allowed
        baseline_avg = sum(r["response_time"] for r in self.baseline_results) / len(self.baseline_results)
        
        # Attack analysis
        attack_allowed = sum(1 for r in self.attack_results if r.get("status_code") == 200)
        attack_limited = sum(1 for r in self.attack_results if r.get("status_code") == 429)
        attack_blocked = sum(1 for r in self.attack_results if r.get("status_code") == 403)
        attack_avg = sum(r["response_time"] for r in self.attack_results if r.get("response_time")) / len(self.attack_results) if self.attack_results else 0
        
        print("📈 Comparison:")
        print(f"\n  Baseline (Normal Traffic):")
        print(f"    - Allowed: {baseline_allowed}/{len(self.baseline_results)} (100%)")
        print(f"    - Blocked: {baseline_blocked}/{len(self.baseline_results)} (0%)")
        print(f"    - Avg Response: {baseline_avg:.3f}s")
        
        print(f"\n  Under Attack (High Rate):")
        print(f"    - Allowed: {attack_allowed}/{len(self.attack_results)} ({attack_allowed/len(self.attack_results)*100:.1f}%)")
        print(f"    - Rate Limited: {attack_limited}/{len(self.attack_results)} ({attack_limited/len(self.attack_results)*100:.1f}%)")
        print(f"    - Blocked: {attack_blocked}/{len(self.attack_results)} ({attack_blocked/len(self.attack_results)*100:.1f}%)")
        print(f"    - Avg Response: {attack_avg:.3f}s")
        
        # Store summary
        self.summary = {
            "baseline": {
                "total": len(self.baseline_results),
                "allowed": baseline_allowed,
                "blocked": baseline_blocked,
                "avg_response_time": baseline_avg
            },
            "attack": {
                "total": len(self.attack_results),
                "allowed": attack_allowed,
                "rate_limited": attack_limited,
                "blocked": attack_blocked,
                "avg_response_time": attack_avg
            }
        }
    
    def verify_detection(self):
        """Verify DDoS detection worked correctly"""
        print("\n✅ Detection Verification Checklist:\n")
        
        checks_passed = 0
        checks_total = 5
        
        # Check 1: Baseline all allowed
        baseline_blocked = len(self.baseline_results) - sum(1 for r in self.baseline_results if r.get("allowed"))
        if baseline_blocked == 0:
            print("  ✅ Check 1: Baseline traffic all allowed (no false positives)")
            checks_passed += 1
        else:
            print(f"  ❌ Check 1: Baseline blocked {baseline_blocked} requests (false positives)")
        
        # Check 2: Attack detected
        attack_mitigated = sum(1 for r in self.attack_results 
                             if r.get("status_code") in [429, 403])
        if attack_mitigated > 0:
            print(f"  ✅ Check 2: DDoS detected and mitigated ({attack_mitigated}/50 requests limited/blocked)")
            checks_passed += 1
        else:
            print("  ❌ Check 2: Attack not detected (no rate limiting/blocking)")
        
        # Check 3: Response time remained reasonable
        if self.summary["attack"]["avg_response_time"] < 5:
            print(f"  ✅ Check 3: Response time acceptable under attack ({self.summary['attack']['avg_response_time']:.3f}s)")
            checks_passed += 1
        else:
            print(f"  ❌ Check 3: Response time too high ({self.summary['attack']['avg_response_time']:.3f}s)")
        
        # Check 4: Some requests succeeded
        if self.summary["attack"]["allowed"] > 0:
            print(f"  ✅ Check 4: Legitimate traffic allowed during attack ({self.summary['attack']['allowed']} requests)")
            checks_passed += 1
        else:
            print("  ⚠️  Check 4: No requests allowed (full lockdown - may be intended)")
        
        # Check 5: Rate limiting/blocking occurred
        if self.summary["attack"]["rate_limited"] > 0 or self.summary["attack"]["blocked"] > 0:
            print(f"  ✅ Check 5: Rate limiting/blocking active ({self.summary['attack']['rate_limited'] + self.summary['attack']['blocked']} requests)")
            checks_passed += 1
        else:
            print("  ❌ Check 5: No rate limiting/blocking detected")
        
        print(f"\n📊 Verification Score: {checks_passed}/{checks_total} checks passed")
        
        if checks_passed >= 4:
            print("\n🎉 PHASE 2 SUCCESSFUL - DDoS Detection & Mitigation Working!")
        elif checks_passed >= 2:
            print("\n⚠️  PHASE 2 PARTIAL - Some detection features working, review results")
        else:
            print("\n❌ PHASE 2 FAILED - Detection system not responding as expected")
    
    def save_results(self):
        """Save detailed results to JSON"""
        results = {
            "phase": "phase2_attack_simulation",
            "timestamp": datetime.now().isoformat(),
            "baseline": self.baseline_results,
            "attack": self.attack_results,
            "summary": self.summary
        }
        
        with open("phase2_attack_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: phase2_attack_results.json")


async def main():
    simulator = Phase2AttackSimulator()
    try:
        await simulator.run_simulation()
        simulator.save_results()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
    except Exception as e:
        print(f"\n\nError during simulation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
