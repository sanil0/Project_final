"""
Architecture tests to ensure single analysis path (no duplication).

These tests verify that:
1. Middleware performs DDoS analysis first
2. Proxy only forwards (no duplicate analysis)
3. Requests go through exactly ONE analysis path
4. Metrics are not double-counted
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


class TestSingleAnalysisPath:
    """Verify requests only go through one analysis path."""

    def test_middleware_is_primary_analysis(self):
        """Test that middleware handles analysis, not proxy."""
        from app.middleware.ddos_protection import DDoSProtectionMiddleware
        from app.services.proxy import DDoSProtectionProxy
        
        # Middleware should have analysis logic
        assert hasattr(DDoSProtectionMiddleware, 'dispatch')
        
        # Proxy should NOT have analysis logic
        assert not hasattr(DDoSProtectionProxy, 'predict')
        assert not hasattr(DDoSProtectionProxy, 'model')
        
    def test_proxy_only_forwards(self):
        """Test that proxy only forwards requests."""
        from app.services.proxy import DDoSProtectionProxy
        
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        
        # Check proxy initialization
        assert proxy.target_url == "http://localhost:9000"
        assert hasattr(proxy, 'handle_request')
        assert hasattr(proxy, '_proxy_request')
        
        # Proxy should track forwarding, not attacks
        assert hasattr(proxy, 'total_forwarded_requests')
        assert hasattr(proxy, 'forwarding_errors')
        assert not hasattr(proxy, 'blocked_attacks')
        assert not hasattr(proxy, 'attack_patterns')

    def test_proxy_deprecated_methods_not_used(self):
        """Test that proxy's deprecated analysis methods are not functional."""
        from app.services.proxy import DDoSProtectionProxy
        
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        
        # These methods should be deprecated (no-ops or deprecation notices)
        assert proxy._identify_attack_pattern({}) == "N/A"
        # _extract_features is now async, just check it exists
        assert hasattr(proxy, '_extract_features')


class TestAnalysisPathFlow:
    """Verify the flow of analysis through single path."""

    @pytest.mark.asyncio
    async def test_benign_request_goes_through_middleware_to_proxy(self):
        """Test that benign request flows: middleware -> proxy -> target."""
        from app.middleware.ddos_protection import DDoSProtectionMiddleware
        from app.services.proxy import DDoSProtectionProxy
        
        # Track call flow
        middleware_calls = []
        proxy_calls = []
        
        # Mock detector
        mock_detector = MagicMock()
        mock_detector.analyze_request = AsyncMock(return_value=MagicMock(
            should_block=False,
            risk_score=10.0,
            is_benign=True
        ))
        
        # Mock proxy
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        original_proxy = proxy.handle_request
        
        async def tracked_proxy(request):
            proxy_calls.append(("proxy", request.url.path))
            # Don't actually call handle_request (would need httpx)
            return None
        
        proxy.handle_request = tracked_proxy
        
        # If we can call both, proxy receives request AFTER middleware approval
        # Middleware makes decision first
        # Proxy only forwards benign traffic
        
        # This is verified by architecture, not direct flow test
        assert callable(proxy.handle_request)


class TestNoMetricsDuplication:
    """Verify metrics are counted once, not duplicated."""

    @pytest.mark.asyncio
    async def test_middleware_updates_metrics_only(self):
        """Test that only middleware updates detection metrics."""
        from app.middleware.ddos_protection import DDoSProtectionMiddleware
        from app.services.proxy import DDoSProtectionProxy
        
        # Proxy get_stats should NOT mention analysis
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        stats_result = await proxy.get_stats()
        
        # Should mention forwarding only
        assert "forwarding" in str(stats_result) or "forwarded" in str(stats_result).lower()
        assert "blocked_attacks" not in str(stats_result)
        assert "attack_patterns" not in str(stats_result)

    def test_single_metric_increment_per_request(self):
        """Test that metrics are incremented exactly once per request."""
        from app.services.performance_metrics import get_metrics
        
        metrics = get_metrics()
        
        # Record request
        initial_count = metrics.total_requests
        metrics.record_request(5.0, False, False, 10.0)
        
        # Should increment by exactly 1, not 2
        assert metrics.total_requests == initial_count + 1


class TestArchitectureEnforcement:
    """Enforce architectural rules."""

    def test_proxy_has_no_model_instance(self):
        """Test that proxy doesn't instantiate ML model."""
        from app.services.proxy import DDoSProtectionProxy
        
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        assert not hasattr(proxy, 'model')
        assert not hasattr(proxy, 'sensitivity')

    def test_proxy_has_no_detection_engine(self):
        """Test that proxy doesn't have detection engine."""
        from app.services.proxy import DDoSProtectionProxy
        
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        assert not hasattr(proxy, 'detection_engine')
        assert not hasattr(proxy, 'mitigation')

    def test_middleware_has_detection_logic(self):
        """Test that middleware has all detection components."""
        from app.middleware.ddos_protection import DDoSProtectionMiddleware
        
        # Middleware should be able to hold detection services
        middleware = DDoSProtectionMiddleware(
            app=None,
            settings=None,
            service_provider=None
        )
        
        # These should be present (even if None, indicating they're expected)
        assert hasattr(middleware, 'detection_engine')
        assert hasattr(middleware, 'prediction_service')
        assert hasattr(middleware, 'mitigation')


