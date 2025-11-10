"""Machine Learning Model for DDoS Detection."""

from __future__ import annotations

import logging
import numpy as np
import joblib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import GridSearchCV
import pandas as pd
import time

from .model_cache import ModelCache
from .model_monitoring import PerformanceMonitor

# Define sensitivity levels
class SensitivityLevel:
    LOW = "low"         # More permissive, fewer false positives
    MEDIUM = "medium"   # Balanced approach
    HIGH = "high"       # More strict, fewer false negatives

# Define threshold configurations for different sensitivity levels
SENSITIVITY_THRESHOLDS = {
    SensitivityLevel.LOW: {
        'confidence_threshold': 0.85,
        'risk_score_threshold': 85,
        'burst_multiplier': 1.5
    },
    SensitivityLevel.MEDIUM: {
        'confidence_threshold': 0.75,
        'risk_score_threshold': 75,
        'burst_multiplier': 1.0
    },
    SensitivityLevel.HIGH: {
        'confidence_threshold': 0.65,
        'risk_score_threshold': 65,
        'burst_multiplier': 0.75
    }
}

logger = logging.getLogger(__name__)

class DDoSDetectionModel:
    """ML-based DDoS Detection using Random Forest with caching and monitoring."""

    def __init__(self, sensitivity_level: str = SensitivityLevel.MEDIUM, 
                 enable_cache: bool = True, cache_size: int = 10000, cache_ttl: int = 300):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt'
        )
        self.scaler = RobustScaler()  # More robust to outliers
        self.sensitivity_level = sensitivity_level
        self.thresholds = SENSITIVITY_THRESHOLDS[sensitivity_level]
        
        # Initialize cache and monitoring
        self.cache = ModelCache(max_size=cache_size, ttl=cache_ttl) if enable_cache else None
        self.monitor = PerformanceMonitor()
        self.enable_cache = enable_cache
        
        # Base features from network flows
        self.feature_columns = [
            'Flow Duration',
            'Total Fwd Packets',
            'Total Backward Packets',
            'Total Length of Fwd Packets',
            'Total Length of Bwd Packets',
            'Fwd Packet Length Max',
            'Fwd Packet Length Min',
            'Flow IAT Mean',
            'Flow IAT Std',
            'Flow IAT Max',
            'Flow IAT Min',
            'Fwd IAT Mean',
            'Fwd IAT Std',
            'Fwd IAT Max',
            'Fwd IAT Min',
            'Flow Bytes/s',
            'Flow Packets/s',
            'PSH Flag Count',
            'Average Packet Size',
            'Packet Length Std'
        ]
        
        # Initialize scaler with default values to prevent NotFittedError
        self._initialize_scaler()

    def _initialize_scaler(self):
        """Initialize the scaler and model with default values to prevent NotFittedError."""
        try:
            # Create a small dummy dataset with both classes
            dummy_data = pd.DataFrame([
                [0.0] * len(self.feature_columns),  # Benign traffic
                [1.0] * len(self.feature_columns)   # Malicious traffic
            ], columns=self.feature_columns)
            dummy_labels = pd.Series([1, 0])  # 1=Benign, 0=Malicious
            
            # Fit scaler
            self.scaler.fit(dummy_data)
            
            # Fit model with dummy data
            X_scaled = self.scaler.transform(dummy_data)
            self.model.fit(X_scaled, dummy_labels)
            
            logger.debug("Scaler and model initialized with default values")
        except Exception as e:
            logger.warning(f"Failed to initialize scaler and model with defaults: {e}")
            # As a fallback, set minimal scaler state
            self.scaler.center_ = np.zeros(len(self.feature_columns))
            self.scaler.scale_ = np.ones(len(self.feature_columns))
            
            # Set minimal model state
            self.model.n_features_in_ = len(self.feature_columns)
            self.model.classes_ = np.array([0, 1])
            self.model.n_outputs_ = 1

    def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer additional features from the base features."""
        df = data.copy()
        
        # Clean up any existing engineered features to avoid duplicates
        base_columns = list(df.columns)
        for col in df.columns:
            if col not in self.feature_columns:
                df.drop(columns=[col], inplace=True)
        
        # Ensure all required base features exist
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        return df[self.feature_columns]

    def prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for prediction."""
        # Engineer additional features
        features = self.engineer_features(data)
        
        # Handle missing values with median for numeric columns
        numeric_features = features.select_dtypes(include=[np.number])
        features[numeric_features.columns] = features[numeric_features.columns].fillna(numeric_features.median())
        
        # Scale the features
        return self.scaler.transform(features)

    def evaluate_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Evaluate model performance using cross-validation.
        
        Args:
            X: Feature DataFrame
            y: Target labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        from sklearn.model_selection import cross_validate
        from sklearn.metrics import make_scorer, precision_score, recall_score, f1_score
        
        scoring = {
            'accuracy': 'accuracy',
            'precision': make_scorer(precision_score),
            'recall': make_scorer(recall_score),
            'f1': make_scorer(f1_score)
        }
        
        # Perform cross-validation
        cv_results = cross_validate(
            self.model, 
            self.scaler.transform(X),
            y,
            scoring=scoring,
            cv=5,
            n_jobs=-1,
            return_train_score=True
        )
        
        # Compute mean and std of metrics
        metrics = {}
        for metric in scoring.keys():
            metrics[f'test_{metric}'] = {
                'mean': float(cv_results[f'test_{metric}'].mean()),
                'std': float(cv_results[f'test_{metric}'].std())
            }
            metrics[f'train_{metric}'] = {
                'mean': float(cv_results[f'train_{metric}'].mean()),
                'std': float(cv_results[f'train_{metric}'].std())
            }
            
        return metrics

    def tune_hyperparameters(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """
        Tune model hyperparameters using grid search with cross-validation.
        
        Args:
            X_train: Training features
            y_train: Training labels
            
        Returns:
            Dictionary with tuning results
        """
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 15, 20],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2']
        }
        
        from sklearn.metrics import make_scorer, f1_score, precision_score, recall_score
        
        scoring = {
            'f1': make_scorer(f1_score),
            'precision': make_scorer(precision_score),
            'recall': make_scorer(recall_score)
        }
        
        grid_search = GridSearchCV(
            estimator=RandomForestClassifier(random_state=42, class_weight='balanced', n_jobs=-1),
            param_grid=param_grid,
            cv=5,
            n_jobs=-1,
            scoring=scoring,
            refit='f1',
            verbose=1,
            return_train_score=True
        )
        
        grid_search.fit(X_train, y_train)
        
        # Update model with best parameters
        self.model = RandomForestClassifier(
            **grid_search.best_params_,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        
        # Collect and return tuning results
        results = {
            'best_params': grid_search.best_params_,
            'best_score': float(grid_search.best_score_),
            'cv_results': {
                metric: {
                    'mean_test_score': float(grid_search.cv_results_[f'mean_test_{metric}'][grid_search.best_index_]),
                    'std_test_score': float(grid_search.cv_results_[f'std_test_{metric}'][grid_search.best_index_]),
                    'mean_train_score': float(grid_search.cv_results_[f'mean_train_{metric}'][grid_search.best_index_]),
                    'std_train_score': float(grid_search.cv_results_[f'std_train_{metric}'][grid_search.best_index_])
                }
                for metric in scoring.keys()
            }
        }
        
        logger.info(
            f"Hyperparameter tuning completed:\n"
            f"Best parameters: {results['best_params']}\n"
            f"Best F1 score: {results['best_score']:.4f}\n"
            f"Best precision: {results['cv_results']['precision']['mean_test_score']:.4f}\n"
            f"Best recall: {results['cv_results']['recall']['mean_test_score']:.4f}"
        )
        
        return results

    def validate_data(self, data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate input data before training.
        
        Args:
            data: Training data DataFrame
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if data is None or data.empty:
            return False, "Training data is empty"
            
        # Check for required columns
        missing_cols = [col for col in self.feature_columns if col not in data.columns]
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}"
            
        # Check for null values
        null_cols = data[self.feature_columns].columns[data[self.feature_columns].isnull().any()].tolist()
        if null_cols:
            return False, f"Null values found in columns: {', '.join(null_cols)}"
            
        # Check for invalid values
        numeric_cols = data[self.feature_columns].select_dtypes(include=[np.number]).columns
        invalid_cols = []
        for col in numeric_cols:
            if (data[col] < 0).any():
                invalid_cols.append(f"{col} (negative values)")
            if np.isinf(data[col]).any():
                invalid_cols.append(f"{col} (infinite values)")
                
        if invalid_cols:
            return False, f"Invalid values found in columns: {', '.join(invalid_cols)}"
            
        return True, ""

    def train(self, train_data: pd.DataFrame, batch_size: int = 10000) -> Dict[str, Any]:
        """
        Train the model on the given data with batching support.
        
        Args:
            train_data: Training DataFrame
            batch_size: Size of batches for processing large datasets
            
        Returns:
            Dictionary with training metrics
        """
        start_time = time.time()
        metrics = {'trained_samples': 0, 'training_time': 0.0}
        
        try:
            # Validate data
            is_valid, error_msg = self.validate_data(train_data)
            if not is_valid:
                raise ValueError(f"Invalid training data: {error_msg}")
            
            X = train_data[self.feature_columns]
            y = (train_data['Label'] == 'BENIGN').astype(int)
            
            # Fit scaler on full dataset
            logger.info("Fitting scaler...")
            self.scaler.fit(X)
            
            # Train model in batches if dataset is large
            if len(X) > batch_size:
                logger.info(f"Training on {len(X)} samples in batches of {batch_size}")
                
                # Initialize model with first batch
                first_batch = slice(0, batch_size)
                X_batch = self.scaler.transform(X.iloc[first_batch])
                y_batch = y.iloc[first_batch]
                self.model.fit(X_batch, y_batch)
                metrics['trained_samples'] += len(X_batch)
                
                # Continue training with remaining batches
                for start_idx in range(batch_size, len(X), batch_size):
                    end_idx = min(start_idx + batch_size, len(X))
                    batch = slice(start_idx, end_idx)
                    
                    X_batch = self.scaler.transform(X.iloc[batch])
                    y_batch = y.iloc[batch]
                    
                    # Warm start for incremental training
                    self.model.n_estimators += 50  # Add trees incrementally
                    self.model.warm_start = True
                    self.model.fit(X_batch, y_batch)
                    
                    metrics['trained_samples'] += len(X_batch)
                    logger.info(f"Trained on {metrics['trained_samples']} samples...")
                
            else:
                # Train on full dataset at once
                logger.info(f"Training on {len(X)} samples")
                X_scaled = self.scaler.transform(X)
                self.model.fit(X_scaled, y)
                metrics['trained_samples'] = len(X)
            
            metrics['training_time'] = time.time() - start_time
            logger.info(
                f"Model training completed in {metrics['training_time']:.2f} seconds. "
                f"Trained on {metrics['trained_samples']} samples."
            )
            
            # Clear cache after training
            if self.enable_cache:
                self.cache.clear()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error during model training: {str(e)}")
            raise

    def save_model(self, model_dir: str) -> None:
        """Save the trained model and scaler to disk."""
        try:
            model_path = Path(model_dir)
            model_path.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.model, model_path / "ddos_model.joblib")
            joblib.dump(self.scaler, model_path / "scaler.joblib")
            joblib.dump(self.feature_columns, model_path / "features.joblib")
            
            logger.info(f"Model saved to {model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    @classmethod
    def load_model(cls, model_dir: str) -> "DDoSDetectionModel":
        """Load a trained model from disk."""
        try:
            model_path = Path(model_dir)
            instance = cls()
            
            instance.model = joblib.load(model_path / "ddos_model.joblib")
            instance.scaler = joblib.load(model_path / "scaler.joblib")
            instance.feature_columns = joblib.load(model_path / "features.joblib")
            
            logger.info(f"Model loaded from {model_path}")
            return instance
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
            
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        try:
            importance = self.model.feature_importances_
            return dict(zip(self.feature_columns, importance))
        except Exception as e:
            logger.error(f"Error getting feature importance: {str(e)}")
            raise
    
    def predict(self, features: Union[Dict[str, float], pd.DataFrame], 
                sensitivity_level: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Predict whether traffic is benign or malicious with sensitivity threshold.
        
        Supports both single prediction and batch prediction modes.
        
        Args:
            features: Either a dictionary of features or a DataFrame for batch prediction
            sensitivity_level: Optional override for sensitivity level
            
        Returns:
            Single prediction dict or list of prediction dicts for batch mode
        """
        batch_mode = isinstance(features, pd.DataFrame)
        start_time = time.time()
        
        try:
            # For single prediction, check cache first
            if not batch_mode and self.enable_cache:
                cached_result = self.cache.get(features, sensitivity_level or self.sensitivity_level)
                if cached_result is not None:
                    self.monitor.record_prediction(cached_result, time.time() - start_time, cached=True)
                    return cached_result
            
            # Use provided sensitivity level or default to instance level
            thresholds = SENSITIVITY_THRESHOLDS[sensitivity_level or self.sensitivity_level]
            
            # Prepare features
            if batch_mode:
                feature_vector = self.engineer_features(features)
            else:
                feature_vector = self.engineer_features(pd.DataFrame([features]))
                
            # Scale features
            X = self.scaler.transform(feature_vector)
            
            # Get predictions and probabilities
            predictions = self.model.predict(X)
            probabilities = self.model.predict_proba(X)
            
            results = []
            for i in range(len(predictions)):
                confidence = float(max(probabilities[i]))
                risk_score = float(1 - probabilities[i][1]) * 100  # Convert to 0-100 scale
                
                # Apply sensitivity thresholds
                is_attack = (
                    confidence >= thresholds['confidence_threshold'] and
                    risk_score >= thresholds['risk_score_threshold']
                )
                
                # Get feature contributions and anomaly scores
                if batch_mode:
                    feature_contributions = self._get_feature_contributions(features.iloc[[i]])
                    anomaly_scores = self._calculate_anomaly_scores(features.iloc[[i]], feature_contributions)
                else:
                    df = pd.DataFrame([features])
                    feature_contributions = self._get_feature_contributions(df)
                    anomaly_scores = self._calculate_anomaly_scores(df, feature_contributions)
                    
                result = {
                    'is_benign': not is_attack,
                    'confidence': confidence,
                    'risk_score': risk_score,
                    'feature_contributions': feature_contributions,
                    'anomaly_scores': anomaly_scores,
                    'sensitivity_level': sensitivity_level or self.sensitivity_level,
                    'thresholds_applied': {
                        'confidence_threshold': thresholds['confidence_threshold'],
                        'risk_score_threshold': thresholds['risk_score_threshold']
                    }
                }
                
                results.append(result)
                
                # Cache single prediction results
                if not batch_mode and self.enable_cache:
                    self.cache.put(features, sensitivity_level or self.sensitivity_level, result)
            
            elapsed = time.time() - start_time
            self.monitor.record_prediction(results[0] if not batch_mode else results[-1], elapsed)
            
            return results[0] if not batch_mode else results
            
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            raise
            
    def _calculate_anomaly_scores(self, features: pd.DataFrame, contributions: Dict[str, float]) -> Dict[str, float]:
        """Calculate specific anomaly scores for different aspects of the traffic."""
        scores = {
            'volumetric_anomaly': 0.0,
            'timing_anomaly': 0.0,
            'protocol_anomaly': 0.0,
            'behavioral_anomaly': 0.0
        }
        
        # Volumetric anomalies
        if 'Flow Bytes/s' in features and 'Flow Packets/s' in features:
            scores['volumetric_anomaly'] = float(np.mean([
                contributions.get('Flow Bytes/s', 0),
                contributions.get('Flow Packets/s', 0),
                contributions.get('Total Length of Fwd Packets', 0)
            ]))
        
        # Timing anomalies
        timing_features = ['Flow IAT Mean', 'Flow IAT Std', 'Fwd IAT Mean', 'Fwd IAT Std']
        timing_contribs = [contributions.get(f, 0) for f in timing_features if f in features]
        if timing_contribs:
            scores['timing_anomaly'] = float(np.mean(timing_contribs))
        
        # Protocol anomalies
        protocol_features = ['PSH Flag Count', 'PSH_Ratio']
        protocol_contribs = [contributions.get(f, 0) for f in protocol_features if f in features]
        if protocol_contribs:
            scores['protocol_anomaly'] = float(np.mean(protocol_contribs))
        
        # Behavioral anomalies (based on packet patterns)
        if 'Packet_Ratio' in features and 'IAT_Variability' in features:
            scores['behavioral_anomaly'] = float(np.mean([
                contributions.get('Packet_Ratio', 0),
                contributions.get('IAT_Variability', 0)
            ]))
        
        return scores
            
    def _get_feature_contributions(self, features_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate how much each feature contributed to the prediction."""
        feature_importance = self.get_feature_importance()
        scaled_features = self.prepare_features(features_df)
        
        # Multiply normalized feature values by their importance
        contributions = {}
        for i, feature in enumerate(self.feature_columns):
            contributions[feature] = abs(float(scaled_features[0][i] * feature_importance[feature]))
            
        return contributions
