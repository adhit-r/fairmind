# Machine Learning & AI Governance Algorithms

## 🧠 ML Architecture Overview

Fairmind v2 implements state-of-the-art machine learning algorithms specifically designed for AI governance, bias detection, and model explainability. Our ML stack combines multiple frameworks to provide comprehensive fairness assessments.

### Core ML Frameworks

- **Fairlearn**: Microsoft's fairness assessment toolkit
- **AIF360**: IBM's comprehensive bias detection library  
- **SHAP**: SHapley Additive exPlanations for model interpretability
- **LIME**: Local Interpretable Model-agnostic Explanations
- **scikit-learn**: Core machine learning algorithms
- **NumPy/Pandas**: Data processing and numerical computations

## 🎯 Bias Detection Algorithms

### 1. Demographic Parity (Statistical Parity)

**Concept**: Ensures equal positive prediction rates across different demographic groups.

```python
# apps/ml-service/algorithms/demographic_parity.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from fairlearn.metrics import demographic_parity_difference, demographic_parity_ratio
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class DemographicParityAnalyzer:
    """
    Analyzes demographic parity violations in ML models
    """
    
    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self.results = {}
    
    def analyze(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_features: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Comprehensive demographic parity analysis
        
        Args:
            y_true: Ground truth labels
            y_pred: Model predictions
            sensitive_features: DataFrame with sensitive attributes
            confidence_level: Confidence level for statistical tests
            
        Returns:
            Dictionary containing analysis results
        """
        results = {}
        
        for attr in sensitive_features.columns:
            logger.info(f"Analyzing demographic parity for attribute: {attr}")
            
            # Calculate basic metrics
            dp_diff = demographic_parity_difference(
                y_true, y_pred, sensitive_features=sensitive_features[attr]
            )
            
            dp_ratio = demographic_parity_ratio(
                y_true, y_pred, sensitive_features=sensitive_features[attr]
            )
            
            # Statistical significance testing
            groups = sensitive_features[attr].unique()
            group_metrics = self._calculate_group_metrics(
                y_true, y_pred, sensitive_features[attr], groups
            )
            
            # Confidence intervals using bootstrap
            ci_lower, ci_upper = self._bootstrap_confidence_interval(
                y_true, y_pred, sensitive_features[attr], confidence_level
            )
            
            # Intersectional analysis
            intersectional_results = self._intersectional_analysis(
                y_true, y_pred, sensitive_features, attr
            )
            
            results[attr] = {
                'demographic_parity_difference': dp_diff,
                'demographic_parity_ratio': dp_ratio,
                'threshold': self.threshold,
                'violation': abs(dp_diff) > self.threshold,
                'severity': self._calculate_severity(dp_diff),
                'confidence_interval': {
                    'lower': ci_lower,
                    'upper': ci_upper,
                    'level': confidence_level
                },
                'group_metrics': group_metrics,
                'statistical_significance': self._statistical_significance_test(
                    y_true, y_pred, sensitive_features[attr]
                ),
                'intersectional_analysis': intersectional_results,
                'recommendations': self._generate_recommendations(dp_diff, group_metrics)
            }
        
        return results
    
    def _calculate_group_metrics(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        groups: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """Calculate detailed metrics for each demographic group"""
        group_metrics = {}
        
        for group in groups:
            mask = sensitive_attr == group
            group_y_true = y_true[mask]
            group_y_pred = y_pred[mask]
            
            if len(group_y_true) == 0:
                continue
                
            # Basic rates
            positive_rate = np.mean(group_y_pred)
            base_rate = np.mean(group_y_true)
            
            # Performance metrics
            if len(np.unique(group_y_true)) > 1:
                tn = np.sum((group_y_true == 0) & (group_y_pred == 0))
                fp = np.sum((group_y_true == 0) & (group_y_pred == 1))
                fn = np.sum((group_y_true == 1) & (group_y_pred == 0))
                tp = np.sum((group_y_true == 1) & (group_y_pred == 1))
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
                
                group_metrics[str(group)] = {
                    'size': len(group_y_true),
                    'positive_rate': positive_rate,
                    'base_rate': base_rate,
                    'precision': precision,
                    'recall': recall,
                    'specificity': specificity,
                    'true_positives': int(tp),
                    'false_positives': int(fp),
                    'true_negatives': int(tn),
                    'false_negatives': int(fn)
                }
            else:
                group_metrics[str(group)] = {
                    'size': len(group_y_true),
                    'positive_rate': positive_rate,
                    'base_rate': base_rate,
                    'precision': 0,
                    'recall': 0,
                    'specificity': 0,
                    'true_positives': 0,
                    'false_positives': 0,
                    'true_negatives': 0,
                    'false_negatives': 0
                }
        
        return group_metrics
    
    def _bootstrap_confidence_interval(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        confidence_level: float,
        n_bootstrap: int = 1000
    ) -> Tuple[float, float]:
        """Calculate confidence interval using bootstrap resampling"""
        bootstrap_diffs = []
        n_samples = len(y_true)
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            indices = np.random.choice(n_samples, n_samples, replace=True)
            boot_y_true = y_true[indices]
            boot_y_pred = y_pred[indices]
            boot_sensitive = sensitive_attr.iloc[indices]
            
            # Calculate demographic parity difference
            dp_diff = demographic_parity_difference(
                boot_y_true, boot_y_pred, sensitive_features=boot_sensitive
            )
            bootstrap_diffs.append(dp_diff)
        
        # Calculate confidence interval
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_diffs, lower_percentile)
        ci_upper = np.percentile(bootstrap_diffs, upper_percentile)
        
        return ci_lower, ci_upper
    
    def _intersectional_analysis(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_features: pd.DataFrame, 
        primary_attr: str
    ) -> Dict[str, Any]:
        """Analyze intersectional bias across multiple attributes"""
        if len(sensitive_features.columns) < 2:
            return {"available": False, "reason": "Insufficient attributes for intersectional analysis"}
        
        intersectional_results = {"available": True, "combinations": {}}
        
        # Analyze combinations with primary attribute
        other_attrs = [col for col in sensitive_features.columns if col != primary_attr]
        
        for other_attr in other_attrs:
            # Create intersectional groups
            intersectional_groups = sensitive_features[primary_attr].astype(str) + "_" + \
                                   sensitive_features[other_attr].astype(str)
            
            # Calculate metrics for each intersectional group
            unique_groups = intersectional_groups.unique()
            group_metrics = {}
            
            for group in unique_groups:
                mask = intersectional_groups == group
                if np.sum(mask) < 10:  # Skip small groups
                    continue
                
                group_y_pred = y_pred[mask]
                positive_rate = np.mean(group_y_pred)
                group_size = np.sum(mask)
                
                group_metrics[group] = {
                    'positive_rate': positive_rate,
                    'size': int(group_size)
                }
            
            if len(group_metrics) > 1:
                # Calculate max difference across intersectional groups
                rates = [metrics['positive_rate'] for metrics in group_metrics.values()]
                max_diff = max(rates) - min(rates)
                
                intersectional_results["combinations"][f"{primary_attr}_x_{other_attr}"] = {
                    'max_difference': max_diff,
                    'violation': max_diff > self.threshold,
                    'group_metrics': group_metrics
                }
        
        return intersectional_results
    
    def _statistical_significance_test(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series
    ) -> Dict[str, Any]:
        """Perform statistical significance tests"""
        groups = sensitive_attr.unique()
        if len(groups) != 2:
            return {"available": False, "reason": "Chi-square test requires binary sensitive attribute"}
        
        # Prepare contingency table
        group1_mask = sensitive_attr == groups[0]
        group2_mask = sensitive_attr == groups[1]
        
        group1_pos = np.sum(y_pred[group1_mask])
        group1_neg = np.sum(group1_mask) - group1_pos
        group2_pos = np.sum(y_pred[group2_mask])
        group2_neg = np.sum(group2_mask) - group2_pos
        
        contingency_table = np.array([
            [group1_pos, group1_neg],
            [group2_pos, group2_neg]
        ])
        
        # Chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        return {
            "available": True,
            "test": "chi_square",
            "statistic": chi2,
            "p_value": p_value,
            "degrees_of_freedom": dof,
            "significant": p_value < 0.05,
            "effect_size": self._calculate_cramers_v(chi2, contingency_table.sum())
        }
    
    def _calculate_cramers_v(self, chi2: float, n: int) -> float:
        """Calculate Cramer's V effect size"""
        return np.sqrt(chi2 / n)
    
    def _calculate_severity(self, dp_diff: float) -> str:
        """Calculate severity level of bias violation"""
        abs_diff = abs(dp_diff)
        
        if abs_diff <= self.threshold:
            return "none"
        elif abs_diff <= 2 * self.threshold:
            return "low"
        elif abs_diff <= 3 * self.threshold:
            return "moderate"
        else:
            return "high"
    
    def _generate_recommendations(
        self, 
        dp_diff: float, 
        group_metrics: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        if abs(dp_diff) > self.threshold:
            # Identify disadvantaged group
            group_rates = {group: metrics['positive_rate'] for group, metrics in group_metrics.items()}
            min_rate_group = min(group_rates, key=group_rates.get)
            max_rate_group = max(group_rates, key=group_rates.get)
            
            recommendations.append({
                "type": "bias_mitigation",
                "priority": "high",
                "description": f"Demographic parity violation detected. Group '{min_rate_group}' has significantly lower positive prediction rate.",
                "action": "Consider bias mitigation techniques such as resampling, reweighting, or fairness constraints."
            })
            
            # Check for sample size issues
            small_groups = [group for group, metrics in group_metrics.items() if metrics['size'] < 100]
            if small_groups:
                recommendations.append({
                    "type": "data_collection",
                    "priority": "medium", 
                    "description": f"Small sample size detected for groups: {', '.join(small_groups)}",
                    "action": "Collect more data for underrepresented groups or use synthetic data generation."
                })
        
        return recommendations
```

