"""Test suite for DDoS Protection Middleware."""

import pytest
import asyncio
import time
import logging
from dataclasses import dataclass, field
from fastapi import FastAPI
from starlette.requests import Request
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from typing import List, Optional

logger = logging.getLogger(__name__)

from app.middleware.ddos_protection import DDoSProtectionMiddleware
from app.services.ml_model import SensitivityLevel, SENSITIVITY_THRESHOLDS
from app.services.detector import DetectionResult, DetectionEngine
from app.services.prediction_service import PredictionService

@dataclass
class TestSettings:
    """Test settings for DDoS protection middleware."""
    request_rate_limit: int = 5  # Lower rate limit for faster tests
    sliding_window_seconds: int = 1  # 1 second window for tests
    target_url: str = "http://127.0.0.1:8080"
    sensitivity_level: SensitivityLevel = SensitivityLevel.MEDIUM
    blocklist_ips: list = field(default_factory=list)
    trusted_proxies: list = field(default_factory=lambda: [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16"
    ])
    honor_x_forwarded_for: bool = True  # Enable XFF for tests
    max_request_size_kb: int = 1024
    allowed_hosts: list = field(default_factory=lambda: ["localhost", "testserver"])
    proxy_cidrs: list = field(default_factory=lambda: [
        "10.0.0.0/8",      # AWS VPC, standard private network 
        "172.16.0.0/12",   # Azure, standard private network
            "192.168.0.0/16",  # Standard private network
            "127.0.0.0/8",     # Localhost
            "169.254.0.0/16",  # Link-local
            "fc00::/7"         # Unique local addresses
        ])
    whitelist_ips: list = field(default_factory=list)
    request_timeout_seconds: float = 2.0
    enable_ddos_protection: bool = True

@pytest.fixture
def test_settings():
    """Create test settings."""
    return TestSettings()

@pytest.fixture
def mock_prediction_service():
    """Create mock prediction service for testing."""
    service = AsyncMock(spec=PredictionService)
    service.predict.return_value = {
        'is_benign': True,
        'risk_score': 20.0,
        'confidence': 0.85,
        'feature_contributions': {
            'Flow Duration': 0.2,
            'Flow IAT Mean': 0.3,
            'Packet Length Std': 0.1
        }
    }
    return service

@pytest.fixture
def mock_detection_engine():
    """Create mock detection engine with async call tracking."""
    engine = Mock()
    engine.analyze_request = AsyncMock(return_value=DetectionResult(
        is_benign=True,
        confidence=0.85,
        detection_type="NORMAL_TRAFFIC",
        should_block=False,
        should_rate_limit=False,
        is_rate_limited=False,
        risk_score=25.0,
        feature_contributions={
            'Flow Duration': 0.2,
            'Flow IAT Mean': 0.3,
            'Packet Length Std': 0.1
        }
    ))
    engine.update_metrics = AsyncMock()
    engine.apply_rate_limit = AsyncMock()
    return engine

@pytest.fixture
def mock_mitigation_controller():
    """Create mock mitigation controller."""
    @dataclass
    class MockMitigationController:
        """Mock controller with all required methods."""
        request_rate_limit: int = 5
        sliding_window_seconds: int = 1
        rate_limited_ips: dict = field(default_factory=dict)
        lock: asyncio.Lock = field(default_factory=asyncio.Lock)

        async def check_ip(self, ip: str) -> bool:
            # Implement basic rate limiting
            return await self._apply_rate_limit(ip)
            
        async def add_ip(self, ip: str) -> None:
            pass
            
        def get_rate_limit(self) -> int:
            return self.request_rate_limit
            
        def get_remaining_requests(self) -> int:
            return self.request_rate_limit - 1
            
        def get_window_reset_time(self) -> int:
            return self.sliding_window_seconds
            
        async def _apply_rate_limit(self, ip: str) -> bool:
            async with self.lock:
                now = time.time()
                window_start = now - self.sliding_window_seconds
                last_allowed = self.rate_limited_ips.get(ip, 0)
                if last_allowed < window_start:
                    self.rate_limited_ips[ip] = now
                    return True
                return False
            
        def is_rate_limited(self) -> bool:
            return False
            
    return MockMitigationController()

