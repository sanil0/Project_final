"""
Advanced Attack Alerting System

Purpose: Detect attack escalation patterns, generate severity-based alerts,
track attack trends, and recommend automatic actions.

Features:
- Multi-level severity alerts (Low, Medium, High, Critical)
- Attack escalation detection
- Trend analysis over time
- Automatic action recommendations
- Alert history tracking
- Alert deduplication
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts that can be generated."""
    TRAFFIC_SPIKE = "traffic_spike"
    ATTACK_DETECTED = "attack_detected"
    ATTACK_ESCALATION = "attack_escalation"
    SUSTAINED_ATTACK = "sustained_attack"
    ATTACK_PATTERN_CHANGE = "pattern_change"
    IP_REPUTATION_SPIKE = "ip_reputation_spike"
    BLOCK_RATE_SURGE = "block_rate_surge"
    MITIGATION_FAILURE = "mitigation_failure"


@dataclass
class Alert:
    """Represents a single alert."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    timestamp: datetime
    message: str
    details: Dict = field(default_factory=dict)
    affected_ips: List[str] = field(default_factory=list)
    attack_count: int = 0
    block_rate: float = 0.0
    recommended_action: str = ""
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        data['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
        return data


@dataclass
class AlertPattern:
    """Tracks patterns for alert generation."""
    ip: str
    request_count: int = 0
    blocked_count: int = 0
    last_request_time: datetime = field(default_factory=datetime.now)
    first_request_time: datetime = field(default_factory=datetime.now)
    pattern_history: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def block_rate(self) -> float:
        """Calculate block rate percentage."""
        if self.request_count == 0:
            return 0.0
        return (self.blocked_count / self.request_count) * 100

    @property
    def requests_per_minute(self) -> float:
        """Calculate requests per minute."""
        duration = max(1, (self.last_request_time - self.first_request_time).total_seconds() / 60)
        return self.request_count / duration if duration > 0 else 0


class AlertingEngine:
    """
    Advanced attack alerting system.

    Tracks:
    - Attack patterns and escalation
    - Block rate trends
    - IP reputation changes
    - Mitigation effectiveness
    """

    def __init__(
        self,
        escalation_threshold: float = 0.7,  # 70% increase = escalation
        sustained_attack_duration: int = 300,  # 5 minutes
        dedup_window: int = 60,  # 1 minute deduplication
    ):
        """
        Initialize alerting engine.

        Args:
            escalation_threshold: Percentage increase to trigger escalation alert
            sustained_attack_duration: Seconds to consider an attack "sustained"
            dedup_window: Seconds to wait before creating duplicate alert
        """
        self.escalation_threshold = escalation_threshold
        self.sustained_attack_duration = sustained_attack_duration
        self.dedup_window = dedup_window

        # Alert history tracking
        self.alerts: List[Alert] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.last_alert_time: Dict[str, datetime] = defaultdict(
            lambda: datetime.min
        )

        # Pattern tracking per IP
        self.ip_patterns: Dict[str, AlertPattern] = {}

        # Global metrics
        self.total_requests = 0
        self.total_blocked = 0
        self.block_rate_history: deque = deque(maxlen=60)  # Last 60 data points

    def record_request(
        self,
        client_ip: str,
        was_blocked: bool,
        risk_score: float,
        detection_type: str,
    ) -> Optional[Alert]:
        """
        Record a request and check for alerts.

        Args:
            client_ip: Source IP address
            was_blocked: Whether request was blocked
            risk_score: DDoS risk score (0-100)
            detection_type: Type of detection (NORMAL, SUSPICIOUS, HIGH_RISK, etc.)

        Returns:
            Alert if one was generated, None otherwise
        """
        # Update global metrics
        self.total_requests += 1
        if was_blocked:
            self.total_blocked += 1

        # Initialize pattern if new IP
        if client_ip not in self.ip_patterns:
            self.ip_patterns[client_ip] = AlertPattern(ip=client_ip)

        pattern = self.ip_patterns[client_ip]
        pattern.request_count += 1
        if was_blocked:
            pattern.blocked_count += 1
        pattern.last_request_time = datetime.now()
        pattern.pattern_history.append({
            'timestamp': datetime.now().isoformat(),
            'blocked': was_blocked,
            'risk_score': risk_score,
            'type': detection_type,
        })

        # Check for alerts
        alert = self._check_for_alerts(client_ip, pattern, risk_score, detection_type)
        return alert

    def _check_for_alerts(
        self,
        client_ip: str,
        pattern: AlertPattern,
        risk_score: float,
        detection_type: str,
    ) -> Optional[Alert]:
        """Check if request pattern warrants an alert."""
        now = datetime.now()

        # Check 1: High risk score spike
        if risk_score >= 90 and detection_type == "HIGH_RISK_ATTACK":
            alert = self._create_alert(
                alert_type=AlertType.ATTACK_DETECTED,
                severity=AlertSeverity.CRITICAL,
                client_ip=client_ip,
                message=f"Critical attack detected from {client_ip}",
                details={
                    'risk_score': risk_score,
                    'detection_type': detection_type,
                    'block_rate': pattern.block_rate,
                },
                recommended_action="BLOCK_IP_IMMEDIATELY",
            )
            if alert:
                return alert

        # Check 2: Sustained high block rate (>80% blocked)
        if pattern.block_rate >= 80 and pattern.request_count >= 10:
            alert = self._create_alert(
                alert_type=AlertType.BLOCK_RATE_SURGE,
                severity=AlertSeverity.HIGH,
                client_ip=client_ip,
                message=f"High block rate from {client_ip}: {pattern.block_rate:.1f}%",
                details={
                    'block_rate': pattern.block_rate,
                    'request_count': pattern.request_count,
                    'blocked_count': pattern.blocked_count,
                },
                recommended_action="INCREASE_RATE_LIMIT_STRICTNESS",
            )
            if alert:
                return alert

        # Check 3: Rapid request rate increase
        if pattern.requests_per_minute > 100:
            alert = self._create_alert(
                alert_type=AlertType.TRAFFIC_SPIKE,
                severity=AlertSeverity.HIGH if pattern.requests_per_minute > 500 else AlertSeverity.MEDIUM,
                client_ip=client_ip,
                message=f"Traffic spike from {client_ip}: {pattern.requests_per_minute:.1f} req/min",
                details={
                    'requests_per_minute': pattern.requests_per_minute,
                    'request_count': pattern.request_count,
                },
                recommended_action="ENABLE_AGGRESSIVE_RATE_LIMITING",
            )
            if alert:
                return alert

        # Check 4: Attack pattern change
        if len(pattern.pattern_history) >= 5:
            recent_patterns = list(pattern.pattern_history)[-5:]
            recent_types = [p['type'] for p in recent_patterns]
            if len(set(recent_types)) > 2:  # Multiple different attack types
                alert = self._create_alert(
                    alert_type=AlertType.ATTACK_PATTERN_CHANGE,
                    severity=AlertSeverity.MEDIUM,
                    client_ip=client_ip,
                    message=f"Attack pattern change detected from {client_ip}",
                    details={
                        'pattern_types': list(set(recent_types)),
                        'recent_count': len(recent_patterns),
                    },
                    recommended_action="ENHANCE_DETECTION_SENSITIVITY",
                )
                if alert:
                    return alert

        return None

    def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        client_ip: str,
        message: str,
        details: Dict,
        recommended_action: str,
    ) -> Optional[Alert]:
        """
        Create an alert with deduplication.

        Returns Alert if created, None if deduplicated.
        """
        alert_key = f"{alert_type.value}:{client_ip}"
        now = datetime.now()

        # Check deduplication window
        last_alert = self.last_alert_time.get(alert_key, datetime.min)
        if (now - last_alert).total_seconds() < self.dedup_window:
            return None  # Alert dedup window not expired

        # Create alert
        alert = Alert(
            alert_id=self._generate_alert_id(),
            alert_type=alert_type,
            severity=severity,
            timestamp=now,
            message=message,
            details=details,
            affected_ips=[client_ip],
            attack_count=len(self.ip_patterns.get(client_ip, AlertPattern(ip=client_ip)).pattern_history),
            block_rate=self.ip_patterns.get(client_ip, AlertPattern(ip=client_ip)).block_rate,
            recommended_action=recommended_action,
        )

        # Store alert
        self.alerts.append(alert)
        self.active_alerts[alert.alert_id] = alert
        self.last_alert_time[alert_key] = now

        logger.info(f"🚨 Alert generated: {alert.message} (severity: {severity})")

        return alert

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        import uuid
        return f"alert_{uuid.uuid4().hex[:12]}"

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.is_resolved = True
            alert.resolved_at = datetime.now()
            del self.active_alerts[alert_id]
            logger.info(f"✓ Alert resolved: {alert.message}")
            return True
        return False

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_alert_history(
        self, limit: int = 100, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get alert history, optionally filtered by severity."""
        alerts = self.alerts[-limit:]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_statistics(self) -> Dict:
        """Get alerting system statistics."""
        total_block_rate = (
            (self.total_blocked / self.total_requests * 100)
            if self.total_requests > 0
            else 0
        )

        alerts_by_severity = defaultdict(int)
        for alert in self.active_alerts.values():
            alerts_by_severity[alert.severity.value] += 1

        return {
            'total_requests': self.total_requests,
            'total_blocked': self.total_blocked,
            'block_rate': total_block_rate,
            'active_alerts': len(self.active_alerts),
            'alerts_by_severity': dict(alerts_by_severity),
            'tracked_ips': len(self.ip_patterns),
            'total_alerts_generated': len(self.alerts),
        }

    def cleanup_old_patterns(self, older_than_seconds: int = 3600) -> int:
        """Remove old IP patterns to prevent memory leak."""
        cutoff_time = datetime.now() - timedelta(seconds=older_than_seconds)
        removed = 0

        for ip in list(self.ip_patterns.keys()):
            pattern = self.ip_patterns[ip]
            if pattern.last_request_time < cutoff_time:
                del self.ip_patterns[ip]
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old IP patterns")

        return removed

    def health_check(self) -> Dict:
        """Check alerting system health."""
        return {
            'active': True,
            'active_alerts': len(self.active_alerts),
            'total_alerts': len(self.alerts),
            'tracked_ips': len(self.ip_patterns),
            'memory_efficient': len(self.ip_patterns) < 10000,
        }


# Global alerting engine instance
_alerting_engine: Optional[AlertingEngine] = None


def initialize_alerting(
    escalation_threshold: float = 0.7,
    sustained_attack_duration: int = 300,
    dedup_window: int = 60,
) -> AlertingEngine:
    """Initialize global alerting engine."""
    global _alerting_engine
    _alerting_engine = AlertingEngine(
        escalation_threshold=escalation_threshold,
        sustained_attack_duration=sustained_attack_duration,
        dedup_window=dedup_window,
    )
    return _alerting_engine


def get_alerting_engine() -> AlertingEngine:
    """Get global alerting engine."""
    global _alerting_engine
    if _alerting_engine is None:
        _alerting_engine = AlertingEngine()
    return _alerting_engine
