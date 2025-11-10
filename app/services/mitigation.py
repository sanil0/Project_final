"""Mitigation controller applying edge actions based on detection verdicts."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict

from ..schemas import DetectionVerdict, MitigationAction, MitigationResult


@dataclass
class MitigationController:
    request_rate_limit: int
    sliding_window_seconds: int
    rate_limited_ips: Dict[str, float] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def apply(self, ip: str, verdict: DetectionVerdict) -> MitigationResult:
        action = verdict.action
        if action == MitigationAction.RATE_LIMIT:
            allowed = await self._apply_rate_limit(ip)
        elif action == MitigationAction.BLOCK:
            allowed = False
        else:
            allowed = True
        return MitigationResult(verdict=verdict, allowed=allowed)

    async def _apply_rate_limit(self, ip: str) -> bool:
        async with self.lock:
            now = time.time()
            window_start = now - self.sliding_window_seconds
            last_allowed = self.rate_limited_ips.get(ip, 0)
            if last_allowed < window_start:
                self.rate_limited_ips[ip] = now
                return True
            return False

    async def apply_rate_limit(self, ip: str) -> bool:
        """Public wrapper for applying rate limits to an IP.

        Returns True when the IP is allowed (i.e., first hit in window), False when rate-limited.
        This exposes the internal behavior safely for external callers.
        """
        return await self._apply_rate_limit(ip)

    async def unblock(self, ip: str) -> None:
        async with self.lock:
            self.rate_limited_ips.pop(ip, None)
            
    async def check_ip(self, ip: str) -> bool:
        """Check if an IP is allowed to make requests.
        
        This is a simplified check that only looks at rate limits.
        For full mitigation with ML detection, use apply() instead.
        """
        return await self._apply_rate_limit(ip)

    def get_rate_limit(self, ip: str) -> int:
        """Get the rate limit for an IP."""
        return self.request_rate_limit

    def get_remaining_requests(self, ip: str) -> int:
        """Get remaining requests allowed for an IP in current window."""
        now = time.time()
        window_start = now - self.sliding_window_seconds
        last_allowed = self.rate_limited_ips.get(ip, 0)
        if last_allowed < window_start:
            return self.request_rate_limit
        return 0

    def get_window_reset_time(self, ip: str) -> int:
        """Get seconds until rate limit window resets for an IP."""
        now = time.time()
        last_allowed = self.rate_limited_ips.get(ip, 0)
        if not last_allowed:
            return 0
        return max(0, int(last_allowed + self.sliding_window_seconds - now))
