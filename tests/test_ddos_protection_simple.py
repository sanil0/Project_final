"""Simplified test suite for DDoS Protection components."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from app.services.detector import DetectionEngine, DetectionResult
from app.services.mitigation import MitigationController
from app.services.feature_mapping import FeatureMapping
from app.services.ml_model import SensitivityLevel


def test_detection_engine_blocklist():
    """Test that blocklisted IPs are detected."""
    engine = DetectionEngine(blocklist_ips={"192.168.1.100"})
    
    # Mock prediction
    prediction = {
        'is_benign': True,
        'risk_score': 10.0,
        'confidence': 0.9,
        'feature_contributions': {}
    }
    
    # Test blocklisted IP
    result = asyncio.run(engine.analyze_request(
        client_ip="192.168.1.100",
        request_time=time.time(),
        features={'ip_request_rate': 1.0},
        prediction=prediction
    ))
    
    assert not result.is_benign
    assert result.should_block
    assert result.detection_type == "BLOCKLISTED"


def test_detection_engine_normal_traffic():
    """Test that normal traffic is allowed."""
    engine = DetectionEngine()
    
    # Mock benign prediction
    prediction = {
        'is_benign': True,
        'risk_score': 10.0,
        'confidence': 0.9,
        'feature_contributions': {}
    }
    
    result = asyncio.run(engine.analyze_request(
        client_ip="192.168.1.1",
        request_time=time.time(),
        features={'ip_request_rate': 1.0},
        prediction=prediction
    ))
    
    assert result.is_benign
    assert not result.should_block
    assert result.detection_type == "NORMAL_TRAFFIC"


def test_detection_engine_high_risk():
    """Test that high-risk traffic is blocked."""
    engine = DetectionEngine()
    
    # Mock malicious prediction
    prediction = {
        'is_benign': False,
        'risk_score': 95.0,
        'confidence': 0.95,
        'feature_contributions': {}
    }
    
    result = asyncio.run(engine.analyze_request(
        client_ip="192.168.1.2",
        request_time=time.time(),
        features={'ip_request_rate': 10.0},
        prediction=prediction
    ))
    
    assert not result.is_benign
    assert result.should_block
    assert result.detection_type == "HIGH_RISK_ATTACK"


@pytest.mark.asyncio
async def test_mitigation_controller_rate_limiting():
    """Test rate limiting functionality."""
    controller = MitigationController(
        request_rate_limit=5,
        sliding_window_seconds=60
    )
    
    # First request should be allowed
    allowed = await controller.apply_rate_limit("192.168.1.3")
    assert allowed == True
    
    # Immediate second request should be blocked
    allowed = await controller.apply_rate_limit("192.168.1.3")
    assert allowed == False


def test_feature_mapping():
    """Test feature computation."""
    mapping = FeatureMapping()
    
    current_time = time.time()
    timestamps = [current_time - 5, current_time - 3, current_time - 1]
    bytes_data = [(current_time - 5, 100), (current_time - 3, 200), (current_time - 1, 150)]
    
    features = mapping.compute_features(
        window_size=10,
        request_timestamps=timestamps,
        request_bytes=bytes_data,
        current_time=current_time
    )
    
    assert 'Flow Duration' in features
    assert 'Total Fwd Packets' in features
    assert features['Total Fwd Packets'] == 3
    assert 'Flow Bytes/s' in features
    assert features['Flow Bytes/s'] == 45.0  # (100+200+150)/10


def test_sensitivity_levels():
    """Test that sensitivity level constants are defined."""
    assert hasattr(SensitivityLevel, 'LOW')
    assert hasattr(SensitivityLevel, 'MEDIUM')
    assert hasattr(SensitivityLevel, 'HIGH')
    assert SensitivityLevel.LOW == "low"
    assert SensitivityLevel.MEDIUM == "medium"
    assert SensitivityLevel.HIGH == "high"
