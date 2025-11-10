"""Test configuration validation and loading."""

import os
import pytest
from pathlib import Path
from typing import Dict, Any

from app.config import Settings, parse_list, parse_cidrs
from app.services.ml_model import SensitivityLevel

def test_parse_list():
    """Test parsing of comma-separated lists."""
    assert parse_list("") == []
    assert parse_list("  ") == []
    assert parse_list("a,b,c") == ["a", "b", "c"]
    assert parse_list(" a, b ,c ") == ["a", "b", "c"]

def test_parse_cidrs():
    """Test CIDR list parsing and validation."""
    # Valid CIDRs
    assert parse_cidrs("10.0.0.0/24,192.168.1.0/24") == ["10.0.0.0/24", "192.168.1.0/24"]
    
    # Invalid CIDR
    with pytest.raises(ValueError):
        parse_cidrs("10.0.0.0/33")  # Invalid prefix
    with pytest.raises(ValueError):
        parse_cidrs("256.256.256.256/24")  # Invalid IP

def test_settings_validation():
    """Test settings validation logic."""
    # Test valid settings
    settings = Settings(
        upstream_base_url="http://localhost:8000",
        target_url="http://localhost:8000",
        sensitivity_level=SensitivityLevel.MEDIUM,
        block_duration_minutes=30,
        max_block_duration_hours=24
    )
    assert settings.block_duration_minutes == 30
    
    # Test block duration validation
    settings = Settings(
        upstream_base_url="http://localhost:8000",
        target_url="http://localhost:8000",
        sensitivity_level=SensitivityLevel.MEDIUM,
        block_duration_minutes=2000,  # Exceeds max
        max_block_duration_hours=24
    )
    assert settings.block_duration_minutes == 24 * 60  # Should be capped at max
    
    # Test invalid sensitivity level
    with pytest.raises(ValueError):
        Settings(
            upstream_base_url="http://localhost:8000",
            target_url="http://localhost:8000",
            sensitivity_level="invalid"
        )

def test_feature_window_validation():
    """Test feature window validation."""
    settings = Settings(
        upstream_base_url="http://localhost:8000",
        target_url="http://localhost:8000",
        rate_window_seconds=60,
        feature_window_seconds=30  # Too small
    )
    assert settings.feature_window_seconds == 60  # Should be adjusted to match rate window

def test_ip_lists():
    """Test IP list parsing and validation."""
    settings = Settings(
        upstream_base_url="http://localhost:8000",
        target_url="http://localhost:8000",
        blocklist_ips="1.2.3.4, 5.6.7.8",
        whitelist_ips="10.0.0.1,10.0.0.2",
        trusted_proxies="192.168.1.0/24, 10.0.0.0/8"
    )
    
    assert settings.blocklist == ["1.2.3.4", "5.6.7.8"]
    assert settings.whitelist == ["10.0.0.1", "10.0.0.2"]
    assert settings.proxy_cidrs == ["192.168.1.0/24", "10.0.0.0/8"]

def test_bool_parsing():
    """Test boolean setting parsing."""
    settings = Settings(
        upstream_base_url="http://localhost:8000",
        target_url="http://localhost:8000",
        honor_x_forwarded_for="true",
        dynamic_rate_adjustment="yes",
        progressive_blocking="1",
        enable_model_cache="on"
    )
    
    assert settings.honor_x_forwarded_for is True
    assert settings.dynamic_rate_adjustment is True
    assert settings.progressive_blocking is True
    assert settings.enable_model_cache is True
    
    settings = Settings(
        upstream_base_url="http://localhost:8000",
        target_url="http://localhost:8000",
        honor_x_forwarded_for="false",
        dynamic_rate_adjustment="no",
        progressive_blocking="0",
        enable_model_cache="off"
    )
    
    assert settings.honor_x_forwarded_for is False
    assert settings.dynamic_rate_adjustment is False
    assert settings.progressive_blocking is False
    assert settings.enable_model_cache is False