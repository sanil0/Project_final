"""In-memory sliding window store for request telemetry."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


@dataclass
class SlidingWindowSnapshot:
    ip_request_rate: float
    global_request_rate: float
    unique_ip_count: int
    ip_event_count: int
    global_event_count: int


class SlidingWindowStore:
    """Tracks request activity over a sliding time window."""

    def __init__(self, window_seconds: int) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.window_seconds = window_seconds
        self._lock = asyncio.Lock()
        self._per_ip: Dict[str, Deque[float]] = defaultdict(deque)
        self._global: Deque[float] = deque()
        self._active_ips: Dict[str, float] = {}

    async def add_event(self, ip: str, timestamp: Optional[float] = None) -> SlidingWindowSnapshot:
        """Record an event for an IP and return updated metrics."""
        ts = timestamp or time.time()
        async with self._lock:
            self._record_event(ip, ts)
            self._prune_all(ts)
            return self._snapshot(ip)

    async def peek(self, ip: str, timestamp: Optional[float] = None) -> SlidingWindowSnapshot:
        """Return current metrics for an IP without adding a new event."""
        ts = timestamp or time.time()
        async with self._lock:
            self._prune_all(ts)
            return self._snapshot(ip)

    async def snapshot(self, timestamp: Optional[float] = None) -> SlidingWindowSnapshot:
        """Return aggregate metrics without focusing on a specific IP."""
        ts = timestamp or time.time()
        async with self._lock:
            self._prune_all(ts)
            global_count = len(self._global)
            unique_ip_count = len(self._active_ips)
            rate = global_count / self.window_seconds
            return SlidingWindowSnapshot(
                ip_request_rate=0.0,
                global_request_rate=rate,
                unique_ip_count=unique_ip_count,
                ip_event_count=0,
                global_event_count=global_count,
            )

    def _record_event(self, ip: str, timestamp: float) -> None:
        queue = self._per_ip[ip]
        queue.append(timestamp)
        self._active_ips[ip] = timestamp
        self._global.append(timestamp)

    def _prune_all(self, now: float) -> None:
        window_start = now - self.window_seconds
        # Prune global queue
        while self._global and self._global[0] < window_start:
            self._global.popleft()
        # Prune per-ip queues and active ip map
        for ip in list(self._per_ip.keys()):
            queue = self._per_ip[ip]
            while queue and queue[0] < window_start:
                queue.popleft()
            if queue:
                self._active_ips[ip] = queue[-1]
            else:
                self._per_ip.pop(ip, None)
                self._active_ips.pop(ip, None)
        # Remove stale entries from active IPs (safety guard)
        for ip, last_seen in list(self._active_ips.items()):
            if last_seen < window_start:
                self._active_ips.pop(ip, None)

    def _snapshot(self, ip: str) -> SlidingWindowSnapshot:
        ip_queue = self._per_ip.get(ip, deque())
        ip_count = len(ip_queue)
        global_count = len(self._global)
        ip_rate = ip_count / self.window_seconds
        global_rate = global_count / self.window_seconds
        unique_ip_count = len(self._active_ips)
        return SlidingWindowSnapshot(
            ip_request_rate=ip_rate,
            global_request_rate=global_rate,
            unique_ip_count=unique_ip_count,
            ip_event_count=ip_count,
            global_event_count=global_count,
        )