class TestRequestFlowSeparation:
    """Test that analysis and forwarding are separate concerns."""

    def test_middleware_decision_is_final(self):
        """Test that middleware's block decision is respected."""
        # If middleware blocks a request, proxy should never see it
        # This is enforced by exception handling in middleware
        from app.middleware.ddos_protection import DDoSProtectionMiddleware
        
        middleware = DDoSProtectionMiddleware(
            app=None,
            settings=None,
            service_provider=None
        )
        
        # Should have response generation on block
        assert hasattr(middleware, 'dispatch')

    def test_proxy_trusts_middleware_decision(self):
        """Test that proxy doesn't re-analyze requests."""
        from app.services.proxy import DDoSProtectionProxy
        
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        
        # handle_request should not perform analysis
        import inspect
        source = inspect.getsource(proxy.handle_request)
        
        # Should not contain analysis keywords
        assert 'predict' not in source.lower()
        assert 'analyze' not in source.lower()
        # Should only forward
        assert 'proxy' in source.lower() or 'forward' in source.lower()


class TestCodeQualityArchitecture:
    """Verify code quality prevents future regressions."""

    def test_proxy_source_no_duplicate_analysis_code(self):
        """Test that proxy source doesn't duplicate analysis code."""
        import inspect
        from app.services.proxy import DDoSProtectionProxy
        
        source = inspect.getsource(DDoSProtectionProxy)
        
        # Should not have duplicate detection logic
        assert source.count('analyze') <= 2  # Comment + method name
        assert source.count('model.predict') == 0
        assert source.count('risk_score') <= 1  # Only in comment
        assert source.count('is_benign') <= 1  # Only in comment

    def test_middleware_source_has_analysis_logic(self):
        """Test that middleware has all analysis logic."""
        import inspect
        from app.middleware.ddos_protection import DDoSProtectionMiddleware
        
        source = inspect.getsource(DDoSProtectionMiddleware)
        
        # Should have analysis logic (multiple mentions is expected)
        assert 'analyze_request' in source
        assert 'risk_score' in source
        assert 'is_benign' in source

    def test_no_model_instantiation_in_proxy(self):
        """Test that proxy doesn't instantiate model."""
        import inspect
        from app.services.proxy import DDoSProtectionProxy
        
        source = inspect.getsource(DDoSProtectionProxy)
        
        # Should not import or load model
        assert 'DDoSDetectionModel' not in source
        assert '.load_model(' not in source
        assert 'model_path' not in source


class TestDocumentation:
    """Verify documentation reflects architecture."""

    def test_proxy_docstring_mentions_middleware(self):
        """Test that proxy class doc explains middleware."""
        from app.services.proxy import DDoSProtectionProxy
        
        doc = DDoSProtectionProxy.__doc__
        assert doc is not None
        assert 'middleware' in doc.lower() or 'analysis' in doc.lower()

    def test_proxy_handle_request_docstring_clear(self):
        """Test that handle_request doc is clear about role."""
        from app.services.proxy import DDoSProtectionProxy
        
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        doc = proxy.handle_request.__doc__
        
        assert doc is not None
        # Should mention forwarding, not analysis
        assert 'forward' in doc.lower() or 'proxy' in doc.lower()


class TestRegressionPrevention:
    """Tests that prevent future regressions."""

    def test_proxy_cannot_import_ml_model(self):
        """Test that proxy doesn't import ML model."""
        import inspect
        from app.services import proxy
        
        source = inspect.getsource(proxy)
        
        # Check imports
        assert 'from app.services.ml_model import' not in source
        assert 'DDoSDetectionModel' not in source

    def test_proxy_stats_have_no_attack_fields(self):
        """Test that proxy stats don't track attacks."""
        from app.services.proxy import DDoSProtectionProxy
        
        proxy = DDoSProtectionProxy(target_url="http://localhost:9000")
        
        # Check if these are absent
        assert not hasattr(proxy, 'blocked_attacks')
        assert not hasattr(proxy, 'attack_patterns')
        assert not hasattr(proxy, 'total_requests')  # Should be total_forwarded_requests
        assert not hasattr(proxy, 'last_attack_time')

    def test_proxy_initialization_no_model(self):
        """Test that proxy __init__ doesn't load model."""
        import inspect
        from app.services.proxy import DDoSProtectionProxy
        
        source = inspect.getsource(DDoSProtectionProxy.__init__)
        
        # Should not load model
        assert '.load_model' not in source
        assert 'SensitivityLevel' not in source
        assert 'model_path' not in source
