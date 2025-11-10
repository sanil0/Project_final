"""Script to evaluate model performance on specific attack types."""

import logging
import os
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from app.services.ml_model import DDoSDetectionModel
from app.services.model_trainer import load_and_preprocess_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def evaluate_model_performance(model_dir: str, test_files: dict) -> None:
    """Evaluate model performance on different attack types."""
    try:
        # Load the trained model
        model = DDoSDetectionModel.load_model(model_dir)
        
        # Evaluate each attack type
        for attack_type, file_path in test_files.items():
            logger.info(f"\nEvaluating {attack_type} attack type:")
            
            # Load test data
            test_data = load_and_preprocess_data(file_path, sample_size=10000)
            
            # Prepare features
            X = test_data[model.feature_columns]
            y_true = (test_data['Label'].str.strip() == 'BENIGN').astype(int)
            
            # Make predictions
            X_scaled = model.scaler.transform(X)
            y_pred = model.model.predict(X_scaled)
            
            # Calculate metrics
            logger.info("\nClassification Report:")
            logger.info(classification_report(y_true, y_pred, target_names=['Attack', 'Benign']))
            
            # Calculate confusion matrix
            cm = confusion_matrix(y_true, y_pred)
            logger.info("\nConfusion Matrix:")
            logger.info("              Predicted Attack  Predicted Benign")
            logger.info(f"Actual Attack      {cm[0][0]}              {cm[0][1]}")
            logger.info(f"Actual Benign      {cm[1][0]}              {cm[1][1]}")
            
            # Calculate feature importance for this attack type
            importance = model.get_feature_importance()
            sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            
            logger.info(f"\nTop 10 important features for {attack_type}:")
            for feature, score in sorted_importance[:10]:
                logger.info(f"{feature}: {score:.4f}")
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        raise

def main():
    model_dir = "models"
    
    # Define test files for different attack types
    test_files = {
        "DNS_DDoS": "Datasets/CSV-01-12/01-12/DrDoS_DNS.csv",
        "LDAP_DDoS": "Datasets/CSV-01-12/01-12/DrDoS_LDAP.csv",
        "Syn_Flood": "Datasets/CSV-01-12/01-12/Syn.csv",
        "UDP_Lag": "Datasets/CSV-01-12/01-12/UDPLag.csv"
    }
    
    evaluate_model_performance(model_dir, test_files)

if __name__ == "__main__":
    main()