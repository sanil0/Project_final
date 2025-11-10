"""Tests for IP extraction with trusted proxy handling."""

import pytest
from fastapi import Request
from starlette.datastructures import Headers

from app.utils.ip import extract_client_ip


def create_mock_request(client_ip: str, xff_header: str = None) -> Request:
    """Create a mock request with the given client IP and optional X-Forwarded-For."""
    scope = {
        "type": "http",
        "client": ("127.0.0.1", 1234) if client_ip == "127.0.0.1" else (client_ip, 1234),
        "headers": Headers({}).raw,
    }
    if xff_header:
        scope["headers"] = Headers({"x-forwarded-for": xff_header}).raw
    
    return Request(scope)


@pytest.mark.parametrize(
    "client_ip,xff_header,trusted_proxies,honor_xff,expected",
    [
        # Basic client IP test
        ("192.168.1.2", None, [], False, "192.168.1.2"),
        
        # Trusted proxy with XFF disabled
        ("10.0.0.1", "8.8.8.8", ["10.0.0.0/8"], False, "10.0.0.1"),
        
        # Trusted proxy with XFF enabled
        ("10.0.0.1", "8.8.8.8", ["10.0.0.0/8"], True, "8.8.8.8"),
        
        # Untrusted proxy attempting XFF spoofing
        ("1.2.3.4", "8.8.8.8", ["10.0.0.0/8"], True, "1.2.3.4"),
        
        # Multiple proxies in chain
        ("10.0.0.2", "8.8.8.8, 10.0.0.1", ["10.0.0.0/8"], True, "8.8.8.8"),
        
        # All trusted proxies in chain
        ("10.0.0.2", "10.0.0.1, 10.0.0.3", ["10.0.0.0/8"], True, "10.0.0.1"),
        
        # Invalid IP in chain
        ("10.0.0.1", "invalid-ip, 8.8.8.8", ["10.0.0.0/8"], True, "8.8.8.8"),
        
        # Empty XFF with trusted proxy
        ("10.0.0.1", "", ["10.0.0.0/8"], True, "10.0.0.1"),
        
        # Multiple CIDR ranges
        ("10.0.0.1", "8.8.8.8", ["10.0.0.0/8", "192.168.0.0/16"], True, "8.8.8.8"),
    ]
)
def test_extract_client_ip(client_ip, xff_header, trusted_proxies, honor_xff, expected):
    """Test various scenarios of client IP extraction."""
    request = create_mock_request(client_ip, xff_header)
    result = extract_client_ip(request, trusted_proxies, honor_xff)
    assert result == expected


def test_extract_client_ip_invalid_peer():
    """Test handling of invalid peer IP."""
    request = create_mock_request("invalid", None)
    result = extract_client_ip(request, [], False)
    assert result is None