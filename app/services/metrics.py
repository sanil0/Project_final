"""Prometheus metrics instrumentation for DDoS protection."""

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# DDoS Protection Metrics
requests_total = Counter(
    'ddos_requests_total',
    'Total number of requests processed',
    ['status', 'method']
)

requests_blocked_total = Counter(
    'ddos_requests_blocked_total',
    'Total number of requests blocked',
    ['reason']  # reason: high_risk, rate_limited, etc.
)

requests_allowed_total = Counter(
    'ddos_requests_allowed_total',
    'Total number of requests allowed',
    ['risk_level']  # risk_level: low, medium, high
)

request_duration_seconds = Histogram(
    'ddos_request_duration_seconds',
    'Request processing duration in seconds',
    ['status'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0)
)

blocked_ips_total = Counter(
    'ddos_blocked_ips_total',
    'Total number of unique IPs blocked',
    ['reason']
)

active_blocked_ips = Gauge(
    'ddos_active_blocked_ips',
    'Number of currently blocked IPs'
)

risk_score_histogram = Histogram(
    'ddos_risk_score',
    'Distribution of risk scores for analyzed requests',
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
)

rate_limit_hits = Counter(
    'ddos_rate_limit_hits_total',
    'Total number of rate limit hits'
)

model_inference_duration = Histogram(
    'ddos_model_inference_seconds',
    'ML model inference duration in seconds',
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
)

feature_extraction_duration = Histogram(
    'ddos_feature_extraction_seconds',
    'Feature extraction duration in seconds',
    buckets=(0.001, 0.01, 0.05, 0.1)
)


def track_request_metrics(func):
    """Decorator to track request metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            request_duration_seconds.labels(status='success').observe(duration)
            requests_total.labels(status='success', method='POST').inc()
            return result
        except Exception as e:
            duration = time.time() - start_time
            request_duration_seconds.labels(status='error').observe(duration)
            requests_total.labels(status='error', method='POST').inc()
            raise
    return wrapper


def track_model_inference(func):
    """Decorator to track ML model inference duration."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        model_inference_duration.observe(duration)
        return result
    return wrapper


def record_blocked_request(reason: str, risk_score: float = 0.0):
    """Record metrics for a blocked request."""
    requests_blocked_total.labels(reason=reason).inc()
    if risk_score > 0:
        risk_score_histogram.observe(risk_score)


def record_allowed_request(risk_level: str = 'low'):
    """Record metrics for an allowed request."""
    requests_allowed_total.labels(risk_level=risk_level).inc()


def record_blocked_ip(reason: str):
    """Record metrics for a newly blocked IP."""
    blocked_ips_total.labels(reason=reason).inc()


def update_active_blocked_ips(count: int):
    """Update gauge of currently active blocked IPs."""
    active_blocked_ips.set(count)
