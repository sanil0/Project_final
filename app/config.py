from functools import lru_cache
from typing import List, Optional, Dict, Any
from ipaddress import ip_network
from datetime import timedelta
import json

from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
try:
    # Pydantic v2 style config
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = None  # type: ignore

from .services.ml_model import SensitivityLevel


def parse_list(value: str) -> List[str]:
    """Parse a comma-separated list of strings."""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_cidrs(value: str) -> List[str]:
    """Parse and validate comma-separated CIDR list."""
    cidrs = parse_list(value)
    for cidr in cidrs:
        try:
            ip_network(cidr)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR format {cidr}: {e}")
    return cidrs


class Settings(BaseSettings):
    """Runtime configuration for the DDoS guard service."""
    # Pydantic v2 config: ignore unknown env/inputs to avoid test pollution
    if ConfigDict is not None:  # type: ignore
        model_config = ConfigDict(
            extra='ignore',
            env_ignore_empty=True,
            env_file='.env',
            case_sensitive=False,
            env_file_encoding='utf-8'
        )  # type: ignore

    # Core Application Settings
    upstream_base_url: AnyHttpUrl = Field(..., description="Base URL for upstream service")
    admin_api_key: Optional[str] = Field(None, description="API key required for admin endpoints")
    
    # DDoS Protection Settings
    target_url: AnyHttpUrl = Field(..., description="The URL of the protected web application")
    sensitivity_level: str = Field("medium", description="DDoS detection sensitivity (low/medium/high)")
    
    # Rate Limiting Configuration
    base_rate_limit: int = Field(120, ge=1, description="Base requests per window allowed")
    rate_window_seconds: int = Field(60, ge=1, description="Time window for rate limiting")
    burst_multiplier: float = Field(1.5, ge=1.0, description="Multiplier for burst allowance")
    dynamic_rate_adjustment: bool = Field(True, description="Enable ML-based rate adjustment")
    # Compatibility fields expected by middleware/tests
    request_rate_limit: int = Field(5, ge=1, description="Max requests allowed per window")
    sliding_window_seconds: int = Field(60, ge=1, description="Sliding window size in seconds")
    
    # Blocking Rules
    block_duration_minutes: int = Field(30, ge=1, description="Duration to block malicious IPs")
    block_threshold_violations: int = Field(3, ge=1, description="Number of violations before blocking")
    progressive_blocking: bool = Field(True, description="Increase block duration for repeat offenders")
    max_block_duration_hours: int = Field(24, ge=1, description="Maximum block duration for repeat offenders")
    
    # ML Model Configuration
    model_path: str = Field("models", description="Path to ML model files")
    model_update_interval_hours: int = Field(24, ge=1, description="Interval to check for model updates")
    enable_model_cache: bool = Field(True, description="Enable prediction caching")
    model_cache_ttl_seconds: int = Field(300, ge=1, description="TTL for cached predictions")
    model_cache_max_size: int = Field(10000, ge=100, description="Maximum number of cached predictions")
    batch_prediction_size: int = Field(100, ge=10, description="Batch size for predictions")
    
    # Feature Extraction Settings
    feature_window_seconds: int = Field(300, ge=1, description="Time window for feature extraction")
    min_samples_required: int = Field(10, ge=1, description="Minimum samples needed for prediction")
    
    # IP Management
    blocklist_ips: str = Field("", description="Comma-separated list of blocked IPs")
    whitelist_ips: str = Field("", description="Comma-separated list of trusted IPs")
    trusted_proxies: str = Field("", description="Comma-separated list of trusted proxy CIDRs")
    country_blocklist: str = Field("", description="Comma-separated list of blocked country codes")
    asn_blocklist: str = Field("", description="Comma-separated list of blocked ASNs")
    ip_reputation_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum IP reputation score")
    
    # Request Processing
    honor_x_forwarded_for: bool = Field(False, description="Trust X-Forwarded-For header")
    max_request_size_kb: int = Field(1024, ge=1, description="Maximum request size in KB")
    enable_request_validation: bool = Field(True, description="Enable request payload validation")
    
    @field_validator("blocklist_ips", "trusted_proxies", "whitelist_ips", "country_blocklist", "asn_blocklist", mode='before')
    @classmethod
    def ensure_string(cls, v):
        if v is None:
            return ""
        return str(v)

    @field_validator("upstream_base_url", "target_url", mode='after')
    @classmethod
    def validate_urls(cls, v):
        if not str(v).startswith(("http://", "https://")):
            raise ValueError("URLs must start with http:// or https://")
        return v
    
    @field_validator("honor_x_forwarded_for", "dynamic_rate_adjustment", "progressive_blocking", 
              "enable_model_cache", "enable_request_validation", mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return False
        
    @model_validator(mode='after')
    def validate_settings(self):
        """Validate interdependent settings."""
        # Ensure block duration doesn't exceed max
        max_block_mins = self.max_block_duration_hours * 60
        if self.block_duration_minutes > max_block_mins:
            self.block_duration_minutes = max_block_mins
            
        # Ensure feature window is less than rate window
        if self.feature_window_seconds < self.rate_window_seconds:
            self.feature_window_seconds = self.rate_window_seconds
            
        # Validate sensitivity level
        if self.sensitivity_level not in [SensitivityLevel.LOW, SensitivityLevel.MEDIUM, SensitivityLevel.HIGH]:
            raise ValueError(f"Invalid sensitivity level: {self.sensitivity_level}")
            
        return self
    
    @property
    def blocklist(self) -> List[str]:
        """Parse and return blocklist IPs."""
        return parse_list(self.blocklist_ips)
    
    @property
    def whitelist(self) -> List[str]:
        """Parse and return whitelisted IPs."""
        return parse_list(self.whitelist_ips)
    
    @property
    def proxy_cidrs(self) -> List[str]:
        """Parse and return trusted proxy CIDRs."""
        return parse_cidrs(self.trusted_proxies)
        
    @property
    def blocked_countries(self) -> List[str]:
        """Parse and return blocked country codes."""
        return parse_list(self.country_blocklist)
        
    @property
    def blocked_asns(self) -> List[str]:
        """Parse and return blocked ASNs."""
        return parse_list(self.asn_blocklist)
        
    @property
    def block_duration(self) -> timedelta:
        """Get block duration as timedelta."""
        return timedelta(minutes=self.block_duration_minutes)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
