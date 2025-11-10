"""Load testing configuration."""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class LoadTestProfile:
    """Configuration for a load test scenario."""
    name: str
    duration_seconds: int
    ramp_up_time: int
    target_rps: float
    max_users: int
    request_patterns: List[Dict]
    
# Normal traffic profile
NORMAL_TRAFFIC = LoadTestProfile(
    name="normal_traffic",
    duration_seconds=30,   # 30 seconds
    ramp_up_time=5,       # 5 seconds ramp-up
    target_rps=50.0,      # 50 requests per second
    max_users=100,
    request_patterns=[
        {
            "weight": 60,
            "endpoint": "/",
            "method": "GET"
        },
        {
            "weight": 20,
            "endpoint": "/api/test",
            "method": "GET"
        },
        {
            "weight": 20,
            "endpoint": "/healthz",
            "method": "GET"
        }
    ]
)

# DDoS simulation profile
DDOS_TRAFFIC = LoadTestProfile(
    name="ddos_simulation",
    duration_seconds=45,   # 45 seconds
    ramp_up_time=5,       # Quick ramp-up
    target_rps=1000.0,    # 1000 requests per second
    max_users=500,
    request_patterns=[
        {
            "weight": 90,
            "endpoint": "/",
            "method": "GET"
        },
        {
            "weight": 10,
            "endpoint": "/api/heavy",
            "method": "POST",
            "payload": {"data": "X" * 1000}  # 1KB payload
        }
    ]
)

# Slow Loris attack simulation
SLOW_LORIS = LoadTestProfile(
    name="slow_loris",
    duration_seconds=30,   # 30 seconds
    ramp_up_time=5,       # 5 seconds ramp-up
    target_rps=10.0,      # Low RPS but long-living connections
    max_users=100,        # Reduced concurrent users
    request_patterns=[
        {
            "weight": 100,
            "endpoint": "/",
            "method": "GET",
            "headers": {
                "X-Test": "A" * 100  # Large header
            },
            "connection": "keep-alive",
            "chunk_size": 1,         # Send 1 byte at a time
            "chunk_delay": 10        # 10 second delay between chunks
        }
    ]
)

# Burst attack simulation
BURST_ATTACK = LoadTestProfile(
    name="burst_attack",
    duration_seconds=20,    # 20 seconds
    ramp_up_time=1,        # Almost no ramp-up
    target_rps=2000.0,     # Reduced RPS for testing
    max_users=200,
    request_patterns=[
        {
            "weight": 100,
            "endpoint": "/api/heavy",
            "method": "POST",
            "payload": {"data": "X" * 10000}  # 10KB payload
        }
    ]
)

# Mixed traffic profile
MIXED_TRAFFIC = LoadTestProfile(
    name="mixed_traffic",
    duration_seconds=40,    # 40 seconds
    ramp_up_time=5,        # 5 seconds ramp-up
    target_rps=200.0,      # Moderate RPS
    max_users=100,
    request_patterns=[
        # Normal traffic
        {
            "weight": 40,
            "endpoint": "/",
            "method": "GET"
        },
        # API calls
        {
            "weight": 20,
            "endpoint": "/api/docs",
            "method": "GET"
        },
        # Heavy requests
        {
            "weight": 20,
            "endpoint": "/api/heavy",
            "method": "POST",
            "payload": {"data": "X" * 5000}
        },
        # Slow requests
        {
            "weight": 20,
            "endpoint": "/api/slow",
            "method": "GET",
            "connection": "keep-alive",
            "chunk_size": 100,
            "chunk_delay": 1
        }
    ]
)