"""Telemetry client for monitoring, logging, and metrics collection."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional
from uuid import uuid4

import structlog
from prometheus_client import Counter, Gauge, Histogram, Info
from prometheus_client.utils import INF

from ..schemas import DetectionVerdict, MitigationResult, TrafficSample

# Configure structlog for JSON logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Define Prometheus metrics
DDOS_EVENTS = Counter(
    "ddos_events_total",
    "Total number of DDoS detection events",
    ["action", "severity", "result"]
)

DDOS_RESPONSE_TIME = Histogram(
    "ddos_response_time_seconds",
    "Response time for DDoS detection and mitigation",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, INF)
)

DDOS_ACTIVE_BLOCKS = Gauge(
    "ddos_active_blocks",
    "Number of currently active IP blocks",
    ["severity"]
)

DDOS_ML_METRICS = Counter(
    "ddos_ml_predictions_total",
    "ML model prediction metrics",
    ["result", "confidence_level"]
)

DDOS_SYSTEM_INFO = Info("ddos_system", "DDoS protection system information")


@dataclass
class TelemetryClient:
    max_events: int = 200
    _events: Deque[dict] = field(default_factory=deque)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    logger: structlog.BoundLogger = field(default_factory=lambda: structlog.get_logger())
    
    def __post_init__(self):
        """Initialize system info metrics."""
        DDOS_SYSTEM_INFO.info({
            "start_time": datetime.utcnow().isoformat(),
            "max_events": str(self.max_events),
            "version": "1.0.0"  # TODO: Get from package version
        })
    
    async def record(self, sample: TrafficSample, verdict: DetectionVerdict, result: MitigationResult) -> None:
        """Record detection and mitigation events with metrics and logging."""
        trace_id = str(uuid4())
        start_time = time.time()
        
        # Record response time
        response_time = time.time() - start_time

        # Record the event details
        event = {
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": sample.client_ip,
            "action": verdict.action,
            "severity": verdict.severity,
            "reason": verdict.reason,
            "detail": verdict.detail,
            "allowed": result.allowed,
            "request_rate": sample.request_rate,
            "bytes_per_second": sample.bytes_per_second,
            "packet_rate": sample.packet_rate,
            "response_time": response_time
        }
        
        # Update Prometheus metrics
        DDOS_EVENTS.labels(
            action=verdict.action,
            severity=verdict.severity,
            result="allowed" if result.allowed else "blocked"
        ).inc()
        
        # Track active blocks
        if not result.allowed:
            DDOS_ACTIVE_BLOCKS.labels(severity=verdict.severity).inc()
            
        # Record ML metrics if available
        if hasattr(verdict, "confidence") and verdict.confidence is not None:
            confidence_level = "high" if verdict.confidence > 0.8 else "medium" if verdict.confidence > 0.5 else "low"
            DDOS_ML_METRICS.labels(
                result="malicious" if not result.allowed else "benign",
                confidence_level=confidence_level
            ).inc()
        
        # Record response time
        response_time = time.time() - start_time
        DDOS_RESPONSE_TIME.observe(response_time)
        
        # Structured logging
        self.logger.info(
            "ddos_detection_event",
            client_ip=sample.client_ip,
            action=verdict.action,
            severity=verdict.severity,
            allowed=result.allowed,
            response_time=response_time,
            request_rate=sample.request_rate,
            bytes_per_second=sample.bytes_per_second,
            packet_rate=sample.packet_rate
        )
        
        # Store in event history
        async with self._lock:
            self._events.appendleft(event)
            while len(self._events) > self.max_events:
                self._events.pop()
                
    async def recent_events(self, limit: Optional[int] = None) -> List[dict]:
        """Get recent events with optional limit."""
        async with self._lock:
            events = list(self._events)
            if limit:
                events = events[:limit]
            return events
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        # Helper to safely get metric value
        def safe_get_value(metric) -> int:
            try:
                val = metric._value.get()
                return int(val) if val is not None else 0
            except (AttributeError, TypeError):
                return 0

        # Get metric samples
        try:
            samples = list(DDOS_RESPONSE_TIME.collect()[0].samples)
            percentiles = {
                s.labels.get("quantile", "sum"): s.value
                for s in samples
                if s.name.endswith("_bucket")
            }
        except (IndexError, AttributeError):
            percentiles = {"0.5": 0, "0.95": 0, "0.99": 0}

        # Compute total events by summing all counter samples regardless of labels
        try:
            events_samples = DDOS_EVENTS.collect()[0].samples
            total_events = int(sum(s.value for s in events_samples if s.name.endswith('_total')))
        except Exception:
            total_events = 0

        return {
            "active_blocks": {
                severity: safe_get_value(DDOS_ACTIVE_BLOCKS.labels(severity=severity))
                for severity in ["low", "medium", "high", "critical"]
            },
            "total_events": total_events,
            "response_time_percentiles": {
                "p50": float(percentiles.get("0.5", 0)),
                "p95": float(percentiles.get("0.95", 0)),
                "p99": float(percentiles.get("0.99", 0))
            }
        }
