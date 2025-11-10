"""Tests for IP utilities and extraction."""
import pytest
from fastapi import Request
from starlette.datastructures import Headers, Address

from app.utils.ip import (
    normalize_ip,
    is_private_ip,
    is_valid_ip,
    is_ip_in_cidr_list,
    extract_client_ip,
)


def create_mock_request(client_ip: str, headers: dict = None) -> Request:
    """Create a mock request with the given client IP and optional headers."""
    headers = headers or {}
    scope = {
        "type": "http",
        "client": Address(host=client_ip, port=1234),
        "headers": Headers(headers).raw,
    }
    return Request(scope)


@pytest.mark.parametrize(
    "client_ip,xff_header,trusted_proxies,honor_xff,expected",
    [
        # Basic client IP extraction
        ("192.168.1.2", {}, [], False, "192.168.1.2"),
        
        # Trusted proxy with XFF disabled
        ("10.0.0.1", {"x-forwarded-for": "8.8.8.8"}, ["10.0.0.0/8"], False, "10.0.0.1"),
        
        # Trusted proxy with XFF enabled
        ("10.0.0.1", {"x-forwarded-for": "8.8.8.8"}, ["10.0.0.0/8"], True, "8.8.8.8"),
        
        # Untrusted proxy XFF spoofing attempt
        ("1.2.3.4", {"x-forwarded-for": "8.8.8.8"}, ["10.0.0.0/8"], True, "1.2.3.4"),
        
        # Multiple proxies in chain
        (
            "10.0.0.2", 
            {"x-forwarded-for": "8.8.8.8, 10.0.0.1"}, 
            ["10.0.0.0/8"], 
            True, 
            "8.8.8.8"
        ),
        
        # All trusted proxies in chain - use leftmost
        (
            "10.0.0.2",
            {"x-forwarded-for": "10.0.0.1, 10.0.0.3"},
            ["10.0.0.0/8"],
            True,
            "10.0.0.1"
        ),
        
        # Invalid IP in XFF chain - skip it
        (
            "10.0.0.1",
            {"x-forwarded-for": "invalid-ip, 8.8.8.8"},
            ["10.0.0.0/8"],
            True,
            "8.8.8.8"
        ),
        
        # Empty XFF with trusted proxy
        ("10.0.0.1", {"x-forwarded-for": ""}, ["10.0.0.0/8"], True, "10.0.0.1"),
        
        # Multiple CIDR ranges
        (
            "10.0.0.1",
            {"x-forwarded-for": "8.8.8.8"},
            ["10.0.0.0/8", "192.168.0.0/16"],
            True,
            "8.8.8.8"
        ),
    ]
)
def test_extract_client_ip(client_ip, xff_header, trusted_proxies, honor_xff, expected):
    """Test various scenarios for client IP extraction."""
    request = create_mock_request(client_ip, xff_header)
    result = extract_client_ip(request, trusted_proxies, honor_xff)
    assert result == expected


def test_extract_client_ip_invalid_peer():
    """Test handling of invalid peer IP."""
    request = create_mock_request("invalid-ip")
    result = extract_client_ip(request, [], False)
    assert result is None


def test_extract_client_ip_no_client():
    """Test handling of request with no client info."""
    scope = {
        "type": "http",
        "client": None,
        "headers": Headers({}).raw,
    }
    request = Request(scope)
    result = extract_client_ip(request, [], False)
    assert result is None


@pytest.mark.parametrize(
    "ip,cidr_list,expected",
    [
        ("10.0.0.1", ["10.0.0.0/8"], True),
        ("192.168.1.1", ["10.0.0.0/8"], False),
        ("10.0.0.1", ["10.0.0.0/8", "192.168.0.0/16"], True),
        ("invalid-ip", ["10.0.0.0/8"], False),
        ("10.0.0.1", [], False),
    ]
)
def test_is_ip_in_cidr_list(ip, cidr_list, expected):
    """Test CIDR list membership checks."""
    assert is_ip_in_cidr_list(ip, cidr_list) == expected