"""Test configuration and shared fixtures."""
import pytest
from types import SimpleNamespace

@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return SimpleNamespace(
        trusted_proxies=["10.0.0.0/8", "172.16.0.0/12"],
        honor_x_forwarded_for=True,
        block_duration_seconds=300,
        request_timeout_seconds=30.0,
        request_rate_limit=5,
        max_request_size_kb=1024,
        whitelist_ips="",
        allowed_hosts=["testserver", "localhost"],
        enable_host_validation=False  # Added for test stability
    )