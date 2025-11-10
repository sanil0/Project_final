"""Feature extraction logic for inbound traffic samples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..schemas import FeatureVector, TrafficSample
from .storage import SlidingWindowStore


@dataclass
class FeatureExtractor:
    store: SlidingWindowStore

    async def compute_features(self, sample: TrafficSample) -> FeatureVector:
        snapshot = await self.store.add_event(sample.client_ip)
        burst_score = 0.0
        if snapshot.ip_request_rate > 0:
            average_rate = max(snapshot.global_request_rate / max(snapshot.unique_ip_count, 1), 1e-6)
            burst_score = snapshot.ip_request_rate / average_rate
        headers = self._normalize_headers(sample.headers)
        # Placeholder for entropy or content-based features if needed
        _ = headers
        return FeatureVector(
            ip_request_rate=snapshot.ip_request_rate,
            global_request_rate=snapshot.global_request_rate,
            unique_ip_count=snapshot.unique_ip_count,
            burst_score=burst_score,
        )

    def _normalize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        return {key.lower(): value for key, value in headers.items()}
