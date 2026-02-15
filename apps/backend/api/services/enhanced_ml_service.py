"""
Enhanced ML Service - Advanced Algorithms and Bias Detection
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedMLService:
    """Enhanced ML service with advanced algorithms and bias detection"""
    
    def __init__(self):
        self.supported_algorithms = {
            'classification': {
                'random_forest': RandomForestClassifier,
                'gradient_boosting': GradientBoostingClassifier,
                'ada_boost': AdaBoostClassifier,
                'logistic_regression': LogisticRegression,
                'svm': SVC,
                'neural_network': MLPClassifier,
                'decision_tree': DecisionTreeClassifier,
                'naive_bayes': GaussianNB,
                'knn': KNeighborsClassifier
            },
            'regression': {
                'linear_regression': LinearRegression,
                'ridge': Ridge,
                'lasso': Lasso,
                'svr': SVR,
                'neural_network': MLPRegressor,
                'gradient_boosting': GradientBoostingClassifier  # Can be used for regression too
            },
            'clustering': {
                'kmeans': KMeans,
                'dbscan': DBSCAN
            }
        }
        
        self.bias_metrics = {
            'demographic_parity': self._calculate_demographic_parity,
            'equalized_odds': self._calculate_equalized_odds,
            'equal_opportunity': self._calculate_equal_opportunity,
            'statistical_parity': self._calculate_statistical_parity,
            'calibration': self._calculate_calibration,
            'individual_fairness': self._calculate_individual_fairness,
            'counterfactual_fairness': self._calculate_counterfactual_fairness
        }
    
    def get_available_algorithms(self) -> Dict[str, List[str]]:
        """Get list of available algorithms by task type"""
        return {task_type: list(algorithms.keys()) for task_type, algorithms in self.supported_algorithms.items()}
    
    def train_model(self, 
                   data: pd.DataFrame, 
                   target_column: str, 
                   algorithm: str, 
                   task_type: str = 'classification',
                   protected_attributes: List[str] = None,
                   test_size: float = 0.2,
                   random_state: int = 42) -> Dict[str, Any]:
        """Train a model with enhanced algorithms and bias detection"""
        
        try:
            # Prepare data
            X = data.drop(columns=[target_column])
            y = data[target_column]
            
            # Handle categorical variables
            X_encoded = self._encode_categorical_variables(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_encoded, y, test_size=test_size, random_state=random_state, stratify=y if task_type == 'classification' else None
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Get algorithm class
            if task_type not in self.supported_algorithms:
                raise ValueError(f"Unsupported task type: {task_type}")
            
            if algorithm not in self.supported_algorithms[task_type]:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            algorithm_class = self.supported_algorithms[task_type][algorithm]
            
            # Train model
            model = algorithm_class()
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled) if hasattr(model, 'predict_proba') else None
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(y_test, y_pred, y_pred_proba, task_type)
            
            # Calculate bias metrics
            bias_metrics = self._calculate_bias_metrics(
                X_test, y_test, y_pred, protected_attributes or []
            )
            
            # Feature importance
            feature_importance = self._get_feature_importance(model, X.columns.tolist())
            
            # Model metadata
            model_metadata = {
                'algorithm': algorithm,
                'task_type': task_type,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features': X.columns.tolist(),
                'target_column': target_column,
                'protected_attributes': protected_attributes or [],
                'timestamp': datetime.now().isoformat()
            }
            
            return {
                'model': model,
                'scaler': scaler,
                'performance_metrics': performance_metrics,
                'bias_metrics': bias_metrics,
                'feature_importance': feature_importance,
                'metadata': model_metadata,
                'predictions': {
                    'y_test': y_test.tolist(),
                    'y_pred': y_pred.tolist(),
                    'y_pred_proba': y_pred_proba.tolist() if y_pred_proba is not None else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def _encode_categorical_variables(self, X: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical variables"""
        X_encoded = X.copy()
        
        for column in X_encoded.columns:
            if X_encoded[column].dtype == 'object':
                le = LabelEncoder()
                X_encoded[column] = le.fit_transform(X_encoded[column].astype(str))
        
        return X_encoded
    
    def _calculate_performance_metrics(self, y_true, y_pred, y_pred_proba, task_type: str) -> Dict[str, float]:
        """Calculate performance metrics based on task type"""
        metrics = {}
        
        if task_type == 'classification':
            metrics.update({
                'accuracy': accuracy_score(y_true, y_pred),
                'precision': precision_score(y_true, y_pred, average='weighted'),
                'recall': recall_score(y_true, y_pred, average='weighted'),
                'f1_score': f1_score(y_true, y_pred, average='weighted')
            })
            
            if y_pred_proba is not None and len(np.unique(y_true)) == 2:
                metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba[:, 1])
        
        elif task_type == 'regression':
            metrics.update({
                'mse': mean_squared_error(y_true, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
                'mae': mean_absolute_error(y_true, y_pred),
                'r2_score': r2_score(y_true, y_pred)
            })
        
        return metrics
    
    def _calculate_bias_metrics(self, X: pd.DataFrame, y_true, y_pred, protected_attributes: List[str]) -> Dict[str, Any]:
        """Calculate comprehensive bias metrics"""
        bias_results = {}
        
        for attr in protected_attributes:
            if attr in X.columns:
                bias_results[attr] = {}
                
                for metric_name, metric_func in self.bias_metrics.items():
                    try:
                        bias_results[attr][metric_name] = metric_func(X, y_true, y_pred, attr)
                    except Exception as e:
                        logger.warning(f"Could not calculate {metric_name} for {attr}: {str(e)}")
                        bias_results[attr][metric_name] = None
        
        return bias_results
    
    def _calculate_demographic_parity(self, X: pd.DataFrame, y_true, y_pred, protected_attr: str) -> float:
        """Calculate demographic parity difference"""
        groups = X[protected_attr].unique()
        positive_rates = []
        
        for group in groups:
            group_mask = X[protected_attr] == group
            if group_mask.sum() > 0:
                positive_rate = y_pred[group_mask].mean()
                positive_rates.append(positive_rate)
        
        return max(positive_rates) - min(positive_rates) if len(positive_rates) > 1 else 0.0
    
    def _calculate_equalized_odds(self, X: pd.DataFrame, y_true, y_pred, protected_attr: str) -> Dict[str, float]:
        """Calculate equalized odds (TPR and FPR differences)"""
        groups = X[protected_attr].unique()
        tprs = []
        fprs = []
        
        for group in groups:
            group_mask = X[protected_attr] == group
            if group_mask.sum() > 0:
                group_y_true = y_true[group_mask]
                group_y_pred = y_pred[group_mask]
                
                # True Positive Rate
                tp = ((group_y_true == 1) & (group_y_pred == 1)).sum()
                fn = ((group_y_true == 1) & (group_y_pred == 0)).sum()
                tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
                tprs.append(tpr)
                
                # False Positive Rate
                fp = ((group_y_true == 0) & (group_y_pred == 1)).sum()
                tn = ((group_y_true == 0) & (group_y_pred == 0)).sum()
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
                fprs.append(fpr)
        
        return {
            'tpr_difference': max(tprs) - min(tprs) if len(tprs) > 1 else 0.0,
            'fpr_difference': max(fprs) - min(fprs) if len(fprs) > 1 else 0.0
        }
    
    def _calculate_equal_opportunity(self, X: pd.DataFrame, y_true, y_pred, protected_attr: str) -> float:
        """Calculate equal opportunity (TPR difference)"""
        equalized_odds = self._calculate_equalized_odds(X, y_true, y_pred, protected_attr)
        return equalized_odds['tpr_difference']
    
    def _calculate_statistical_parity(self, X: pd.DataFrame, y_true, y_pred, protected_attr: str) -> float:
        """Calculate statistical parity difference"""
        return self._calculate_demographic_parity(X, y_true, y_pred, protected_attr)
    
    def _calculate_calibration(self, X: pd.DataFrame, y_true, y_pred, protected_attr: str) -> Dict[str, float]:
        """Calculate calibration metrics"""
        groups = X[protected_attr].unique()
        calibration_scores = []
        
        for group in groups:
            group_mask = X[protected_attr] == group
            if group_mask.sum() > 0:
                group_y_true = y_true[group_mask]
                group_y_pred = y_pred[group_mask]
                
                # Calibration score (how well predicted probabilities match actual outcomes)
                calibration_score = abs(group_y_pred.mean() - group_y_true.mean())
                calibration_scores.append(calibration_score)
        
        return {
            'max_calibration_difference': max(calibration_scores) if calibration_scores else 0.0,
            'mean_calibration_difference': np.mean(calibration_scores) if calibration_scores else 0.0
        }
    
    def _calculate_individual_fairness(self, X: pd.DataFrame, y_true, y_pred, protected_attr: str) -> float:
        """Calculate individual fairness (simplified version)"""
        # This is a simplified implementation
        # In practice, you'd need similarity metrics and more sophisticated approaches
        groups = X[protected_attr].unique()
        individual_fairness_scores = []
        
        for group in groups:
            group_mask = X[protected_attr] == group
            if group_mask.sum() > 0:
                group_y_pred = y_pred[group_mask]
                # Calculate variance in predictions within group
                variance = np.var(group_y_pred)
                individual_fairness_scores.append(variance)
        
        return np.mean(individual_fairness_scores) if individual_fairness_scores else 0.0
    
    def _calculate_counterfactual_fairness(self, X: pd.DataFrame, y_true, y_pred, protected_attr: str) -> float:
        """Calculate counterfactual fairness (simplified version)"""
        # This is a simplified implementation
        # In practice, you'd need causal inference methods
        return self._calculate_demographic_parity(X, y_true, y_pred, protected_attr)
    
    def _get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from model"""
        try:
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(feature_names, model.feature_importances_))
                return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            elif hasattr(model, 'coef_'):
                # For linear models
                coef_dict = dict(zip(feature_names, model.coef_.flatten()))
                return dict(sorted(coef_dict.items(), key=lambda x: abs(x[1]), reverse=True))
            else:
                return {}
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {str(e)}")
            return {}
    
    def save_model(self, model_data: Dict[str, Any], model_path: str) -> str:
        """Save trained model and metadata"""
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Save model and scaler
            joblib.dump({
                'model': model_data['model'],
                'scaler': model_data['scaler'],
                'metadata': model_data['metadata']
            }, f"{model_path}_model.pkl")
            
            # Save results
            results = {
                'performance_metrics': model_data['performance_metrics'],
                'bias_metrics': model_data['bias_metrics'],
                'feature_importance': model_data['feature_importance'],
                'predictions': model_data['predictions']
            }
            
            joblib.dump(results, f"{model_path}_results.pkl")
            
            return model_path
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, model_path: str) -> Dict[str, Any]:
        """Load trained model and metadata"""
        try:
            model_data = joblib.load(f"{model_path}_model.pkl")
            results = joblib.load(f"{model_path}_results.pkl")
            
            return {
                'model': model_data['model'],
                'scaler': model_data['scaler'],
                'metadata': model_data['metadata'],
                'performance_metrics': results['performance_metrics'],
                'bias_metrics': results['bias_metrics'],
                'feature_importance': results['feature_importance'],
                'predictions': results['predictions']
            }
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
