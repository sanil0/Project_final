"""
Performance Metrics and Trend Analysis System

Purpose: Track system performance, measure detection effectiveness,
monitor mitigation success, and analyze trends over time.

Features:
- Latency measurement and histograms
- Cache effectiveness tracking
- Detection accuracy metrics
- Attack trend analysis
- Real-time performance statistics
- Historical data retention
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class LatencyMetrics:
    """Tracks latency measurements."""
    detection_latency_ms: deque = field(default_factory=lambda: deque(maxlen=1000))
    cache_hit_latency_ms: deque = field(default_factory=lambda: deque(maxlen=1000))
    cache_miss_latency_ms: deque = field(default_factory=lambda: deque(maxlen=1000))
    mitigation_latency_ms: deque = field(default_factory=lambda: deque(maxlen=1000))

    def record_detection_latency(self, latency_ms: float) -> None:
        """Record detection latency."""
        self.detection_latency_ms.append(latency_ms)

    def record_cache_hit_latency(self, latency_ms: float) -> None:
        """Record cache hit latency."""
        self.cache_hit_latency_ms.append(latency_ms)

    def record_cache_miss_latency(self, latency_ms: float) -> None:
        """Record cache miss latency."""
        self.cache_miss_latency_ms.append(latency_ms)

    def record_mitigation_latency(self, latency_ms: float) -> None:
        """Record mitigation latency."""
        self.mitigation_latency_ms.append(latency_ms)

    def get_stats(self, latencies: deque) -> Dict:
        """Calculate statistics for a deque of latencies."""
        if not latencies:
            return {
                'min': 0,
                'max': 0,
                'mean': 0,
                'median': 0,
                'p95': 0,
                'p99': 0,
                'count': 0,
            }

        sorted_latencies = sorted(latencies)
        count = len(sorted_latencies)

        return {
            'min': min(sorted_latencies),
            'max': max(sorted_latencies),
            'mean': statistics.mean(sorted_latencies),
            'median': statistics.median(sorted_latencies),
            'p95': sorted_latencies[int(count * 0.95)] if count > 0 else 0,
            'p99': sorted_latencies[int(count * 0.99)] if count > 0 else 0,
            'count': count,
        }

    def get_latency_summary(self) -> Dict:
        """Get comprehensive latency summary."""
        return {
            'detection': self.get_stats(self.detection_latency_ms),
            'cache_hit': self.get_stats(self.cache_hit_latency_ms),
            'cache_miss': self.get_stats(self.cache_miss_latency_ms),
            'mitigation': self.get_stats(self.mitigation_latency_ms),
        }


@dataclass
class CacheEffectiveness:
    """Tracks cache performance."""
    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    bytes_saved: int = 0
    time_saved_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def record_hit(self, latency_saved_ms: float = 0.0) -> None:
        """Record cache hit."""
        self.hits += 1
        self.total_requests += 1
        self.time_saved_ms += latency_saved_ms

    def record_miss(self) -> None:
        """Record cache miss."""
        self.misses += 1
        self.total_requests += 1

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': self.total_requests,
            'hit_rate': self.hit_rate,
            'bytes_saved': self.bytes_saved,
            'time_saved_ms': self.time_saved_ms,
        }


@dataclass
class DetectionAccuracy:
    """Tracks detection accuracy metrics."""
    true_positives: int = 0  # Correctly identified attacks
    true_negatives: int = 0  # Correctly identified benign
    false_positives: int = 0  # Incorrectly flagged benign
    false_negatives: int = 0  # Missed attacks
    blocked_requests: int = 0
    allowed_requests: int = 0

    @property
    def total_predictions(self) -> int:
        """Total number of predictions."""
        return (
            self.true_positives
            + self.true_negatives
            + self.false_positives
            + self.false_negatives
        )

    @property
    def accuracy(self) -> float:
        """Overall accuracy percentage."""
        if self.total_predictions == 0:
            return 0.0
        correct = self.true_positives + self.true_negatives
        return (correct / self.total_predictions) * 100

    @property
    def precision(self) -> float:
        """Attack detection precision."""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return (
            self.true_positives / (self.true_positives + self.false_positives)
        ) * 100

    @property
    def recall(self) -> float:
        """Attack detection recall (sensitivity)."""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return (
            self.true_positives / (self.true_positives + self.false_negatives)
        ) * 100

    @property
    def f1_score(self) -> float:
        """F1 score (harmonic mean of precision and recall)."""
        if self.precision + self.recall == 0:
            return 0.0
        return (
            2
            * (self.precision * self.recall)
            / (self.precision + self.recall)
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'total_predictions': self.total_predictions,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'blocked_requests': self.blocked_requests,
            'allowed_requests': self.allowed_requests,
        }


@dataclass
class AttackTrend:
    """Tracks attack trends over time."""
    timestamp: datetime
    attack_count: int
    blocked_count: int
    avg_risk_score: float
    attack_types: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'attack_count': self.attack_count,
            'blocked_count': self.blocked_count,
            'avg_risk_score': self.avg_risk_score,
            'attack_types': self.attack_types,
        }


class PerformanceMetrics:
    """
    Comprehensive performance metrics tracking system.

    Tracks:
    - Request latency (detection, cache, mitigation)
    - Cache effectiveness
    - Detection accuracy
    - Attack trends over time
    """

    def __init__(self, history_window_minutes: int = 60):
        """
        Initialize performance metrics.

        Args:
            history_window_minutes: Number of minutes to retain trend data
        """
        self.history_window_minutes = history_window_minutes

        # Core metrics
        self.latency = LatencyMetrics()
        self.cache_effectiveness = CacheEffectiveness()
        self.detection_accuracy = DetectionAccuracy()

        # Trend tracking
        self.attack_trends: deque = deque(maxlen=history_window_minutes)
        self.hourly_trends: Dict[str, Dict] = {}

        # Counters
        self.total_requests = 0
        self.total_attacks = 0
        self.total_blocked = 0
        self.total_mitigations = 0

        # Timestamps for rate calculation
        self.session_start = datetime.now()
        self.last_trend_update = datetime.now()

    def record_request(
        self,
        detection_latency_ms: float,
        was_attack: bool,
        was_blocked: bool,
        risk_score: float,
    ) -> None:
        """Record a request and its metrics."""
        self.total_requests += 1
        self.latency.record_detection_latency(detection_latency_ms)

        if was_attack:
            self.total_attacks += 1
            self.detection_accuracy.true_positives += 1
            if was_blocked:
                self.total_blocked += 1
                self.detection_accuracy.blocked_requests += 1
        else:
            self.detection_accuracy.true_negatives += 1
            self.detection_accuracy.allowed_requests += 1

    def record_cache_hit(self, latency_saved_ms: float = 0.0) -> None:
        """Record cache hit."""
        self.cache_effectiveness.record_hit(latency_saved_ms)

    def record_cache_miss(self) -> None:
        """Record cache miss."""
        self.cache_effectiveness.record_miss()

    def record_mitigation(self, mitigation_latency_ms: float) -> None:
        """Record mitigation action."""
        self.total_mitigations += 1
        self.latency.record_mitigation_latency(mitigation_latency_ms)

    def record_false_positive(self) -> None:
        """Record false positive (benign flagged as attack)."""
        self.detection_accuracy.false_positives += 1

    def record_false_negative(self) -> None:
        """Record false negative (attack missed)."""
        self.detection_accuracy.false_negatives += 1

    def update_attack_trends(
        self,
        attack_count: int,
        blocked_count: int,
        avg_risk_score: float,
        attack_types: List[str],
    ) -> None:
        """Update attack trend data."""
        trend = AttackTrend(
            timestamp=datetime.now(),
            attack_count=attack_count,
            blocked_count=blocked_count,
            avg_risk_score=avg_risk_score,
            attack_types=attack_types,
        )
        self.attack_trends.append(trend)

    def get_requests_per_minute(self) -> float:
        """Calculate requests per minute."""
        elapsed = max(1, (datetime.now() - self.session_start).total_seconds() / 60)
        return self.total_requests / elapsed if elapsed > 0 else 0

    def get_attack_rate(self) -> float:
        """Calculate attack rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.total_attacks / self.total_requests) * 100

    def get_block_rate(self) -> float:
        """Calculate block rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.total_blocked / self.total_requests) * 100

    def get_mitigation_effectiveness(self) -> float:
        """Calculate mitigation effectiveness percentage."""
        if self.total_attacks == 0:
            return 0.0
        return (self.total_blocked / self.total_attacks) * 100

    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        return {
            'timestamp': datetime.now().isoformat(),
            'session_duration_minutes': (
                (datetime.now() - self.session_start).total_seconds() / 60
            ),
            'total_requests': self.total_requests,
            'requests_per_minute': self.get_requests_per_minute(),
            'total_attacks': self.total_attacks,
            'attack_rate': self.get_attack_rate(),
            'total_blocked': self.total_blocked,
            'block_rate': self.get_block_rate(),
            'total_mitigations': self.total_mitigations,
            'mitigation_effectiveness': self.get_mitigation_effectiveness(),
            'latency': self.latency.get_latency_summary(),
            'cache_effectiveness': self.cache_effectiveness.to_dict(),
            'detection_accuracy': self.detection_accuracy.to_dict(),
        }

    def get_trend_analysis(self) -> Dict:
        """Analyze trends over time."""
        if not self.attack_trends:
            return {
                'trend_count': 0,
                'average_attack_count': 0,
                'average_blocked_count': 0,
                'average_risk_score': 0,
                'peak_attack_count': 0,
                'trend_direction': 'stable',
            }

        trends_list = list(self.attack_trends)
        attack_counts = [t.attack_count for t in trends_list]
        blocked_counts = [t.blocked_count for t in trends_list]
        risk_scores = [t.avg_risk_score for t in trends_list]

        avg_attack = statistics.mean(attack_counts) if attack_counts else 0
        avg_blocked = statistics.mean(blocked_counts) if blocked_counts else 0
        avg_risk = statistics.mean(risk_scores) if risk_scores else 0

        # Determine trend direction
        if len(attack_counts) > 1:
            recent_avg = statistics.mean(attack_counts[-5:])
            older_avg = statistics.mean(attack_counts[:-5])
            if recent_avg > older_avg * 1.2:
                trend_direction = 'increasing'
            elif recent_avg < older_avg * 0.8:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'

        return {
            'trend_count': len(trends_list),
            'average_attack_count': avg_attack,
            'average_blocked_count': avg_blocked,
            'average_risk_score': avg_risk,
            'peak_attack_count': max(attack_counts) if attack_counts else 0,
            'trend_direction': trend_direction,
        }

    def health_check(self) -> Dict:
        """Check metrics system health."""
        return {
            'active': True,
            'total_requests_tracked': self.total_requests,
            'total_trends_recorded': len(self.attack_trends),
            'latency_samples': len(self.latency.detection_latency_ms),
            'memory_efficient': True,
        }

    def reset_session(self) -> None:
        """Reset session metrics."""
        self.total_requests = 0
        self.total_attacks = 0
        self.total_blocked = 0
        self.total_mitigations = 0
        self.session_start = datetime.now()
        self.latency = LatencyMetrics()
        self.cache_effectiveness = CacheEffectiveness()
        self.detection_accuracy = DetectionAccuracy()

    def export_metrics(self) -> Dict:
        """Export all metrics for external systems."""
        return {
            'summary': self.get_performance_summary(),
            'trends': self.get_trend_analysis(),
            'health': self.health_check(),
        }


# Global metrics instance
_performance_metrics: Optional[PerformanceMetrics] = None


def initialize_metrics(history_window_minutes: int = 60) -> PerformanceMetrics:
    """Initialize global metrics system."""
    global _performance_metrics
    _performance_metrics = PerformanceMetrics(history_window_minutes)
    return _performance_metrics


def get_metrics() -> PerformanceMetrics:
    """Get global metrics system."""
    global _performance_metrics
    if _performance_metrics is None:
        _performance_metrics = PerformanceMetrics()
    return _performance_metrics
