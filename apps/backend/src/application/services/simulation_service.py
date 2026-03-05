"""
Simulation Service
Executes ML models on datasets and calculates fairness metrics
"""

import asyncio
import logging
import uuid
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, r2_score, classification_report
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import tempfile
import os
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SimulationConfig(BaseModel):
    """Configuration for ML simulation"""
    model_type: str  # 'classification' or 'regression'
    algorithm: str   # 'random_forest', 'logistic_regression', 'linear_regression'
    target_column: str
    feature_columns: List[str]
    protected_attributes: List[str]
    test_size: float = 0.2
    random_state: int = 42
    hyperparameters: Optional[Dict[str, Any]] = None

class SimulationResult(BaseModel):
    """Results from ML simulation"""
    simulation_id: str
    dataset_id: str
    config: SimulationConfig
    performance_metrics: Dict[str, Any]
    fairness_metrics: Dict[str, Any]
    model_path: Optional[str] = None
    execution_time_ms: int
    status: str
    created_at: datetime
    error_message: Optional[str] = None

class SimulationService:
    """Service for executing ML simulations and calculating fairness metrics"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.results_dir = Path("simulation_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Available algorithms
        self.classification_algorithms = {
            'random_forest': RandomForestClassifier,
            'logistic_regression': LogisticRegression
        }
        
        self.regression_algorithms = {
            'random_forest': RandomForestRegressor,
            'linear_regression': LinearRegression
        }
        
        # Hyperparameter defaults
        self.default_hyperparameters = {
            'random_forest': {'n_estimators': 100, 'random_state': 42},
            'logistic_regression': {'random_state': 42, 'max_iter': 1000},
            'linear_regression': {}
        }
    
    async def run_simulation(
        self,
        dataset_path: str,
        config: SimulationConfig,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run ML simulation on dataset
        
        Args:
            dataset_path: Path to dataset file
            config: Simulation configuration
            user_id: Optional user ID for tracking
            
        Returns:
            Simulation results with performance and fairness metrics
        """
        simulation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            logger.info(f"Starting simulation {simulation_id} with config: {config}")
            
            # Load and prepare dataset
            df = await self._load_dataset(dataset_path)
            
            # Validate configuration
            await self._validate_config(df, config)
            
            # Prepare data
            X, y, protected_groups = await self._prepare_data(df, config)
            
            # Split data
            X_train, X_test, y_train, y_test, protected_train, protected_test = await self._split_data(
                X, y, protected_groups, config.test_size, config.random_state
            )
            
            # Train model
            model = await self._train_model(X_train, y_train, config)
            
            # Make predictions
            y_pred = await self._make_predictions(model, X_test)
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(
                y_test, y_pred, config.model_type
            )
            
            # Calculate fairness metrics
            fairness_metrics = await self._calculate_fairness_metrics(
                y_test, y_pred, protected_test, config
            )
            
            # Save model
            model_path = await self._save_model(model, simulation_id)
            
            # Calculate execution time
            execution_time = int((time.time() - start_time) * 1000)
            
            # Create results
            results = SimulationResult(
                simulation_id=simulation_id,
                dataset_id=Path(dataset_path).stem,
                config=config,
                performance_metrics=performance_metrics,
                fairness_metrics=fairness_metrics,
                model_path=model_path,
                execution_time_ms=execution_time,
                status="completed",
                created_at=datetime.now()
            )
            
            # Save results
            await self._save_results(results)
            
            logger.info(f"Simulation {simulation_id} completed successfully in {execution_time}ms")
            
            return {
                "success": True,
                "simulation_id": simulation_id,
                "results": results.dict(),
                "message": "Simulation completed successfully"
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_message = str(e)
            
            logger.error(f"Simulation {simulation_id} failed: {error_message}")
            
            # Create error result
            error_results = SimulationResult(
                simulation_id=simulation_id,
                dataset_id=Path(dataset_path).stem if 'dataset_path' in locals() else "unknown",
                config=config,
                performance_metrics={},
                fairness_metrics={},
                execution_time_ms=execution_time,
                status="failed",
                created_at=datetime.now(),
                error_message=error_message
            )
            
            await self._save_results(error_results)
            
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": error_message,
                "execution_time_ms": execution_time
            }
    
    async def _load_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Load dataset from file"""
        try:
            file_path = Path(dataset_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
            
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            logger.info(f"Loaded dataset with shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    async def _validate_config(self, df: pd.DataFrame, config: SimulationConfig) -> None:
        """Validate simulation configuration against dataset"""
        # Check if columns exist
        all_columns = set(df.columns)
        
        if config.target_column not in all_columns:
            raise ValueError(f"Target column '{config.target_column}' not found in dataset")
        
        missing_features = [col for col in config.feature_columns if col not in all_columns]
        if missing_features:
            raise ValueError(f"Feature columns not found: {missing_features}")
        
        missing_protected = [col for col in config.protected_attributes if col not in all_columns]
        if missing_protected:
            raise ValueError(f"Protected attribute columns not found: {missing_protected}")
        
        # Check for conflicts
        if config.target_column in config.feature_columns:
            raise ValueError("Target column cannot be in feature columns")
        
        if config.target_column in config.protected_attributes:
            raise ValueError("Target column cannot be in protected attributes")
        
        # Check data types
        target_data = df[config.target_column]
        if config.model_type == 'classification':
            if target_data.dtype in ['int64', 'float64'] and target_data.nunique() > 100:
                logger.warning(f"Target column '{config.target_column}' has many unique values for classification")
        elif config.model_type == 'regression':
            if target_data.dtype == 'object':
                raise ValueError(f"Target column '{config.target_column}' must be numeric for regression")
        
        logger.info("Configuration validation passed")
    
    async def _prepare_data(self, df: pd.DataFrame, config: SimulationConfig) -> tuple:
        """Prepare data for ML training"""
        # Select features and target
        X = df[config.feature_columns].copy()
        y = df[config.target_column].copy()
        
        # Handle categorical features
        categorical_features = X.select_dtypes(include=['object', 'category']).columns
        if len(categorical_features) > 0:
            logger.info(f"Encoding categorical features: {list(categorical_features)}")
            for col in categorical_features:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        
        # Handle missing values
        if X.isnull().any().any():
            logger.info("Handling missing values in features")
            X = X.fillna(X.mean())
        
        if y.isnull().any():
            logger.info("Handling missing values in target")
            y = y.dropna()
            X = X.loc[y.index]
        
        # Prepare protected attributes
        protected_groups = {}
        for attr in config.protected_attributes:
            if df[attr].dtype in ['object', 'category']:
                # Categorical protected attribute
                le = LabelEncoder()
                protected_groups[attr] = le.fit_transform(df[attr].astype(str))
            else:
                # Numeric protected attribute - create binary groups
                median_val = df[attr].median()
                protected_groups[attr] = (df[attr] > median_val).astype(int)
        
        # Ensure all arrays have same length
        min_length = min(len(X), len(y), min(len(groups) for groups in protected_groups.values()))
        X = X.iloc[:min_length]
        y = y.iloc[:min_length]
        protected_groups = {attr: groups[:min_length] for attr, groups in protected_groups.items()}
        
        logger.info(f"Prepared data: X={X.shape}, y={len(y)}, protected_groups={len(protected_groups)}")
        return X, y, protected_groups
    
    async def _split_data(self, X, y, protected_groups, test_size, random_state):
        """Split data into train/test sets"""
        # Split features and target
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y if len(y.unique()) < 10 else None
        )
        
        # Split protected attributes accordingly
        train_indices = X_train.index
        test_indices = X_test.index
        
        protected_train = {attr: groups[train_indices] for attr, groups in protected_groups.items()}
        protected_test = {attr: groups[test_indices] for attr, groups in protected_groups.items()}
        
        logger.info(f"Split data: train={len(X_train)}, test={len(X_test)}")
        return X_train, X_test, y_train, y_test, protected_train, protected_test
    
    async def _train_model(self, X_train, y_train, config: SimulationConfig):
        """Train ML model based on configuration"""
        # Get algorithm class
        if config.model_type == 'classification':
            algorithm_class = self.classification_algorithms.get(config.algorithm)
        else:
            algorithm_class = self.regression_algorithms.get(config.algorithm)
        
        if not algorithm_class:
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")
        
        # Get hyperparameters
        hyperparams = config.hyperparameters or self.default_hyperparameters.get(config.algorithm, {})
        
        # Create and train model
        model = algorithm_class(**hyperparams)
        
        # Scale features if needed
        if config.algorithm in ['logistic_regression', 'linear_regression']:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            model.fit(X_train_scaled, y_train)
            # Store scaler for later use
            model.scaler = scaler
        else:
            model.fit(X_train, y_train)
        
        logger.info(f"Trained {config.algorithm} model for {config.model_type}")
        return model
    
    async def _make_predictions(self, model, X_test):
        """Make predictions using trained model"""
        if hasattr(model, 'scaler'):
            X_test_scaled = model.scaler.transform(X_test)
            predictions = model.predict(X_test_scaled)
        else:
            predictions = model.predict(X_test)
        
        return predictions
    
    async def _calculate_performance_metrics(self, y_true, y_pred, model_type: str) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if model_type == 'classification':
            metrics = {
                'accuracy': float(accuracy_score(y_true, y_pred)),
                'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
                'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
            }
            
            # Add detailed classification report
            try:
                report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
                metrics['detailed_report'] = report
            except:
                pass
                
        else:  # regression
            metrics = {
                'mse': float(mean_squared_error(y_true, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
                'r2_score': float(r2_score(y_true, y_pred))
            }
        
        return metrics
    
    async def _calculate_fairness_metrics(self, y_true, y_pred, protected_test, config: SimulationConfig) -> Dict[str, Any]:
        """Calculate fairness metrics across protected groups"""
        fairness_metrics = {}
        
        for attr_name, attr_values in protected_test.items():
            attr_metrics = {}
            
            # Get unique values for this attribute
            unique_values = np.unique(attr_values)
            
            if len(unique_values) < 2:
                logger.warning(f"Protected attribute {attr_name} has only one value, skipping fairness metrics")
                continue
            
            # Calculate metrics for each group
            for group_value in unique_values:
                group_mask = attr_values == group_value
                group_y_true = y_true[group_mask]
                group_y_pred = y_pred[group_mask]
                
                if len(group_y_true) == 0:
                    continue
                
                if config.model_type == 'classification':
                    group_metrics = {
                        'accuracy': float(accuracy_score(group_y_true, group_y_pred)),
                        'precision': float(precision_score(group_y_true, group_y_pred, average='weighted', zero_division=0)),
                        'recall': float(recall_score(group_y_true, group_y_pred, average='weighted', zero_division=0)),
                        'f1_score': float(f1_score(group_y_true, group_y_pred, average='weighted', zero_division=0)),
                        'sample_size': int(len(group_y_true))
                    }
                else:
                    group_metrics = {
                        'mse': float(mean_squared_error(group_y_true, group_y_pred)),
                        'rmse': float(np.sqrt(mean_squared_error(group_y_true, group_y_pred))),
                        'r2_score': float(r2_score(group_y_true, group_y_pred)),
                        'sample_size': int(len(group_y_true))
                    }
                
                attr_metrics[f"group_{group_value}"] = group_metrics
            
            # Calculate fairness ratios
            if len(attr_metrics) >= 2:
                group_names = list(attr_metrics.keys())
                base_group = group_names[0]
                
                fairness_ratios = {}
                for metric in ['accuracy', 'precision', 'recall', 'f1_score'] if config.model_type == 'classification' else ['r2_score']:
                    if metric in attr_metrics[base_group]:
                        try:
                            ratio = attr_metrics[group_names[1]][metric] / attr_metrics[base_group][metric]
                            fairness_ratios[f"{metric}_ratio"] = float(ratio)
                        except ZeroDivisionError:
                            fairness_ratios[f"{metric}_ratio"] = None
                
                attr_metrics['fairness_ratios'] = fairness_ratios
            
            fairness_metrics[attr_name] = attr_metrics
        
        return fairness_metrics
    
    async def _save_model(self, model, simulation_id: str) -> str:
        """Save trained model to disk"""
        model_filename = f"model_{simulation_id}.joblib"
        model_path = self.models_dir / model_filename
        
        try:
            joblib.dump(model, model_path)
            logger.info(f"Saved model to: {model_path}")
            return str(model_path)
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return None
    
    async def _save_results(self, results: SimulationResult) -> None:
        """Save simulation results to disk"""
        results_filename = f"results_{results.simulation_id}.json"
        results_path = self.results_dir / results_filename
        
        try:
            with open(results_path, 'w') as f:
                json.dump(results.dict(), f, indent=2, default=str)
            logger.info(f"Saved results to: {results_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    async def get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get status of a simulation"""
        results_path = self.results_dir / f"results_{simulation_id}.json"
        
        if not results_path.exists():
            return {"status": "not_found"}
        
        try:
            with open(results_path, 'r') as f:
                results = json.load(f)
            return results
        except Exception as e:
            logger.error(f"Failed to load results: {e}")
            return {"status": "error", "error": str(e)}
    
    async def list_simulations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent simulations"""
        results_files = list(self.results_dir.glob("results_*.json"))
        results_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        simulations = []
        for file_path in results_files[:limit]:
            try:
                with open(file_path, 'r') as f:
                    results = json.load(f)
                simulations.append(results)
            except Exception as e:
                logger.error(f"Failed to load results from {file_path}: {e}")
        
        return simulations
    
    async def delete_simulation(self, simulation_id: str) -> bool:
        """Delete simulation results and model"""
        try:
            # Delete results file
            results_path = self.results_dir / f"results_{simulation_id}.json"
            if results_path.exists():
                results_path.unlink()
            
            # Delete model file
            model_path = self.models_dir / f"model_{simulation_id}.joblib"
            if model_path.exists():
                model_path.unlink()
            
            logger.info(f"Deleted simulation: {simulation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete simulation {simulation_id}: {e}")
            return False

# Create service instance
simulation_service = SimulationService()
