"""Model caching implementation for DDoS detection."""

from typing import Any, Dict, Optional
import time

class ModelCache:
    """Cache for model predictions to reduce redundant computations."""
    
    def __init__(self, max_size: int = 10000, ttl: int = 300):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of items to store in cache
            ttl: Time-to-live in seconds for cache entries
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl

    def _generate_key(self, features: Dict[str, float], sensitivity_level: str) -> str:
        """Generate a cache key from features and sensitivity level."""
        # Sort features to ensure consistent key generation
        feature_str = ','.join(f"{k}:{v}" for k, v in sorted(features.items()))
        return f"{feature_str}:{sensitivity_level}"

    def get(self, features: Dict[str, float], sensitivity_level: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached prediction if it exists and is still valid.
        
        Args:
            features: Feature dictionary
            sensitivity_level: Current sensitivity level
            
        Returns:
            Cached prediction or None if not found/expired
        """
        key = self._generate_key(features, sensitivity_level)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < self._ttl:
                return entry['prediction']
            else:
                del self._cache[key]
        return None

    def put(self, features: Dict[str, float], sensitivity_level: str, prediction: Dict[str, Any]) -> None:
        """
        Cache a prediction result.
        
        Args:
            features: Feature dictionary
            sensitivity_level: Current sensitivity level
            prediction: Prediction result to cache
        """
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]

        key = self._generate_key(features, sensitivity_level)
        self._cache[key] = {
            'timestamp': time.time(),
            'prediction': prediction
        }

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()