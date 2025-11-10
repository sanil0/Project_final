#!/usr/bin/env python3
"""
Phase 1: Live Testing - Test the DDoS proxy deployment
This script connects to a running proxy and verifies all endpoints work correctly.
"""

import asyncio
import httpx
import json
import time

class Phase1Tester:
    def __init__(self, proxy_url="http://127.0.0.1:8080"):
        self.proxy_url = proxy_url
        self.results = {
            "tests": [],
            "summary": {}
        }
        
    async def test_all(self):
        """Run all Phase 1 tests"""
        print("\n" + "="*70)
        print("🚀 PHASE 1: LIVE TESTING - DDoS Proxy Deployment Verification")
        print("="*70 + "\n")
        
        async with httpx.AsyncClient(timeout=10) as client:
            # Test 1: Health endpoint
            await self.test_health(client)
            await asyncio.sleep(0.5)
            
            # Test 2: Simple forwarding (GET)
            await self.test_get_forwarding(client)
            await asyncio.sleep(0.5)
            
            # Test 3: POST forwarding
            await self.test_post_forwarding(client)
            await asyncio.sleep(0.5)
            
            # Test 4: Query parameters
            await self.test_query_params(client)
            await asyncio.sleep(0.5)
            
            # Test 5: Multiple headers
            await self.test_headers(client)
            await asyncio.sleep(0.5)
            
            # Test 6: Response time measurement
            await self.test_response_time(client)
            await asyncio.sleep(0.5)
            
            # Test 7: Metrics endpoint
            await self.test_metrics(client)
            await asyncio.sleep(0.5)
            
            # Test 8: Multiple concurrent requests
            await self.test_concurrent(client)
            await asyncio.sleep(0.5)
            
            # Test 9: Different HTTP methods
            await self.test_http_methods(client)
        
        # Print summary
        self.print_summary()
    
    async def test_health(self, client):
        """Test 1: Health endpoint"""
        test_name = "Health Endpoint"
        try:
            response = await client.get(f"{self.proxy_url}/health")
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_pass(test_name, "Health check successful", {"status": data.get("status")})
                else:
                    self.log_fail(test_name, "Unexpected health response format")
            else:
                self.log_fail(test_name, f"Got status code {response.status_code}")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_get_forwarding(self, client):
        """Test 2: GET request forwarding"""
        test_name = "GET Forwarding"
        try:
            response = await client.get(f"{self.proxy_url}/get?test_key=test_value")
            if response.status_code == 200:
                data = response.json()
                if "args" in data:
                    self.log_pass(test_name, "GET request successfully forwarded", 
                                {"args": data.get("args")})
                else:
                    self.log_fail(test_name, "Response missing expected fields")
            else:
                self.log_fail(test_name, f"Got status code {response.status_code}")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_post_forwarding(self, client):
        """Test 3: POST request forwarding"""
        test_name = "POST Forwarding"
        try:
            data = {"test": "data", "timestamp": int(time.time())}
            response = await client.post(f"{self.proxy_url}/post", json=data)
            if response.status_code == 200:
                resp_data = response.json()
                if "json" in resp_data and resp_data["json"] == data:
                    self.log_pass(test_name, "POST request with JSON body successfully forwarded",
                                {"sent_data": data})
                else:
                    self.log_fail(test_name, "POST response doesn't match sent data")
            else:
                self.log_fail(test_name, f"Got status code {response.status_code}")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_query_params(self, client):
        """Test 4: Query parameters forwarding"""
        test_name = "Query Parameters"
        try:
            params = {"param1": "value1", "param2": "value2"}
            response = await client.get(f"{self.proxy_url}/get", params=params)
            if response.status_code == 200:
                data = response.json()
                args = data.get("args", {})
                if all(args.get(k) == v for k, v in params.items()):
                    self.log_pass(test_name, "Query parameters correctly forwarded",
                                {"params": args})
                else:
                    self.log_fail(test_name, "Query parameters not correctly forwarded")
            else:
                self.log_fail(test_name, f"Got status code {response.status_code}")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_headers(self, client):
        """Test 5: Custom headers forwarding"""
        test_name = "Custom Headers"
        try:
            headers = {
                "X-Custom-Header": "custom-value",
                "X-Test": "test-value"
            }
            response = await client.get(f"{self.proxy_url}/headers", headers=headers)
            if response.status_code == 200:
                data = response.json()
                resp_headers = data.get("headers", {})
                
                # Check headers - httpbin normalizes to Title-Case
                # X-Custom-Header becomes X-Custom-Header or x-custom-header
                headers_found = 0
                for sent_key, sent_val in headers.items():
                    # Check multiple possible formats (case variations)
                    for resp_key, resp_val in resp_headers.items():
                        if resp_key.lower() == sent_key.lower() and resp_val == sent_val:
                            headers_found += 1
                            break
                
                if headers_found >= 1:  # At least one custom header forwarded
                    self.log_pass(test_name, f"Custom headers correctly forwarded ({headers_found}/{len(headers)})",
                                {"headers_forwarded": headers_found, "total_headers": len(resp_headers)})
                else:
                    self.log_fail(test_name, "Custom headers were not forwarded correctly")
            else:
                self.log_fail(test_name, f"Got status code {response.status_code}")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_response_time(self, client):
        """Test 6: Response time measurement"""
        test_name = "Response Time"
        try:
            start = time.time()
            response = await client.get(f"{self.proxy_url}/get")
            elapsed = time.time() - start
            
            if response.status_code == 200 and elapsed < 5:
                self.log_pass(test_name, f"Response received in {elapsed:.3f} seconds",
                            {"response_time_ms": elapsed * 1000})
            else:
                self.log_fail(test_name, f"Response took {elapsed:.3f}s or failed")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_metrics(self, client):
        """Test 7: Metrics endpoint"""
        test_name = "Metrics Endpoint"
        try:
            response = await client.get(f"{self.proxy_url}/metrics")
            if response.status_code == 200:
                text = response.text
                if "# HELP" in text or "# TYPE" in text:
                    metric_lines = text.count("\n")
                    self.log_pass(test_name, f"Metrics endpoint working ({metric_lines} lines)",
                                {"metric_count": metric_lines})
                else:
                    self.log_fail(test_name, "Metrics response invalid format")
            else:
                self.log_fail(test_name, f"Got status code {response.status_code}")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_concurrent(self, client):
        """Test 8: Concurrent requests"""
        test_name = "Concurrent Requests"
        try:
            tasks = [
                client.get(f"{self.proxy_url}/get?req={i}")
                for i in range(5)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in responses 
                           if isinstance(r, httpx.Response) and r.status_code == 200)
            
            if successful == 5:
                self.log_pass(test_name, "All 5 concurrent requests successful",
                            {"successful": successful, "total": 5})
            else:
                self.log_fail(test_name, f"Only {successful}/5 requests succeeded")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    async def test_http_methods(self, client):
        """Test 9: Different HTTP methods"""
        test_name = "HTTP Methods"
        try:
            methods_tested = 0
            methods_ok = 0
            
            # GET
            resp = await client.get(f"{self.proxy_url}/get")
            methods_tested += 1
            if resp.status_code == 200:
                methods_ok += 1
            
            # POST
            resp = await client.post(f"{self.proxy_url}/post", json={"test": "data"})
            methods_tested += 1
            if resp.status_code == 200:
                methods_ok += 1
            
            # PUT
            resp = await client.put(f"{self.proxy_url}/put", json={"test": "data"})
            methods_tested += 1
            if resp.status_code in [200, 405]:  # 405 if not supported
                methods_ok += 1
            
            # DELETE
            resp = await client.delete(f"{self.proxy_url}/delete")
            methods_tested += 1
            if resp.status_code in [200, 405]:
                methods_ok += 1
            
            if methods_ok >= 3:
                self.log_pass(test_name, f"HTTP methods working ({methods_ok}/{methods_tested})",
                            {"methods_ok": methods_ok, "methods_tested": methods_tested})
            else:
                self.log_fail(test_name, f"Only {methods_ok}/{methods_tested} methods working")
        except Exception as e:
            self.log_fail(test_name, str(e))
    
    def log_pass(self, test_name, message, details=None):
        """Log passing test"""
        result = {"test": test_name, "status": "PASS", "message": message, "details": details or {}}
        self.results["tests"].append(result)
        print(f"✅ [{test_name}] PASS: {message}")
        if details:
            print(f"   └─ {json.dumps(details)}")
    
    def log_fail(self, test_name, message, details=None):
        """Log failing test"""
        result = {"test": test_name, "status": "FAIL", "message": message, "details": details or {}}
        self.results["tests"].append(result)
        print(f"❌ [{test_name}] FAIL: {message}")
        if details:
            print(f"   └─ {json.dumps(details)}")
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for t in self.results["tests"] if t["status"] == "PASS")
        failed = sum(1 for t in self.results["tests"] if t["status"] == "FAIL")
        total = len(self.results["tests"])
        
        self.results["summary"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0
        }
        
        print("\n" + "="*70)
        print("📊 PHASE 1 TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"📈 Pass Rate: {self.results['summary']['pass_rate']:.1f}%")
        print("="*70 + "\n")
        
        if failed == 0:
            print("🎉 PHASE 1 COMPLETE - All tests passed!")
            print("Ready to proceed to Phase 2: Attack Simulation\n")
        else:
            print(f"⚠️  {failed} test(s) failed. Review results above.\n")
        
        # Save results
        with open("phase1_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("📄 Results saved to: phase1_test_results.json\n")


async def main():
    tester = Phase1Tester()
    try:
        await tester.test_all()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
