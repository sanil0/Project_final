"""Security scanning and vulnerability assessment runner."""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import pytest
from zapv2 import ZAPv2

from security_config import (
    zap_config,
    security_test_config,
    vuln_scan_config,
    auth_test_config
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityScanner:
    def __init__(self):
        self.results_dir = Path(__file__).parent / "scan_results"
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def run_security_tests(self) -> bool:
        """Run pytest security test suite."""
        logger.info("Running security test suite...")
        
        result = pytest.main([
            "test_security.py",
            "-v",
            "--junitxml=scan_results/security_test_results.xml"
        ])
        
        return result == 0

    async def run_vulnerability_scan(self) -> bool:
        """Run vulnerability scan using OWASP ZAP."""
        logger.info("Starting vulnerability scan...")
        
        try:
            zap = ZAPv2(
                apikey=zap_config["api_key"],
                proxies={"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
            )
            
            # Start Spider scan
            logger.info("Starting spider scan...")
            scan_id = zap.spider.scan(zap_config["target_url"])
            while int(zap.spider.status(scan_id)) < 100:
                await asyncio.sleep(5)
            
            # Start Active scan
            logger.info("Starting active scan...")
            scan_id = zap.ascan.scan(zap_config["target_url"])
            while int(zap.ascan.status(scan_id)) < 100:
                await asyncio.sleep(5)
            
            # Generate report
            report = zap.core.htmlreport()
            report_path = self.results_dir / f"vulnerability_scan_{self.timestamp}.html"
            report_path.write_text(report)
            
            # Check for high-risk findings
            alerts = zap.core.alerts()
            high_risks = [a for a in alerts if a["risk"] == "High"]
            
            if high_risks:
                logger.warning(f"Found {len(high_risks)} high-risk vulnerabilities!")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Vulnerability scan failed: {e}")
            return False

    async def check_security_headers(self) -> bool:
        """Check security headers of the application."""
        logger.info("Checking security headers...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(zap_config["target_url"]) as response:
                headers = response.headers
                
                required_headers = {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                    "X-XSS-Protection": "1; mode=block",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                }
                
                for header, expected in required_headers.items():
                    if header not in headers:
                        logger.warning(f"Missing security header: {header}")
                        return False
                    
                    value = headers[header]
                    if isinstance(expected, list):
                        if value not in expected:
                            logger.warning(f"Invalid {header} value: {value}")
                            return False
                    elif value != expected:
                        logger.warning(f"Invalid {header} value: {value}")
                        return False
                
                return True

    async def test_rate_limiting(self) -> bool:
        """Test rate limiting effectiveness."""
        logger.info("Testing rate limiting...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(security_test_config["rate_limits"]["default"] * 2):
                tasks.append(session.get(zap_config["target_url"]))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if rate limiting kicked in
            status_codes = [
                r.status if isinstance(r, aiohttp.ClientResponse) else None 
                for r in responses
            ]
            
            return 429 in status_codes

    async def run_all_scans(self) -> bool:
        """Run all security scans and tests."""
        tasks = [
            self.run_security_tests(),
            self.run_vulnerability_scan(),
            self.check_security_headers(),
            self.test_rate_limiting()
        ]
        
        results = await asyncio.gather(*tasks)
        success = all(results)
        
        # Generate summary report
        summary = {
            "timestamp": self.timestamp,
            "overall_success": success,
            "tests": {
                "security_tests": results[0],
                "vulnerability_scan": results[1],
                "security_headers": results[2],
                "rate_limiting": results[3]
            }
        }
        
        summary_path = self.results_dir / f"scan_summary_{self.timestamp}.json"
        summary_path.write_text(json.dumps(summary, indent=2))
        
        return success

async def main():
    """Main entry point for security scanning."""
    scanner = SecurityScanner()
    success = await scanner.run_all_scans()
    
    if success:
        logger.info("All security scans completed successfully!")
        return 0
    else:
        logger.error("Some security scans failed. Check the reports for details.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))