### 2. Equalized Odds Implementation

```python
# apps/ml-service/algorithms/equalized_odds.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from fairlearn.metrics import equalized_odds_difference, equalized_odds_ratio
from sklearn.metrics import confusion_matrix
import logging

logger = logging.getLogger(__name__)

class EqualizedOddsAnalyzer:
    """
    Analyzes equalized odds violations in ML models
    Ensures equal true positive rates and false positive rates across groups
    """
    
    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
    
    def analyze(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_features: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Comprehensive equalized odds analysis
        """
        results = {}
        
        for attr in sensitive_features.columns:
            logger.info(f"Analyzing equalized odds for attribute: {attr}")
            
            # Calculate equalized odds metrics
            eo_diff = equalized_odds_difference(
                y_true, y_pred, sensitive_features=sensitive_features[attr]
            )
            
            eo_ratio = equalized_odds_ratio(
                y_true, y_pred, sensitive_features=sensitive_features[attr]
            )
            
            # Detailed TPR and FPR analysis
            tpr_fpr_analysis = self._analyze_tpr_fpr_by_group(
                y_true, y_pred, sensitive_features[attr]
            )
            
            # Statistical significance
            significance_test = self._statistical_significance_test(
                y_true, y_pred, sensitive_features[attr]
            )
            
            # Confidence intervals
            ci_lower, ci_upper = self._bootstrap_confidence_interval(
                y_true, y_pred, sensitive_features[attr], confidence_level
            )
            
            results[attr] = {
                'equalized_odds_difference': eo_diff,
                'equalized_odds_ratio': eo_ratio,
                'threshold': self.threshold,
                'violation': abs(eo_diff) > self.threshold,
                'severity': self._calculate_severity(eo_diff),
                'tpr_fpr_analysis': tpr_fpr_analysis,
                'confidence_interval': {
                    'lower': ci_lower,
                    'upper': ci_upper,
                    'level': confidence_level
                },
                'statistical_significance': significance_test,
                'recommendations': self._generate_recommendations(eo_diff, tpr_fpr_analysis)
            }
        
        return results
    
    def _analyze_tpr_fpr_by_group(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series
    ) -> Dict[str, Dict[str, float]]:
        """Analyze True Positive Rate and False Positive Rate by group"""
        groups = sensitive_attr.unique()
        group_analysis = {}
        
        for group in groups:
            mask = sensitive_attr == group
            group_y_true = y_true[mask]
            group_y_pred = y_pred[mask]
            
            if len(group_y_true) == 0:
                continue
            
            # Calculate confusion matrix
            if len(np.unique(group_y_true)) > 1:
                tn, fp, fn, tp = confusion_matrix(
                    group_y_true, group_y_pred, labels=[0, 1]
                ).ravel()
                
                # Calculate rates
                tpr = tp / (tp + fn) if (tp + fn) > 0 else 0  # Sensitivity/Recall
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0  # 1 - Specificity
                tnr = tn / (tn + fp) if (tn + fp) > 0 else 0  # Specificity
                fnr = fn / (fn + tp) if (fn + tp) > 0 else 0  # 1 - Sensitivity
                
                group_analysis[str(group)] = {
                    'size': len(group_y_true),
                    'true_positive_rate': tpr,
                    'false_positive_rate': fpr,
                    'true_negative_rate': tnr,
                    'false_negative_rate': fnr,
                    'positive_cases': int(tp + fn),
                    'negative_cases': int(tn + fp),
                    'confusion_matrix': {
                        'tp': int(tp), 'fp': int(fp), 
                        'tn': int(tn), 'fn': int(fn)
                    }
                }
            else:
                # Handle case with only one class
                group_analysis[str(group)] = {
                    'size': len(group_y_true),
                    'true_positive_rate': 0,
                    'false_positive_rate': 0,
                    'true_negative_rate': 0,
                    'false_negative_rate': 0,
                    'positive_cases': int(np.sum(group_y_true)),
                    'negative_cases': int(len(group_y_true) - np.sum(group_y_true)),
                    'warning': 'Only one class present in group'
                }
        
        return group_analysis
    
    def _bootstrap_confidence_interval(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        confidence_level: float,
        n_bootstrap: int = 1000
    ) -> Tuple[float, float]:
        """Calculate confidence interval for equalized odds difference"""
        bootstrap_diffs = []
        n_samples = len(y_true)
        
        for _ in range(n_bootstrap):
            indices = np.random.choice(n_samples, n_samples, replace=True)
            boot_y_true = y_true[indices]
            boot_y_pred = y_pred[indices]
            boot_sensitive = sensitive_attr.iloc[indices]
            
            try:
                eo_diff = equalized_odds_difference(
                    boot_y_true, boot_y_pred, sensitive_features=boot_sensitive
                )
                bootstrap_diffs.append(eo_diff)
            except:
                # Skip bootstrap samples that cause calculation errors
                continue
        
        if len(bootstrap_diffs) < n_bootstrap * 0.5:
            return 0.0, 0.0  # Return default if too many bootstrap samples failed
        
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_diffs, lower_percentile)
        ci_upper = np.percentile(bootstrap_diffs, upper_percentile)
        
        return ci_lower, ci_upper
    
    def _statistical_significance_test(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series
    ) -> Dict[str, Any]:
        """Statistical significance test for equalized odds"""
        from scipy.stats import chi2_contingency
        
        groups = sensitive_attr.unique()
        if len(groups) != 2:
            return {"available": False, "reason": "Test requires binary sensitive attribute"}
        
        # Create contingency tables for positive and negative classes separately
        results = {"available": True, "positive_class_test": {}, "negative_class_test": {}}
        
        for class_val, class_name in [(1, "positive_class_test"), (0, "negative_class_test")]:
            class_mask = y_true == class_val
            if np.sum(class_mask) < 5:  # Too few samples
                results[class_name] = {"available": False, "reason": f"Too few {class_val} class samples"}
                continue
            
            class_y_true = y_true[class_mask]
            class_y_pred = y_pred[class_mask]
            class_sensitive = sensitive_attr[class_mask]
            
            # Create contingency table: [group1_correct, group1_incorrect], [group2_correct, group2_incorrect]
            group1_mask = class_sensitive == groups[0]
            group2_mask = class_sensitive == groups[1]
            
            group1_correct = np.sum(class_y_true[group1_mask] == class_y_pred[group1_mask])
            group1_incorrect = np.sum(group1_mask) - group1_correct
            group2_correct = np.sum(class_y_true[group2_mask] == class_y_pred[group2_mask])
            group2_incorrect = np.sum(group2_mask) - group2_correct
            
            contingency_table = np.array([
                [group1_correct, group1_incorrect],
                [group2_correct, group2_incorrect]
            ])
            
            if np.any(contingency_table < 5):  # Chi-square assumption violation
                results[class_name] = {
                    "available": False, 
                    "reason": "Expected frequencies too low for chi-square test"
                }
                continue
            
            chi2, p_value, dof, expected = chi2_contingency(contingency_table)
            
            results[class_name] = {
                "available": True,
                "chi2_statistic": chi2,
                "p_value": p_value,
                "degrees_of_freedom": dof,
                "significant": p_value < 0.05,
                "contingency_table": contingency_table.tolist()
            }
        
        return results
    
    def _calculate_severity(self, eo_diff: float) -> str:
        """Calculate severity of equalized odds violation"""
        abs_diff = abs(eo_diff)
        
        if abs_diff <= self.threshold:
            return "none"
        elif abs_diff <= 2 * self.threshold:
            return "low"
        elif abs_diff <= 3 * self.threshold:
            return "moderate"
        else:
            return "high"
    
    def _generate_recommendations(
        self, 
        eo_diff: float, 
        group_analysis: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, str]]:
        """Generate recommendations for equalized odds violations"""
        recommendations = []
        
        if abs(eo_diff) > self.threshold:
            # Identify which group has performance issues
            tpr_by_group = {group: analysis['true_positive_rate'] 
                           for group, analysis in group_analysis.items() 
                           if 'true_positive_rate' in analysis}
            
            if tpr_by_group:
                min_tpr_group = min(tpr_by_group, key=tpr_by_group.get)
                max_tpr_group = max(tpr_by_group, key=tpr_by_group.get)
                
                recommendations.append({
                    "type": "performance_parity",
                    "priority": "high",
                    "description": f"Equalized odds violation: Group '{min_tpr_group}' has lower true positive rate than '{max_tpr_group}'.",
                    "action": "Consider threshold optimization, model recalibration, or separate models per group."
                })
            
            # Check for class imbalance within groups
            for group, analysis in group_analysis.items():
                if 'positive_cases' in analysis and 'negative_cases' in analysis:
                    pos_cases = analysis['positive_cases']
                    neg_cases = analysis['negative_cases']
                    
                    if pos_cases > 0 and neg_cases > 0:
                        imbalance_ratio = max(pos_cases, neg_cases) / min(pos_cases, neg_cases)
                        
                        if imbalance_ratio > 10:  # Severe class imbalance
                            recommendations.append({
                                "type": "class_imbalance",
                                "priority": "medium",
                                "description": f"Severe class imbalance in group '{group}' (ratio: {imbalance_ratio:.1f}:1)",
                                "action": "Address class imbalance using resampling, cost-sensitive learning, or synthetic data generation."
                            })
        
        return recommendations
```

