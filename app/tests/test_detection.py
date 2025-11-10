import asyncio

import pytest

from app.schemas import FeatureVector, TrafficSample
from app.services.detector import DetectionEngine


@pytest.mark.asyncio
async def test_blocklist_enforced():
    engine = DetectionEngine(blocklist_ips={"1.2.3.4"})
    sample = TrafficSample(client_ip="1.2.3.4", method="GET", path="/", headers={}, content_length=0)
    features = FeatureVector(ip_request_rate=0, global_request_rate=0, unique_ip_count=1, burst_score=0)

    verdict = await engine.evaluate(sample, features)
    assert verdict.action.value == "block"


@pytest.mark.asyncio
async def test_rate_limit_triggered():
    engine = DetectionEngine(ip_rate_threshold=1.0, burst_threshold=1.0)
    sample = TrafficSample(client_ip="5.6.7.8", method="GET", path="/", headers={}, content_length=0)
    features = FeatureVector(ip_request_rate=5.0, global_request_rate=10.0, unique_ip_count=1, burst_score=10.0)

    verdict = await engine.evaluate(sample, features)
    assert verdict.action.value == "rate_limit"
