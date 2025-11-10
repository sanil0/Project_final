"""Feature mapping service for consistent feature construction."""

from typing import Dict
import numpy as np
from dataclasses import dataclass

@dataclass
class FeatureMapping:
    """Mapping of input traffic data to model features."""
    
    REQUIRED_FEATURES = {
        'Flow Duration',
        'Total Fwd Packets',
        'Total Backward Packets',
        'Total Length of Fwd Packets',
        'Total Length of Bwd Packets',
        'Flow Bytes/s',
        'Flow Packets/s',
        'Flow IAT Mean',
        'Flow IAT Std',
        'Flow IAT Max',
        'Flow IAT Min',
        'Fwd IAT Mean',
        'Fwd IAT Std',
        'Fwd IAT Max',
        'Fwd IAT Min',
        'Fwd Packet Length Max',
        'Fwd Packet Length Min',
        'PSH Flag Count',
        'Average Packet Size',
        'Packet Length Std'
    }
    
    @staticmethod
    def compute_features(
        window_size: float,
        request_timestamps: list[float],
        request_bytes: list[tuple[float, int]],
        current_time: float
    ) -> Dict[str, float]:
        """Compute unified feature vector from raw traffic data."""
        # Filter to window
        window_start = current_time - window_size
        timestamps = [t for t in request_timestamps if t > window_start]
        bytes_data = [(t, b) for t, b in request_bytes if t > window_start]
        
        # Base features
        features = {
            'Flow Duration': window_size,
            'Total Fwd Packets': len(timestamps),
            'Total Backward Packets': 0,  # Will be updated with response
            'Total Length of Fwd Packets': sum(b for _, b in bytes_data),
            'Total Length of Bwd Packets': 0,  # Will be updated with response
            'Flow Bytes/s': sum(b for _, b in bytes_data) / window_size,
            'Flow Packets/s': len(timestamps) / window_size
        }
        
        # IAT features
        if len(timestamps) > 1:
            iats = np.diff(sorted(timestamps))
            iat_features = {
                'Flow IAT Mean': float(np.mean(iats)),
                'Flow IAT Std': float(np.std(iats)),
                'Flow IAT Max': float(np.max(iats)),
                'Flow IAT Min': float(np.min(iats)),
                'Fwd IAT Mean': float(np.mean(iats)),
                'Fwd IAT Std': float(np.std(iats)),
                'Fwd IAT Max': float(np.max(iats)),
                'Fwd IAT Min': float(np.min(iats))
            }
        else:
            iat_features = {
                'Flow IAT Mean': 0.0,
                'Flow IAT Std': 0.0,
                'Flow IAT Max': 0.0,
                'Flow IAT Min': 0.0,
                'Fwd IAT Mean': 0.0,
                'Fwd IAT Std': 0.0,
                'Fwd IAT Max': 0.0,
                'Fwd IAT Min': 0.0
            }
        features.update(iat_features)
        
        # Packet features
        if bytes_data:
            packet_bytes = [b for _, b in bytes_data]
            features.update({
                'Fwd Packet Length Max': float(max(packet_bytes)),
                'Fwd Packet Length Min': float(min(packet_bytes)),
                'PSH Flag Count': 0,  # Not applicable for HTTP/HTTPS
                'Average Packet Size': float(np.mean(packet_bytes)),
                'Packet Length Std': float(np.std(packet_bytes))
            })
        else:
            features.update({
                'Fwd Packet Length Max': 0.0,
                'Fwd Packet Length Min': 0.0,
                'PSH Flag Count': 0,
                'Average Packet Size': 0.0,
                'Packet Length Std': 0.0
            })
            
        return features
        
    @staticmethod
    def validate_features(features: Dict[str, float]) -> bool:
        """Validate that all required features are present with correct types."""
        return all(
            feature in features and isinstance(features[feature], (int, float))
            for feature in FeatureMapping.REQUIRED_FEATURES
        )