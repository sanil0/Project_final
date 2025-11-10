"""Script to run all DDoS detection model components."""

import logging
import os
import asyncio
from app.services.model_trainer import train_model
from app.services.ml_model import DDoSDetectionModel
from app.schemas import TrafficSample, FeatureVector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_real_time_prediction(model: DDoSDetectionModel) -> None:
    """Test real-time prediction capabilities."""
    test_cases = [
        {
            "name": "Normal Traffic",
            "features": {
                "Flow Duration": 100,
                "Total Fwd Packets": 5,
                "Total Backward Packets": 3,
                "Total Length of Fwd Packets": 1000,
                "Total Length of Bwd Packets": 500,
                "Flow Bytes/s": 1000,
                "Flow Packets/s": 10,
                "Flow IAT Mean": 20,
                "Flow IAT Std": 5,
                "Flow IAT Max": 30,
                "Flow IAT Min": 10,
                "Fwd IAT Mean": 15,
                "Fwd IAT Std": 3,
                "Fwd IAT Max": 25,
                "Fwd IAT Min": 5,
                "Fwd Packet Length Max": 200,
                "Fwd Packet Length Min": 40,
                "PSH Flag Count": 0,
                "Average Packet Size": 100,
                "Packet Length Std": 20
            }
        },
        {
            "name": "DDoS Attack Traffic",
            "features": {
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
                "PSH Flag Count": 1000,
                "Average Packet Size": 64,
                "Packet Length Std": 0
            }
        }
    ]
    
    for test_case in test_cases:
        logger.info(f"\nTesting {test_case['name']}:")
        result = model.predict(test_case['features'])
        logger.info(f"Prediction: {'Benign' if result['is_benign'] else 'Attack'}")
        logger.info(f"Confidence: {result['confidence']:.4f}")
        logger.info(f"Risk Score: {result['risk_score']:.2f}")
        
        logger.info("\nTop 5 Contributing Features:")
        sorted_contributions = sorted(
            result['feature_contributions'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for feature, contribution in sorted_contributions:
            logger.info(f"{feature}: {contribution:.4f}")

async def main():
    try:
        # Step 1: Train and save the model
        logger.info("Step 1: Training model...")
        dataset_dir = os.path.join('Datasets', 'CSV-01-12', '01-12')
        dataset_files = [
            os.path.join(dataset_dir, file) for file in [
                'DrDoS_DNS.csv',
                'DrDoS_LDAP.csv',
                'DrDoS_MSSQL.csv',
                'DrDoS_NetBIOS.csv',
                'DrDoS_NTP.csv',
                'DrDoS_SNMP.csv',
                'DrDoS_SSDP.csv',
                'DrDoS_UDP.csv',
                'Syn.csv',
                'TFTP.csv',
                'UDPLag.csv'
            ]
        ]
        
        model = train_model(dataset_files)
        model.save_model('models')
        
        # Step 2: Load the saved model
        logger.info("\nStep 2: Loading saved model...")
        loaded_model = DDoSDetectionModel.load_model('models')
        
        # Step 3: Show feature importance
        logger.info("\nStep 3: Feature Importance Analysis:")
        importance = loaded_model.get_feature_importance()
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        for feature, score in sorted_importance:
            logger.info(f"{feature}: {score:.4f}")
        
        # Step 4: Test real-time predictions
        logger.info("\nStep 4: Testing real-time predictions...")
        await test_real_time_prediction(loaded_model)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())