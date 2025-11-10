"""Test suite for Telemetry Service."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, Mock

from prometheus_client import REGISTRY

from app.services.telemetry import TelemetryClient
from app.schemas import TrafficSample, DetectionVerdict, MitigationResult

@pytest.fixture
def telemetry_client():
    """Create a telemetry client for testing."""
    return TelemetryClient(max_events=5)

@pytest.fixture
def sample_traffic():
    """Create a sample traffic event for testing."""
    return TrafficSample(
        client_ip="192.168.1.100",
        method="GET",
        path="/api/test",
        headers={"User-Agent": "Test"},
        content_length=0,
        request_rate=1000.0,
        bytes_per_second=50000.0,
        packet_rate=800.0,
        timestamp=datetime.utcnow().isoformat()
    )

@pytest.fixture
def sample_verdict():
    """Create a sample detection verdict for testing."""
    return DetectionVerdict(
        action="block",
        severity="high",
        reason="High traffic volume",
        detail="Request rate exceeds threshold",
        confidence=0.95
    )

@pytest.fixture
def sample_result():
    """Create a sample mitigation result for testing."""
    return MitigationResult(
        allowed=False,
        rule_matched="rate_limit",
        duration_seconds=300
    )

@pytest.mark.asyncio
async def test_record_event(telemetry_client, sample_traffic, sample_verdict, sample_result):
    """Test recording of detection events."""
    # Record an event
    await telemetry_client.record(sample_traffic, sample_verdict, sample_result)
    
    # Get recent events
    events = await telemetry_client.recent_events()
    
    assert len(events) == 1
    event = events[0]
    
    # Verify event data
    assert event["client_ip"] == sample_traffic.client_ip
    assert event["action"] == sample_verdict.action
    assert event["severity"] == sample_verdict.severity
    assert event["allowed"] == sample_result.allowed
    assert "trace_id" in event
    assert "timestamp" in event
    assert "response_time" in event

@pytest.mark.asyncio
async def test_max_events_limit(telemetry_client, sample_traffic, sample_verdict, sample_result):
    """Test max events limit enforcement."""
    # Record more events than the limit
    for _ in range(7):
        await telemetry_client.record(sample_traffic, sample_verdict, sample_result)
    
    events = await telemetry_client.recent_events()
    assert len(events) == 5  # max_events limit

@pytest.mark.asyncio
async def test_recent_events_with_limit(telemetry_client, sample_traffic, sample_verdict, sample_result):
    """Test recent_events with limit parameter."""
    # Record multiple events
    for _ in range(4):
        await telemetry_client.record(sample_traffic, sample_verdict, sample_result)
    
    # Get limited events
    events = await telemetry_client.recent_events(limit=2)
    assert len(events) == 2

def test_prometheus_metrics(telemetry_client, sample_traffic, sample_verdict, sample_result):
    """Test Prometheus metrics integration."""
    # Get initial metrics state
    initial_metrics = telemetry_client.get_metrics_snapshot()
    
    # Record an event
    asyncio.run(telemetry_client.record(sample_traffic, sample_verdict, sample_result))
    
    # Get updated metrics
    updated_metrics = telemetry_client.get_metrics_snapshot()
    
    # Verify metrics were updated
    assert updated_metrics["total_events"] > initial_metrics["total_events"]
    assert updated_metrics["active_blocks"]["high"] > initial_metrics["active_blocks"]["high"]
    assert "response_time_percentiles" in updated_metrics

@pytest.mark.asyncio
async def test_structured_logging(telemetry_client, sample_traffic, sample_verdict, sample_result):
    """Test structured logging output."""
    with patch("structlog.get_logger") as mock_logger:
        mock_bound_logger = Mock()
        mock_logger.return_value = mock_bound_logger

        # Create new client with mocked logger
        client = TelemetryClient(max_events=5)
        client.logger = mock_bound_logger

        # Record an event
        await client.record(sample_traffic, sample_verdict, sample_result)

        # Verify logging was called
        mock_bound_logger.info.assert_called_once()

        # Get call args
        call_args = mock_bound_logger.info.call_args
        event_name = call_args[0][0]
        log_data = call_args[1]

        # Verify event name
        assert event_name == "ddos_detection_event"

        # Verify log context
        assert log_data["client_ip"] == sample_traffic.client_ip
        assert log_data["action"] == sample_verdict.action
        assert log_data["severity"] == sample_verdict.severity
        assert isinstance(log_data["response_time"], (int, float))
        assert log_data["bytes_per_second"] == sample_traffic.bytes_per_second