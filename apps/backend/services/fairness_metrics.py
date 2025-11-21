"""
Production-ready fairness metrics implementation.
Based on industry standards (Fairlearn, AIF360, AWS Clarify).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FairnessMetric(Enum):
    """Supported fairness metrics"""
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    EQUAL_OPPORTUNITY = "equal_opportunity"
    PREDICTIVE_PARITY = "predictive_parity"
    CALIBRATION = "calibration"


@dataclass
class FairnessResult:
    """Result of a fairness metric calculation"""
    metric_name: str
    overall_score: float
    group_scores: Dict[str, float]
    disparity: float
    passed: bool
    threshold: float
    interpretation: str
    recommendations: List[str]


class FairnessCalculator:
    """Calculate fairness metrics for binary classification models"""
    
    def __init__(self, threshold: float = 0.8):
        """
        Args:
            threshold: Minimum acceptable fairness ratio (0.8 = 80% rule)
        """
        self.threshold = threshold
    
    def calculate_demographic_parity(
        self,
        predictions: np.ndarray,
        protected_attribute: np.ndarray,
        positive_label: int = 1
    ) -> FairnessResult:
        """
        Demographic Parity (Statistical Parity):
        P(Ŷ=1 | A=a) = P(Ŷ=1 | A=b) for all groups a, b
        
        Measures if positive prediction rate is equal across groups.
        """
        df = pd.DataFrame({
            'prediction': predictions,
            'group': protected_attribute
        })
        
        # Calculate positive rate for each group
        group_rates = df.groupby('group')['prediction'].apply(
            lambda x: (x == positive_label).mean()
        ).to_dict()
        
        # Calculate disparity (min/max ratio)
        rates = list(group_rates.values())
        if max(rates) == 0:
            disparity = 1.0
        else:
            disparity = min(rates) / max(rates)
        
        passed = disparity >= self.threshold
        
        # Generate interpretation
        interpretation = self._interpret_demographic_parity(group_rates, disparity)
        
        # Generate recommendations
        recommendations = self._recommend_demographic_parity(disparity, group_rates)
        
        return FairnessResult(
            metric_name="Demographic Parity",
            overall_score=disparity,
            group_scores=group_rates,
            disparity=1 - disparity,
            passed=passed,
            threshold=self.threshold,
            interpretation=interpretation,
            recommendations=recommendations
        )
    
    def calculate_equalized_odds(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        protected_attribute: np.ndarray,
        positive_label: int = 1
    ) -> FairnessResult:
        """
        Equalized Odds:
        P(Ŷ=1 | Y=y, A=a) = P(Ŷ=1 | Y=y, A=b) for all groups a, b and labels y
        
        Measures if TPR and FPR are equal across groups.
        """
        df = pd.DataFrame({
            'prediction': predictions,
            'truth': ground_truth,
            'group': protected_attribute
        })
        
        group_scores = {}
        tpr_scores = {}
        fpr_scores = {}
        
        for group in df['group'].unique():
            group_data = df[df['group'] == group]
            
            # True Positive Rate (Recall)
            tp = ((group_data['prediction'] == positive_label) & 
                  (group_data['truth'] == positive_label)).sum()
            fn = ((group_data['prediction'] != positive_label) & 
                  (group_data['truth'] == positive_label)).sum()
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            # False Positive Rate
            fp = ((group_data['prediction'] == positive_label) & 
                  (group_data['truth'] != positive_label)).sum()
            tn = ((group_data['prediction'] != positive_label) & 
                  (group_data['truth'] != positive_label)).sum()
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            
            tpr_scores[group] = tpr
            fpr_scores[group] = fpr
            group_scores[group] = (tpr + (1 - fpr)) / 2  # Combined score
        
        # Calculate disparity
        tpr_values = list(tpr_scores.values())
        fpr_values = list(fpr_scores.values())
        
        tpr_disparity = min(tpr_values) / max(tpr_values) if max(tpr_values) > 0 else 1.0
        fpr_disparity = min(fpr_values) / max(fpr_values) if max(fpr_values) > 0 else 1.0
        
        overall_disparity = (tpr_disparity + fpr_disparity) / 2
        passed = overall_disparity >= self.threshold
        
        interpretation = self._interpret_equalized_odds(tpr_scores, fpr_scores, overall_disparity)
        recommendations = self._recommend_equalized_odds(overall_disparity, tpr_scores, fpr_scores)
        
        return FairnessResult(
            metric_name="Equalized Odds",
            overall_score=overall_disparity,
            group_scores=group_scores,
            disparity=1 - overall_disparity,
            passed=passed,
            threshold=self.threshold,
            interpretation=interpretation,
            recommendations=recommendations
        )
    
    def calculate_equal_opportunity(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        protected_attribute: np.ndarray,
        positive_label: int = 1
    ) -> FairnessResult:
        """
        Equal Opportunity:
        P(Ŷ=1 | Y=1, A=a) = P(Ŷ=1 | Y=1, A=b) for all groups a, b
        
        Measures if TPR (recall) is equal across groups.
        """
        df = pd.DataFrame({
            'prediction': predictions,
            'truth': ground_truth,
            'group': protected_attribute
        })
        
        group_scores = {}
        
        for group in df['group'].unique():
            group_data = df[df['group'] == group]
            
            # True Positive Rate for positive class
            tp = ((group_data['prediction'] == positive_label) & 
                  (group_data['truth'] == positive_label)).sum()
            fn = ((group_data['prediction'] != positive_label) & 
                  (group_data['truth'] == positive_label)).sum()
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            group_scores[group] = tpr
        
        # Calculate disparity
        scores = list(group_scores.values())
        disparity = min(scores) / max(scores) if max(scores) > 0 else 1.0
        passed = disparity >= self.threshold
        
        interpretation = self._interpret_equal_opportunity(group_scores, disparity)
        recommendations = self._recommend_equal_opportunity(disparity, group_scores)
        
        return FairnessResult(
            metric_name="Equal Opportunity",
            overall_score=disparity,
            group_scores=group_scores,
            disparity=1 - disparity,
            passed=passed,
            threshold=self.threshold,
            interpretation=interpretation,
            recommendations=recommendations
        )
    
    def calculate_predictive_parity(
        self,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        protected_attribute: np.ndarray,
        positive_label: int = 1
    ) -> FairnessResult:
        """
        Predictive Parity (Precision Parity):
        P(Y=1 | Ŷ=1, A=a) = P(Y=1 | Ŷ=1, A=b) for all groups a, b
        
        Measures if precision is equal across groups.
        """
        df = pd.DataFrame({
            'prediction': predictions,
            'truth': ground_truth,
            'group': protected_attribute
        })
        
        group_scores = {}
        
        for group in df['group'].unique():
            group_data = df[df['group'] == group]
            
            # Precision
            tp = ((group_data['prediction'] == positive_label) & 
                  (group_data['truth'] == positive_label)).sum()
            fp = ((group_data['prediction'] == positive_label) & 
                  (group_data['truth'] != positive_label)).sum()
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            group_scores[group] = precision
        
        # Calculate disparity
        scores = list(group_scores.values())
        disparity = min(scores) / max(scores) if max(scores) > 0 else 1.0
        passed = disparity >= self.threshold
        
        interpretation = self._interpret_predictive_parity(group_scores, disparity)
        recommendations = self._recommend_predictive_parity(disparity, group_scores)
        
        return FairnessResult(
            metric_name="Predictive Parity",
            overall_score=disparity,
            group_scores=group_scores,
            disparity=1 - disparity,
            passed=passed,
            threshold=self.threshold,
            interpretation=interpretation,
            recommendations=recommendations
        )
    
    def calculate_all_metrics(
        self,
        predictions: np.ndarray,
        ground_truth: Optional[np.ndarray],
        protected_attribute: np.ndarray,
        positive_label: int = 1
    ) -> Dict[str, FairnessResult]:
        """Calculate all applicable fairness metrics"""
        results = {}
        
        # Demographic Parity (doesn't need ground truth)
        results['demographic_parity'] = self.calculate_demographic_parity(
            predictions, protected_attribute, positive_label
        )
        
        if ground_truth is not None:
            # Metrics that require ground truth
            results['equalized_odds'] = self.calculate_equalized_odds(
                predictions, ground_truth, protected_attribute, positive_label
            )
            results['equal_opportunity'] = self.calculate_equal_opportunity(
                predictions, ground_truth, protected_attribute, positive_label
            )
            results['predictive_parity'] = self.calculate_predictive_parity(
                predictions, ground_truth, protected_attribute, positive_label
            )
        
        return results
    
    # Interpretation helpers
    def _interpret_demographic_parity(self, group_rates: Dict, disparity: float) -> str:
        """Generate human-readable interpretation"""
        max_group = max(group_rates, key=group_rates.get)
        min_group = min(group_rates, key=group_rates.get)
        
        max_rate = group_rates[max_group] * 100
        min_rate = group_rates[min_group] * 100
        diff = max_rate - min_rate
        
        if disparity >= 0.9:
            level = "excellent"
        elif disparity >= 0.8:
            level = "acceptable"
        elif disparity >= 0.7:
            level = "concerning"
        else:
            level = "critical"
        
        return (
            f"Demographic parity is {level} (score: {disparity:.2f}). "
            f"Group '{max_group}' has {max_rate:.1f}% positive rate, "
            f"while group '{min_group}' has {min_rate:.1f}% positive rate "
            f"({diff:.1f} percentage point difference)."
        )
    
    def _interpret_equalized_odds(self, tpr_scores: Dict, fpr_scores: Dict, disparity: float) -> str:
        """Generate interpretation for equalized odds"""
        if disparity >= 0.9:
            level = "excellent"
        elif disparity >= 0.8:
            level = "acceptable"
        else:
            level = "concerning"
        
        return (
            f"Equalized odds is {level} (score: {disparity:.2f}). "
            f"Both true positive rates and false positive rates show "
            f"{'minimal' if disparity >= 0.9 else 'some'} disparity across groups."
        )
    
    def _interpret_equal_opportunity(self, group_scores: Dict, disparity: float) -> str:
        """Generate interpretation for equal opportunity"""
        max_group = max(group_scores, key=group_scores.get)
        min_group = min(group_scores, key=group_scores.get)
        
        return (
            f"Equal opportunity score: {disparity:.2f}. "
            f"Group '{max_group}' has {group_scores[max_group]:.1%} recall, "
            f"while group '{min_group}' has {group_scores[min_group]:.1%} recall."
        )
    
    def _interpret_predictive_parity(self, group_scores: Dict, disparity: float) -> str:
        """Generate interpretation for predictive parity"""
        max_group = max(group_scores, key=group_scores.get)
        min_group = min(group_scores, key=group_scores.get)
        
        return (
            f"Predictive parity score: {disparity:.2f}. "
            f"Group '{max_group}' has {group_scores[max_group]:.1%} precision, "
            f"while group '{min_group}' has {group_scores[min_group]:.1%} precision."
        )
    
    # Recommendation helpers
    def _recommend_demographic_parity(self, disparity: float, group_rates: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if disparity < 0.8:
            recommendations.append(
                "⚠️ CRITICAL: Demographic parity below 80% threshold. "
                "This may violate fair lending or EEOC guidelines."
            )
            recommendations.append(
                "🔧 Mitigation: Consider reweighting training data to balance group representation."
            )
            recommendations.append(
                "🔧 Mitigation: Adjust decision threshold separately for each group."
            )
            recommendations.append(
                "🔍 Investigation: Check if protected attribute is correlated with other features."
            )
        elif disparity < 0.9:
            recommendations.append(
                "⚠️ WARNING: Demographic parity below 90%. Monitor closely."
            )
            recommendations.append(
                "🔧 Consider: Review feature importance to identify indirect discrimination."
            )
        else:
            recommendations.append(
                "✅ PASS: Demographic parity is acceptable. Continue monitoring."
            )
        
        return recommendations
    
    def _recommend_equalized_odds(self, disparity: float, tpr_scores: Dict, fpr_scores: Dict) -> List[str]:
        """Generate recommendations for equalized odds"""
        recommendations = []
        
        if disparity < 0.8:
            recommendations.append(
                "⚠️ CRITICAL: Equalized odds below threshold. "
                "Model has different error rates across groups."
            )
            recommendations.append(
                "🔧 Mitigation: Use post-processing techniques (e.g., threshold optimization per group)."
            )
            recommendations.append(
                "🔧 Mitigation: Retrain model with fairness constraints."
            )
        else:
            recommendations.append(
                "✅ PASS: Equalized odds is acceptable."
            )
        
        return recommendations
    
    def _recommend_equal_opportunity(self, disparity: float, group_scores: Dict) -> List[str]:
        """Generate recommendations for equal opportunity"""
        recommendations = []
        
        if disparity < 0.8:
            recommendations.append(
                "⚠️ CRITICAL: Equal opportunity violated. "
                "Model has different recall rates for qualified individuals across groups."
            )
            recommendations.append(
                "🔧 Mitigation: Adjust classification threshold to equalize true positive rates."
            )
        else:
            recommendations.append(
                "✅ PASS: Equal opportunity is acceptable."
            )
        
        return recommendations
    
    def _recommend_predictive_parity(self, disparity: float, group_scores: Dict) -> List[str]:
        """Generate recommendations for predictive parity"""
        recommendations = []
        
        if disparity < 0.8:
            recommendations.append(
                "⚠️ WARNING: Predictive parity below threshold. "
                "Positive predictions have different accuracy across groups."
            )
            recommendations.append(
                "🔧 Mitigation: Calibrate model separately for each group."
            )
        else:
            recommendations.append(
                "✅ PASS: Predictive parity is acceptable."
            )
        
        return recommendations
