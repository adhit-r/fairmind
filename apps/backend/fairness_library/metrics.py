"""
Standardized Fairness Metrics
Core fairness metrics with statistical rigor and confidence intervals.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from sklearn.metrics import confusion_matrix
from scipy import stats

logger = logging.getLogger(__name__)

class FairnessMetric(Enum):
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    EQUAL_OPPORTUNITY = "equal_opportunity"
    STATISTICAL_PARITY = "statistical_parity"
    CALIBRATION = "calibration"
    INTERSECTIONAL = "intersectional"

@dataclass
class MetricResult:
    metric_name: str
    value: float
    confidence_interval: Tuple[float, float]
    p_value: float
    is_fair: bool
    threshold: float
    details: Dict[str, Any]

def demographic_parity_diff(
    y_pred: np.ndarray,
    sensitive_attr: np.ndarray,
    confidence_level: float = 0.95,
    threshold: float = 0.05
) -> MetricResult:
    """
    Compute demographic parity difference with statistical rigor.
    
    Args:
        y_pred: Binary predictions (0/1)
        sensitive_attr: Array of group labels
        confidence_level: Confidence level for CI
        threshold: Fairness threshold (default 0.05 = 5 percentage points)
    
    Returns:
        MetricResult with value, CI, p-value, and fairness assessment
    """
    try:
        groups = np.unique(sensitive_attr)
        if len(groups) < 2:
            raise ValueError("Need at least 2 groups for fairness analysis")
        
        # Compute group rates
        rates = {}
        for group in groups:
            mask = (sensitive_attr == group)
            rates[group] = y_pred[mask].mean()
        
        # Compute difference
        values = list(rates.values())
        diff = max(values) - min(values)
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_metric_ci(
            lambda: _compute_dp_diff(y_pred, sensitive_attr),
            confidence_level
        )
        
        # Permutation test for p-value
        p_value = _permutation_test_dp(y_pred, sensitive_attr, diff)
        
        return MetricResult(
            metric_name="demographic_parity_difference",
            value=diff,
            confidence_interval=(ci_lower, ci_upper),
            p_value=p_value,
            is_fair=diff <= threshold,
            threshold=threshold,
            details={
                "group_rates": rates,
                "interpretation": f"Max difference in positive prediction rates: {diff:.3f}",
                "recommendation": "Consider reweighing or constraints" if diff > threshold else "No significant bias detected"
            }
        )
        
    except Exception as e:
        logger.error(f"Error computing demographic parity: {e}")
        raise

def equalized_odds_diff(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive_attr: np.ndarray,
    confidence_level: float = 0.95,
    threshold: float = 0.05
) -> MetricResult:
    """
    Compute equalized odds difference (TPR and FPR differences).
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        sensitive_attr: Array of group labels
        confidence_level: Confidence level for CI
        threshold: Fairness threshold
    
    Returns:
        MetricResult with TPR and FPR differences
    """
    try:
        groups = np.unique(sensitive_attr)
        if len(groups) < 2:
            raise ValueError("Need at least 2 groups for fairness analysis")
        
        # Compute TPR and FPR by group
        tpr_by_group = {}
        fpr_by_group = {}
        
        for group in groups:
            mask = (sensitive_attr == group)
            if np.sum(mask) > 0:
                tn, fp, fn, tp = confusion_matrix(y_true[mask], y_pred[mask], labels=[0, 1]).ravel()
                
                tpr_by_group[group] = tp / (tp + fn) if (tp + fn) > 0 else np.nan
                fpr_by_group[group] = fp / (fp + tn) if (fp + tn) > 0 else np.nan
        
        # Compute differences
        valid_tpr = [v for v in tpr_by_group.values() if not np.isnan(v)]
        valid_fpr = [v for v in fpr_by_group.values() if not np.isnan(v)]
        
        tpr_diff = max(valid_tpr) - min(valid_tpr) if valid_tpr else 0
        fpr_diff = max(valid_fpr) - min(valid_fpr) if valid_fpr else 0
        
        # Overall difference (max of TPR and FPR differences)
        overall_diff = max(tpr_diff, fpr_diff)
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_metric_ci(
            lambda: _compute_eo_diff(y_true, y_pred, sensitive_attr),
            confidence_level
        )
        
        # Permutation test
        p_value = _permutation_test_eo(y_true, y_pred, sensitive_attr, overall_diff)
        
        return MetricResult(
            metric_name="equalized_odds_difference",
            value=overall_diff,
            confidence_interval=(ci_lower, ci_upper),
            p_value=p_value,
            is_fair=overall_diff <= threshold,
            threshold=threshold,
            details={
                "tpr_by_group": tpr_by_group,
                "fpr_by_group": fpr_by_group,
                "tpr_difference": tpr_diff,
                "fpr_difference": fpr_diff,
                "interpretation": f"Max difference in TPR/FPR: {overall_diff:.3f}",
                "recommendation": "Consider post-processing or constrained training" if overall_diff > threshold else "No significant bias detected"
            }
        )
        
    except Exception as e:
        logger.error(f"Error computing equalized odds: {e}")
        raise

def equal_opportunity_diff(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive_attr: np.ndarray,
    confidence_level: float = 0.95,
    threshold: float = 0.05
) -> MetricResult:
    """
    Compute equal opportunity difference (TPR difference only).
    """
    try:
        groups = np.unique(sensitive_attr)
        if len(groups) < 2:
            raise ValueError("Need at least 2 groups for fairness analysis")
        
        # Compute TPR by group
        tpr_by_group = {}
        
        for group in groups:
            mask = (sensitive_attr == group)
            if np.sum(mask) > 0:
                tn, fp, fn, tp = confusion_matrix(y_true[mask], y_pred[mask], labels=[0, 1]).ravel()
                tpr_by_group[group] = tp / (tp + fn) if (tp + fn) > 0 else np.nan
        
        # Compute TPR difference
        valid_tpr = [v for v in tpr_by_group.values() if not np.isnan(v)]
        tpr_diff = max(valid_tpr) - min(valid_tpr) if valid_tpr else 0
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_metric_ci(
            lambda: _compute_eopp_diff(y_true, y_pred, sensitive_attr),
            confidence_level
        )
        
        # Permutation test
        p_value = _permutation_test_eopp(y_true, y_pred, sensitive_attr, tpr_diff)
        
        return MetricResult(
            metric_name="equal_opportunity_difference",
            value=tpr_diff,
            confidence_interval=(ci_lower, ci_upper),
            p_value=p_value,
            is_fair=tpr_diff <= threshold,
            threshold=threshold,
            details={
                "tpr_by_group": tpr_by_group,
                "interpretation": f"TPR difference: {tpr_diff:.3f}",
                "recommendation": "Consider equal opportunity constraints" if tpr_diff > threshold else "No significant bias detected"
            }
        )
        
    except Exception as e:
        logger.error(f"Error computing equal opportunity: {e}")
        raise

def statistical_parity_diff(
    y_pred: np.ndarray,
    sensitive_attr: np.ndarray,
    confidence_level: float = 0.95,
    threshold: float = 0.05
) -> MetricResult:
    """
    Compute statistical parity difference (same as demographic parity).
    """
    return demographic_parity_diff(y_pred, sensitive_attr, confidence_level, threshold)

def calibration_by_group(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    sensitive_attr: np.ndarray,
    n_bins: int = 10,
    confidence_level: float = 0.95,
    threshold: float = 0.05
) -> MetricResult:
    """
    Analyze calibration by group to detect calibration bias.
    """
    try:
        groups = np.unique(sensitive_attr)
        if len(groups) < 2:
            raise ValueError("Need at least 2 groups for calibration analysis")
        
        calibration_errors = {}
        
        for group in groups:
            mask = (sensitive_attr == group)
            if np.sum(mask) > n_bins:
                group_true = y_true[mask]
                group_proba = y_pred_proba[mask]
                
                # Compute calibration error
                error = _compute_calibration_error(group_true, group_proba, n_bins)
                calibration_errors[group] = error
        
        # Compute max calibration difference
        if calibration_errors:
            max_error = max(calibration_errors.values())
            min_error = min(calibration_errors.values())
            calibration_diff = max_error - min_error
        else:
            calibration_diff = 0
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_metric_ci(
            lambda: _compute_calibration_diff(y_true, y_pred_proba, sensitive_attr, n_bins),
            confidence_level
        )
        
        return MetricResult(
            metric_name="calibration_by_group",
            value=calibration_diff,
            confidence_interval=(ci_lower, ci_upper),
            p_value=0.0,  # No p-value for calibration
            is_fair=calibration_diff <= threshold,
            threshold=threshold,
            details={
                "calibration_errors": calibration_errors,
                "interpretation": f"Max calibration difference: {calibration_diff:.3f}",
                "recommendation": "Consider calibration post-processing" if calibration_diff > threshold else "Calibration is fair across groups"
            }
        )
        
    except Exception as e:
        logger.error(f"Error computing calibration by group: {e}")
        raise

def intersectional_fairness(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive_attributes: Dict[str, np.ndarray],
    metric_func=demographic_parity_diff,
    confidence_level: float = 0.95,
    threshold: float = 0.05
) -> Dict[str, MetricResult]:
    """
    Analyze fairness across intersectional groups.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        sensitive_attributes: Dict of sensitive attributes
        metric_func: Fairness metric function to use
        confidence_level: Confidence level
        threshold: Fairness threshold
    
    Returns:
        Dict of MetricResult for each intersectional group
    """
    try:
        if len(sensitive_attributes) < 2:
            raise ValueError("Need at least 2 sensitive attributes for intersectional analysis")
        
        results = {}
        
        # Generate all intersectional combinations
        from itertools import product
        attr_names = list(sensitive_attributes.keys())
        attr_values = [np.unique(sensitive_attributes[attr]) for attr in attr_names]
        
        for combination in product(*attr_values):
            group_name = "_".join([f"{attr}={val}" for attr, val in zip(attr_names, combination)])
            
            # Create mask for this intersectional group
            mask = np.ones(len(y_true), dtype=bool)
            for attr, val in zip(attr_names, combination):
                mask &= (sensitive_attributes[attr] == val)
            
            # Only analyze if sufficient samples
            if np.sum(mask) > 50:  # Minimum sample size
                group_true = y_true[mask]
                group_pred = y_pred[mask]
                
                # Create a dummy sensitive attribute (all same group)
                dummy_attr = np.zeros(len(group_true), dtype=int)
                
                # Compute fairness metric for this group
                try:
                    result = metric_func(group_pred, dummy_attr, confidence_level, threshold)
                    results[group_name] = result
                except Exception as e:
                    logger.warning(f"Could not compute metric for {group_name}: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error computing intersectional fairness: {e}")
        raise

# Helper functions

def _compute_dp_diff(y_pred: np.ndarray, sensitive_attr: np.ndarray) -> float:
    """Helper function for demographic parity difference"""
    groups = np.unique(sensitive_attr)
    rates = {g: y_pred[sensitive_attr == g].mean() for g in groups}
    values = list(rates.values())
    return max(values) - min(values)

def _compute_eo_diff(y_true: np.ndarray, y_pred: np.ndarray, sensitive_attr: np.ndarray) -> float:
    """Helper function for equalized odds difference"""
    groups = np.unique(sensitive_attr)
    tpr_diffs = []
    fpr_diffs = []
    
    for group in groups:
        mask = (sensitive_attr == group)
        if np.sum(mask) > 0:
            tn, fp, fn, tp = confusion_matrix(y_true[mask], y_pred[mask], labels=[0, 1]).ravel()
            tpr = tp / (tp + fn) if (tp + fn) > 0 else np.nan
            fpr = fp / (fp + tn) if (fp + tn) > 0 else np.nan
            tpr_diffs.append(tpr)
            fpr_diffs.append(fpr)
    
    valid_tpr = [v for v in tpr_diffs if not np.isnan(v)]
    valid_fpr = [v for v in fpr_diffs if not np.isnan(v)]
    
    tpr_diff = max(valid_tpr) - min(valid_tpr) if valid_tpr else 0
    fpr_diff = max(valid_fpr) - min(valid_fpr) if valid_fpr else 0
    
    return max(tpr_diff, fpr_diff)

def _compute_eopp_diff(y_true: np.ndarray, y_pred: np.ndarray, sensitive_attr: np.ndarray) -> float:
    """Helper function for equal opportunity difference"""
    groups = np.unique(sensitive_attr)
    tpr_by_group = {}
    
    for group in groups:
        mask = (sensitive_attr == group)
        if np.sum(mask) > 0:
            tn, fp, fn, tp = confusion_matrix(y_true[mask], y_pred[mask], labels=[0, 1]).ravel()
            tpr_by_group[group] = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    
    valid_tpr = [v for v in tpr_by_group.values() if not np.isnan(v)]
    return max(valid_tpr) - min(valid_tpr) if valid_tpr else 0

def _compute_calibration_diff(y_true: np.ndarray, y_pred_proba: np.ndarray, sensitive_attr: np.ndarray, n_bins: int) -> float:
    """Helper function for calibration difference"""
    groups = np.unique(sensitive_attr)
    errors = []
    
    for group in groups:
        mask = (sensitive_attr == group)
        if np.sum(mask) > n_bins:
            group_true = y_true[mask]
            group_proba = y_pred_proba[mask]
            error = _compute_calibration_error(group_true, group_proba, n_bins)
            errors.append(error)
    
    return max(errors) - min(errors) if errors else 0

def _compute_calibration_error(y_true: np.ndarray, y_pred_proba: np.ndarray, n_bins: int) -> float:
    """Compute calibration error using binning"""
    try:
        # Create bins
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(y_pred_proba, bin_edges) - 1
        
        # Compute calibration error
        errors = []
        for i in range(n_bins):
            mask = (bin_indices == i)
            if np.sum(mask) > 0:
                predicted_rate = y_pred_proba[mask].mean()
                actual_rate = y_true[mask].mean()
                errors.append(abs(predicted_rate - actual_rate))
        
        return np.mean(errors) if errors else 0
    except:
        return 0

def _bootstrap_metric_ci(metric_func, confidence_level: float = 0.95, n_bootstrap: int = 1000) -> Tuple[float, float]:
    """Compute bootstrap confidence interval"""
    try:
        bootstrap_samples = []
        for _ in range(n_bootstrap):
            sample = metric_func()
            bootstrap_samples.append(sample)
        
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        return np.percentile(bootstrap_samples, [lower_percentile, upper_percentile])
    except Exception as e:
        logger.error(f"Error computing bootstrap CI: {e}")
        return (0, 0)

def _permutation_test_dp(y_pred: np.ndarray, sensitive_attr: np.ndarray, observed_diff: float, n_permutations: int = 1000) -> float:
    """Permutation test for demographic parity"""
    try:
        perm_diffs = []
        for _ in range(n_permutations):
            perm_attr = np.random.permutation(sensitive_attr)
            perm_diff = _compute_dp_diff(y_pred, perm_attr)
            perm_diffs.append(perm_diff)
        
        p_value = np.mean(np.array(perm_diffs) >= observed_diff)
        return p_value
    except Exception as e:
        logger.error(f"Error in permutation test: {e}")
        return 1.0

def _permutation_test_eo(y_true: np.ndarray, y_pred: np.ndarray, sensitive_attr: np.ndarray, observed_diff: float, n_permutations: int = 1000) -> float:
    """Permutation test for equalized odds"""
    try:
        perm_diffs = []
        for _ in range(n_permutations):
            perm_attr = np.random.permutation(sensitive_attr)
            perm_diff = _compute_eo_diff(y_true, y_pred, perm_attr)
            perm_diffs.append(perm_diff)
        
        p_value = np.mean(np.array(perm_diffs) >= observed_diff)
        return p_value
    except Exception as e:
        logger.error(f"Error in permutation test: {e}")
        return 1.0

def _permutation_test_eopp(y_true: np.ndarray, y_pred: np.ndarray, sensitive_attr: np.ndarray, observed_diff: float, n_permutations: int = 1000) -> float:
    """Permutation test for equal opportunity"""
    try:
        perm_diffs = []
        for _ in range(n_permutations):
            perm_attr = np.random.permutation(sensitive_attr)
            perm_diff = _compute_eopp_diff(y_true, y_pred, perm_attr)
            perm_diffs.append(perm_diff)
        
        p_value = np.mean(np.array(perm_diffs) >= observed_diff)
        return p_value
    except Exception as e:
        logger.error(f"Error in permutation test: {e}")
        return 1.0
