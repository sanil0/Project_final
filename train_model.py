"""Script to train the DDoS Detection Model using CICDDOS2019 dataset."""

import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.services.model_trainer import train_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # Define dataset paths
        dataset_dir = os.path.join('Datasets', 'CSV-01-12', '01-12')
        dataset_files = [
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
        
        dataset_paths = [os.path.join(dataset_dir, file) for file in dataset_files]
        
        # Verify files exist
        for path in dataset_paths:
            if not os.path.exists(path):
                logger.error(f"Dataset file not found: {path}")
                return
        
        logger.info("Starting model training...")
        model = train_model(dataset_paths)
        logger.info("Model training completed successfully")
        
        # You can save the model here if needed
        # import joblib
        # joblib.dump(model, 'ddos_detection_model.joblib')
        
    except Exception as e:
        logger.error(f"Error during model training: {str(e)}")
        raise

if __name__ == "__main__":
    main()