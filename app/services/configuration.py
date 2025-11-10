"""Configuration management service for dynamic config updates."""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps

from pydantic import ValidationError
from fastapi import HTTPException

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Manages configuration state and updates."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._settings: Settings = get_settings()
        self._last_reload: Optional[datetime] = None
        self._subscribers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        
    async def reload_config(self) -> Dict[str, Any]:
        """
        Reload configuration from environment and notify subscribers.
        
        Returns:
            Dict containing reload status and timestamp
        """
        async with self._lock:
            try:
                # Clear cached settings
                if hasattr(get_settings, 'cache_clear'):
                    get_settings.cache_clear()
                
                # Load new settings
                new_settings = get_settings()
                
                # Validate new settings
                self._validate_config_changes(new_settings)
                
                # Update current settings
                self._settings = new_settings
                self._last_reload = datetime.utcnow()
                
                # Notify subscribers
                await self._notify_subscribers()
                
                logger.info("Configuration reloaded successfully")
                return {
                    "status": "success",
                    "timestamp": self._last_reload.isoformat(),
                    "message": "Configuration reloaded successfully"
                }
                
            except ValidationError as e:
                logger.error(f"Configuration validation error: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Configuration validation failed: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error reloading configuration: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to reload configuration: {str(e)}"
                )
    
    def _validate_config_changes(self, new_settings: Settings) -> None:
        """
        Validate configuration changes for safety.
        
        Args:
            new_settings: New settings to validate
        
        Raises:
            ValidationError: If changes are invalid
        """
        # Check for dangerous changes in rate limiting
        if (hasattr(self._settings, 'base_rate_limit') and 
            new_settings.base_rate_limit < self._settings.base_rate_limit * 0.5):
            raise ValidationError(
                "Rate limit decrease too large (>50%)",
                model=Settings
            )
        
        # Check for unsafe changes in blocking duration
        if (hasattr(self._settings, 'block_duration_minutes') and
            new_settings.block_duration_minutes < self._settings.block_duration_minutes * 0.5):
            raise ValidationError(
                "Block duration decrease too large (>50%)",
                model=Settings
            )
    
    async def _notify_subscribers(self) -> None:
        """Notify all subscribers of configuration changes."""
        for callback in self._subscribers.values():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._settings)
                else:
                    callback(self._settings)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, name: str, callback: Callable) -> None:
        """
        Subscribe to configuration changes.
        
        Args:
            name: Unique name for the subscriber
            callback: Function to call on config changes
        """
        self._subscribers[name] = callback
        logger.debug(f"Added configuration subscriber: {name}")
    
    def unsubscribe(self, name: str) -> None:
        """
        Unsubscribe from configuration changes.
        
        Args:
            name: Name of subscriber to remove
        """
        if name in self._subscribers:
            del self._subscribers[name]
            logger.debug(f"Removed configuration subscriber: {name}")
    
    @property
    def settings(self) -> Settings:
        """Get current settings."""
        return self._settings
    
    @property
    def last_reload(self) -> Optional[datetime]:
        """Get timestamp of last reload."""
        return self._last_reload
    
    def export_config(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export current configuration.
        
        Args:
            path: Optional path to save config to
            
        Returns:
            Dict containing current configuration
        """
        config = self._settings.model_dump()
        
        if path:
            save_path = Path(path)
            save_path.write_text(json.dumps(config, indent=2))
            logger.info(f"Configuration exported to {save_path}")
            
        return config