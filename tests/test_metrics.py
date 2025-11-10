"""
Comprehensive test suite for Performance Metrics System.

Tests cover:
- Latency tracking and statistics
- Cache effectiveness measurement
- Detection accuracy calculation
- Attack trend analysis
- Performance summary generation
"""

import pytest
from datetime import datetime, timedelta
import statistics

from app.services.performance_metrics import (
    PerformanceMetrics,
    LatencyMetrics,
    CacheEffectiveness,
    DetectionAccuracy,
    AttackTrend,
    initialize_metrics,
    get_metrics,
)


class TestLatencyMetrics:
    """Test latency tracking and statistics."""

    def test_latency_initialization(self):
        """Test latency metrics initialization."""
        metrics = LatencyMetrics()
        assert len(metrics.detection_latency_ms) == 0
        assert len(metrics.cache_hit_latency_ms) == 0
        assert len(metrics.cache_miss_latency_ms) == 0
        assert len(metrics.mitigation_latency_ms) == 0

    def test_record_detection_latency(self):
        """Test recording detection latency."""
        metrics = LatencyMetrics()
        metrics.record_detection_latency(5.0)
        metrics.record_detection_latency(10.0)
        metrics.record_detection_latency(7.5)
        assert len(metrics.detection_latency_ms) == 3

    def test_latency_stats_calculation(self):
        """Test latency statistics calculation."""
        metrics = LatencyMetrics()
        latencies = [1.0, 2.0, 3.0, 4.0, 5.0]
        for lat in latencies:
            metrics.record_detection_latency(lat)

        stats = metrics.get_stats(metrics.detection_latency_ms)
        assert stats['min'] == 1.0
        assert stats['max'] == 5.0
        assert stats['mean'] == 3.0
        assert stats['median'] == 3.0
        assert stats['count'] == 5

    def test_latency_percentiles(self):
        """Test percentile calculations."""
        metrics = LatencyMetrics()
        for i in range(1, 101):
            metrics.record_detection_latency(float(i))

        stats = metrics.get_stats(metrics.detection_latency_ms)
        assert stats['p95'] > 90
        assert stats['p99'] > 98

    def test_latency_summary(self):
        """Test comprehensive latency summary."""
        metrics = LatencyMetrics()
        metrics.record_detection_latency(5.0)
        metrics.record_cache_hit_latency(2.0)
        metrics.record_cache_miss_latency(8.0)
        metrics.record_mitigation_latency(10.0)

        summary = metrics.get_latency_summary()
        assert 'detection' in summary
        assert 'cache_hit' in summary
        assert 'cache_miss' in summary
        assert 'mitigation' in summary


class TestCacheEffectiveness:
    """Test cache effectiveness tracking."""

    def test_cache_effectiveness_initialization(self):
        """Test cache effectiveness initialization."""
        cache = CacheEffectiveness()
        assert cache.hits == 0
        assert cache.misses == 0
        assert cache.total_requests == 0
        assert cache.hit_rate == 0.0

    def test_record_cache_hit(self):
        """Test recording cache hit."""
        cache = CacheEffectiveness()
        cache.record_hit(latency_saved_ms=5.0)
        assert cache.hits == 1
        assert cache.total_requests == 1
        assert cache.time_saved_ms == 5.0

    def test_record_cache_miss(self):
        """Test recording cache miss."""
        cache = CacheEffectiveness()
        cache.record_miss()
        assert cache.misses == 1
        assert cache.total_requests == 1

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        cache = CacheEffectiveness()
        for _ in range(100):
            cache.record_hit()
        for _ in range(100):
            cache.record_miss()

        assert cache.hit_rate == 50.0

    def test_cache_effectiveness_to_dict(self):
        """Test cache effectiveness serialization."""
        cache = CacheEffectiveness()
        for _ in range(80):
            cache.record_hit(latency_saved_ms=2.0)
        for _ in range(20):
            cache.record_miss()

        data = cache.to_dict()
        assert data['hits'] == 80
        assert data['misses'] == 20
        assert data['total_requests'] == 100
        assert data['hit_rate'] == 80.0


