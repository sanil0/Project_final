"""Hybrid detection engine evaluating inbound traffic risk."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, Set, Optional

from ..schemas import DetectionVerdict, FeatureVector, MitigationAction, TrafficSample
from .ml_model import DDoSDetectionModel
from .cache import get_cache, CACHE_KEYS
from .alerting import get_alerting_engine
from .performance_metrics import get_metrics


@dataclass
class DetectionResult:
    """Result of DDoS detection analysis."""
    is_benign: bool
    risk_score: float
    confidence: float
    detection_type: str
    should_block: bool
    should_rate_limit: bool
    is_rate_limited: bool
    block_reason: Optional[str] = None
    rate_limit_window: Optional[int] = None
    feature_contributions: Dict[str, float] = None

logger = logging.getLogger(__name__)


@dataclass
class DetectionEngine:
    blocklist_ips: Set[str] = field(default_factory=set)
    suspicious_user_agents: Set[str] = field(default_factory=lambda: {
        "masscan",
        "sqlmap",
        "wget",
    })
    burst_threshold: float = 6.0
    ip_rate_threshold: float = 5.0
    global_rate_threshold: float = 400.0
    ml_model: Optional[DDoSDetectionModel] = None
    window_size: int = 60
    cleanup_interval: int = 300
    thresholds: Dict[str, any] = field(default_factory=dict)
    ip_metrics: Dict[str, Dict] = field(default_factory=dict)
    ip_metrics_lock: Optional[asyncio.Lock] = field(default=None)
    async def analyze_request(
        self,
        client_ip: str,
        request_time: float,
        features: Dict[str, float],
        prediction: Dict[str, any]
    ) -> DetectionResult:
        """Analyze a request for DDoS patterns."""
        # Check if IP is blocklisted
        if client_ip in self.blocklist_ips:
            return DetectionResult(
                is_benign=False,
                risk_score=100.0,
                confidence=1.0,
                detection_type="BLOCKLISTED",
                should_block=True,
                should_rate_limit=False,
                is_rate_limited=False,
                block_reason="IP address is blocklisted",
                feature_contributions={}
            )

        # Use ML model prediction and features to make decision
        risk_score = prediction['risk_score']
        is_benign = prediction['is_benign']
        confidence = prediction['confidence']

        # Determine detection type and actions
        if risk_score >= 90:
            detection_type = "HIGH_RISK_ATTACK"
            should_block = True
            should_rate_limit = True
        elif risk_score >= 70:
            detection_type = "SUSPICIOUS_TRAFFIC"
            should_block = False
            should_rate_limit = True
        elif not is_benign:
            detection_type = "ANOMALOUS_TRAFFIC"
            should_block = False
            should_rate_limit = features.get('ip_request_rate', 0) > self.ip_rate_threshold
        else:
            detection_type = "NORMAL_TRAFFIC"
            should_block = False
            should_rate_limit = False

        return DetectionResult(
            is_benign=is_benign,
            risk_score=risk_score,
            confidence=confidence,
            detection_type=detection_type,
            should_block=should_block,
            should_rate_limit=should_rate_limit,
            is_rate_limited=False,  # This will be set by apply_rate_limit if needed
            block_reason=f"High-risk traffic pattern detected (score: {risk_score:.1f})" if should_block else None,
            rate_limit_window=60 if should_rate_limit else None,
            feature_contributions=prediction.get('feature_contributions', {})
        )

    def __post_init__(self):
        """Post-init: set up locks, defaults and ML model.

        - Ensure ip_metrics_lock is created exactly once.
        - Apply sensible default thresholds when none provided.
        - Attempt to load a pre-trained ML model; fall back to a fresh instance on error.
        """
        # Initialize the ip metrics lock once
        if self.ip_metrics_lock is None:
            self.ip_metrics_lock = asyncio.Lock()

        # Apply default thresholds if caller didn't provide any
        if not self.thresholds:
            self.thresholds = {
                'burst_threshold': 6.0,
                'flow_threshold': 5.0,
                'global_threshold': 400.0,
                'confidence_threshold': 0.75,
                'risk_score_threshold': 75,
                'burst_multiplier': 1.0,
                # conservative defaults for optional keys used by middleware
                'block_duration': 300,
                'request_timeout': 30.0
            }

        # Load ML model if available; if loading fails, instantiate a fresh model
        try:
            self.ml_model = DDoSDetectionModel.load_model("models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained model: {e}. Initializing new model.")
            try:
                self.ml_model = DDoSDetectionModel()
            except Exception:
                # Last-resort: set to None and let callers handle missing model
                logger.exception("Failed to instantiate fallback DDoSDetectionModel; continuing with ml_model=None")
                self.ml_model = None

    async def evaluate(self, sample: TrafficSample, features: FeatureVector) -> DetectionVerdict:
        if sample.client_ip in self.blocklist_ips:
            return DetectionVerdict(
                action=MitigationAction.BLOCK,
                severity="critical",
                reason="ip_blocklisted",
                detail=f"Client IP {sample.client_ip} present in blocklist",
            )
        headers_lower = {key.lower(): value for key, value in sample.headers.items()}
        user_agent = headers_lower.get("user-agent", "").lower()
        if any(ua in user_agent for ua in self.suspicious_user_agents):
            return DetectionVerdict(
                action=MitigationAction.CHALLENGE,
                severity="high",
                reason="suspicious_user_agent",
                detail=f"User-Agent: {user_agent}",
            )
        # Volumetric heuristics
        if features.ip_request_rate >= self.ip_rate_threshold and features.burst_score >= self.burst_threshold:
            return DetectionVerdict(
                action=MitigationAction.RATE_LIMIT,
                severity="high",
                reason="ip_rate_exceeded",
                detail=f"rate={features.ip_request_rate:.2f}, burst={features.burst_score:.2f}",
            )
        if features.global_request_rate >= self.global_rate_threshold:
            return DetectionVerdict(
                action=MitigationAction.RATE_LIMIT,
                severity="medium",
                reason="global_rate_spike",
                detail=f"global_rate={features.global_request_rate:.2f}",
            )
            
        # ML-based detection
        if self.ml_model:
            try:
                ml_features = {
                    'Flow Duration': features.burst_score * 1000,  # Convert to milliseconds
                    'Total Fwd Packets': features.ip_request_rate * self.burst_threshold,
                    'Total Backward Packets': 0,  # Will be updated with actual data
                    'Total Length of Fwd Packets': sample.content_length,
                    'Total Length of Bwd Packets': 0,  # Will be updated with actual data
                    'Flow IAT Mean': 1000 / max(features.ip_request_rate, 0.1),  # Avg time between requests
                    'Flow IAT Std': features.burst_score * 100,  # Use burst score as proxy for variance
                    'Flow IAT Max': features.burst_score * 2000,
                    'Flow IAT Min': 100,  # Minimum 100ms between requests
                    'Fwd IAT Mean': 1000 / max(features.global_request_rate, 0.1),
                    'Fwd IAT Std': features.burst_score * 50,
                    'Fwd IAT Max': features.burst_score * 1500,
                    'Fwd IAT Min': 50,
                    'Fwd Packet Length Max': sample.content_length,
                    'Fwd Packet Length Min': 0
                }
                
                result = self.ml_model.predict(ml_features)
                if not result['is_benign'] and result['confidence'] > 0.8:
                    return DetectionVerdict(
                        action=MitigationAction.BLOCK,
                        severity="high" if result['risk_score'] >= 80 else "medium",
                        reason="ml_detection",
                        detail=f"ML confidence: {result['confidence']:.2f}, Risk score: {result['risk_score']:.2f}"
                    )
            except Exception as e:
                logger.warning(f"ML detection failed: {str(e)}")
                
        return DetectionVerdict(
            action=MitigationAction.ALLOW,
            severity="low",
            reason="baseline",
        )

    def load_blocklist(self, ips: Iterable[str]) -> None:
        self.blocklist_ips = {ip.strip() for ip in ips if ip}

    def add_to_blocklist(self, ip: str) -> None:
        if ip:
            self.blocklist_ips.add(ip)

    def remove_from_blocklist(self, ip: str) -> None:
        self.blocklist_ips.discard(ip)

    async def update_metrics(
        self, 
        client_ip: str,
        request_time: float,
        response_time: float,
        response_status: int,
        response_size: int
    ) -> None:
        """Update traffic metrics after a request is processed."""
        # Update response metrics
        async with self.ip_metrics_lock:
            if client_ip not in self.ip_metrics:
                self.ip_metrics[client_ip] = {
                    'total_requests': 0,
                    'total_bytes': 0,
                    'response_times': [],
                    'status_codes': []
                }

            metrics = self.ip_metrics[client_ip]
            metrics['total_requests'] += 1
            metrics['total_bytes'] += response_size
            metrics['response_times'].append(response_time - request_time)
            metrics['status_codes'].append(response_status)
