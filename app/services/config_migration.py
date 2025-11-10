"""Configuration migration and version control tools."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil
import hashlib

logger = logging.getLogger(__name__)

class ConfigMigration:
    """Handle configuration versioning and migrations."""
    
    VERSION_FILE = "version.json"
    BACKUP_DIR = "config_backups"
    MIGRATIONS_DIR = "migrations"
    
    def __init__(self, config_dir: str = "config"):
        """Initialize migration manager."""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup and migrations directories
        self.backup_dir = self.config_dir / self.BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        
        self.migrations_dir = self.config_dir / self.MIGRATIONS_DIR
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Load or create version tracking
        self.version_file = self.config_dir / self.VERSION_FILE
        self.version_info = self._load_version_info()
    
    def _load_version_info(self) -> Dict[str, Any]:
        """Load or create version tracking information."""
        if self.version_file.exists():
            return json.loads(self.version_file.read_text())
        
        # Initialize version tracking
        version_info = {
            "current_version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "history": [],
            "checksum": None
        }
        self._save_version_info(version_info)
        return version_info
    
    def _save_version_info(self, version_info: Dict[str, Any]) -> None:
        """Save version tracking information."""
        self.version_file.write_text(json.dumps(version_info, indent=2))
    
    def _calculate_checksum(self, config: Dict[str, Any]) -> str:
        """Calculate checksum of configuration."""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def create_backup(self, config: Dict[str, Any], reason: str = "manual") -> str:
        """
        Create a backup of the current configuration.
        
        Args:
            config: Current configuration
            reason: Reason for backup
            
        Returns:
            Backup filename
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        backup_file = self.backup_dir / f"config_backup_{timestamp}.json"
        
        backup_data = {
            "config": config,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.version_info["current_version"],
                "reason": reason,
                "checksum": self._calculate_checksum(config)
            }
        }
        
        backup_file.write_text(json.dumps(backup_data, indent=2))
        logger.info(f"Created backup: {backup_file.name}")
        return backup_file.name
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Restore configuration from backup.
        
        Args:
            backup_name: Name of backup file
            
        Returns:
            Restored configuration
        """
        backup_file = self.backup_dir / backup_name
        if not backup_file.exists():
            raise ValueError(f"Backup not found: {backup_name}")
        
        backup_data = json.loads(backup_file.read_text())
        logger.info(f"Restored configuration from: {backup_name}")
        return backup_data["config"]
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata."""
        backups = []
        for backup_file in self.backup_dir.glob("config_backup_*.json"):
            try:
                backup_data = json.loads(backup_file.read_text())
                backups.append({
                    "filename": backup_file.name,
                    "metadata": backup_data["metadata"]
                })
            except Exception as e:
                logger.warning(f"Error reading backup {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x["metadata"]["timestamp"], reverse=True)
    
    def create_migration(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> str:
        """
        Create a migration record between configurations.
        
        Args:
            old_config: Previous configuration
            new_config: New configuration
            
        Returns:
            Migration filename
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        migration_file = self.migrations_dir / f"migration_{timestamp}.json"
        
        # Calculate changes
        changes = self._calculate_changes(old_config, new_config)
        
        migration_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "from_version": self.version_info["current_version"],
            "to_version": self._increment_version(self.version_info["current_version"]),
            "changes": changes,
            "checksums": {
                "old": self._calculate_checksum(old_config),
                "new": self._calculate_checksum(new_config)
            }
        }
        
        migration_file.write_text(json.dumps(migration_data, indent=2))
        
        # Update version info
        self.version_info["current_version"] = migration_data["to_version"]
        self.version_info["last_updated"] = migration_data["timestamp"]
        self.version_info["history"].append({
            "version": migration_data["to_version"],
            "timestamp": migration_data["timestamp"],
            "migration_file": migration_file.name
        })
        self._save_version_info(self.version_info)
        
        logger.info(f"Created migration: {migration_file.name}")
        return migration_file.name
    
    def _calculate_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes between configurations."""
        changes = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # Find added and modified
        for key, new_value in new_config.items():
            if key not in old_config:
                changes["added"][key] = new_value
            elif old_config[key] != new_value:
                changes["modified"][key] = {
                    "old": old_config[key],
                    "new": new_value
                }
        
        # Find removed
        for key in old_config:
            if key not in new_config:
                changes["removed"][key] = old_config[key]
        
        return changes
    
    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        major, minor, patch = map(int, version.split('.'))
        return f"{major}.{minor}.{patch + 1}"
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get full migration history."""
        return self.version_info["history"]