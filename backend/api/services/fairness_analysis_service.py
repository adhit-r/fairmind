"""
Advanced Fairness Analysis Service

This service provides comprehensive fairness analysis capabilities using:
- TensorFlow Fairness Indicators for fairness metrics
- MinDiff for training-time bias mitigation
- Advanced bias detection techniques
"""

import logging
import numpy as np
import pandas as pd
import tensorflow as tf
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json

# Import TensorFlow Fairness Indicators and MinDiff
try:
    import tensorflow_model_analysis as tfma
    from google.protobuf import text_format
    from tensorflow_model_remediation import min_diff
    from tensorflow_model_remediation.min_diff.keras import MinDiffModel
    from tensorflow_model_remediation.min_diff.keras.utils import pack_min_diff_data
    FAIRNESS_AVAILABLE = True
except ImportError:
    FAIRNESS_AVAILABLE = False
    logging.warning("TensorFlow Fairness Indicators not available - using fallback fairness metrics")

logger = logging.getLogger(__name__)

class FairnessMetricsCalculator:
    """Calculate various fairness metrics for model evaluation"""
    
    def __init__(self):
        self.metrics = {}
    
    def calculate_statistical_parity(self, predictions: np.ndarray, labels: np.ndarray, 
                                   sensitive_attr: np.ndarray) -> Dict[str, float]:
        """Calculate statistical parity difference"""
        try:
            # Group predictions by sensitive attribute
            unique_groups = np.unique(sensitive_attr)
            group_rates = {}
            
            for group in unique_groups:
                group_mask = sensitive_attr == group
                group_predictions = predictions[group_mask]
                group_rate = np.mean(group_predictions)
                group_rates[str(group)] = group_rate
            
            # Calculate statistical parity difference
            if len(group_rates) >= 2:
                rates = list(group_rates.values())
                sp_difference = max(rates) - min(rates)
            else:
                sp_difference = 0.0
            
            return {
                "statistical_parity_difference": sp_difference,
                "group_rates": group_rates,
                "overall_rate": np.mean(predictions)
            }
        except Exception as e:
            logger.error(f"Error calculating statistical parity: {e}")
            return {"error": str(e)}
    
    def calculate_equalized_odds(self, predictions: np.ndarray, labels: np.ndarray, 
                               sensitive_attr: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
        """Calculate equalized odds metrics"""
        try:
            binary_predictions = (predictions >= threshold).astype(int)
            unique_groups = np.unique(sensitive_attr)
            group_metrics = {}
            
            for group in unique_groups:
                group_mask = sensitive_attr == group
                group_preds = binary_predictions[group_mask]
                group_labels = labels[group_mask]
                
                # Calculate TPR and FPR for this group
                tp = np.sum((group_preds == 1) & (group_labels == 1))
                fp = np.sum((group_preds == 1) & (group_labels == 0))
                tn = np.sum((group_preds == 0) & (group_labels == 0))
                fn = np.sum((group_preds == 0) & (group_labels == 1))
                
                tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                
                group_metrics[str(group)] = {
                    "true_positive_rate": tpr,
                    "false_positive_rate": fpr,
                    "accuracy": (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
                }
            
            # Calculate equalized odds difference
            if len(group_metrics) >= 2:
                tprs = [metrics["true_positive_rate"] for metrics in group_metrics.values()]
                fprs = [metrics["false_positive_rate"] for metrics in group_metrics.values()]
                
                tpr_difference = max(tprs) - min(tprs)
                fpr_difference = max(fprs) - min(fprs)
            else:
                tpr_difference = 0.0
                fpr_difference = 0.0
            
            return {
                "equalized_odds_tpr_difference": tpr_difference,
                "equalized_odds_fpr_difference": fpr_difference,
                "group_metrics": group_metrics
            }
        except Exception as e:
            logger.error(f"Error calculating equalized odds: {e}")
            return {"error": str(e)}
    
    def calculate_equal_opportunity(self, predictions: np.ndarray, labels: np.ndarray, 
                                  sensitive_attr: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
        """Calculate equal opportunity metrics"""
        try:
            binary_predictions = (predictions >= threshold).astype(int)
            unique_groups = np.unique(sensitive_attr)
            group_tprs = {}
            
            for group in unique_groups:
                group_mask = sensitive_attr == group
                group_preds = binary_predictions[group_mask]
                group_labels = labels[group_mask]
                
                # Calculate TPR for positive class only
                positive_mask = group_labels == 1
                if np.sum(positive_mask) > 0:
                    tp = np.sum((group_preds == 1) & positive_mask)
                    fn = np.sum((group_preds == 0) & positive_mask)
                    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                else:
                    tpr = 0.0
                
                group_tprs[str(group)] = tpr
            
            # Calculate equal opportunity difference
            if len(group_tprs) >= 2:
                tprs = list(group_tprs.values())
                eo_difference = max(tprs) - min(tprs)
            else:
                eo_difference = 0.0
            
            return {
                "equal_opportunity_difference": eo_difference,
                "group_true_positive_rates": group_tprs
            }
        except Exception as e:
            logger.error(f"Error calculating equal opportunity: {e}")
            return {"error": str(e)}

class MinDiffTrainer:
    """Train models with fairness constraints using MinDiff"""
    
    def __init__(self):
        self.min_diff_model = None
        self.base_model = None
    
    def prepare_min_diff_data(self, original_dataset: pd.DataFrame, 
                            sensitive_group: pd.DataFrame,
                            non_sensitive_group: pd.DataFrame,
                            label_column: str = 'label') -> Tuple[tf.data.Dataset, tf.data.Dataset, tf.data.Dataset]:
        """Prepare data for MinDiff training"""
        try:
            # Convert DataFrames to TensorFlow datasets
            def df_to_dataset(df: pd.DataFrame) -> tf.data.Dataset:
                labels = df.pop(label_column)
                dataset = tf.data.Dataset.from_tensor_slices((dict(df), labels))
                return dataset
            
            original_ds = df_to_dataset(original_dataset.copy())
            sensitive_ds = df_to_dataset(sensitive_group.copy())
            non_sensitive_ds = df_to_dataset(non_sensitive_group.copy())
            
            # Batch the datasets
            batch_size = 32
            original_batches = original_ds.batch(batch_size)
            sensitive_batches = sensitive_ds.batch(batch_size, drop_remainder=True)
            non_sensitive_batches = non_sensitive_ds.batch(batch_size, drop_remainder=True)
            
            return original_batches, sensitive_batches, non_sensitive_batches
            
        except Exception as e:
            logger.error(f"Error preparing MinDiff data: {e}")
            raise
    
    def create_base_model(self, input_features: List[str], model_type: str = "neural_network") -> tf.keras.Model:
        """Create a base model for MinDiff training"""
        try:
            if model_type == "neural_network":
                # Create a simple neural network
                inputs = {}
                for feature in input_features:
                    inputs[feature] = tf.keras.Input(shape=(1,), name=feature, dtype=tf.float32)
                
                # Stack inputs
                x = tf.keras.layers.Concatenate()(list(inputs.values()))
                
                # Add layers
                x = tf.keras.layers.Dense(64, activation='relu')(x)
                x = tf.keras.layers.Dropout(0.2)(x)
                x = tf.keras.layers.Dense(32, activation='relu')(x)
                x = tf.keras.layers.Dropout(0.2)(x)
                outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
                
                model = tf.keras.Model(inputs, outputs)
                model.compile(
                    optimizer='adam',
                    loss='binary_crossentropy',
                    metrics=['accuracy', 'auc']
                )
                
                return model
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
                
        except Exception as e:
            logger.error(f"Error creating base model: {e}")
            raise
    
    def train_with_fairness_constraints(self, base_model: tf.keras.Model,
                                      original_data: tf.data.Dataset,
                                      sensitive_data: tf.data.Dataset,
                                      non_sensitive_data: tf.data.Dataset,
                                      fairness_weight: float = 1.0,
                                      epochs: int = 10) -> MinDiffModel:
        """Train model with MinDiff fairness constraints"""
        try:
            # Pack the datasets for MinDiff
            min_diff_data = pack_min_diff_data(
                original_dataset=original_data,
                sensitive_group_dataset=sensitive_data,
                nonsensitive_group_dataset=non_sensitive_data
            )
            
            # Create MinDiff model
            min_diff_model = MinDiffModel(
                original_model=base_model,
                loss=min_diff.losses.MMDLoss(),
                loss_weight=fairness_weight
            )
            
            # Compile the MinDiff model
            min_diff_model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy', 'auc']
            )
            
            # Train the model
            history = min_diff_model.fit(
                min_diff_data,
                epochs=epochs,
                verbose=1
            )
            
            self.min_diff_model = min_diff_model
            return min_diff_model
            
        except Exception as e:
            logger.error(f"Error training with fairness constraints: {e}")
            raise

class FairnessAnalysisService:
    """Main service for comprehensive fairness analysis"""
    
    def __init__(self):
        self.metrics_calculator = FairnessMetricsCalculator()
        self.min_diff_trainer = MinDiffTrainer()
        self.fairness_available = FAIRNESS_AVAILABLE
    
    async def analyze_model_fairness(self, model_predictions: np.ndarray,
                                   ground_truth: np.ndarray,
                                   sensitive_attributes: Dict[str, np.ndarray],
                                   analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive fairness analysis"""
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "analysis_config": analysis_config,
                "fairness_metrics": {},
                "bias_detection": {},
                "recommendations": []
            }
            
            # Calculate fairness metrics for each sensitive attribute
            for attr_name, attr_values in sensitive_attributes.items():
                attr_results = {}
                
                # Statistical parity
                sp_results = self.metrics_calculator.calculate_statistical_parity(
                    model_predictions, ground_truth, attr_values
                )
                attr_results["statistical_parity"] = sp_results
                
                # Equalized odds
                eo_results = self.metrics_calculator.calculate_equalized_odds(
                    model_predictions, ground_truth, attr_values
                )
                attr_results["equalized_odds"] = eo_results
                
                # Equal opportunity
                eo_results = self.metrics_calculator.calculate_equal_opportunity(
                    model_predictions, ground_truth, attr_values
                )
                attr_results["equal_opportunity"] = eo_results
                
                results["fairness_metrics"][attr_name] = attr_results
            
            # Generate bias detection insights
            results["bias_detection"] = self._detect_bias_patterns(results["fairness_metrics"])
            
            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(results["fairness_metrics"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fairness analysis: {e}")
            return {"error": str(e)}
    
    def _detect_bias_patterns(self, fairness_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bias patterns in fairness metrics"""
        try:
            bias_patterns = {
                "high_bias_attributes": [],
                "bias_severity": {},
                "bias_direction": {}
            }
            
            for attr_name, metrics in fairness_metrics.items():
                # Check statistical parity
                if "statistical_parity" in metrics:
                    sp_diff = metrics["statistical_parity"].get("statistical_parity_difference", 0)
                    if sp_diff > 0.1:  # Threshold for high bias
                        bias_patterns["high_bias_attributes"].append(attr_name)
                        bias_patterns["bias_severity"][attr_name] = "high"
                    elif sp_diff > 0.05:
                        bias_patterns["bias_severity"][attr_name] = "medium"
                    else:
                        bias_patterns["bias_severity"][attr_name] = "low"
                
                # Check equal opportunity
                if "equal_opportunity" in metrics:
                    eo_diff = metrics["equal_opportunity"].get("equal_opportunity_difference", 0)
                    if eo_diff > 0.1:
                        bias_patterns["high_bias_attributes"].append(attr_name)
            
            return bias_patterns
            
        except Exception as e:
            logger.error(f"Error detecting bias patterns: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, fairness_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on fairness analysis"""
        try:
            recommendations = []
            
            for attr_name, metrics in fairness_metrics.items():
                # Statistical parity recommendations
                if "statistical_parity" in metrics:
                    sp_diff = metrics["statistical_parity"].get("statistical_parity_difference", 0)
                    if sp_diff > 0.1:
                        recommendations.append(
                            f"High statistical parity difference ({sp_diff:.3f}) detected for {attr_name}. "
                            "Consider using MinDiff training or post-processing techniques."
                        )
                
                # Equal opportunity recommendations
                if "equal_opportunity" in metrics:
                    eo_diff = metrics["equal_opportunity"].get("equal_opportunity_difference", 0)
                    if eo_diff > 0.1:
                        recommendations.append(
                            f"High equal opportunity difference ({eo_diff:.3f}) detected for {attr_name}. "
                            "Consider using equal opportunity constraints in training."
                        )
            
            if not recommendations:
                recommendations.append("No significant bias detected. Continue monitoring for fairness.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [f"Error generating recommendations: {str(e)}"]
    
    async def train_fair_model(self, training_data: pd.DataFrame,
                             sensitive_attributes: List[str],
                             label_column: str,
                             model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Train a model with fairness constraints"""
        try:
            if not self.fairness_available:
                return {"error": "TensorFlow Fairness Indicators not available"}
            
            # Prepare data
            original_data = training_data.copy()
            
            # Create sensitive and non-sensitive groups (example for binary sensitive attribute)
            if len(sensitive_attributes) > 0:
                sensitive_attr = sensitive_attributes[0]
                sensitive_group = original_data[original_data[sensitive_attr] == 1]
                non_sensitive_group = original_data[original_data[sensitive_attr] == 0]
                
                # Prepare MinDiff data
                original_batches, sensitive_batches, non_sensitive_batches = \
                    self.min_diff_trainer.prepare_min_diff_data(
                        original_data, sensitive_group, non_sensitive_group, label_column
                    )
                
                # Create base model
                feature_columns = [col for col in original_data.columns if col != label_column]
                base_model = self.min_diff_trainer.create_base_model(feature_columns)
                
                # Train with fairness constraints
                fair_model = self.min_diff_trainer.train_with_fairness_constraints(
                    base_model, original_batches, sensitive_batches, non_sensitive_batches,
                    fairness_weight=model_config.get("fairness_weight", 1.0),
                    epochs=model_config.get("epochs", 10)
                )
                
                return {
                    "success": True,
                    "model_type": "MinDiff",
                    "fairness_weight": model_config.get("fairness_weight", 1.0),
                    "training_epochs": model_config.get("epochs", 10),
                    "sensitive_attributes": sensitive_attributes
                }
            else:
                return {"error": "No sensitive attributes provided"}
                
        except Exception as e:
            logger.error(f"Error training fair model: {e}")
            return {"error": str(e)}

# Create service instance
fairness_analysis_service = FairnessAnalysisService()
