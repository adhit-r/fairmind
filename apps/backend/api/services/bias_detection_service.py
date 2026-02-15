"""
Comprehensive Bias Detection Service

This service implements bias detection and analysis based on Google's Machine Learning Crash Course
and industry best practices for AI fairness and bias detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_curve
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class BiasDetectionService:
    """Comprehensive bias detection and analysis service"""
    
    def __init__(self):
        self.bias_types = {
            'reporting_bias': 'Frequency of events in dataset does not reflect real-world frequency',
            'historical_bias': 'Historical data reflects past inequities',
            'automation_bias': 'Favoring automated results over manual ones',
            'selection_bias': 'Dataset examples not reflective of real-world distribution',
            'coverage_bias': 'Data not selected in representative fashion',
            'non_response_bias': 'Data unrepresentative due to participation gaps',
            'sampling_bias': 'Proper randomization not used in data collection',
            'group_attribution_bias': 'Generalizing individuals to entire groups',
            'in_group_bias': 'Preference for members of own group',
            'out_group_homogeneity_bias': 'Stereotyping members of other groups',
            'implicit_bias': 'Assumptions based on personal experiences',
            'confirmation_bias': 'Processing data to affirm pre-existing beliefs',
            'experimenter_bias': 'Training until results align with hypothesis'
        }
    
    def analyze_dataset_bias(self, df: pd.DataFrame, sensitive_attributes: List[str], 
                           target_column: str) -> Dict[str, Any]:
        """
        Comprehensive bias analysis of a dataset
        
        Args:
            df: Input DataFrame
            sensitive_attributes: List of sensitive attribute column names
            target_column: Target variable column name
            
        Returns:
            Dictionary containing comprehensive bias analysis results
        """
        try:
            analysis_results = {
                'timestamp': datetime.now().isoformat(),
                'dataset_info': self._analyze_dataset_info(df),
                'data_quality': self._analyze_data_quality(df, sensitive_attributes),
                'bias_detection': self._detect_bias_types(df, sensitive_attributes, target_column),
                'fairness_metrics': self._calculate_fairness_metrics(df, sensitive_attributes, target_column),
                'recommendations': []
            }
            
            # Generate recommendations based on findings
            analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in bias analysis: {str(e)}")
            raise
    
    def _analyze_dataset_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze basic dataset information"""
        return {
            'total_samples': len(df),
            'total_features': len(df.columns),
            'missing_values_total': df.isnull().sum().sum(),
            'missing_values_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            'data_types': df.dtypes.to_dict(),
            'numeric_features': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_features': df.select_dtypes(include=['object']).columns.tolist()
        }
    
    def _analyze_data_quality(self, df: pd.DataFrame, sensitive_attributes: List[str]) -> Dict[str, Any]:
        """Analyze data quality for potential bias indicators"""
        
        # Missing values analysis
        missing_analysis = {}
        for attr in sensitive_attributes:
            if attr in df.columns:
                missing_by_group = df.groupby(attr).apply(
                    lambda x: x.isnull().sum() / len(x)
                )
                missing_analysis[attr] = missing_by_group.to_dict()
        
        # Unexpected values analysis
        unexpected_values = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in sensitive_attributes:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
                unexpected_values[col] = {
                    'outlier_count': len(outliers),
                    'outlier_percentage': (len(outliers) / len(df)) * 100
                }
        
        # Data skew analysis
        data_skew = {}
        for attr in sensitive_attributes:
            if attr in df.columns:
                group_counts = df[attr].value_counts()
                total = len(df)
                
                data_skew[attr] = {
                    'distribution': (group_counts / total).to_dict(),
                    'imbalance_ratio': group_counts.max() / group_counts.min() if group_counts.min() > 0 else float('inf'),
                    'minority_group_size': group_counts.min(),
                    'majority_group_size': group_counts.max(),
                    'groups': group_counts.to_dict()
                }
        
        return {
            'missing_values': missing_analysis,
            'unexpected_values': unexpected_values,
            'data_skew': data_skew
        }
    
    def _detect_bias_types(self, df: pd.DataFrame, sensitive_attributes: List[str], 
                          target_column: str) -> Dict[str, Any]:
        """Detect specific types of bias in the dataset"""
        
        bias_detections = {}
        
        # Reporting bias detection
        bias_detections['reporting_bias'] = self._detect_reporting_bias(df, target_column)
        
        # Historical bias detection
        bias_detections['historical_bias'] = self._detect_historical_bias(df, sensitive_attributes)
        
        # Selection bias detection
        bias_detections['selection_bias'] = self._detect_selection_bias(df, sensitive_attributes)
        
        # Group attribution bias detection
        bias_detections['group_attribution_bias'] = self._detect_group_attribution_bias(df, sensitive_attributes)
        
        # Implicit bias detection
        bias_detections['implicit_bias'] = self._detect_implicit_bias(df, sensitive_attributes)
        
        return bias_detections
    
    def _detect_reporting_bias(self, df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """Detect reporting bias by analyzing target variable distribution"""
        
        if target_column not in df.columns:
            return {'detected': False, 'reason': 'Target column not found'}
        
        target_distribution = df[target_column].value_counts(normalize=True)
        
        # Check for extreme distributions (potential reporting bias)
        max_proportion = target_distribution.max()
        min_proportion = target_distribution.min()
        
        # Reporting bias indicators
        extreme_distribution = max_proportion > 0.8  # More than 80% in one class
        very_skewed = max_proportion / min_proportion > 10  # 10:1 ratio
        
        return {
            'detected': extreme_distribution or very_skewed,
            'target_distribution': target_distribution.to_dict(),
            'max_proportion': max_proportion,
            'min_proportion': min_proportion,
            'ratio': max_proportion / min_proportion if min_proportion > 0 else float('inf'),
            'indicators': {
                'extreme_distribution': extreme_distribution,
                'very_skewed': very_skewed
            }
        }
    
    def _detect_historical_bias(self, df: pd.DataFrame, sensitive_attributes: List[str]) -> Dict[str, Any]:
        """Detect historical bias by analyzing temporal patterns and group disparities"""
        
        historical_bias_indicators = {}
        
        for attr in sensitive_attributes:
            if attr in df.columns:
                # Analyze group distributions
                group_distribution = df[attr].value_counts(normalize=True)
                
                # Check for extreme disparities (potential historical bias)
                max_proportion = group_distribution.max()
                min_proportion = group_distribution.min()
                
                extreme_disparity = max_proportion / min_proportion > 5  # 5:1 ratio
                
                historical_bias_indicators[attr] = {
                    'detected': extreme_disparity,
                    'group_distribution': group_distribution.to_dict(),
                    'disparity_ratio': max_proportion / min_proportion if min_proportion > 0 else float('inf'),
                    'majority_group': group_distribution.idxmax(),
                    'minority_group': group_distribution.idxmin()
                }
        
        return {
            'detected': any(indicator['detected'] for indicator in historical_bias_indicators.values()),
            'indicators': historical_bias_indicators
        }
    
    def _detect_selection_bias(self, df: pd.DataFrame, sensitive_attributes: List[str]) -> Dict[str, Any]:
        """Detect selection bias by analyzing sampling patterns"""
        
        selection_bias_indicators = {}
        
        for attr in sensitive_attributes:
            if attr in df.columns:
                # Check for coverage bias
                group_counts = df[attr].value_counts()
                total_samples = len(df)
                
                # Coverage bias: groups with very small representation
                coverage_bias = (group_counts / total_samples < 0.05).any()  # Less than 5%
                
                # Non-response bias: missing values correlated with groups
                missing_by_group = df.groupby(attr).apply(lambda x: x.isnull().sum().sum() / len(x))
                non_response_bias = missing_by_group.std() > missing_by_group.mean() * 0.5
                
                selection_bias_indicators[attr] = {
                    'detected': coverage_bias or non_response_bias,
                    'coverage_bias': coverage_bias,
                    'non_response_bias': non_response_bias,
                    'group_representation': (group_counts / total_samples).to_dict(),
                    'missing_by_group': missing_by_group.to_dict()
                }
        
        return {
            'detected': any(indicator['detected'] for indicator in selection_bias_indicators.values()),
            'indicators': selection_bias_indicators
        }
    
    def _detect_group_attribution_bias(self, df: pd.DataFrame, sensitive_attributes: List[str]) -> Dict[str, Any]:
        """Detect group attribution bias by analyzing group stereotypes"""
        
        group_attribution_indicators = {}
        
        for attr in sensitive_attributes:
            if attr in df.columns:
                # Analyze feature correlations with sensitive attributes
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                correlations = {}
                
                for col in numeric_cols:
                    if col != attr:
                        correlation = df[attr].corr(df[col])
                        correlations[col] = correlation
                
                # Strong correlations might indicate group attribution bias
                strong_correlations = {k: v for k, v in correlations.items() if abs(v) > 0.3}
                
                group_attribution_indicators[attr] = {
                    'detected': len(strong_correlations) > 0,
                    'strong_correlations': strong_correlations,
                    'all_correlations': correlations
                }
        
        return {
            'detected': any(indicator['detected'] for indicator in group_attribution_indicators.values()),
            'indicators': group_attribution_indicators
        }
    
    def _detect_implicit_bias(self, df: pd.DataFrame, sensitive_attributes: List[str]) -> Dict[str, Any]:
        """Detect implicit bias by analyzing feature patterns"""
        
        implicit_bias_indicators = {}
        
        for attr in sensitive_attributes:
            if attr in df.columns:
                # Analyze feature distributions across groups
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                feature_disparities = {}
                
                for col in numeric_cols:
                    if col != attr:
                        group_means = df.groupby(attr)[col].mean()
                        group_stds = df.groupby(attr)[col].std()
                        
                        # Check for significant differences in feature distributions
                        if len(group_means) > 1:
                            max_mean = group_means.max()
                            min_mean = group_means.min()
                            mean_disparity = (max_mean - min_mean) / group_means.mean()
                            
                            feature_disparities[col] = {
                                'mean_disparity': mean_disparity,
                                'group_means': group_means.to_dict(),
                                'group_stds': group_stds.to_dict(),
                                'significant_disparity': mean_disparity > 0.5  # 50% difference
                            }
                
                significant_disparities = {k: v for k, v in feature_disparities.items() 
                                         if v['significant_disparity']}
                
                implicit_bias_indicators[attr] = {
                    'detected': len(significant_disparities) > 0,
                    'significant_disparities': significant_disparities,
                    'all_disparities': feature_disparities
                }
        
        return {
            'detected': any(indicator['detected'] for indicator in implicit_bias_indicators.values()),
            'indicators': implicit_bias_indicators
        }
    
    def _calculate_fairness_metrics(self, df: pd.DataFrame, sensitive_attributes: List[str], 
                                  target_column: str) -> Dict[str, Any]:
        """Calculate fairness metrics for the dataset"""
        
        fairness_metrics = {}
        
        for attr in sensitive_attributes:
            if attr in df.columns and target_column in df.columns:
                # Demographic parity
                demographic_parity = self._calculate_demographic_parity(df, attr, target_column)
                
                # Equality of opportunity
                equality_of_opportunity = self._calculate_equality_of_opportunity(df, attr, target_column)
                
                # Statistical parity
                statistical_parity = self._calculate_statistical_parity(df, attr, target_column)
                
                fairness_metrics[attr] = {
                    'demographic_parity': demographic_parity,
                    'equality_of_opportunity': equality_of_opportunity,
                    'statistical_parity': statistical_parity
                }
        
        return fairness_metrics
    
    def _calculate_demographic_parity(self, df: pd.DataFrame, sensitive_attr: str, 
                                    target_column: str) -> Dict[str, Any]:
        """Calculate demographic parity across groups"""
        
        groups = df[sensitive_attr].unique()
        acceptance_rates = {}
        
        for group in groups:
            group_data = df[df[sensitive_attr] == group]
            acceptance_rates[group] = group_data[target_column].mean()
        
        # Calculate disparity
        max_rate = max(acceptance_rates.values())
        min_rate = min(acceptance_rates.values())
        disparity = max_rate - min_rate
        ratio = max_rate / min_rate if min_rate > 0 else float('inf')
        
        return {
            'acceptance_rates': acceptance_rates,
            'disparity': disparity,
            'ratio': ratio,
            'fair': disparity < 0.1,  # Less than 10% difference
            'groups': list(groups)
        }
    
    def _calculate_equality_of_opportunity(self, df: pd.DataFrame, sensitive_attr: str, 
                                         target_column: str) -> Dict[str, Any]:
        """Calculate equality of opportunity for positive class"""
        
        groups = df[sensitive_attr].unique()
        opportunity_rates = {}
        
        for group in groups:
            group_data = df[df[sensitive_attr] == group]
            # Only consider positive examples (target = 1)
            positive_data = group_data[group_data[target_column] == 1]
            
            if len(positive_data) > 0:
                # Calculate true positive rate for this group
                opportunity_rates[group] = len(positive_data) / len(group_data)
            else:
                opportunity_rates[group] = 0
        
        # Calculate disparity
        max_rate = max(opportunity_rates.values())
        min_rate = min(opportunity_rates.values())
        disparity = max_rate - min_rate
        ratio = max_rate / min_rate if min_rate > 0 else float('inf')
        
        return {
            'opportunity_rates': opportunity_rates,
            'disparity': disparity,
            'ratio': ratio,
            'fair': disparity < 0.1,  # Less than 10% difference
            'groups': list(groups)
        }
    
    def _calculate_statistical_parity(self, df: pd.DataFrame, sensitive_attr: str, 
                                    target_column: str) -> Dict[str, Any]:
        """Calculate statistical parity difference"""
        
        groups = df[sensitive_attr].unique()
        if len(groups) != 2:
            return {'error': 'Statistical parity requires exactly 2 groups'}
        
        group1, group2 = groups
        
        # Calculate positive prediction rates
        group1_rate = df[df[sensitive_attr] == group1][target_column].mean()
        group2_rate = df[df[sensitive_attr] == group2][target_column].mean()
        
        statistical_parity_difference = group1_rate - group2_rate
        
        return {
            'group1_rate': group1_rate,
            'group2_rate': group2_rate,
            'statistical_parity_difference': statistical_parity_difference,
            'fair': abs(statistical_parity_difference) < 0.1,  # Less than 10% difference
            'groups': [group1, group2]
        }
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on bias analysis findings"""
        
        recommendations = []
        
        # Data quality recommendations
        data_quality = analysis_results.get('data_quality', {})
        
        if data_quality.get('data_skew'):
            for attr, skew_info in data_quality['data_skew'].items():
                if skew_info['imbalance_ratio'] > 5:
                    recommendations.append(
                        f"High data imbalance detected in {attr} (ratio: {skew_info['imbalance_ratio']:.2f}). "
                        "Consider oversampling minority groups or collecting more balanced data."
                    )
        
        # Bias detection recommendations
        bias_detection = analysis_results.get('bias_detection', {})
        
        if bias_detection.get('reporting_bias', {}).get('detected'):
            recommendations.append(
                "Reporting bias detected in target variable. Consider collecting more representative data "
                "or using techniques like SMOTE to balance the dataset."
            )
        
        if bias_detection.get('historical_bias', {}).get('detected'):
            recommendations.append(
                "Historical bias detected. Consider using more recent data or applying bias mitigation "
                "techniques like MinDiff or Counterfactual Logit Pairing."
            )
        
        if bias_detection.get('selection_bias', {}).get('detected'):
            recommendations.append(
                "Selection bias detected. Review data collection methodology and consider "
                "collecting more representative samples."
            )
        
        # Fairness metrics recommendations
        fairness_metrics = analysis_results.get('fairness_metrics', {})
        
        for attr, metrics in fairness_metrics.items():
            if not metrics.get('demographic_parity', {}).get('fair'):
                recommendations.append(
                    f"Demographic parity violation detected for {attr}. Consider applying "
                    "fairness-aware training techniques."
                )
            
            if not metrics.get('equality_of_opportunity', {}).get('fair'):
                recommendations.append(
                    f"Equality of opportunity violation detected for {attr}. Consider using "
                    "techniques that ensure equal true positive rates across groups."
                )
        
        if not recommendations:
            recommendations.append("No significant bias issues detected. Continue monitoring for bias as the model evolves.")
        
        return recommendations
    
    def analyze_model_bias(self, model, test_data: pd.DataFrame, sensitive_attributes: List[str], 
                          target_column: str) -> Dict[str, Any]:
        """
        Analyze bias in model predictions
        
        Args:
            model: Trained machine learning model
            test_data: Test dataset
            sensitive_attributes: List of sensitive attribute column names
            target_column: Target variable column name
            
        Returns:
            Dictionary containing model bias analysis results
        """
        try:
            # Generate predictions
            X_test = test_data.drop([target_column] + sensitive_attributes, axis=1, errors='ignore')
            predictions = model.predict(X_test)
            
            # Add predictions to test data
            test_data_with_preds = test_data.copy()
            test_data_with_preds['predictions'] = predictions
            
            # Calculate model fairness metrics
            model_fairness = {}
            
            for attr in sensitive_attributes:
                if attr in test_data.columns:
                    # Demographic parity with predictions
                    demo_parity = self._calculate_demographic_parity(
                        test_data_with_preds, attr, 'predictions'
                    )
                    
                    # Equality of opportunity with predictions
                    eq_opportunity = self._calculate_equality_of_opportunity(
                        test_data_with_preds, attr, target_column
                    )
                    
                    # Subgroup performance analysis
                    subgroup_performance = self._analyze_subgroup_performance(
                        test_data_with_preds, attr, target_column, 'predictions'
                    )
                    
                    model_fairness[attr] = {
                        'demographic_parity': demo_parity,
                        'equality_of_opportunity': eq_opportunity,
                        'subgroup_performance': subgroup_performance
                    }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'model_fairness': model_fairness,
                'overall_performance': self._calculate_overall_performance(
                    test_data[target_column], predictions
                ),
                'bias_summary': self._summarize_model_bias(model_fairness)
            }
            
        except Exception as e:
            logger.error(f"Error in model bias analysis: {str(e)}")
            raise
    
    def _analyze_subgroup_performance(self, df: pd.DataFrame, sensitive_attr: str, 
                                    target_column: str, prediction_column: str) -> Dict[str, Any]:
        """Analyze model performance across subgroups"""
        
        groups = df[sensitive_attr].unique()
        performance_by_group = {}
        
        for group in groups:
            group_data = df[df[sensitive_attr] == group]
            
            if len(group_data) > 0:
                y_true = group_data[target_column]
                y_pred = group_data[prediction_column]
                
                performance_by_group[group] = {
                    'sample_size': len(group_data),
                    'accuracy': accuracy_score(y_true, y_pred),
                    'precision': precision_score(y_true, y_pred, zero_division=0),
                    'recall': recall_score(y_true, y_pred, zero_division=0),
                    'f1_score': f1_score(y_true, y_pred, zero_division=0)
                }
        
        return performance_by_group
    
    def _calculate_overall_performance(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate overall model performance metrics"""
        
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0)
        }
    
    def _summarize_model_bias(self, model_fairness: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize bias findings across all sensitive attributes"""
        
        bias_summary = {
            'total_attributes_analyzed': len(model_fairness),
            'attributes_with_bias': 0,
            'demographic_parity_violations': 0,
            'equality_of_opportunity_violations': 0,
            'performance_disparities': 0
        }
        
        for attr, metrics in model_fairness.items():
            if not metrics['demographic_parity']['fair']:
                bias_summary['demographic_parity_violations'] += 1
            
            if not metrics['equality_of_opportunity']['fair']:
                bias_summary['equality_of_opportunity_violations'] += 1
            
            # Check for performance disparities
            subgroup_perf = metrics['subgroup_performance']
            if len(subgroup_perf) > 1:
                accuracies = [perf['accuracy'] for perf in subgroup_perf.values()]
                if max(accuracies) - min(accuracies) > 0.1:  # 10% difference
                    bias_summary['performance_disparities'] += 1
        
        bias_summary['attributes_with_bias'] = (
            bias_summary['demographic_parity_violations'] +
            bias_summary['equality_of_opportunity_violations'] +
            bias_summary['performance_disparities']
        )
        
        bias_summary['overall_bias_level'] = 'high' if bias_summary['attributes_with_bias'] > 2 else \
                                           'medium' if bias_summary['attributes_with_bias'] > 0 else 'low'
        
        return bias_summary
