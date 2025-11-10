from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class MitigationAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    RATE_LIMIT = "rate_limit"
    CHALLENGE = "challenge"


class TrafficSample(BaseModel):
    client_ip: str = Field(..., description="Normalized client IP address")
    method: str
    path: str
    headers: Dict[str, str]
    content_length: int = 0
    request_rate: float = Field(0.0, description="Requests per second")
    bytes_per_second: float = Field(0.0, description="Bytes transferred per second")
    packet_rate: float = Field(0.0, description="Packets per second")
    timestamp: Optional[str] = Field(None, description="Event timestamp")


class FeatureVector(BaseModel):
    ip_request_rate: float = Field(..., description="Requests per second for IP over sliding window")
    global_request_rate: float = Field(..., description="Requests per second for entire edge over sliding window")
    unique_ip_count: int = Field(..., description="Unique IPs observed over sliding window")
    burst_score: float = Field(..., description="Relative burst indicator for IP")


class DetectionVerdict(BaseModel):
    action: MitigationAction
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    reason: str
    detail: Optional[str] = None
    confidence: Optional[float] = Field(None, description="ML model confidence score")


class MitigationResult(BaseModel):
    allowed: bool
    rule_matched: Optional[str] = None
    duration_seconds: Optional[int] = None


class BlocklistRequest(BaseModel):
    ip: str
    reason: Optional[str]