class TestDetectionAccuracy:
    """Test detection accuracy metrics."""

    def test_detection_accuracy_initialization(self):
        """Test detection accuracy initialization."""
        accuracy = DetectionAccuracy()
        assert accuracy.true_positives == 0
        assert accuracy.true_negatives == 0
        assert accuracy.false_positives == 0
        assert accuracy.false_negatives == 0
        assert accuracy.total_predictions == 0

    def test_accuracy_calculation(self):
        """Test overall accuracy calculation."""
        accuracy = DetectionAccuracy()
        accuracy.true_positives = 80
        accuracy.true_negatives = 80
        accuracy.false_positives = 10
        accuracy.false_negatives = 10

        assert accuracy.total_predictions == 180
        assert accuracy.accuracy == pytest.approx(88.89, rel=0.1)

    def test_precision_calculation(self):
        """Test precision calculation."""
        accuracy = DetectionAccuracy()
        accuracy.true_positives = 80
        accuracy.false_positives = 20

        assert accuracy.precision == pytest.approx(80.0, rel=0.1)

    def test_recall_calculation(self):
        """Test recall (sensitivity) calculation."""
        accuracy = DetectionAccuracy()
        accuracy.true_positives = 80
        accuracy.false_negatives = 20

        assert accuracy.recall == pytest.approx(80.0, rel=0.1)

    def test_f1_score_calculation(self):
        """Test F1 score calculation."""
        accuracy = DetectionAccuracy()
        accuracy.true_positives = 100
        accuracy.false_positives = 0
        accuracy.false_negatives = 0

        assert accuracy.f1_score == 100.0

    def test_accuracy_to_dict(self):
        """Test accuracy serialization."""
        accuracy = DetectionAccuracy()
        accuracy.true_positives = 80
        accuracy.true_negatives = 80
        accuracy.false_positives = 10
        accuracy.false_negatives = 10
        accuracy.blocked_requests = 90
        accuracy.allowed_requests = 90

        data = accuracy.to_dict()
        assert data['true_positives'] == 80
        assert data['true_negatives'] == 80
        assert data['accuracy'] == pytest.approx(88.89, rel=0.1)
        assert data['blocked_requests'] == 90


class TestPerformanceMetrics:
    """Test comprehensive performance metrics."""

    def test_performance_metrics_initialization(self):
        """Test performance metrics initialization."""
        metrics = PerformanceMetrics()
        assert metrics.total_requests == 0
        assert metrics.total_attacks == 0
        assert metrics.total_blocked == 0
        assert metrics.total_mitigations == 0

    def test_record_request(self):
        """Test recording requests."""
        metrics = PerformanceMetrics()
        metrics.record_request(
            detection_latency_ms=5.0,
            was_attack=False,
            was_blocked=False,
            risk_score=10.0,
        )
        assert metrics.total_requests == 1
        assert metrics.total_attacks == 0

    def test_record_attack_request(self):
        """Test recording attack requests."""
        metrics = PerformanceMetrics()
        metrics.record_request(
            detection_latency_ms=5.0,
            was_attack=True,
            was_blocked=True,
            risk_score=90.0,
        )
        assert metrics.total_requests == 1
        assert metrics.total_attacks == 1
        assert metrics.total_blocked == 1

    def test_attack_rate_calculation(self):
        """Test attack rate calculation."""
        metrics = PerformanceMetrics()
        for _ in range(80):
            metrics.record_request(5.0, False, False, 10.0)
        for _ in range(20):
            metrics.record_request(5.0, True, True, 90.0)

        assert metrics.get_attack_rate() == 20.0

    def test_block_rate_calculation(self):
        """Test block rate calculation."""
        metrics = PerformanceMetrics()
        for _ in range(50):
            metrics.record_request(5.0, False, False, 10.0)
        for _ in range(30):
            metrics.record_request(5.0, True, True, 90.0)
        for _ in range(20):
            metrics.record_request(5.0, True, False, 85.0)

        assert metrics.get_block_rate() == 30.0

    def test_mitigation_effectiveness(self):
        """Test mitigation effectiveness calculation."""
        metrics = PerformanceMetrics()
        for _ in range(80):
            metrics.record_request(5.0, True, True, 90.0)
        for _ in range(20):
            metrics.record_request(5.0, True, False, 85.0)

        assert metrics.get_mitigation_effectiveness() == 80.0

    def test_requests_per_minute(self):
        """Test requests per minute calculation."""
        metrics = PerformanceMetrics()
        for _ in range(60):
            metrics.record_request(5.0, False, False, 10.0)

        rpm = metrics.get_requests_per_minute()
        assert rpm >= 50  # Allow some tolerance

    def test_cache_operations(self):
        """Test cache effectiveness recording."""
        metrics = PerformanceMetrics()
        for _ in range(80):
            metrics.record_cache_hit(latency_saved_ms=2.0)
        for _ in range(20):
            metrics.record_cache_miss()

        assert metrics.cache_effectiveness.hits == 80
        assert metrics.cache_effectiveness.hit_rate == 80.0

    def test_accuracy_recording(self):
        """Test accuracy metrics recording."""
        metrics = PerformanceMetrics()
        metrics.record_false_positive()
        metrics.record_false_negative()

        assert metrics.detection_accuracy.false_positives == 1
        assert metrics.detection_accuracy.false_negatives == 1

    def test_mitigation_recording(self):
        """Test mitigation action recording."""
        metrics = PerformanceMetrics()
        metrics.record_mitigation(10.0)
        metrics.record_mitigation(12.5)

        assert metrics.total_mitigations == 2

    def test_attack_trends_update(self):
        """Test attack trend updates."""
        metrics = PerformanceMetrics()
        metrics.update_attack_trends(
            attack_count=100,
            blocked_count=90,
            avg_risk_score=75.0,
            attack_types=["DDoS", "Brute Force"],
        )
        assert len(metrics.attack_trends) == 1
        trend = list(metrics.attack_trends)[0]
        assert trend.attack_count == 100
        assert trend.blocked_count == 90

    def test_performance_summary(self):
        """Test comprehensive performance summary."""
        metrics = PerformanceMetrics()
        for _ in range(100):
            metrics.record_request(5.0, False, False, 10.0)

        summary = metrics.get_performance_summary()
        assert 'timestamp' in summary
        assert summary['total_requests'] == 100
        assert 'latency' in summary
        assert 'cache_effectiveness' in summary
        assert 'detection_accuracy' in summary

    def test_trend_analysis_empty(self):
        """Test trend analysis with no trends."""
        metrics = PerformanceMetrics()
        analysis = metrics.get_trend_analysis()
        assert analysis['trend_count'] == 0
        assert analysis['trend_direction'] == 'stable'

    def test_trend_analysis_increasing(self):
        """Test trend analysis with increasing attacks."""
        metrics = PerformanceMetrics()
        # Add increasing trend
        for count in [10, 20, 30, 40, 50, 60]:
            metrics.update_attack_trends(
                attack_count=count,
                blocked_count=count,
                avg_risk_score=50.0,
                attack_types=["DDoS"],
            )

        analysis = metrics.get_trend_analysis()
        assert analysis['trend_direction'] == 'increasing'

    def test_trend_analysis_decreasing(self):
        """Test trend analysis with decreasing attacks."""
        metrics = PerformanceMetrics()
        # Add decreasing trend
        for count in [60, 50, 40, 30, 20, 10]:
            metrics.update_attack_trends(
                attack_count=count,
                blocked_count=count,
                avg_risk_score=50.0,
                attack_types=["DDoS"],
            )

        analysis = metrics.get_trend_analysis()
        assert analysis['trend_direction'] == 'decreasing'

    def test_health_check(self):
        """Test metrics health check."""
        metrics = PerformanceMetrics()
        health = metrics.health_check()
        assert health['active'] is True
        assert health['memory_efficient'] is True

    def test_reset_session(self):
        """Test session reset."""
        metrics = PerformanceMetrics()
        metrics.total_requests = 100
        metrics.total_attacks = 50
        metrics.total_blocked = 40

        metrics.reset_session()
        assert metrics.total_requests == 0
        assert metrics.total_attacks == 0
        assert metrics.total_blocked == 0

    def test_export_metrics(self):
        """Test metrics export."""
        metrics = PerformanceMetrics()
        for _ in range(50):
            metrics.record_request(5.0, False, False, 10.0)

        export = metrics.export_metrics()
        assert 'summary' in export
        assert 'trends' in export
        assert 'health' in export


