from fastapi import Request, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from .config import Settings, get_settings
from .services import (
    DetectionEngine,
    FeatureExtractor,
    MitigationController,
    SlidingWindowStore,
    TelemetryClient,
)
from .services.configuration import ConfigurationManager

# API key header for admin endpoints
API_KEY_HEADER = APIKeyHeader(name="X-Admin-Token", auto_error=True)

# Global configuration manager instance
_config_manager: ConfigurationManager = None


async def get_settings_dep() -> Settings:
    return get_settings()


async def get_admin_api_key(
    api_key: str = Security(API_KEY_HEADER),
    settings: Settings = Depends(get_settings_dep)
) -> str:
    """Validate admin API key."""
    if not settings.admin_api_key or api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key"
        )
    return api_key

def get_config_manager() -> ConfigurationManager:
    """Get or create the configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_sliding_window_store(request: Request) -> SlidingWindowStore:
    return request.app.state.sliding_window_store


def get_feature_extractor(request: Request) -> FeatureExtractor:
    return request.app.state.feature_extractor


def get_detection_engine(request: Request) -> DetectionEngine:
    return request.app.state.detection_engine


def get_mitigation_controller(request: Request) -> MitigationController:
    return request.app.state.mitigation_controller


def get_telemetry_client(request: Request) -> TelemetryClient:
    return request.app.state.telemetry_client


def get_http_client(request: Request):  # pragma: no cover - accessor
    return request.app.state.http_client
