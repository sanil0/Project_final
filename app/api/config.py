"""Configuration management API endpoints."""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKey

from ..dependencies import get_admin_api_key, get_config_manager
from ..services.configuration import ConfigurationManager

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])

@router.get("/current")
async def get_current_config(
    config_manager: ConfigurationManager = Depends(get_config_manager),
    api_key: APIKey = Security(get_admin_api_key)
) -> Dict[str, Any]:
    """
    Get current configuration.
    
    Returns:
        Dict containing current configuration settings
    """
    return config_manager.export_config()

@router.post("/reload")
async def reload_config(
    config_manager: ConfigurationManager = Depends(get_config_manager),
    api_key: APIKey = Security(get_admin_api_key)
) -> Dict[str, Any]:
    """
    Reload configuration from environment.
    
    Returns:
        Dict containing reload status
    """
    return await config_manager.reload_config()

@router.get("/status")
async def get_config_status(
    config_manager: ConfigurationManager = Depends(get_config_manager),
    api_key: APIKey = Security(get_admin_api_key)
) -> Dict[str, Any]:
    """
    Get configuration status.
    
    Returns:
        Dict containing configuration status information
    """
    return {
        "last_reload": config_manager.last_reload.isoformat() if config_manager.last_reload else None,
        "subscriber_count": len(config_manager._subscribers),
    }

@router.post("/export")
async def export_config(
    path: Optional[str] = None,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    api_key: APIKey = Security(get_admin_api_key)
) -> Dict[str, Any]:
    """
    Export current configuration to file.
    
    Args:
        path: Optional path to save config to
        
    Returns:
        Dict containing exported configuration
    """
    try:
        return config_manager.export_config(path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export configuration: {str(e)}"
        )