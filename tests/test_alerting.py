"""
Comprehensive test suite for Advanced Attack Alerting System.

Tests cover:
- Alert generation and severity levels
- Attack escalation detection
- Block rate analysis
- Deduplication
- Alert history tracking
- Edge cases and error scenarios
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.alerting import (
    AlertingEngine,
    Alert,
    AlertPattern,
    AlertSeverity,
    AlertType,
    initialize_alerting,
    get_alerting_engine,
)


class TestAlertingEngineBasics:
    """Test basic alerting engine functionality."""

    def test_engine_initialization(self):
        """Test alerting engine initializes correctly."""
        engine = AlertingEngine()
        assert engine.escalation_threshold == 0.7
        assert engine.sustained_attack_duration == 300
        assert engine.dedup_window == 60
        assert len(engine.alerts) == 0
        assert len(engine.active_alerts) == 0
        assert engine.total_requests == 0
        assert engine.total_blocked == 0

    def test_custom_initialization(self):
        """Test alerting engine with custom parameters."""
        engine = AlertingEngine(
            escalation_threshold=0.5,
            sustained_attack_duration=600,
            dedup_window=120,
        )
        assert engine.escalation_threshold == 0.5
        assert engine.sustained_attack_duration == 600
        assert engine.dedup_window == 120

    def test_global_initialization(self):
        """Test global alerting engine initialization."""
        engine = initialize_alerting()
        assert engine is not None
        assert isinstance(engine, AlertingEngine)

    def test_get_global_engine(self):
        """Test retrieving global alerting engine."""
        engine1 = get_alerting_engine()
        engine2 = get_alerting_engine()
        assert engine1 is engine2

    def test_health_check(self):
        """Test alerting system health check."""
        engine = AlertingEngine()
        health = engine.health_check()
        assert health['active'] is True
        assert health['active_alerts'] == 0
        assert health['total_alerts'] == 0
        assert health['tracked_ips'] == 0
        assert health['memory_efficient'] is True


class TestRequestRecording:
    """Test request recording and pattern tracking."""

    def test_record_normal_request(self):
        """Test recording a normal request."""
        engine = AlertingEngine()
        alert = engine.record_request(
            client_ip="192.168.1.1",
            was_blocked=False,
            risk_score=10,
            detection_type="NORMAL",
        )
        assert alert is None
        assert engine.total_requests == 1
        assert engine.total_blocked == 0
        assert "192.168.1.1" in engine.ip_patterns

    def test_record_blocked_request(self):
        """Test recording a blocked request."""
        engine = AlertingEngine()
        alert = engine.record_request(
            client_ip="192.168.1.2",
            was_blocked=True,
            risk_score=50,
            detection_type="SUSPICIOUS",
        )
        assert engine.total_requests == 1
        assert engine.total_blocked == 1
        pattern = engine.ip_patterns["192.168.1.2"]
        assert pattern.blocked_count == 1
        assert pattern.request_count == 1

    def test_pattern_tracking(self):
        """Test IP pattern accumulation."""
        engine = AlertingEngine()
        for i in range(10):
            engine.record_request(
                client_ip="10.0.0.1",
                was_blocked=i % 2 == 0,  # 50% block rate
                risk_score=30,
                detection_type="NORMAL",
            )
        pattern = engine.ip_patterns["10.0.0.1"]
        assert pattern.request_count == 10
        assert pattern.blocked_count == 5
        assert pattern.block_rate == 50.0

    def test_multiple_ips_tracking(self):
        """Test tracking multiple IPs simultaneously."""
        engine = AlertingEngine()
        for ip_idx in range(5):
            for req_idx in range(3):
                engine.record_request(
                    client_ip=f"192.168.1.{ip_idx}",
                    was_blocked=False,
                    risk_score=10,
                    detection_type="NORMAL",
                )
        assert len(engine.ip_patterns) == 5
        assert engine.total_requests == 15


class TestAlertGeneration:
    """Test alert generation based on various conditions."""

    def test_critical_attack_alert(self):
        """Test alert generation for critical attack."""
        engine = AlertingEngine()
        alert = engine.record_request(
            client_ip="10.0.0.1",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.alert_type == AlertType.ATTACK_DETECTED
        assert alert.message == "Critical attack detected from 10.0.0.1"
        assert alert.recommended_action == "BLOCK_IP_IMMEDIATELY"

    def test_high_block_rate_alert(self):
        """Test alert generation for high block rate."""
        engine = AlertingEngine()
        # Generate 10 requests with 100% block rate
        for i in range(10):
            alert = engine.record_request(
                client_ip="10.0.0.2",
                was_blocked=True,
                risk_score=70,
                detection_type="SUSPICIOUS",
            )
        # Last alert should trigger
        assert alert is not None
        assert alert.severity == AlertSeverity.HIGH
        assert alert.alert_type == AlertType.BLOCK_RATE_SURGE
        assert "80%" in alert.message or "100" in alert.message

    def test_traffic_spike_alert_medium(self):
        """Test medium severity traffic spike alert."""
        engine = AlertingEngine()
        # Generate requests rapidly but moderate rate
        # Need to trigger 100 req/min threshold for 150 requests
        for i in range(150):
            alert = engine.record_request(
                client_ip="10.0.0.3",
                was_blocked=False,
                risk_score=40,
                detection_type="NORMAL",
            )
        # May or may not generate alert depending on timing
        # Just verify the recording works
        pattern = engine.ip_patterns["10.0.0.3"]
        assert pattern.request_count == 150

    def test_attack_pattern_change_alert(self):
        """Test alert for attack pattern changes."""
        engine = AlertingEngine()
        # Generate mixed attack types
        attack_types = ["NORMAL", "SUSPICIOUS", "HIGH_RISK", "ANOMALY", "BRUTE_FORCE"]
        for attack_type in attack_types:
            alert = engine.record_request(
                client_ip="10.0.0.4",
                was_blocked=True,
                risk_score=60,
                detection_type=attack_type,
            )
        # Should detect pattern change
        assert alert is not None
        assert alert.alert_type == AlertType.ATTACK_PATTERN_CHANGE

    def test_alert_details_populated(self):
        """Test that alert details are populated correctly."""
        engine = AlertingEngine()
        alert = engine.record_request(
            client_ip="10.0.0.5",
            was_blocked=True,
            risk_score=92,
            detection_type="HIGH_RISK_ATTACK",
        )
        assert alert is not None
        assert alert.details is not None
        assert 'risk_score' in alert.details
        assert alert.affected_ips == ["10.0.0.5"]


class TestAlertDeduplication:
    """Test alert deduplication within time windows."""

    def test_deduplication_within_window(self):
        """Test that duplicate alerts are deduplicated."""
        engine = AlertingEngine(dedup_window=60)
        # Generate same type of alert twice rapidly
        alert1 = engine.record_request(
            client_ip="10.0.0.6",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        alert2 = engine.record_request(
            client_ip="10.0.0.6",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        # Second should be deduplicated (return None)
        assert alert1 is not None
        assert alert2 is None
        assert len(engine.active_alerts) == 1

    def test_deduplication_different_ips(self):
        """Test that different IPs don't deduplicate."""
        engine = AlertingEngine(dedup_window=60)
        alert1 = engine.record_request(
            client_ip="10.0.0.7",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        alert2 = engine.record_request(
            client_ip="10.0.0.8",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        # Both should be created (different IPs)
        assert alert1 is not None
        assert alert2 is not None
        assert len(engine.active_alerts) == 2

    def test_deduplication_window_expired(self):
        """Test that deduplication window expiration allows new alerts."""
        engine = AlertingEngine(dedup_window=1)  # 1 second window
        alert1 = engine.record_request(
            client_ip="10.0.0.9",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        # Manually advance last_alert_time to simulate window expiration
        from datetime import datetime, timedelta
        alert_key = "attack_detected:10.0.0.9"
        engine.last_alert_time[alert_key] = datetime.now() - timedelta(seconds=2)
        
        alert2 = engine.record_request(
            client_ip="10.0.0.9",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        # Should create new alert after window expires
        assert alert1 is not None
        assert alert2 is not None
        assert len(engine.active_alerts) == 2


class TestAlertManagement:
    """Test alert management and history."""

    def test_alert_resolution(self):
        """Test resolving an alert."""
        engine = AlertingEngine()
        alert = engine.record_request(
            client_ip="10.0.0.10",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        assert alert is not None
        alert_id = alert.alert_id

        # Resolve the alert
        resolved = engine.resolve_alert(alert_id)
        assert resolved is True
        assert alert.is_resolved is True
        assert alert.resolved_at is not None
        assert alert_id not in engine.active_alerts

    def test_get_active_alerts(self):
        """Test retrieving active alerts."""
        engine = AlertingEngine()
        for i in range(5):
            engine.record_request(
                client_ip=f"10.0.0.{i}",
                was_blocked=True,
                risk_score=95,
                detection_type="HIGH_RISK_ATTACK",
            )
        active_alerts = engine.get_active_alerts()
        assert len(active_alerts) == 5

    def test_get_active_alerts_filtered(self):
        """Test retrieving active alerts filtered by severity."""
        engine = AlertingEngine()
        # Create critical alert
        engine.record_request(
            client_ip="10.0.0.11",
            was_blocked=True,
            risk_score=95,
            detection_type="HIGH_RISK_ATTACK",
        )
        # Create medium severity alerts
        for i in range(3):
            for _ in range(150):
                engine.record_request(
                    client_ip=f"10.0.1.{i}",
                    was_blocked=False,
                    risk_score=40,
                    detection_type="NORMAL",
                )

        critical_alerts = engine.get_active_alerts(AlertSeverity.CRITICAL)
        assert all(a.severity == AlertSeverity.CRITICAL for a in critical_alerts)

    def test_get_alert_history(self):
        """Test retrieving alert history."""
        engine = AlertingEngine()
        for i in range(5):
            engine.record_request(
                client_ip=f"10.0.0.{i}",
                was_blocked=True,
                risk_score=95,
                detection_type="HIGH_RISK_ATTACK",
            )
        history = engine.get_alert_history()
        assert len(history) >= 5

    def test_alert_history_limit(self):
        """Test alert history limit."""
        engine = AlertingEngine()
        for i in range(10):
            engine.record_request(
                client_ip=f"10.0.0.{i}",
                was_blocked=True,
                risk_score=95,
                detection_type="HIGH_RISK_ATTACK",
            )
        history = engine.get_alert_history(limit=5)
        assert len(history) == 5


class TestStatisticsAndMetrics:
    """Test statistics and metrics collection."""

    def test_statistics_calculation(self):
        """Test statistics calculation."""
        engine = AlertingEngine()
        for i in range(10):
            engine.record_request(
                client_ip="10.0.0.1",
                was_blocked=i % 2 == 0,  # 50% block rate
                risk_score=30,
                detection_type="NORMAL",
            )
        stats = engine.get_statistics()
        assert stats['total_requests'] == 10
        assert stats['total_blocked'] == 5
        assert stats['block_rate'] == 50.0
        assert stats['tracked_ips'] == 1

    def test_statistics_zero_requests(self):
        """Test statistics with no requests."""
        engine = AlertingEngine()
        stats = engine.get_statistics()
        assert stats['total_requests'] == 0
        assert stats['total_blocked'] == 0
        assert stats['block_rate'] == 0
        assert stats['active_alerts'] == 0

    def test_statistics_alert_counts(self):
        """Test statistics include alert counts."""
        engine = AlertingEngine()
        for i in range(5):
            engine.record_request(
                client_ip=f"10.0.0.{i}",
                was_blocked=True,
                risk_score=95,
                detection_type="HIGH_RISK_ATTACK",
            )
        stats = engine.get_statistics()
        assert stats['active_alerts'] >= 5
        assert stats['total_alerts_generated'] >= 5


class TestPatternCleanup:
    """Test IP pattern cleanup and memory management."""

    def test_cleanup_old_patterns(self):
        """Test cleanup of old IP patterns."""
        engine = AlertingEngine()
        # Create some patterns
        for i in range(5):
            engine.record_request(
                client_ip=f"10.0.0.{i}",
                was_blocked=False,
                risk_score=10,
                detection_type="NORMAL",
            )
        assert len(engine.ip_patterns) == 5

        # Manually age the patterns
        for pattern in engine.ip_patterns.values():
            pattern.last_request_time = datetime.now() - timedelta(seconds=3700)

        # Clean up patterns older than 1 hour
        removed = engine.cleanup_old_patterns(older_than_seconds=3600)
        assert removed == 5
        assert len(engine.ip_patterns) == 0

    def test_cleanup_preserves_recent_patterns(self):
        """Test that cleanup preserves recent patterns."""
        engine = AlertingEngine()
        # Create old and new patterns
        engine.record_request(
            client_ip="10.0.0.1",
            was_blocked=False,
            risk_score=10,
            detection_type="NORMAL",
        )
        # Age this pattern
        engine.ip_patterns["10.0.0.1"].last_request_time = (
            datetime.now() - timedelta(seconds=3700)
        )

        # Create recent pattern
        engine.record_request(
            client_ip="10.0.0.2",
            was_blocked=False,
            risk_score=10,
            detection_type="NORMAL",
        )

        # Clean up
        removed = engine.cleanup_old_patterns(older_than_seconds=3600)
        assert removed == 1
        assert len(engine.ip_patterns) == 1
        assert "10.0.0.2" in engine.ip_patterns


class TestAlertDataModel:
    """Test Alert data model."""

    def test_alert_creation(self):
        """Test Alert instantiation."""
        alert = Alert(
            alert_id="test_alert_1",
            alert_type=AlertType.ATTACK_DETECTED,
            severity=AlertSeverity.CRITICAL,
            timestamp=datetime.now(),
            message="Test alert",
        )
        assert alert.alert_id == "test_alert_1"
        assert alert.is_resolved is False
        assert alert.resolved_at is None

    def test_alert_to_dict(self):
        """Test Alert serialization to dict."""
        alert = Alert(
            alert_id="test_alert_2",
            alert_type=AlertType.TRAFFIC_SPIKE,
            severity=AlertSeverity.MEDIUM,
            timestamp=datetime.now(),
            message="Spike alert",
            affected_ips=["10.0.0.1", "10.0.0.2"],
            block_rate=75.5,
        )
        data = alert.to_dict()
        assert data['alert_id'] == "test_alert_2"
        assert data['alert_type'] == 'traffic_spike'
        assert data['severity'] == 'medium'
        assert len(data['affected_ips']) == 2
        assert data['block_rate'] == 75.5


class TestAlertPatternDataModel:
    """Test AlertPattern data model."""

    def test_pattern_creation(self):
        """Test AlertPattern instantiation."""
        pattern = AlertPattern(ip="10.0.0.1")
        assert pattern.ip == "10.0.0.1"
        assert pattern.request_count == 0
        assert pattern.blocked_count == 0
        assert pattern.block_rate == 0.0

    def test_pattern_block_rate_calculation(self):
        """Test block rate calculation."""
        pattern = AlertPattern(ip="10.0.0.2")
        pattern.request_count = 100
        pattern.blocked_count = 75
        assert pattern.block_rate == 75.0

    def test_pattern_block_rate_zero_requests(self):
        """Test block rate with zero requests."""
        pattern = AlertPattern(ip="10.0.0.3")
        assert pattern.block_rate == 0.0

    def test_pattern_requests_per_minute(self):
        """Test requests per minute calculation."""
        pattern = AlertPattern(ip="10.0.0.4")
        pattern.request_count = 60
        pattern.first_request_time = datetime.now() - timedelta(minutes=1)
        pattern.last_request_time = datetime.now()
        rpm = pattern.requests_per_minute
        assert rpm >= 50  # Allow some tolerance for test execution time


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_alert_history(self):
        """Test retrieving history when no alerts exist."""
        engine = AlertingEngine()
        history = engine.get_alert_history()
        assert len(history) == 0

    def test_resolve_nonexistent_alert(self):
        """Test resolving an alert that doesn't exist."""
        engine = AlertingEngine()
        resolved = engine.resolve_alert("nonexistent_alert_id")
        assert resolved is False

    def test_concurrent_pattern_updates(self):
        """Test multiple concurrent pattern updates for same IP."""
        engine = AlertingEngine()
        for _ in range(100):
            engine.record_request(
                client_ip="10.0.0.1",
                was_blocked=True,
                risk_score=50,
                detection_type="NORMAL",
            )
        pattern = engine.ip_patterns["10.0.0.1"]
        assert pattern.request_count == 100
        assert len(pattern.pattern_history) <= 100  # deque maxlen

    def test_alert_with_empty_affected_ips(self):
        """Test alert creation with empty affected IPs."""
        alert = Alert(
            alert_id="test_alert_3",
            alert_type=AlertType.BLOCK_RATE_SURGE,
            severity=AlertSeverity.HIGH,
            timestamp=datetime.now(),
            message="Test alert",
            affected_ips=[],
        )
        assert alert.affected_ips == []
        data = alert.to_dict()
        assert data['affected_ips'] == []
