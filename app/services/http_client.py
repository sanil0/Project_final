"""Async HTTP client wrapper for forwarding allowed requests upstream."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

import httpx

from ..config import Settings
class UpstreamHTTPClient:
    def __init__(self, base_url: str, timeout: float = 10.0, max_retries: int = 3) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = None
        self._timeout = timeout
        self._max_retries = max_retries
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(__name__)

    async def _ensure_client(self) -> None:
        # Ensure the underlying AsyncClient is created only once in a concurrency-safe way
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    try:
                        self._client = httpx.AsyncClient(
                            base_url=self._base_url,
                            timeout=httpx.Timeout(self._timeout, connect=20.0),
                            follow_redirects=True,
                            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
                        )
                        self._logger.info(f"✅ HTTP client initialized for {self._base_url}")
                    except Exception as e:
                        self._logger.error(f"❌ Failed to create HTTP client: {e}", exc_info=True)
                        self._client = None
                        raise
            
    async def forward(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        content: Optional[bytes] = None,
    ) -> httpx.Response:
        last_error = None
        
        for attempt in range(self._max_retries):
            try:
                await self._ensure_client()
                
                # Do NOT serialize requests via the global lock: allow concurrent requests
                response = await self._client.request(
                    method=method,
                    url=path,
                    headers=headers,
                    content=content,
                )
                return response
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
                last_error = e
                self._logger.warning(
                    f"Request attempt {attempt + 1}/{self._max_retries} failed: {e}",
                    exc_info=True
                )
                # Reset client on connection errors
                await self.close()
                await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                continue
            except Exception as e:
                self._logger.error(f"Unexpected error in forward request: {e}", exc_info=True)
                raise
        
        self._logger.error(f"All {self._max_retries} request attempts failed")
        raise last_error or Exception("Request failed")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


async def create_http_client(settings: Settings) -> UpstreamHTTPClient:
    return UpstreamHTTPClient(base_url=str(settings.upstream_base_url))