class TestAttackTrend:
    """Test attack trend data model."""

    def test_attack_trend_creation(self):
        """Test attack trend instantiation."""
        trend = AttackTrend(
            timestamp=datetime.now(),
            attack_count=100,
            blocked_count=90,
            avg_risk_score=75.0,
            attack_types=["DDoS", "Brute Force"],
        )
        assert trend.attack_count == 100
        assert len(trend.attack_types) == 2

    def test_attack_trend_to_dict(self):
        """Test attack trend serialization."""
        now = datetime.now()
        trend = AttackTrend(
            timestamp=now,
            attack_count=100,
            blocked_count=90,
            avg_risk_score=75.0,
            attack_types=["DDoS"],
        )
        data = trend.to_dict()
        assert data['attack_count'] == 100
        assert data['blocked_count'] == 90
        assert 'timestamp' in data


class TestGlobalMetrics:
    """Test global metrics initialization and retrieval."""

    def test_initialize_metrics(self):
        """Test global metrics initialization."""
        metrics = initialize_metrics()
        assert metrics is not None
        assert isinstance(metrics, PerformanceMetrics)

    def test_get_metrics(self):
        """Test retrieving global metrics."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        assert metrics1 is metrics2


class TestMetricsEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_stats(self):
        """Test statistics with empty data."""
        metrics = LatencyMetrics()
        stats = metrics.get_stats(metrics.detection_latency_ms)
        assert stats['count'] == 0
        assert stats['mean'] == 0

    def test_zero_division_protection(self):
        """Test zero division protection."""
        accuracy = DetectionAccuracy()
        assert accuracy.accuracy == 0.0
        assert accuracy.precision == 0.0
        assert accuracy.recall == 0.0
        assert accuracy.f1_score == 0.0

    def test_single_request_metrics(self):
        """Test metrics with single request."""
        metrics = PerformanceMetrics()
        metrics.record_request(5.0, False, False, 10.0)

        summary = metrics.get_performance_summary()
        assert summary['total_requests'] == 1

    def test_maxlen_deque_behavior(self):
        """Test deque maxlen behavior (circular buffer)."""
        metrics = LatencyMetrics()
        # Fill beyond maxlen
        for i in range(1500):
            metrics.record_detection_latency(float(i))

        assert len(metrics.detection_latency_ms) == 1000

    def test_multiple_requests_performance(self):
        """Test performance with many requests."""
        metrics = PerformanceMetrics()
        for i in range(1000):
            metrics.record_request(
                detection_latency_ms=float(i % 20),
                was_attack=i % 100 < 10,
                was_blocked=i % 100 < 8,
                risk_score=float(i % 100),
            )

        assert metrics.total_requests == 1000
        assert metrics.total_attacks == 100
        assert metrics.total_blocked == 80
