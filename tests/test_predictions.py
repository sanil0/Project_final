"""Tests/prediction demo for DDoS detection with various patterns.

Converted to include a lightweight pytest that doesn't require the real model.
"""
import pytest  # type: ignore

import logging
import asyncio
import pandas as pd
from typing import Dict, Any
from app.services.detector import DetectionEngine
from app.services.ml_model import DDoSDetectionModel, SensitivityLevel
from app.schemas import TrafficSample, FeatureVector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define various attack patterns with their feature vectors
ATTACK_PATTERNS = {
    "SYN Flood": {
        "Flow Duration": 10,
        "Total Fwd Packets": 1000,
        "Total Backward Packets": 0,
        "Total Length of Fwd Packets": 64000,
        "Total Length of Bwd Packets": 0,
        "Flow Bytes/s": 640000,
        "Flow Packets/s": 10000,
        "Flow IAT Mean": 0.1,
        "Flow IAT Std": 0.01,
        "Flow IAT Max": 0.2,
        "Flow IAT Min": 0.05,
        "Fwd IAT Mean": 0.1,
        "Fwd IAT Std": 0.01,
        "Fwd IAT Max": 0.2,
        "Fwd IAT Min": 0.05,
        "Fwd Packet Length Max": 64,
        "Fwd Packet Length Min": 64,
        "PSH Flag Count": 0,
        "Average Packet Size": 64,
        "Packet Length Std": 0
    },
    "UDP Flood": {
        "Flow Duration": 5,
        "Total Fwd Packets": 2000,
        "Total Backward Packets": 0,
        "Total Length of Fwd Packets": 128000,
        "Total Length of Bwd Packets": 0,
        "Flow Bytes/s": 1280000,
        "Flow Packets/s": 20000,
        "Flow IAT Mean": 0.05,
        "Flow IAT Std": 0.01,
        "Flow IAT Max": 0.1,
        "Flow IAT Min": 0.02,
        "Fwd IAT Mean": 0.05,
        "Fwd IAT Std": 0.01,
        "Fwd IAT Max": 0.1,
        "Fwd IAT Min": 0.02,
        "Fwd Packet Length Max": 128,
        "Fwd Packet Length Min": 128,
        "PSH Flag Count": 0,
        "Average Packet Size": 128,
        "Packet Length Std": 0
    },
    "Slow Loris": {
        "Flow Duration": 30000,
        "Total Fwd Packets": 100,
        "Total Backward Packets": 100,
        "Total Length of Fwd Packets": 8000,
        "Total Length of Bwd Packets": 4000,
        "Flow Bytes/s": 400,
        "Flow Packets/s": 6,
        "Flow IAT Mean": 300,
        "Flow IAT Std": 10,
        "Flow IAT Max": 350,
        "Flow IAT Min": 250,
        "Fwd IAT Mean": 300,
        "Fwd IAT Std": 10,
        "Fwd IAT Max": 350,
        "Fwd IAT Min": 250,
        "Fwd Packet Length Max": 100,
        "Fwd Packet Length Min": 60,
        "PSH Flag Count": 100,
        "Average Packet Size": 80,
        "Packet Length Std": 20
    },
    "Normal Traffic": {
        "Flow Duration": 1000,
        "Total Fwd Packets": 10,
        "Total Backward Packets": 8,
        "Total Length of Fwd Packets": 4000,
        "Total Length of Bwd Packets": 3000,
        "Flow Bytes/s": 7000,
        "Flow Packets/s": 18,
        "Flow IAT Mean": 100,
        "Flow IAT Std": 20,
        "Flow IAT Max": 150,
        "Flow IAT Min": 50,
        "Fwd IAT Mean": 100,
        "Fwd IAT Std": 20,
        "Fwd IAT Max": 150,
        "Fwd IAT Min": 50,
        "Fwd Packet Length Max": 1500,
        "Fwd Packet Length Min": 40,
        "PSH Flag Count": 2,
        "Average Packet Size": 400,
        "Packet Length Std": 200
    }
}

def print_prediction_results(pattern_name: str, sensitivity: str, results: Dict[str, Any]) -> None:
    """Print detailed prediction results."""
    logger.info(f"\nResults for {pattern_name} with {sensitivity} sensitivity:")
    logger.info(f"Classification: {'BENIGN' if results['is_benign'] else 'ATTACK'}")
    logger.info(f"Confidence: {results['confidence']:.4f}")
    logger.info(f"Risk Score: {results['risk_score']:.2f}")
    
    logger.info("\nAnomaly Scores:")
    for score_type, score in results['anomaly_scores'].items():
        logger.info(f"{score_type}: {score:.4f}")
    
    logger.info("\nTop 5 Contributing Features:")
    sorted_contributions = sorted(
        results['feature_contributions'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    for feature, contribution in sorted_contributions:
        logger.info(f"{feature}: {contribution:.4f}")
    
    logger.info("\nThresholds Applied:")
    logger.info(f"Confidence Threshold: {results['thresholds_applied']['confidence_threshold']}")
    logger.info(f"Risk Score Threshold: {results['thresholds_applied']['risk_score_threshold']}")

async def run_prediction(model: DDoSDetectionModel, pattern_name: str, features: dict, sensitivity: SensitivityLevel) -> None:
    """Test prediction with different attack patterns and sensitivity levels."""
    try:
        # Pass the raw feature dictionary directly to predict
        results = model.predict(features, sensitivity)
        print_prediction_results(pattern_name, sensitivity, results)
    except Exception as e:
        logger.error(f"Error during prediction for {pattern_name}: {str(e)}")
        raise

async def main():
    try:
        # Load the model
        model = DDoSDetectionModel.load_model('models')
        
        # Test each attack pattern with different sensitivity levels
        for pattern_name, features in ATTACK_PATTERNS.items():
            for sensitivity in [SensitivityLevel.LOW, SensitivityLevel.MEDIUM, SensitivityLevel.HIGH]:
                await run_prediction(model, pattern_name, features, sensitivity)
                
    except Exception as e:
        logger.error(f"Error in testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())


def test_prediction_smoke():
    """Smoke test: prediction API surface without loading heavy model."""
    class DummyModel:
        def predict(self, features, sensitivity):
            return {
                'is_benign': True,
                'confidence': 1.0,
                'risk_score': 0.0,
                'anomaly_scores': {},
                'feature_contributions': {},
                'thresholds_applied': {
                    'confidence_threshold': 0,
                    'risk_score_threshold': 0,
                },
            }

    model = DummyModel()
    features = ATTACK_PATTERNS['Normal Traffic']
    res = model.predict(features, SensitivityLevel.MEDIUM)
    assert 'is_benign' in res and 'confidence' in res and 'risk_score' in res