"""Test suite for IP address utilities."""

import pytest
from fastapi import Request
from app.utils.ip import (
    normalize_ip,
    is_private_ip,
    is_valid_ip,
    is_ip_in_cidr_list,
    get_client_ip,
    extract_client_ip
)

def test_normalize_ip():
    """Test IP address normalization."""
    # Test valid IPv4
    assert normalize_ip("192.168.1.1") == "192.168.1.1"
    # Test valid IPv6
    assert normalize_ip("2001:db8::1") == "2001:db8::1"
    # Test None input
    assert normalize_ip(None) is None
    # Test empty string
    assert normalize_ip("") is None
    # Test invalid IP
    assert normalize_ip("256.256.256.256") is None
    assert normalize_ip("not an ip") is None

def test_is_private_ip():
    """Test private IP detection."""
    # Test private IPv4
    assert is_private_ip("192.168.1.1") is True
    assert is_private_ip("10.0.0.1") is True
    assert is_private_ip("172.16.0.1") is True
    # Test public IPv4
    assert is_private_ip("8.8.8.8") is False
    # Test private IPv6
    assert is_private_ip("fd00::1") is True
    # Test public IPv6
    assert is_private_ip("2606:4700:4700::1111") is False  # Cloudflare DNS
    # Test invalid IP
    assert is_private_ip("not an ip") is False
    assert is_private_ip(None) is False

def test_is_valid_ip():
    """Test IP validation."""
    # Test valid IPs
    assert is_valid_ip("192.168.1.1") is True
    assert is_valid_ip("2001:db8::1") is True
    # Test invalid IPs
    assert is_valid_ip("256.256.256.256") is False
    assert is_valid_ip("not an ip") is False
    assert is_valid_ip("") is False
    assert is_valid_ip(None) is False

def test_is_ip_in_cidr_list():
    """Test CIDR range checking."""
    cidr_list = ["192.168.0.0/16", "10.0.0.0/8", "2001:db8::/32"]
    
    # Test IPs in ranges
    assert is_ip_in_cidr_list("192.168.1.1", cidr_list) is True
    assert is_ip_in_cidr_list("10.0.0.1", cidr_list) is True
    assert is_ip_in_cidr_list("2001:db8:1::1", cidr_list) is True
    
    # Test IPs not in ranges
    assert is_ip_in_cidr_list("172.16.0.1", cidr_list) is False
    assert is_ip_in_cidr_list("2001:db9::1", cidr_list) is False
    
    # Test invalid inputs
    assert is_ip_in_cidr_list("", cidr_list) is False
    assert is_ip_in_cidr_list("not an ip", cidr_list) is False
    assert is_ip_in_cidr_list("192.168.1.1", []) is False
    assert is_ip_in_cidr_list("192.168.1.1", ["invalid cidr"]) is False

class MockRequest:
    """Mock Request class for testing."""
    def __init__(self, client_host, headers=None):
        self.client = type('Client', (), {'host': client_host})()
        self._headers = headers or {}
        
    @property
    def headers(self):
        """Case-insensitive header access."""
        return {k.lower(): v for k, v in self._headers.items()}

def test_get_client_ip():
    """Test client IP extraction from request."""
    # Test direct client IP
    request = MockRequest("192.168.1.1")
    assert extract_client_ip(request, [], honor_xff=False) == "192.168.1.1"
    
    # Test with X-Forwarded-For from trusted proxy
    request = MockRequest(
        "10.0.0.1",  # Proxy IP
        {"X-Forwarded-For": "203.0.113.195"}  # Real client IP
    )
    assert extract_client_ip(request, ["10.0.0.0/8"], honor_xff=True) == "203.0.113.195"
    
    # Test with multiple X-Forwarded-For values
    request = MockRequest(
        "10.0.0.1",  # Our trusted proxy
        {"X-Forwarded-For": "192.168.1.1, 203.0.113.195"}  # proxies are added from left to right
    )
    assert extract_client_ip(request, ["10.0.0.0/8", "192.168.0.0/16"], honor_xff=True) == "203.0.113.195"
    
    # Test with untrusted proxy
    request = MockRequest(
        "8.8.8.8",  # Untrusted proxy
        {"X-Forwarded-For": "203.0.113.195"}
    )
    assert extract_client_ip(request, ["10.0.0.0/8"], honor_xff=True) == "8.8.8.8"  # Should use direct IP