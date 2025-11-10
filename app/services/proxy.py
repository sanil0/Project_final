"""Reverse proxy service for forwarding requests to upstream target.

NOTE: DDoS detection is handled by middleware, not here.
This proxy only forwards benign requests (already validated by middleware).
"""

from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging
from typing import Dict, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DDoSProtectionProxy:
    """
    Reverse proxy that forwards requests to upstream target.
    
    IMPORTANT: All DDoS detection happens in middleware BEFORE requests reach this proxy.
    This proxy assumes all requests are already vetted as benign by the middleware.
    """
    
    def __init__(self, target_url: str):
        # Convert AnyHttpUrl to string (Pydantic v2 compatibility)
        self.target_url = str(target_url).rstrip('/')
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Statistics tracking (for monitoring/metrics only, not analysis)
        self.total_forwarded_requests = 0
        self.forwarding_errors = 0
        logger.info(f"Proxy initialized with target: {self.target_url}")


    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def handle_request(self, request: Request) -> StreamingResponse:
        """
        Forward request to upstream target.
        
        NOTE: All DDoS analysis is done by middleware BEFORE this is called.
        If we receive a request here, it's already been validated as benign.
        """
        try:
            client_ip = request.client.host if request.client else "unknown"
            
            # Just forward the request - no analysis here
            self.total_forwarded_requests += 1
            return await self._proxy_request(request)
            
        except Exception as e:
            self.forwarding_errors += 1
            logger.error(f"Error forwarding request: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail={"error": "Bad gateway", "details": str(e)}
            )


    def _identify_attack_pattern(self, prediction: Dict) -> str:
        """DEPRECATED: Analysis happens in middleware, not here."""
        return "N/A"

    async def _extract_features(self, request: Request) -> Dict:
        """DEPRECATED: Feature extraction happens in middleware, not here."""
        return {}

    async def _proxy_request(self, request: Request) -> StreamingResponse:
        """Proxy the request to the target server."""
        # Prepare the target URL
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"
        target_url = f"{self.target_url}{path}"

        # Get the request body
        body = await request.body()
        
        # Forward the request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
                content=body,
                timeout=30.0
            )

            return StreamingResponse(
                response.aiter_raw(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )

    async def get_stats(self) -> Dict:
        """Get forwarding statistics (not analysis statistics)."""
        return {
            "total_forwarded_requests": self.total_forwarded_requests,
            "forwarding_errors": self.forwarding_errors,
            "note": "Analysis statistics are in middleware/detector, not proxy"
        }