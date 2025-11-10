"""Prediction service with caching and batching support for ML models."""

import asyncio
import logging

logger = logging.getLogger(__name__)
import hashlib
import json
from functools import lru_cache
from typing import Dict, Optional, List, Any

from .ml_model import DDoSDetectionModel, SensitivityLevel

class PredictionService:
    """Service for caching and batching ML model predictions."""
    
    def __init__(
        self,
        model_path: str = "models",
        cache_size: int = 1000,
        batch_size: int = 32,
        batch_timeout: float = 0.1
    ):
        """Initialize the prediction service.
        
        Args:
            model_path: Path to saved model files
            cache_size: Size of LRU prediction cache
            batch_size: Maximum batch size for prediction
            batch_timeout: Maximum time to wait for batch completion
        """
        self.model = DDoSDetectionModel()  # Always use new model in test environment
        self._feature_store = {}
            
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout
        self._batch_queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
        self._cache_size = cache_size
        
    def _feature_hash(self, features: Dict[str, float]) -> str:
        """Generate a stable hash for feature dict to use as cache key."""
        # Sort keys to ensure stable hash
        feature_str = json.dumps(features, sort_keys=True)
        return hashlib.sha256(feature_str.encode()).hexdigest()
        
    @lru_cache(maxsize=1000)
    def _cached_predict(
        self,
        feature_hash: str,
        sensitivity_level: str
    ) -> Dict[str, Any]:
        """Make a prediction with caching based on feature hash."""
        # Reconstruct features from stored batch
        features = self._feature_store.get(feature_hash)
        if not features:
            raise KeyError(f"Features not found for hash {feature_hash}")
            
        return self.model.predict(features, sensitivity_level)
        
    async def predict(
        self,
        features: Dict[str, float],
        sensitivity_level: str = SensitivityLevel.MEDIUM
    ) -> Dict[str, Any]:
        """Get prediction for features, using cache if available."""
        # Try cache first
        feature_hash = self._feature_hash(features)
        try:
            return self._cached_predict(feature_hash, sensitivity_level)
        except KeyError:
            pass  # Cache miss
            
        # Store features for batch reconstruction
        self._feature_store[feature_hash] = features
        
        # Add to batch queue
        future = asyncio.get_event_loop().create_future()
        await self._batch_queue.put((feature_hash, sensitivity_level, future))
        
        # Start processing if not already running
        if not self._processing:
            asyncio.create_task(self._process_batch())
            
        try:
            # Wait for result with timeout
            result = await asyncio.wait_for(future, timeout=self._batch_timeout)
            return result
        except asyncio.TimeoutError:
            # Fallback to immediate prediction
            return self.model.predict(features, sensitivity_level)
            
    async def _process_batch(self):
        """Process batched predictions."""
        self._processing = True
        try:
            while True:
                batch = []
                try:
                    # Get first item
                    feature_hash, sensitivity_level, future = await self._batch_queue.get()
                    batch.append((feature_hash, sensitivity_level, future))
                    
                    # Try to fill batch
                    while len(batch) < self._batch_size:
                        try:
                            item = await asyncio.wait_for(
                                self._batch_queue.get(),
                                timeout=0.01  # Short timeout for batching
                            )
                            batch.append(item)
                        except asyncio.TimeoutError:
                            break  # No more immediate items
                            
                    # Process batch
                    for feature_hash, sensitivity_level, future in batch:
                        if not future.done():
                            try:
                                result = self._cached_predict(feature_hash, sensitivity_level)
                                future.set_result(result)
                            except Exception as e:
                                future.set_exception(e)
                                
                except asyncio.CancelledError:
                    break
                except Exception:
                    # Log error but continue processing
                    logger.exception("Error processing prediction batch")
                    
        finally:
            self._processing = False