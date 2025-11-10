"""Performance monitoring for the ML model."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelMetrics:
    """Container for model performance metrics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_prediction_time: float = 0.0
    num_errors: int = 0
    detection_rates: Dict[str, float] = None
    latency_percentiles: Dict[str, float] = None
    
    def __post_init__(self):
        self.detection_rates = {'benign': 0.0, 'malicious': 0.0}
        self.latency_percentiles = {'p50': 0.0, 'p95': 0.0, 'p99': 0.0}

class PerformanceMonitor:
    """Monitor and track model performance metrics."""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize the monitor.
        
        Args:
            window_size: Number of predictions to keep in rolling window
        """
        self._window_size = window_size
        self._metrics = ModelMetrics()
        self._prediction_times: List[float] = []
        self._predictions: List[Dict] = []
        
    def record_prediction(self, prediction: Dict, latency: float, cached: bool = False) -> None:
        """
        Record a new prediction event.
        
        Args:
            prediction: The prediction result dictionary
            latency: Time taken for prediction in seconds
            cached: Whether the result was from cache
        """
        self._metrics.total_requests += 1
        
        if cached:
            self._metrics.cache_hits += 1
        else:
            self._metrics.cache_misses += 1
            
        # Update rolling windows
        self._prediction_times.append(latency)
        self._predictions.append(prediction)
        
        # Maintain window size
        if len(self._prediction_times) > self._window_size:
            self._prediction_times.pop(0)
            self._predictions.pop(0)
            
        # Update metrics
        self._update_metrics()
        
    def record_error(self) -> None:
        """Record a prediction error."""
        self._metrics.num_errors += 1
        
    def get_metrics(self) -> ModelMetrics:
        """Get current performance metrics."""
        return self._metrics
        
    def _update_metrics(self) -> None:
        """Update all rolling metrics."""
        if not self._prediction_times:
            return
            
        # Update latency metrics
        times = np.array(self._prediction_times)
        self._metrics.avg_prediction_time = float(np.mean(times))
        self._metrics.latency_percentiles = {
            'p50': float(np.percentile(times, 50)),
            'p95': float(np.percentile(times, 95)),
            'p99': float(np.percentile(times, 99))
        }
        
        # Update detection rates
        if self._predictions:
            benign_count = sum(1 for p in self._predictions if p.get('is_benign', False))
            total = len(self._predictions)
            self._metrics.detection_rates = {
                'benign': benign_count / total,
                'malicious': (total - benign_count) / total
            }
            
    def log_metrics(self) -> None:
        """Log current metrics."""
        metrics = self.get_metrics()
        logger.info(
            "Model Performance Metrics:\n"
            f"Total Requests: {metrics.total_requests}\n"
            f"Cache Hit Rate: {metrics.cache_hits/(metrics.total_requests or 1):.2%}\n"
            f"Avg Prediction Time: {metrics.avg_prediction_time*1000:.2f}ms\n"
            f"P95 Latency: {metrics.latency_percentiles['p95']*1000:.2f}ms\n"
            f"Error Rate: {metrics.num_errors/(metrics.total_requests or 1):.2%}\n"
            f"Detection Rates: Benign={metrics.detection_rates['benign']:.2%}, "
            f"Malicious={metrics.detection_rates['malicious']:.2%}"
        )