"""Debug tests for DDoS Protection Middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.middleware.ddos_protection import DDoSProtectionMiddleware
from app.services.mitigation import MitigationController
from app.services.detector import DetectionResult

@pytest.fixture
def mock_prediction_service():
    """Create mock prediction service."""
    service = AsyncMock()
    service.predict.return_value = {
        'is_benign': True,
        'risk_score': 20.0,
        'confidence': 0.85,
        'feature_contributions': {'Flow Duration': 0.2}
    }
    return service

@pytest.fixture
def mock_feature_mapping():
    """Create mock feature mapping."""
    mapping = Mock()
    mapping.compute_features.return_value = {
        'Flow Duration': 60.0,
        'Total Fwd Packets': 10,
        'Flow IAT Mean': 0.1
    }
    return mapping

@pytest.fixture
def mock_detection_engine():
    """Create mock detection engine."""
    engine = AsyncMock()
    engine.analyze_request.return_value = DetectionResult(
        is_benign=True,
        risk_score=20.0,
        confidence=0.85,
        detection_type="NORMAL_TRAFFIC",
        should_block=False,
        should_rate_limit=False,
        is_rate_limited=False,
        feature_contributions={'Flow Duration': 0.2}
    )
    return engine

@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock()
    settings.proxy_cidrs = ["10.0.0.0/8"]
    settings.honor_x_forwarded_for = True
    settings.block_duration_seconds = 300
    return settings

@pytest.fixture
def debug_app(mock_prediction_service, mock_feature_mapping, mock_detection_engine, mock_settings):
    """Create minimal FastAPI app with DDoS protection for debugging."""
    with patch('app.services.prediction_service.PredictionService') as mock_prediction_class, \
         patch('app.services.feature_mapping.FeatureMapping') as mock_feature_mapping_class, \
         patch('app.services.detector.DetectionEngine') as mock_detection_class, \
         patch('app.config.get_settings') as mock_get_settings:

        # Configure mocks
        mock_prediction_class.return_value = mock_prediction_service
        mock_feature_mapping_class.return_value = mock_feature_mapping
        mock_detection_class.return_value = mock_detection_engine
        mock_get_settings.return_value = mock_settings

        # Create app with test endpoints
        app = FastAPI()

        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}
            
        @app.get("/echo")
        async def echo(message: str):
            return {"echo": message}

        # Add middleware without accessing internals
        app.add_middleware(
            DDoSProtectionMiddleware,
            model_path="models",
            sensitivity_level="medium",
            window_size=60,
            cleanup_interval=300
        )

        return app

@pytest.mark.asyncio
async def test_smoke_health_check(debug_app):
    """Debug test: Verify health check endpoint works through middleware."""
    with TestClient(debug_app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_smoke_echo(debug_app):
    """Debug test: Verify echo endpoint works through middleware."""
    with TestClient(debug_app) as client:
        response = client.get("/echo?message=test")
        assert response.status_code == 200
        assert response.json() == {"echo": "test"}

@pytest.mark.asyncio
async def test_middleware_init(debug_app):
    """Debug test: Verify middleware initializes without errors."""
    with TestClient(debug_app) as client:
        # Just initialize client to trigger middleware setup
        pass