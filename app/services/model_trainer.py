"""Training pipeline for DDoS Detection Model."""

from __future__ import annotations

import logging
import pandas as pd
from pathlib import Path
from typing import List
import numpy as np
from sklearn.model_selection import train_test_split
from .ml_model import DDoSDetectionModel

logger = logging.getLogger(__name__)

def load_and_preprocess_data(data_path: str, sample_size: int = None) -> pd.DataFrame:
    """Load and preprocess the CICDDOS2019 dataset."""
    try:
        # Read CSV file in chunks
        chunk_size = 100000  # Adjust this based on your available memory
        chunks = []
        
        for chunk in pd.read_csv(data_path, chunksize=chunk_size, low_memory=False):
            # Sample from chunk if needed
            if sample_size:
                chunk = chunk.sample(n=min(sample_size // 10, len(chunk)), random_state=42)
            
            # Drop rows with missing values
            chunk = chunk.dropna()
            
            # Remove infinite values
            chunk = chunk.replace([np.inf, -np.inf], np.nan).dropna()
            
            chunks.append(chunk)
            
            # Break if we have enough samples
            if sample_size and sum(len(c) for c in chunks) >= sample_size:
                break
        
        # Combine all chunks
        df = pd.concat(chunks, ignore_index=True)
        
        # Final sampling if needed
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            
        return df
        
    except Exception as e:
        logger.error(f"Error loading data from {data_path}: {str(e)}")
        raise

def train_model(dataset_paths: List[str], output_path: str = None, samples_per_file: int = 50000) -> DDoSDetectionModel:
    """Train the DDoS detection model on multiple dataset files."""
    try:
        # Initialize model
        model = DDoSDetectionModel()
        
        # Load and combine datasets
        all_data = []
        for path in dataset_paths:
            logger.info(f"Loading dataset from {path}")
            try:
                data = load_and_preprocess_data(path, sample_size=samples_per_file)
                all_data.append(data)
                logger.info(f"Successfully loaded {len(data)} samples from {path}")
            except Exception as e:
                logger.error(f"Error processing {path}: {str(e)}")
                continue
        
        combined_data = pd.concat(all_data, ignore_index=True)
        logger.info(f"Total samples: {len(combined_data)}")
        
        # Clean column names
        combined_data.columns = [col.strip() for col in combined_data.columns]
        
        # Split data
        train_data, test_data = train_test_split(
            combined_data, 
            test_size=0.2, 
            random_state=42,
            stratify=combined_data['Label']
        )
        
        # Train model
        logger.info("Starting model training...")
        model.train(train_data)
        
        # Evaluate model
        X_test = test_data[model.feature_columns]
        y_test = (test_data['Label'] == 'BENIGN').astype(int)
        X_test_scaled = model.scaler.transform(X_test)
        accuracy = model.model.score(X_test_scaled, y_test)
        logger.info(f"Model accuracy on test set: {accuracy:.4f}")
        
        return model
        
    except Exception as e:
        logger.error(f"Error during model training: {str(e)}")
        raise