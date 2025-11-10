"""Mock settings for testing."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class MockSettings(BaseSettings):
    """Mock settings for testing."""
    
    # DDoS Protection Settings
    request_rate_limit: int = 120
    sliding_window_seconds: int = 60
    blocking_time_seconds: int = 300
    max_request_size_bytes: int = 1024 * 1024  # 1MB
    
    # Security settings
    trusted_proxies: List[str] = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    blocklist_ips: List[str] = []
    whitelist_ips: List[str] = []
    
    # Model settings
    model_path: str = "models"
    model_update_interval_hours: int = 24
    model_cache_ttl_seconds: int = 3600
    model_cache_max_size: int = 10000
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=("settings_",)
    )