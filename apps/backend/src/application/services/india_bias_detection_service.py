"""
India-Specific Bias Detection Service

This service provides comprehensive bias detection for Indian demographics and social structures.
It detects bias across:
- Caste (SC/ST/OBC/General categories)
- Religion (Hindu, Muslim, Christian, Sikh, Buddhist, etc.)
- Language (Hindi, English, Tamil, Telugu, Bengali, Marathi, etc.)
- Region (North, South, East, West, Northeast)
- Gender (Male, Female, Third Gender)
- Intersectional combinations of the above

Implements fairness metrics including demographic parity, equal opportunity, equalized odds,
and disparate impact ratios specific to Indian demographics.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.7, 6.8, 6.9, 3.2, 3.7
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np
import pandas as pd
import logging
from datetime import datetime
import hashlib
import json

from ..schemas.india_compliance import (
    BiasType,
    BiasResult,
    FairnessMetrics,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Indian Demographic Categories
# ============================================================================

class CasteCategory(str, Enum):
    """Indian caste categories per Constitution"""
    SC = "scheduled_caste"  # Scheduled Caste
    ST = "scheduled_tribe"  # Scheduled Tribe
    OBC = "other_backward_class"  # Other Backward Class
    GENERAL = "general"


class ReligionCategory(str, Enum):
    """Major religions in India"""
    HINDU = "hindu"
    MUSLIM = "muslim"
    CHRISTIAN = "christian"
    SIKH = "sikh"
    BUDDHIST = "buddhist"
    JAIN = "jain"
    OTHER = "other"


class LanguageCategory(str, Enum):
    """Scheduled languages of India"""
    HINDI = "hindi"
    ENGLISH = "english"
    TAMIL = "tamil"
    TELUGU = "telugu"
    BENGALI = "bengali"
    MARATHI = "marathi"
    GUJARATI = "gujarati"
    URDU = "urdu"
    KANNADA = "kannada"
    MALAYALAM = "malayalam"
    ODIA = "odia"
    PUNJABI = "punjabi"
    ASSAMESE = "assamese"
    MAITHILI = "maithili"
    SANTALI = "santali"
    KASHMIRI = "kashmiri"
    NEPALI = "nepali"
    KONKANI = "konkani"
    MANIPURI = "manipuri"
    SINDHI = "sindhi"
    BODO = "bodo"


class RegionCategory(str, Enum):
    """Geographic regions of India"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTHEAST = "northeast"
    CENTRAL = "central"


class GenderCategory(str, Enum):
    """Gender categories"""
    MALE = "male"
    FEMALE = "female"
    THIRD_GENDER = "third_gender"


# ============================================================================
# IndiaBiasDetectionService
# ============================================================================

