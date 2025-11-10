"""Test configuration migration functionality."""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
import shutil

from app.services.config_migration import ConfigMigration

@pytest.fixture
def test_config_dir(tmp_path):
    """Create a temporary configuration directory."""
    config_dir = tmp_path / "test_config"
    config_dir.mkdir()
    yield config_dir
    shutil.rmtree(config_dir)

@pytest.fixture
def migration_manager(test_config_dir):
    """Create a ConfigMigration instance."""
    return ConfigMigration(config_dir=str(test_config_dir))

def test_initialization(test_config_dir):
    """Test migration manager initialization."""
    manager = ConfigMigration(config_dir=str(test_config_dir))
    
    # Check directories created
    assert (test_config_dir / "config_backups").exists()
    assert (test_config_dir / "migrations").exists()
    assert (test_config_dir / "version.json").exists()
    
    # Check version info
    version_info = json.loads((test_config_dir / "version.json").read_text())
    assert version_info["current_version"] == "1.0.0"
    assert isinstance(version_info["history"], list)

def test_create_backup(migration_manager):
    """Test backup creation."""
    test_config = {
        "setting1": "value1",
        "setting2": 123
    }
    
    backup_name = migration_manager.create_backup(test_config, "test backup")
    
    # Check backup file exists
    backup_file = migration_manager.backup_dir / backup_name
    assert backup_file.exists()
    
    # Check backup content
    backup_data = json.loads(backup_file.read_text())
    assert backup_data["config"] == test_config
    assert "timestamp" in backup_data["metadata"]
    assert backup_data["metadata"]["reason"] == "test backup"

def test_restore_backup(migration_manager):
    """Test backup restoration."""
    test_config = {"test": "config"}
    
    # Create backup
    backup_name = migration_manager.create_backup(test_config)
    
    # Restore backup
    restored_config = migration_manager.restore_backup(backup_name)
    assert restored_config == test_config
    
    # Test restoring non-existent backup
    with pytest.raises(ValueError):
        migration_manager.restore_backup("nonexistent.json")

def test_create_migration(migration_manager):
    """Test migration creation."""
    old_config = {
        "setting1": "old",
        "setting2": 123,
        "to_remove": True
    }
    
    new_config = {
        "setting1": "new",
        "setting2": 123,
        "new_setting": "added"
    }
    
    migration_file = migration_manager.create_migration(old_config, new_config)
    
    # Check migration file exists
    migration_path = migration_manager.migrations_dir / migration_file
    assert migration_path.exists()
    
    # Check migration content
    migration_data = json.loads(migration_path.read_text())
    
    assert migration_data["changes"]["modified"]["setting1"] == {
        "old": "old",
        "new": "new"
    }
    assert migration_data["changes"]["added"]["new_setting"] == "added"
    assert migration_data["changes"]["removed"]["to_remove"] is True

def test_version_increment(migration_manager):
    """Test version incrementing."""
    old_config = {"version": "1.0"}
    new_config = {"version": "2.0"}
    
    migration_manager.create_migration(old_config, new_config)
    
    assert migration_manager.version_info["current_version"] == "1.0.1"
    
    # Create another migration
    migration_manager.create_migration(new_config, {"version": "3.0"})
    assert migration_manager.version_info["current_version"] == "1.0.2"

def test_list_backups(migration_manager):
    """Test listing backups."""
    # Clear any existing backups first
    import shutil
    for backup_file in migration_manager.backup_dir.glob("config_backup_*.json"):
        backup_file.unlink()
    
    # Create multiple backups with delays to ensure different timestamps
    configs = [
        {"test": "config1"},
        {"test": "config2"},
        {"test": "config3"}
    ]
    
    backup_names = []
    for config in configs:
        name = migration_manager.create_backup(config)
        backup_names.append(name)
        # Add a small delay to ensure different timestamps
        import time
        time.sleep(0.1)
    
    # Verify each backup file exists
    for name in backup_names:
        assert (migration_manager.backup_dir / name).exists()
    
    backups = migration_manager.list_backups()
    
    # Verify the number of backups matches what we created
    assert len(backups) == 3, f"Expected 3 backups, found {len(backups)}"
    assert all("filename" in backup for backup in backups)
    assert all("metadata" in backup for backup in backups)
    
    # Check ordering (most recent first)
    timestamps = [datetime.fromisoformat(b["metadata"]["timestamp"]) for b in backups]
    assert all(t1 >= t2 for t1, t2 in zip(timestamps[:-1], timestamps[1:]))

def test_migration_history(migration_manager):
    """Test migration history tracking."""
    configs = [
        {"version": "1.0"},
        {"version": "2.0"},
        {"version": "3.0"}
    ]
    
    # Create multiple migrations
    for i in range(len(configs) - 1):
        migration_manager.create_migration(configs[i], configs[i + 1])
    
    history = migration_manager.get_migration_history()
    
    assert len(history) == 2  # Two migrations created
    assert all("version" in entry for entry in history)
    assert all("timestamp" in entry for entry in history)
    assert all("migration_file" in entry for entry in history)