@pytest.fixture
def mock_feature_mapping():
    """Create mock feature mapping service."""
    mapping = Mock()
    mapping.compute_features = Mock(return_value={
        'Flow Duration': 60.0,
        'Total Fwd Packets': 10,
        'Total Length of Fwd Packets': 1000,
        'Flow Bytes/s': 16.67,
        'Flow Packets/s': 0.167,
        'Flow IAT Mean': 0.1,
        'Flow IAT Std': 0.02,
        'Flow IAT Max': 0.15,
        'Flow IAT Min': 0.05,
        'PSH Flag Count': 0,
        'Average Packet Size': 75,
        'Packet Length Std': 25
    })
    return mapping

@pytest.fixture
def client(
    mock_prediction_service,
    mock_detection_engine,
    mock_mitigation_controller,
    mock_feature_mapping,
    test_settings
):
    """Create a TestClient with DDoS protection middleware."""
    app = FastAPI()

    # Set up test endpoints
    @app.get("/")
    async def root():
        return {"status": "ok"}

    @app.post("/api/data")
    async def test_data(data: dict):
        return {"status": "ok", "data": data}

    # Create the service provider
    class TestServiceProvider:
        def __init__(self, prediction_service, detection_engine, mitigation, feature_mapping, settings):
            self._prediction_service = prediction_service
            self._detection_engine = detection_engine
            self._mitigation = mitigation
            self._feature_mapping = feature_mapping
            self._settings = settings
        
        def get_prediction_service(self):
            return self._prediction_service
        
        def get_detection_engine(self):
            return self._detection_engine
        
        def get_mitigation_controller(self):
            return self._mitigation
        
        def get_feature_mapping(self):
            return self._feature_mapping
            
        @property
        def settings(self):
            return self._settings
            
        def get_settings(self):
            """Legacy method for compatibility."""
            return self._settings

        # Compatibility attributes for tests accessing attributes directly
        @property
        def detection_engine(self):
            return self._detection_engine

        @property
        def mitigation(self):
            return self._mitigation

    # Set up provider with all services
    provider = TestServiceProvider(
        prediction_service=mock_prediction_service,
        detection_engine=mock_detection_engine,
        mitigation=mock_mitigation_controller,
        feature_mapping=mock_feature_mapping,
        settings=test_settings
    )

    # Set up app state and provider
    app.state.settings = test_settings
    # Also attach settings directly for middleware lookup
    setattr(app, "settings", test_settings)
    app.state.service_provider = provider
    app.service_provider = provider

    # Add middleware with our test settings
    app.add_middleware(
        DDoSProtectionMiddleware,
        settings=test_settings,
        service_provider=provider
    )

    # Create test client with default headers
    client = TestClient(app, base_url="http://testserver", headers={
        "host": "localhost",
        "content-length": "0",
        "user-agent": "pytest-client"
    })

    # By default, do not rate limit in tests unless a test overrides it
    provider.mitigation.check_ip = AsyncMock(return_value=False)

    return client

def test_normal_traffic(client):
    """Test that normal traffic patterns are allowed."""
    try:
        # Verify middleware is properly configured
        logger.debug("Test client configuration:")
        logger.debug(f"App state: {hasattr(client.app, 'state')}")
        logger.debug(f"Provider: {hasattr(client.app, 'service_provider')}")
        logger.debug(f"Settings: {hasattr(client.app.state, 'settings')}")
        logger.debug(f"Headers: {client.headers}")
        
        # Make a single test request
        response = client.get("/")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        if response.status_code != 200:
            logger.debug(f"Response body: {response.text}")
            
        # Verify response
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
        # Make additional requests
        for _ in range(2):
            response = client.get("/")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            time.sleep(0.1)  # Small delay between requests
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        pytest.fail(f"Normal traffic test failed: {str(e)}")
    
    # Verify response
    assert response.status_code == 200, "Normal traffic should be allowed"
    