### 3. Individual Fairness Algorithm

```python
# apps/ml-service/algorithms/individual_fairness.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Callable
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.neighbors import NearestNeighbors
import logging

logger = logging.getLogger(__name__)

class IndividualFairnessAnalyzer:
    """
    Analyzes individual fairness: similar individuals should receive similar predictions
    """
    
    def __init__(self, similarity_threshold: float = 0.1, k_neighbors: int = 5):
        self.similarity_threshold = similarity_threshold
        self.k_neighbors = k_neighbors
    
    def analyze(
        self, 
        X: pd.DataFrame,
        y_pred: np.ndarray,
        sensitive_features: pd.DataFrame,
        distance_metric: str = 'euclidean',
        protected_attr_weight: float = 0.0
    ) -> Dict[str, Any]:
        """
        Analyze individual fairness violations
        
        Args:
            X: Feature matrix
            y_pred: Model predictions
            sensitive_features: Sensitive attributes
            distance_metric: Distance metric for similarity
            protected_attr_weight: Weight for protected attributes in distance calculation
        """
        logger.info("Starting individual fairness analysis")
        
        # Preprocess features for distance calculation
        X_processed = self._preprocess_features(X)
        
        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(
            X_processed, sensitive_features, distance_metric, protected_attr_weight
        )
        
        # Find violations
        violations = self._find_fairness_violations(
            similarity_matrix, y_pred, X, sensitive_features
        )
        
        # Calculate metrics
        metrics = self._calculate_individual_fairness_metrics(
            violations, len(X), y_pred
        )
        
        # Generate detailed analysis
        detailed_analysis = self._detailed_violation_analysis(violations, X, sensitive_features)
        
        results = {
            'individual_fairness_score': metrics['fairness_score'],
            'violation_rate': metrics['violation_rate'],
            'average_prediction_difference': metrics['avg_pred_diff'],
            'max_prediction_difference': metrics['max_pred_diff'],
            'total_violations': len(violations),
            'violations_by_attribute': detailed_analysis['violations_by_attribute'],
            'similarity_threshold': self.similarity_threshold,
            'distance_metric': distance_metric,
            'k_neighbors': self.k_neighbors,
            'detailed_violations': detailed_analysis['detailed_violations'][:100],  # Limit output
            'recommendations': self._generate_recommendations(metrics, detailed_analysis)
        }
        
        return results
    
    def _preprocess_features(self, X: pd.DataFrame) -> np.ndarray:
        """Preprocess features for distance calculation"""
        from sklearn.preprocessing import StandardScaler
        from sklearn.compose import ColumnTransformer
        from sklearn.preprocessing import OneHotEncoder
        
        # Identify numeric and categorical columns
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Create preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numeric_features),
                ('cat', OneHotEncoder(drop='first', sparse_output=False), categorical_features)
            ],
            remainder='passthrough'
        )
        
        X_processed = preprocessor.fit_transform(X)
        return X_processed
    
    def _calculate_similarity_matrix(
        self, 
        X_processed: np.ndarray,
        sensitive_features: pd.DataFrame,
        distance_metric: str,
        protected_attr_weight: float
    ) -> np.ndarray:
        """Calculate similarity matrix between all pairs of individuals"""
        
        # Calculate feature distances
        feature_distances = pairwise_distances(X_processed, metric=distance_metric)
        
        if protected_attr_weight > 0:
            # Calculate protected attribute distances
            protected_distances = self._calculate_protected_distances(sensitive_features)
            
            # Combine distances
            total_distances = (1 - protected_attr_weight) * feature_distances + \
                            protected_attr_weight * protected_distances
        else:
            total_distances = feature_distances
        
        # Convert distances to similarities (0 = identical, 1 = most different)
        max_distance = np.max(total_distances)
        similarity_matrix = 1 - (total_distances / max_distance)
        
        return similarity_matrix
    
    def _calculate_protected_distances(self, sensitive_features: pd.DataFrame) -> np.ndarray:
        """Calculate distances based on protected attributes"""
        n_samples = len(sensitive_features)
        distances = np.zeros((n_samples, n_samples))
        
        for col in sensitive_features.columns:
            # For categorical attributes, distance is 0 if same, 1 if different
            if sensitive_features[col].dtype == 'object' or sensitive_features[col].dtype.name == 'category':
                col_distances = (sensitive_features[col].values[:, np.newaxis] != 
                               sensitive_features[col].values[np.newaxis, :]).astype(float)
            else:
                # For numeric attributes, use normalized absolute difference
                col_values = sensitive_features[col].values
                col_distances = np.abs(col_values[:, np.newaxis] - col_values[np.newaxis, :])
                col_distances = col_distances / np.max(col_distances) if np.max(col_distances) > 0 else col_distances
            
            distances += col_distances
        
        # Average across all protected attributes
        distances = distances / len(sensitive_features.columns)
        return distances
    
    def _find_fairness_violations(
        self, 
        similarity_matrix: np.ndarray,
        y_pred: np.ndarray,
        X: pd.DataFrame,
        sensitive_features: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Find individual fairness violations"""
        violations = []
        n_samples = len(X)
        
        # Use k-nearest neighbors to find similar individuals
        nn = NearestNeighbors(n_neighbors=self.k_neighbors + 1, metric='precomputed')
        nn.fit(1 - similarity_matrix)  # Convert similarity to distance
        
        for i in range(n_samples):
            # Find k nearest neighbors (excluding self)
            distances, neighbor_indices = nn.kneighbors([1 - similarity_matrix[i]])
            neighbor_indices = neighbor_indices[0][1:]  # Exclude self
            distances = 1 - distances[0][1:]  # Convert back to similarities
            
            # Check for violations with similar neighbors
            for j, neighbor_idx in enumerate(neighbor_indices):
                similarity = distances[j]
                
                if similarity >= (1 - self.similarity_threshold):  # Highly similar
                    pred_diff = abs(y_pred[i] - y_pred[neighbor_idx])
                    
                    if pred_diff > self.similarity_threshold:  # Prediction difference too large
                        violations.append({
                            'individual_1': int(i),
                            'individual_2': int(neighbor_idx),
                            'similarity': float(similarity),
                            'prediction_difference': float(pred_diff),
                            'prediction_1': float(y_pred[i]),
                            'prediction_2': float(y_pred[neighbor_idx]),
                            'sensitive_features_1': sensitive_features.iloc[i].to_dict(),
                            'sensitive_features_2': sensitive_features.iloc[neighbor_idx].to_dict(),
                            'feature_vector_1': X.iloc[i].to_dict(),
                            'feature_vector_2': X.iloc[neighbor_idx].to_dict()
                        })
        
        # Remove duplicate violations (A-B and B-A pairs)
        unique_violations = []
        seen_pairs = set()
        
        for violation in violations:
            pair = tuple(sorted([violation['individual_1'], violation['individual_2']]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_violations.append(violation)
        
        return unique_violations
    
    def _calculate_individual_fairness_metrics(
        self, 
        violations: List[Dict[str, Any]], 
        total_samples: int,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Calculate overall individual fairness metrics"""
        if not violations:
            return {
                'fairness_score': 1.0,
                'violation_rate': 0.0,
                'avg_pred_diff': 0.0,
                'max_pred_diff': 0.0
            }
        
        violation_rate = len(violations) / (total_samples * (total_samples - 1) / 2)
        
        pred_differences = [v['prediction_difference'] for v in violations]
        avg_pred_diff = np.mean(pred_differences)
        max_pred_diff = np.max(pred_differences)
        
        # Fairness score: 1 - normalized violation severity
        fairness_score = max(0, 1 - (avg_pred_diff / self.similarity_threshold))
        
        return {
            'fairness_score': fairness_score,
            'violation_rate': violation_rate,
            'avg_pred_diff': avg_pred_diff,
            'max_pred_diff': max_pred_diff
        }
    
    def _detailed_violation_analysis(
        self, 
        violations: List[Dict[str, Any]], 
        X: pd.DataFrame,
        sensitive_features: pd.DataFrame
    ) -> Dict[str, Any]:
        """Perform detailed analysis of violations"""
        if not violations:
            return {
                'violations_by_attribute': {},
                'detailed_violations': []
            }
        
        violations_by_attribute = {}
        
        # Count violations by protected attribute differences
        for attr in sensitive_features.columns:
            violations_by_attribute[attr] = {
                'same_group_violations': 0,
                'different_group_violations': 0,
                'total_violations': 0
            }
            
            for violation in violations:
                val1 = violation['sensitive_features_1'][attr]
                val2 = violation['sensitive_features_2'][attr]
                
                violations_by_attribute[attr]['total_violations'] += 1
                
                if val1 == val2:
                    violations_by_attribute[attr]['same_group_violations'] += 1
                else:
                    violations_by_attribute[attr]['different_group_violations'] += 1
        
        # Calculate percentages
        for attr in violations_by_attribute:
            total = violations_by_attribute[attr]['total_violations']
            if total > 0:
                violations_by_attribute[attr]['same_group_percentage'] = \
                    violations_by_attribute[attr]['same_group_violations'] / total * 100
                violations_by_attribute[attr]['different_group_percentage'] = \
                    violations_by_attribute[attr]['different_group_violations'] / total * 100
        
        return {
            'violations_by_attribute': violations_by_attribute,
            'detailed_violations': violations
        }
    
    def _generate_recommendations(
        self, 
        metrics: Dict[str, float], 
        detailed_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate recommendations for individual fairness violations"""
        recommendations = []
        
        if metrics['fairness_score'] < 0.7:  # Significant violations
            recommendations.append({
                "type": "individual_fairness_violation",
                "priority": "high",
                "description": f"Individual fairness score is low ({metrics['fairness_score']:.2f}). Similar individuals receive different predictions.",
                "action": "Consider using fairness-aware ML algorithms or post-processing techniques to ensure similar treatment of similar individuals."
            })
        
        if metrics['violation_rate'] > 0.1:  # High violation rate
            recommendations.append({
                "type": "high_violation_rate",
                "priority": "medium",
                "description": f"High individual fairness violation rate ({metrics['violation_rate']:.2%})",
                "action": "Review feature engineering and model architecture to reduce prediction variance for similar individuals."
            })
        
        # Analyze violations by protected attributes
        for attr, analysis in detailed_analysis['violations_by_attribute'].items():
            if analysis['different_group_percentage'] > 70:  # Most violations between different groups
                recommendations.append({
                    "type": "between_group_violations",
                    "priority": "medium",
                    "description": f"Most individual fairness violations for '{attr}' occur between different groups ({analysis['different_group_percentage']:.1f}%)",
                    "action": f"Focus on improving fairness between different '{attr}' groups through targeted bias mitigation."
                })
        
        return recommendations
```

This comprehensive ML documentation provides the foundation for implementing sophisticated bias detection and fairness analysis algorithms in the Fairmind v2 platform. The algorithms are designed to be modular, extensible, and provide actionable insights for AI governance.