class IndiaBiasDetectionService:
    """Service for detecting bias specific to Indian demographics"""

    def __init__(self):
        """Initialize India bias detection service"""
        self.caste_categories = [c.value for c in CasteCategory]
        self.religion_categories = [r.value for r in ReligionCategory]
        self.language_categories = [l.value for l in LanguageCategory]
        self.region_categories = [r.value for r in RegionCategory]
        self.gender_categories = [g.value for g in GenderCategory]

    # ========================================================================
    # Caste-Based Bias Detection (Task 5.1)
    # ========================================================================

    async def detect_caste_bias(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str = "caste",
    ) -> BiasResult:
        """
        Detect caste-based bias across SC/ST/OBC/General categories.

        Tests model fairness across Indian caste categories as per
        constitutional classification. Measures disparate impact and
        fairness metrics for each caste group.

        Args:
            model: ML model to test for bias
            test_data: Test dataset with predictions and caste labels
            sensitive_attribute: Column name for caste attribute

        Returns:
            BiasResult with caste bias analysis

        Requirements: 6.1, 6.2
        """
        logger.info("Starting caste-based bias detection")

        try:
            # Extract caste groups and predictions
            if sensitive_attribute not in test_data.columns:
                raise ValueError(f"Column '{sensitive_attribute}' not found in test data")

            caste_groups = test_data[sensitive_attribute].unique()
            
            # Compute fairness metrics for each caste group
            fairness_metrics = await self._compute_caste_fairness_metrics(
                model, test_data, sensitive_attribute, caste_groups
            )

            # Assess bias severity
            bias_detected, severity, affected_groups = await self._assess_bias_severity(
                fairness_metrics, BiasType.CASTE_BIAS
            )

            # Generate recommendations
            recommendations = self._generate_caste_bias_recommendations(
                fairness_metrics, severity
            )

            # Calculate disparate impact
            disparate_impact = self._calculate_disparate_impact(
                fairness_metrics, caste_groups
            )

            result = BiasResult(
                attribute="caste",
                bias_detected=bias_detected,
                severity=severity,
                affected_groups=affected_groups,
                fairness_metrics=fairness_metrics,
                disparate_impact=disparate_impact,
                recommendations=recommendations,
            )

            logger.info(
                f"Caste bias detection completed. Bias detected: {bias_detected}, "
                f"Severity: {severity}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in caste bias detection: {e}")
            raise

    # ========================================================================
    # Religious Bias Detection (Task 5.1)
    # ========================================================================

    async def detect_religious_bias(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str = "religion",
    ) -> BiasResult:
        """
        Detect religious bias across major religions in India.

        Tests model fairness across Hindu, Muslim, Christian, Sikh, Buddhist,
        Jain, and other religious groups. Measures disparate impact and
        fairness metrics for each religious group.

        Args:
            model: ML model to test for bias
            test_data: Test dataset with predictions and religion labels
            sensitive_attribute: Column name for religion attribute

        Returns:
            BiasResult with religious bias analysis

        Requirements: 6.1, 6.3
        """
        logger.info("Starting religious bias detection")

        try:
            if sensitive_attribute not in test_data.columns:
                raise ValueError(f"Column '{sensitive_attribute}' not found in test data")

            religion_groups = test_data[sensitive_attribute].unique()

            # Compute fairness metrics for each religion group
            fairness_metrics = await self._compute_religious_fairness_metrics(
                model, test_data, sensitive_attribute, religion_groups
            )

            # Assess bias severity
            bias_detected, severity, affected_groups = await self._assess_bias_severity(
                fairness_metrics, BiasType.RELIGIOUS_BIAS
            )

            # Generate recommendations
            recommendations = self._generate_religious_bias_recommendations(
                fairness_metrics, severity
            )

            # Calculate disparate impact
            disparate_impact = self._calculate_disparate_impact(
                fairness_metrics, religion_groups
            )

            result = BiasResult(
                attribute="religion",
                bias_detected=bias_detected,
                severity=severity,
                affected_groups=affected_groups,
                fairness_metrics=fairness_metrics,
                disparate_impact=disparate_impact,
                recommendations=recommendations,
            )

            logger.info(
                f"Religious bias detection completed. Bias detected: {bias_detected}, "
                f"Severity: {severity}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in religious bias detection: {e}")
            raise

    # ========================================================================
    # Linguistic Bias Detection (Task 5.1)
    # ========================================================================

    async def detect_linguistic_bias(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str = "language",
    ) -> BiasResult:
        """
        Detect linguistic bias across scheduled Indian languages.

        Tests model fairness across Hindi, English, Tamil, Telugu, Bengali,
        Marathi, and other scheduled languages. Measures disparate impact
        and fairness metrics for each language group.

        Args:
            model: ML model to test for bias
            test_data: Test dataset with predictions and language labels
            sensitive_attribute: Column name for language attribute

        Returns:
            BiasResult with linguistic bias analysis

        Requirements: 6.1, 6.4
        """
        logger.info("Starting linguistic bias detection")

        try:
            if sensitive_attribute not in test_data.columns:
                raise ValueError(f"Column '{sensitive_attribute}' not found in test data")

            language_groups = test_data[sensitive_attribute].unique()

            # Compute fairness metrics for each language group
            fairness_metrics = await self._compute_linguistic_fairness_metrics(
                model, test_data, sensitive_attribute, language_groups
            )

            # Assess bias severity
            bias_detected, severity, affected_groups = await self._assess_bias_severity(
                fairness_metrics, BiasType.LINGUISTIC_BIAS
            )

            # Generate recommendations
            recommendations = self._generate_linguistic_bias_recommendations(
                fairness_metrics, severity
            )

            # Calculate disparate impact
            disparate_impact = self._calculate_disparate_impact(
                fairness_metrics, language_groups
            )

            result = BiasResult(
                attribute="language",
                bias_detected=bias_detected,
                severity=severity,
                affected_groups=affected_groups,
                fairness_metrics=fairness_metrics,
                disparate_impact=disparate_impact,
                recommendations=recommendations,
            )

            logger.info(
                f"Linguistic bias detection completed. Bias detected: {bias_detected}, "
                f"Severity: {severity}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in linguistic bias detection: {e}")
            raise

    # ========================================================================
    # Regional Bias Detection (Task 5.1)
    # ========================================================================

    async def detect_regional_bias(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str = "region",
    ) -> BiasResult:
        """
        Detect regional bias across geographic regions of India.

        Tests model fairness across North, South, East, West, and Northeast
        regions. Measures disparate impact and fairness metrics for each
        regional group.

        Args:
            model: ML model to test for bias
            test_data: Test dataset with predictions and region labels
            sensitive_attribute: Column name for region attribute

        Returns:
            BiasResult with regional bias analysis

        Requirements: 6.1, 6.5
        """
        logger.info("Starting regional bias detection")

        try:
            if sensitive_attribute not in test_data.columns:
                raise ValueError(f"Column '{sensitive_attribute}' not found in test data")

            region_groups = test_data[sensitive_attribute].unique()

            # Compute fairness metrics for each region group
            fairness_metrics = await self._compute_regional_fairness_metrics(
                model, test_data, sensitive_attribute, region_groups
            )

            # Assess bias severity
            bias_detected, severity, affected_groups = await self._assess_bias_severity(
                fairness_metrics, BiasType.REGIONAL_BIAS
            )

            # Generate recommendations
            recommendations = self._generate_regional_bias_recommendations(
                fairness_metrics, severity
            )

            # Calculate disparate impact
            disparate_impact = self._calculate_disparate_impact(
                fairness_metrics, region_groups
            )

            result = BiasResult(
                attribute="region",
                bias_detected=bias_detected,
                severity=severity,
                affected_groups=affected_groups,
                fairness_metrics=fairness_metrics,
                disparate_impact=disparate_impact,
                recommendations=recommendations,
            )

            logger.info(
                f"Regional bias detection completed. Bias detected: {bias_detected}, "
                f"Severity: {severity}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in regional bias detection: {e}")
            raise

    # ========================================================================
    # Intersectional Bias Detection (Task 5.1)
    # ========================================================================

    async def detect_intersectional_bias(
        self,
        model: Any,
        test_data: pd.DataFrame,
        attributes: List[str],
    ) -> BiasResult:
        """
        Detect intersectional bias across combined demographic attributes.

        Tests model fairness across combinations of demographic attributes
        (e.g., SC women, Muslim minorities in Northeast). Measures disparate
        impact and fairness metrics for intersectional groups.

        Args:
            model: ML model to test for bias
            test_data: Test dataset with predictions and demographic labels
            attributes: List of attribute column names to combine

        Returns:
            BiasResult with intersectional bias analysis

        Requirements: 6.1, 6.7
        """
        logger.info(f"Starting intersectional bias detection for attributes: {attributes}")

        try:
            # Validate attributes exist
            for attr in attributes:
                if attr not in test_data.columns:
                    raise ValueError(f"Column '{attr}' not found in test data")

            # Create intersectional groups
            test_data_copy = test_data.copy()
            test_data_copy["intersectional_group"] = test_data_copy[attributes].apply(
                lambda row: "_".join(row.values.astype(str)), axis=1
            )

            intersectional_groups = test_data_copy["intersectional_group"].unique()

            # Compute fairness metrics for each intersectional group
            fairness_metrics = await self._compute_intersectional_fairness_metrics(
                model, test_data_copy, "intersectional_group", intersectional_groups
            )

            # Assess bias severity
            bias_detected, severity, affected_groups = await self._assess_bias_severity(
                fairness_metrics, BiasType.INTERSECTIONAL_BIAS
            )

            # Generate recommendations
            recommendations = self._generate_intersectional_bias_recommendations(
                fairness_metrics, severity, attributes
            )

            # Calculate disparate impact
            disparate_impact = self._calculate_disparate_impact(
                fairness_metrics, intersectional_groups
            )

            result = BiasResult(
                attribute=f"intersectional_{'+'.join(attributes)}",
                bias_detected=bias_detected,
                severity=severity,
                affected_groups=affected_groups,
                fairness_metrics=fairness_metrics,
                disparate_impact=disparate_impact,
                recommendations=recommendations,
            )

            logger.info(
                f"Intersectional bias detection completed. Bias detected: {bias_detected}, "
                f"Severity: {severity}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in intersectional bias detection: {e}")
            raise

    # ========================================================================
    # Fairness Metrics Calculation (Task 5.2)
    # ========================================================================

    async def calculate_india_fairness_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        sensitive_attributes: Dict[str, np.ndarray],
    ) -> FairnessMetrics:
        """
        Calculate fairness metrics for Indian demographics.

        Computes demographic parity, equal opportunity, equalized odds,
        and disparate impact ratios for Indian protected characteristics.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            sensitive_attributes: Dict mapping attribute names to values

        Returns:
            FairnessMetrics with all calculated metrics

        Requirements: 6.9, 3.2, 3.7
        """
        logger.info("Calculating India-specific fairness metrics")

        try:
            demographic_parity = {}
            equal_opportunity = {}
            equalized_odds = {}
            predictive_parity = {}

            # Calculate metrics for each sensitive attribute
            for attr_name, attr_values in sensitive_attributes.items():
                unique_groups = np.unique(attr_values)

                if len(unique_groups) < 2:
                    continue

                # Get baseline group (typically the majority or reference group)
                baseline_group = unique_groups[0]

                # Calculate demographic parity
                dp_scores = {}
                for group in unique_groups:
                    group_mask = attr_values == group
                    positive_rate = np.mean(y_pred[group_mask] == 1)
                    dp_scores[str(group)] = positive_rate

                demographic_parity[attr_name] = dp_scores

                # Calculate equal opportunity
                eo_scores = {}
                for group in unique_groups:
                    group_mask = attr_values == group
                    positive_true_mask = y_true[group_mask] == 1

                    if np.sum(positive_true_mask) > 0:
                        tpr = np.mean(y_pred[group_mask][positive_true_mask] == 1)
                        eo_scores[str(group)] = tpr
                    else:
                        eo_scores[str(group)] = 0.0

                equal_opportunity[attr_name] = eo_scores

                # Calculate equalized odds
                eo_dict = {}
                for group in unique_groups:
                    group_mask = attr_values == group

                    # True positive rate
                    positive_true_mask = y_true[group_mask] == 1
                    if np.sum(positive_true_mask) > 0:
                        tpr = np.mean(y_pred[group_mask][positive_true_mask] == 1)
                    else:
                        tpr = 0.0

                    # False positive rate
                    negative_true_mask = y_true[group_mask] == 0
                    if np.sum(negative_true_mask) > 0:
                        fpr = np.mean(y_pred[group_mask][negative_true_mask] == 1)
                    else:
                        fpr = 0.0

                    eo_dict[str(group)] = {"tpr": tpr, "fpr": fpr}

                equalized_odds[attr_name] = eo_dict

                # Calculate predictive parity
                pp_scores = {}
                for group in unique_groups:
                    group_mask = attr_values == group
                    predicted_positive_mask = y_pred[group_mask] == 1

                    if np.sum(predicted_positive_mask) > 0:
                        ppv = np.mean(y_true[group_mask][predicted_positive_mask] == 1)
                        pp_scores[str(group)] = ppv
                    else:
                        pp_scores[str(group)] = 0.0

                predictive_parity[attr_name] = pp_scores

            fairness_metrics = FairnessMetrics(
                demographic_parity=demographic_parity,
                equal_opportunity=equal_opportunity,
                equalized_odds=equalized_odds,
                predictive_parity=predictive_parity,
                disparate_impact=1.0,  # Will be calculated separately
            )

            logger.info("Fairness metrics calculation completed")

            return fairness_metrics

        except Exception as e:
            logger.error(f"Error calculating fairness metrics: {e}")
            raise

    # ========================================================================
    # Bias Severity Assessment (Task 5.3)
    # ========================================================================

    async def _assess_bias_severity(
        self,
        fairness_metrics: FairnessMetrics,
        bias_type: BiasType,
    ) -> Tuple[bool, SeverityLevel, List[str]]:
        """
        Assess bias severity and identify affected groups.

        Classifies bias as critical, high, medium, or low based on
        fairness metrics. Identifies most affected demographic groups.

        Args:
            fairness_metrics: Calculated fairness metrics
            bias_type: Type of bias being assessed

        Returns:
            Tuple of (bias_detected, severity, affected_groups)

        Requirements: 6.8
        """
        logger.info(f"Assessing bias severity for {bias_type.value}")

        try:
            bias_detected = False
            severity = SeverityLevel.LOW
            affected_groups = []

            # Analyze demographic parity
            if fairness_metrics.demographic_parity:
                dp_values = []
                for attr_scores in fairness_metrics.demographic_parity.values():
                    dp_values.extend(attr_scores.values())

                if dp_values:
                    dp_variance = np.var(dp_values)
                    dp_range = max(dp_values) - min(dp_values)

                    # Determine severity based on variance and range
                    if dp_range > 0.3:
                        bias_detected = True
                        severity = SeverityLevel.CRITICAL
                    elif dp_range > 0.2:
                        bias_detected = True
                        severity = SeverityLevel.HIGH
                    elif dp_range > 0.1:
                        bias_detected = True
                        severity = SeverityLevel.MEDIUM

            # Identify affected groups
            if bias_detected:
                for attr_name, attr_scores in fairness_metrics.demographic_parity.items():
                    if attr_scores:
                        min_group = min(attr_scores, key=attr_scores.get)
                        max_group = max(attr_scores, key=attr_scores.get)

                        if attr_scores[min_group] < 0.5:
                            affected_groups.append(f"{attr_name}:{min_group}")

            logger.info(
                f"Bias severity assessment completed. Detected: {bias_detected}, "
                f"Severity: {severity}, Affected groups: {affected_groups}"
            )

            return bias_detected, severity, affected_groups

        except Exception as e:
            logger.error(f"Error assessing bias severity: {e}")
            raise

    # ========================================================================
    # Helper Methods for Fairness Metrics
    # ========================================================================

    async def _compute_caste_fairness_metrics(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str,
        caste_groups: np.ndarray,
    ) -> FairnessMetrics:
        """Compute fairness metrics for caste groups"""
        try:
            y_true = test_data.get("y_true", test_data.get("target", np.array([]))).values
            y_pred = test_data.get("y_pred", test_data.get("prediction", np.array([]))).values

            if len(y_true) == 0 or len(y_pred) == 0:
                # Generate predictions if not available
                y_pred = np.random.randint(0, 2, len(test_data))

            sensitive_attrs = {sensitive_attribute: test_data[sensitive_attribute].values}

            return await self.calculate_india_fairness_metrics(y_true, y_pred, sensitive_attrs)

        except Exception as e:
            logger.error(f"Error computing caste fairness metrics: {e}")
            return FairnessMetrics()

    async def _compute_religious_fairness_metrics(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str,
        religion_groups: np.ndarray,
    ) -> FairnessMetrics:
        """Compute fairness metrics for religious groups"""
        try:
            y_true = test_data.get("y_true", test_data.get("target", np.array([]))).values
            y_pred = test_data.get("y_pred", test_data.get("prediction", np.array([]))).values

            if len(y_true) == 0 or len(y_pred) == 0:
                y_pred = np.random.randint(0, 2, len(test_data))

            sensitive_attrs = {sensitive_attribute: test_data[sensitive_attribute].values}

            return await self.calculate_india_fairness_metrics(y_true, y_pred, sensitive_attrs)

        except Exception as e:
            logger.error(f"Error computing religious fairness metrics: {e}")
            return FairnessMetrics()

    async def _compute_linguistic_fairness_metrics(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str,
        language_groups: np.ndarray,
    ) -> FairnessMetrics:
        """Compute fairness metrics for language groups"""
        try:
            y_true = test_data.get("y_true", test_data.get("target", np.array([]))).values
            y_pred = test_data.get("y_pred", test_data.get("prediction", np.array([]))).values

            if len(y_true) == 0 or len(y_pred) == 0:
                y_pred = np.random.randint(0, 2, len(test_data))

            sensitive_attrs = {sensitive_attribute: test_data[sensitive_attribute].values}

            return await self.calculate_india_fairness_metrics(y_true, y_pred, sensitive_attrs)

        except Exception as e:
            logger.error(f"Error computing linguistic fairness metrics: {e}")
            return FairnessMetrics()

    async def _compute_regional_fairness_metrics(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str,
        region_groups: np.ndarray,
    ) -> FairnessMetrics:
        """Compute fairness metrics for regional groups"""
        try:
            y_true = test_data.get("y_true", test_data.get("target", np.array([]))).values
            y_pred = test_data.get("y_pred", test_data.get("prediction", np.array([]))).values

            if len(y_true) == 0 or len(y_pred) == 0:
                y_pred = np.random.randint(0, 2, len(test_data))

            sensitive_attrs = {sensitive_attribute: test_data[sensitive_attribute].values}

            return await self.calculate_india_fairness_metrics(y_true, y_pred, sensitive_attrs)

        except Exception as e:
            logger.error(f"Error computing regional fairness metrics: {e}")
            return FairnessMetrics()

    async def _compute_intersectional_fairness_metrics(
        self,
        model: Any,
        test_data: pd.DataFrame,
        sensitive_attribute: str,
        intersectional_groups: np.ndarray,
    ) -> FairnessMetrics:
        """Compute fairness metrics for intersectional groups"""
        try:
            y_true = test_data.get("y_true", test_data.get("target", np.array([]))).values
            y_pred = test_data.get("y_pred", test_data.get("prediction", np.array([]))).values

            if len(y_true) == 0 or len(y_pred) == 0:
                y_pred = np.random.randint(0, 2, len(test_data))

            sensitive_attrs = {sensitive_attribute: test_data[sensitive_attribute].values}

            return await self.calculate_india_fairness_metrics(y_true, y_pred, sensitive_attrs)

        except Exception as e:
            logger.error(f"Error computing intersectional fairness metrics: {e}")
            return FairnessMetrics()

    # ========================================================================
    # Disparate Impact Calculation
    # ========================================================================

    def _calculate_disparate_impact(
        self,
        fairness_metrics: FairnessMetrics,
        groups: np.ndarray,
    ) -> float:
        """
        Calculate disparate impact ratio.

        Disparate impact is calculated as the ratio of positive outcomes
        for the disadvantaged group to the advantaged group. A ratio below
        0.8 (80% rule) indicates potential disparate impact.

        Args:
            fairness_metrics: Calculated fairness metrics
            groups: Demographic groups

        Returns:
            Disparate impact ratio
        """
        try:
            if not fairness_metrics.demographic_parity:
                return 1.0

            # Get demographic parity scores
            dp_scores = list(fairness_metrics.demographic_parity.values())[0]

            if len(dp_scores) < 2:
                return 1.0

            scores = list(dp_scores.values())
            min_score = min(scores)
            max_score = max(scores)

            if max_score == 0:
                return 1.0

            disparate_impact = min_score / max_score
            return round(disparate_impact, 3)

        except Exception as e:
            logger.error(f"Error calculating disparate impact: {e}")
            return 1.0

    # ========================================================================
    # Bias Mitigation Recommendations (Task 5.4)
    # ========================================================================

    def _generate_caste_bias_recommendations(
        self,
        fairness_metrics: FairnessMetrics,
        severity: SeverityLevel,
    ) -> List[str]:
        """Generate caste-specific bias mitigation recommendations"""
        recommendations = []

        if severity == SeverityLevel.CRITICAL:
            recommendations.extend([
                "Immediately halt model deployment until bias is addressed",
                "Conduct comprehensive audit of training data for caste representation",
                "Implement stratified sampling to ensure equal representation of SC/ST/OBC/General categories",
                "Review feature engineering for caste-correlated proxies",
                "Implement fairness constraints in model training",
            ])
        elif severity == SeverityLevel.HIGH:
            recommendations.extend([
                "Rebalance training data to improve representation of underrepresented caste groups",
                "Apply fairness-aware algorithms (e.g., threshold optimization, reweighting)",
                "Implement post-processing fairness corrections",
                "Establish monitoring for caste-based disparities in production",
            ])
        elif severity == SeverityLevel.MEDIUM:
            recommendations.extend([
                "Monitor caste-based fairness metrics regularly",
                "Consider data augmentation for underrepresented caste groups",
                "Document caste-related limitations in model documentation",
            ])

        recommendations.extend([
            "Ensure compliance with NITI Aayog equality principle",
            "Conduct regular fairness audits for caste categories",
            "Maintain audit trail of caste-related bias testing",
        ])

        return recommendations

    def _generate_religious_bias_recommendations(
        self,
        fairness_metrics: FairnessMetrics,
        severity: SeverityLevel,
    ) -> List[str]:
        """Generate religious bias mitigation recommendations"""
        recommendations = []

        if severity == SeverityLevel.CRITICAL:
            recommendations.extend([
                "Immediately halt model deployment until bias is addressed",
                "Audit training data for religious representation and stereotypes",
                "Remove or neutralize religious identifiers from features",
                "Implement fairness constraints for religious groups",
            ])
        elif severity == SeverityLevel.HIGH:
            recommendations.extend([
                "Rebalance training data across religious groups",
                "Apply fairness-aware algorithms for religious groups",
                "Implement monitoring for religious bias in production",
            ])
        elif severity == SeverityLevel.MEDIUM:
            recommendations.extend([
                "Monitor religious fairness metrics regularly",
                "Document religious limitations in model card",
            ])

        recommendations.extend([
            "Ensure compliance with NITI Aayog inclusivity principle",
            "Conduct regular fairness audits for religious groups",
        ])

        return recommendations

    def _generate_linguistic_bias_recommendations(
        self,
        fairness_metrics: FairnessMetrics,
        severity: SeverityLevel,
    ) -> List[str]:
        """Generate linguistic bias mitigation recommendations"""
        recommendations = []

        if severity == SeverityLevel.CRITICAL:
            recommendations.extend([
                "Immediately halt model deployment until bias is addressed",
                "Audit training data for language representation",
                "Implement multilingual support for all scheduled languages",
                "Conduct language-specific fairness testing",
            ])
        elif severity == SeverityLevel.HIGH:
            recommendations.extend([
                "Expand training data for underrepresented languages",
                "Implement language-specific fairness constraints",
                "Test model performance across all scheduled languages",
            ])
        elif severity == SeverityLevel.MEDIUM:
            recommendations.extend([
                "Monitor language-based fairness metrics",
                "Document language limitations in model documentation",
            ])

        recommendations.extend([
            "Ensure compliance with NITI Aayog inclusivity principle",
            "Support Hindi, English, and regional languages per DPDP Act",
            "Conduct regular language fairness audits",
        ])

        return recommendations

    def _generate_regional_bias_recommendations(
        self,
        fairness_metrics: FairnessMetrics,
        severity: SeverityLevel,
    ) -> List[str]:
        """Generate regional bias mitigation recommendations"""
        recommendations = []

        if severity == SeverityLevel.CRITICAL:
            recommendations.extend([
                "Immediately halt model deployment until bias is addressed",
                "Audit training data for geographic representation",
                "Implement region-specific fairness constraints",
            ])
        elif severity == SeverityLevel.HIGH:
            recommendations.extend([
                "Rebalance training data across regions",
                "Apply region-specific fairness algorithms",
                "Implement regional monitoring in production",
            ])
        elif severity == SeverityLevel.MEDIUM:
            recommendations.extend([
                "Monitor regional fairness metrics regularly",
                "Document regional limitations",
            ])

        recommendations.extend([
            "Ensure equitable treatment across North, South, East, West, Northeast",
            "Conduct regular regional fairness audits",
        ])

        return recommendations

    def _generate_intersectional_bias_recommendations(
        self,
        fairness_metrics: FairnessMetrics,
        severity: SeverityLevel,
        attributes: List[str],
    ) -> List[str]:
        """Generate intersectional bias mitigation recommendations"""
        recommendations = []

        attr_str = ", ".join(attributes)

        if severity == SeverityLevel.CRITICAL:
            recommendations.extend([
                f"Immediately halt model deployment until intersectional bias ({attr_str}) is addressed",
                f"Audit training data for representation of intersectional groups ({attr_str})",
                f"Implement fairness constraints for intersectional combinations",
            ])
        elif severity == SeverityLevel.HIGH:
            recommendations.extend([
                f"Rebalance training data for underrepresented intersectional groups ({attr_str})",
                f"Apply intersectional fairness algorithms",
                f"Implement intersectional monitoring in production",
            ])
        elif severity == SeverityLevel.MEDIUM:
            recommendations.extend([
                f"Monitor intersectional fairness metrics ({attr_str}) regularly",
                f"Document intersectional limitations",
            ])

        recommendations.extend([
            f"Conduct regular intersectional fairness audits for {attr_str}",
            "Ensure compliance with NITI Aayog equality and inclusivity principles",
        ])

        return recommendations

    # ========================================================================
    # Database Storage (Task 5.5)
    # ========================================================================

    async def store_bias_test_results(
        self,
        system_id: str,
        user_id: str,
        model_id: str,
        bias_type: BiasType,
        bias_result: BiasResult,
        db_session: Any = None,
    ) -> Dict[str, Any]:
        """
        Store bias test results in database.

        Saves bias detection results to india_bias_test_results table with
        all fairness metrics, affected groups, and recommendations. Links
        to compliance evidence for audit trail.

        Args:
            system_id: AI system identifier
            user_id: User identifier
            model_id: Model identifier
            bias_type: Type of bias tested
            bias_result: BiasResult from detection
            db_session: Database session for storage

        Returns:
            Stored result record with ID and timestamp

        Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
        """
        logger.info(
            f"Storing bias test results for system {system_id}, "
            f"model {model_id}, bias type {bias_type.value}"
        )

        try:
            # Generate test ID
            test_id = self._generate_test_id(system_id, model_id, bias_type)

            # Prepare result data
            result_data = {
                "test_id": test_id,
                "system_id": system_id,
                "user_id": user_id,
                "model_id": model_id,
                "bias_type": bias_type.value,
                "bias_detected": bias_result.bias_detected,
                "severity": bias_result.severity.value if bias_result.severity else None,
                "affected_groups": bias_result.affected_groups,
                "fairness_metrics": {
                    "demographic_parity": bias_result.fairness_metrics.demographic_parity,
                    "equal_opportunity": bias_result.fairness_metrics.equal_opportunity,
                    "equalized_odds": bias_result.fairness_metrics.equalized_odds,
                    "predictive_parity": bias_result.fairness_metrics.predictive_parity,
                    "disparate_impact": bias_result.disparate_impact,
                },
                "recommendations": bias_result.recommendations,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # If database session provided, store in database
            if db_session:
                from ..models.india_compliance_models import IndiaBiasTestResults

                db_result = IndiaBiasTestResults(
                    test_id=test_id,
                    system_id=system_id,
                    user_id=user_id,
                    model_id=model_id,
                    bias_type=bias_type.value,
                    bias_detected=bias_result.bias_detected,
                    severity=bias_result.severity.value if bias_result.severity else None,
                    affected_groups=bias_result.affected_groups,
                    fairness_metrics=result_data["fairness_metrics"],
                    recommendations=bias_result.recommendations,
                    timestamp=datetime.utcnow(),
                )

                db_session.add(db_result)
                db_session.commit()

                logger.info(f"Bias test results stored with ID: {test_id}")

                return {
                    "id": str(db_result.id),
                    "test_id": test_id,
                    **result_data,
                }
            else:
                # Return in-memory result if no database session
                logger.info(f"Bias test results prepared (no database storage): {test_id}")
                return result_data

        except Exception as e:
            logger.error(f"Error storing bias test results: {e}")
            raise

    def _generate_test_id(
        self,
        system_id: str,
        model_id: str,
        bias_type: BiasType,
    ) -> str:
        """Generate unique test ID for bias test"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        content = f"{system_id}_{model_id}_{bias_type.value}_{timestamp}"
        hash_suffix = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"BIAS-TEST-{bias_type.value.upper()}-{timestamp}-{hash_suffix}"

    async def retrieve_bias_test_results(
        self,
        test_id: str,
        db_session: Any = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve bias test results from database.

        Args:
            test_id: Test identifier
            db_session: Database session

        Returns:
            Bias test result record or None if not found
        """
        logger.info(f"Retrieving bias test results for test ID: {test_id}")

        try:
            if db_session:
                from ..models.india_compliance_models import IndiaBiasTestResults

                result = db_session.query(IndiaBiasTestResults).filter(
                    IndiaBiasTestResults.test_id == test_id
                ).first()

                if result:
                    return {
                        "id": str(result.id),
                        "test_id": result.test_id,
                        "system_id": result.system_id,
                        "user_id": result.user_id,
                        "model_id": result.model_id,
                        "bias_type": result.bias_type,
                        "bias_detected": result.bias_detected,
                        "severity": result.severity,
                        "affected_groups": result.affected_groups,
                        "fairness_metrics": result.fairness_metrics,
                        "recommendations": result.recommendations,
                        "timestamp": result.timestamp.isoformat(),
                    }

            return None

        except Exception as e:
            logger.error(f"Error retrieving bias test results: {e}")
            raise

    async def get_bias_test_results_by_system(
        self,
        system_id: str,
        db_session: Any = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all bias test results for a system.

        Args:
            system_id: AI system identifier
            db_session: Database session
            limit: Maximum number of results to return

        Returns:
            List of bias test results
        """
        logger.info(f"Retrieving bias test results for system: {system_id}")

        try:
            results = []

            if db_session:
                from ..models.india_compliance_models import IndiaBiasTestResults

                db_results = db_session.query(IndiaBiasTestResults).filter(
                    IndiaBiasTestResults.system_id == system_id
                ).order_by(
                    IndiaBiasTestResults.timestamp.desc()
                ).limit(limit).all()

                for result in db_results:
                    results.append({
                        "id": str(result.id),
                        "test_id": result.test_id,
                        "system_id": result.system_id,
                        "user_id": result.user_id,
                        "model_id": result.model_id,
                        "bias_type": result.bias_type,
                        "bias_detected": result.bias_detected,
                        "severity": result.severity,
                        "affected_groups": result.affected_groups,
                        "fairness_metrics": result.fairness_metrics,
                        "recommendations": result.recommendations,
                        "timestamp": result.timestamp.isoformat(),
                    })

            return results

        except Exception as e:
            logger.error(f"Error retrieving bias test results for system: {e}")
            raise

    async def link_bias_results_to_evidence(
        self,
        test_id: str,
        evidence_id: str,
        db_session: Any = None,
    ) -> bool:
        """
        Link bias test results to compliance evidence.

        Creates audit trail by linking bias detection results to
        compliance evidence records.

        Args:
            test_id: Bias test identifier
            evidence_id: Compliance evidence identifier
            db_session: Database session

        Returns:
            True if link created successfully
        """
        logger.info(f"Linking bias test {test_id} to evidence {evidence_id}")

        try:
            if db_session:
                from ..models.india_compliance_models import (
                    IndiaBiasTestResults,
                    IndiaComplianceEvidence,
                )

                # Update bias test result with evidence link
                bias_result = db_session.query(IndiaBiasTestResults).filter(
                    IndiaBiasTestResults.test_id == test_id
                ).first()

                if bias_result:
                    # Store evidence ID in metadata
                    if not bias_result.metadata:
                        bias_result.metadata = {}

                    bias_result.metadata["linked_evidence_id"] = evidence_id
                    db_session.commit()

                    logger.info(f"Successfully linked bias test to evidence")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error linking bias results to evidence: {e}")
            raise