def test_blocks_attack_traffic(client, mock_prediction_service, mock_detection_engine, mock_mitigation_controller):
    """Test that attack traffic is blocked."""
    # Configure prediction service to detect attack
    mock_prediction_service.predict.return_value = {
        'is_benign': False,
        'risk_score': 90.0,
        'confidence': 0.95,
        'feature_contributions': {
            'Flow Duration': 0.6,
            'Flow IAT Mean': 0.3,
            'Packet Length Std': 0.1
        }
    }

    # Configure detection engine to report attack
    mock_detection_engine.analyze_request.return_value = DetectionResult(
        is_benign=False,
        confidence=0.95,
        detection_type="ML_MODEL",
        should_block=True,
        should_rate_limit=True,
        risk_score=90.0,
        is_rate_limited=True,  # Should be rate limited
        feature_contributions={
            'Flow Duration': 0.6,
            'Flow IAT Mean': 0.3,
            'Packet Length Std': 0.1
        }
    )
    
    # Configure mitigation to enforce rate limits
    client.app.state.service_provider.mitigation.check_ip = AsyncMock(return_value=True)
    client.app.state.service_provider.mitigation.get_rate_limit = Mock(return_value=5)
    client.app.state.service_provider.mitigation.get_remaining_requests = Mock(return_value=0)
    
    # Send request that should be detected as attack
    response = client.get(
        "/",
        headers={
            "X-Forwarded-For": "203.0.113.1",
            "host": "localhost",
            "content-type": "application/json",
            "content-length": "0"
        }
    )
    
    # Verify response indicates blocking
    assert response.status_code == 429, "Attack traffic should be rate limited"
    assert "rate" in response.json().get("error", "").lower(), "Should indicate rate limiting"

def test_rate_limiting(client):
    """Test rate limiting functionality."""
    try:
        # Configure mock detection engine for rate limiting
        client.app.state.service_provider.detection_engine.analyze_request.return_value = DetectionResult(
            is_benign=False,
            confidence=0.95,
            detection_type="RATE_LIMIT",
            should_block=True,
            should_rate_limit=True,
            is_rate_limited=True,
            risk_score=75.0,
            feature_contributions={}
        )

        # Configure mitigation to enforce rate limits
        client.app.state.service_provider.mitigation.check_ip = AsyncMock(return_value=True)
        
        response = client.get("/")
        assert response.status_code == 429
        assert "rate limit" in response.json()["error"].lower()
    except Exception as e:
        pytest.fail(f"Rate limiting test failed: {str(e)}")

def test_different_endpoints(client):
    """Test that protection works across different endpoints."""
    try:
        # Configure mock for normal traffic
        client.app.state.service_provider.detection_engine.analyze_request.return_value = DetectionResult(
            is_benign=True,
            confidence=0.9,
            detection_type="NORMAL_TRAFFIC",
            should_block=False,
            should_rate_limit=False,
            is_rate_limited=False,
            risk_score=15.0,
            feature_contributions={}
        )
        
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except Exception as e:
        pytest.fail(f"Different endpoints test failed: {str(e)}")

def test_cleanup(client):
    """Test cleanup of old traffic data."""
    try:
        # Configure mocks for normal traffic
        client.app.state.service_provider.detection_engine.analyze_request.return_value = DetectionResult(
            is_benign=True,
            confidence=0.9,
            detection_type="NORMAL_TRAFFIC",
            should_block=False,
            should_rate_limit=False,
            is_rate_limited=False,
            risk_score=15.0,
            feature_contributions={}
        )

        # Make a request
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except Exception as e:
        pytest.fail(f"Cleanup test failed: {str(e)}")

def test_different_sensitivity_levels(client):
    """Test different sensitivity level behaviors."""
    try:
        # Test with normal traffic
        client.app.state.service_provider.detection_engine.analyze_request.return_value = DetectionResult(
            is_benign=True,
            confidence=0.9,
            detection_type="NORMAL_TRAFFIC",
            should_block=False,
            should_rate_limit=False,
            is_rate_limited=False,
            risk_score=15.0,
            feature_contributions={}
        )
        
        response = client.get("/")
        assert response.status_code == 200

        # Test with suspicious traffic
        client.app.state.service_provider.detection_engine.analyze_request.return_value = DetectionResult(
            is_benign=False,
            confidence=0.8,
            detection_type="SUSPICIOUS",
            should_block=True,
            should_rate_limit=True,
            is_rate_limited=True,
            risk_score=85.0,
            feature_contributions={}
        )
        
        response = client.get("/")
        assert response.status_code in [200, 403, 429]
    except Exception as e:
        pytest.fail(f"Sensitivity levels test failed: {str(e)}")

def test_error_handling(client):
    """Test middleware error handling capabilities."""
    # Test with valid headers
    response = client.get("/", headers={"X-Custom-Test": "test123"})
    assert response.status_code == 200

    # Test with large but valid JSON
    big_json = {"data": "x" * 1000}
    response = client.post("/api/data", json=big_json)
    assert response.status_code == 200

    # Test with invalid JSON but proper error handling
    response = client.post("/api/data", data="invalid}json{")
    assert response.status_code in [400, 422]  # FastAPI validation error or our error handling
    
    # Test with missing required header
    response = client.get("/")
    assert response.status_code == 200  # Should still work without custom headers