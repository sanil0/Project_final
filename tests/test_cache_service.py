"""
Tests for Redis Cache Service

Tests ensure:
- Cache works when Redis is available
- Cache gracefully degrades when Redis is unavailable
- Data serialization works correctly
- TTL management works
- No exceptions propagate to caller
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.cache import CacheService, CACHE_KEYS
import json


class TestCacheServiceWithRedis:
    """Tests for cache service when Redis is available."""

    @pytest.fixture
    def cache(self):
        """Create cache service for testing."""
        cache_svc = CacheService(enabled=True)
        cache_svc.redis_client = MagicMock()
        cache_svc.available = True
        return cache_svc

    def test_get_returns_value(self, cache):
        """Test getting a value from cache."""
        cache.redis_client.get.return_value = json.dumps({"score": 0.95})
        result = cache.get("test_key")
        assert result == {"score": 0.95}

    def test_get_returns_string_value(self, cache):
        """Test getting a string value from cache."""
        cache.redis_client.get.return_value = "simple_string"
        result = cache.get("test_key")
        assert result == "simple_string"

    def test_get_returns_none_when_not_found(self, cache):
        """Test getting a non-existent key."""
        cache.redis_client.get.return_value = None
        result = cache.get("nonexistent")
        assert result is None

    def test_set_stores_dict_value(self, cache):
        """Test setting a dict value."""
        result = cache.set("test_key", {"score": 0.95}, ttl=300)
        assert result is True
        cache.redis_client.setex.assert_called_once()

    def test_set_uses_default_ttl(self, cache):
        """Test that set uses default TTL."""
        cache.default_ttl = 600
        cache.set("test_key", "value")
        args = cache.redis_client.setex.call_args
        assert args[0][1] == 600  # TTL argument

    def test_set_uses_custom_ttl(self, cache):
        """Test that set uses custom TTL when provided."""
        cache.set("test_key", "value", ttl=120)
        args = cache.redis_client.setex.call_args
        assert args[0][1] == 120  # Custom TTL

    def test_delete_removes_key(self, cache):
        """Test deleting a key."""
        result = cache.delete("test_key")
        assert result is True
        cache.redis_client.delete.assert_called_once_with("test_key")

    def test_exists_checks_key(self, cache):
        """Test checking if key exists."""
        cache.redis_client.exists.return_value = 1
        result = cache.exists("test_key")
        assert result is True

    def test_exists_returns_false_when_not_found(self, cache):
        """Test exists returns false for non-existent key."""
        cache.redis_client.exists.return_value = 0
        result = cache.exists("test_key")
        assert result is False

    def test_increment_increases_counter(self, cache):
        """Test incrementing a counter."""
        cache.redis_client.incrby.return_value = 5
        result = cache.increment("counter", 1)
        assert result == 5

    def test_get_ttl_returns_remaining_time(self, cache):
        """Test getting TTL for a key."""
        cache.redis_client.ttl.return_value = 250
        result = cache.get_ttl("test_key")
        assert result == 250

    def test_clear_pattern_deletes_matching_keys(self, cache):
        """Test clearing keys by pattern."""
        cache.redis_client.keys.return_value = ["key1", "key2", "key3"]
        result = cache.clear_pattern("key:*")
        assert result == 3

    def test_clear_pattern_returns_zero_when_no_matches(self, cache):
        """Test clear pattern when no keys match."""
        cache.redis_client.keys.return_value = []
        result = cache.clear_pattern("nomatch:*")
        assert result == 0

    def test_health_check_returns_stats(self, cache):
        """Test health check when Redis is available."""
        cache.redis_client.info.return_value = {
            "used_memory_human": "2M",
            "connected_clients": 5,
            "total_commands_processed": 1000,
        }
        result = cache.health_check()
        assert result["available"] is True
        assert result["memory_used"] == "2M"


class TestCacheServiceWithoutRedis:
    """Tests for cache service when Redis is unavailable (graceful degradation)."""

    @pytest.fixture
    def cache(self):
        """Create cache service with Redis unavailable."""
        cache_svc = CacheService(enabled=True)
        cache_svc.redis_client = None
        cache_svc.available = False
        return cache_svc

    def test_get_returns_none_when_unavailable(self, cache):
        """Test that get returns None gracefully."""
        result = cache.get("test_key")
        assert result is None

    def test_set_returns_false_when_unavailable(self, cache):
        """Test that set returns False gracefully."""
        result = cache.set("test_key", "value")
        assert result is False

    def test_delete_returns_false_when_unavailable(self, cache):
        """Test that delete returns False gracefully."""
        result = cache.delete("test_key")
        assert result is False

    def test_exists_returns_false_when_unavailable(self, cache):
        """Test that exists returns False gracefully."""
        result = cache.exists("test_key")
        assert result is False

    def test_increment_returns_none_when_unavailable(self, cache):
        """Test that increment returns None gracefully."""
        result = cache.increment("counter")
        assert result is None

    def test_get_ttl_returns_none_when_unavailable(self, cache):
        """Test that get_ttl returns None gracefully."""
        result = cache.get_ttl("test_key")
        assert result is None

    def test_clear_pattern_returns_zero_when_unavailable(self, cache):
        """Test that clear_pattern returns 0 gracefully."""
        result = cache.clear_pattern("key:*")
        assert result == 0

    def test_health_check_shows_unavailable(self, cache):
        """Test health check when cache is unavailable."""
        result = cache.health_check()
        assert result["available"] is False


class TestCacheServiceDisabled:
    """Tests for cache service when disabled."""

    @pytest.fixture
    def cache(self):
        """Create cache service with caching disabled."""
        return CacheService(enabled=False)

    def test_disabled_cache_returns_none(self, cache):
        """Test that disabled cache returns None."""
        result = cache.get("test_key")
        assert result is None

    def test_disabled_cache_set_returns_false(self, cache):
        """Test that disabled cache set returns False."""
        result = cache.set("test_key", "value")
        assert result is False

    def test_disabled_cache_health_check(self, cache):
        """Test health check for disabled cache."""
        result = cache.health_check()
        assert result["enabled"] is False
        assert result["available"] is False


class TestCacheServiceEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def cache(self):
        """Create cache service for testing."""
        cache_svc = CacheService(enabled=True)
        cache_svc.redis_client = MagicMock()
        cache_svc.available = True
        return cache_svc

    def test_get_with_invalid_json(self, cache):
        """Test handling of invalid JSON."""
        cache.redis_client.get.return_value = "not json {invalid"
        result = cache.get("test_key")
        assert result == "not json {invalid"  # Returns as string

    def test_set_handles_connection_error(self, cache):
        """Test that set handles connection errors gracefully."""
        cache.redis_client.setex.side_effect = Exception("Connection error")
        result = cache.set("test_key", "value")
        assert result is False

    def test_get_handles_connection_error(self, cache):
        """Test that get handles connection errors gracefully."""
        cache.redis_client.get.side_effect = Exception("Connection error")
        result = cache.get("test_key")
        assert result is None

    def test_delete_handles_connection_error(self, cache):
        """Test that delete handles connection errors gracefully."""
        cache.redis_client.delete.side_effect = Exception("Connection error")
        result = cache.delete("test_key")
        assert result is False

    def test_increment_with_non_numeric_value(self, cache):
        """Test increment handles non-numeric values."""
        cache.redis_client.incrby.side_effect = Exception("Invalid increment")
        result = cache.increment("counter")
        assert result is None

    def test_cache_keys_constants(self):
        """Test that cache key constants are properly defined."""
        assert "ML_INFERENCE" in CACHE_KEYS
        assert "IP_REPUTATION" in CACHE_KEYS
        assert "REQUEST_COUNT" in CACHE_KEYS
        assert "{ip}" in CACHE_KEYS["ML_INFERENCE"]


class TestCacheServiceIntegration:
    """Integration-style tests."""

    @pytest.fixture
    def cache(self):
        """Create cache service for testing."""
        cache_svc = CacheService(enabled=True, default_ttl=300)
        cache_svc.redis_client = MagicMock()
        cache_svc.available = True
        return cache_svc

    def test_workflow_set_get_delete(self, cache):
        """Test typical workflow: set, get, delete."""
        # Set value
        result = cache.set("user:123", {"name": "John"}, ttl=600)
        assert result is True

        # Get value
        cache.redis_client.get.return_value = json.dumps({"name": "John"})
        result = cache.get("user:123")
        assert result == {"name": "John"}

        # Delete value
        result = cache.delete("user:123")
        assert result is True

    def test_multiple_operations_succeed(self, cache):
        """Test multiple cache operations in sequence."""
        # Set multiple values
        for i in range(5):
            result = cache.set(f"key:{i}", f"value:{i}")
            assert result is True

        # Get multiple values
        cache.redis_client.get.side_effect = [
            f"value:{i}" for i in range(5)
        ]
        for i in range(5):
            result = cache.get(f"key:{i}")
            assert result == f"value:{i}"

        # Clear by pattern
        cache.redis_client.keys.return_value = [f"key:{i}" for i in range(5)]
        result = cache.clear_pattern("key:*")
        assert result == 5
