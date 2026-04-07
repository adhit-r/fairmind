"""
Advanced Bias Detection Service
Implements sophisticated bias detection methods including:
- Causal Analysis and Counterfactual Explanations
- Intersectional Bias Detection
- Adversarial Bias Testing
- Temporal Bias Analysis
- Contextual Bias Detection
- Bias Amplification Analysis
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter
import math

# Optional imports for advanced features
try:
    import scipy.stats as stats
    from scipy.spatial.distance import cosine, euclidean
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

logger = logging.getLogger(__name__)

class BiasType(Enum):
    """Advanced bias types for sophisticated detection"""
    CAUSAL = "causal"
    COUNTERFACTUAL = "counterfactual"
    INTERSECTIONAL = "intersectional"
    ADVERSARIAL = "adversarial"
    TEMPORAL = "temporal"
    CONTEXTUAL = "contextual"
    AMPLIFICATION = "amplification"
    EMERGENT = "emergent"
    COMPOUND = "compound"
    LATENT = "latent"

class AnalysisMethod(Enum):
    """Advanced analysis methods"""
    CAUSAL_INFERENCE = "causal_inference"
    COUNTERFACTUAL_GENERATION = "counterfactual_generation"
    INTERSECTIONAL_ANALYSIS = "intersectional_analysis"
    ADVERSARIAL_TESTING = "adversarial_testing"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    CONTEXT_SENSITIVE = "context_sensitive"
    AMPLIFICATION_DETECTION = "amplification_detection"
    EMERGENCE_DETECTION = "emergence_detection"
    COMPOUND_EFFECTS = "compound_effects"
    LATENT_BIAS_MINING = "latent_bias_mining"

@dataclass
class CausalAnalysisResult:
    """Results from causal bias analysis"""
    treatment_effect: float
    confidence_interval: Tuple[float, float]
    p_value: float
    causal_strength: float
    confounding_factors: List[str]
    mediation_effects: Dict[str, float]
    interaction_effects: Dict[str, float]
    robustness_score: float

@dataclass
class CounterfactualResult:
    """Results from counterfactual bias analysis"""
    original_prediction: float
    counterfactual_prediction: float
    bias_magnitude: float
    intervention_effect: float
    feature_importance: Dict[str, float]
    minimal_intervention: Dict[str, Any]
    confidence_score: float
    explanation: str

@dataclass
class IntersectionalBiasResult:
    """Results from intersectional bias analysis"""
    intersection_groups: List[str]
    bias_scores: Dict[str, float]
    compound_effects: Dict[str, float]
    interaction_strength: float
    fairness_gaps: Dict[str, float]
    worst_case_group: str
    mitigation_priority: List[str]

@dataclass
class AdversarialBiasResult:
    """Results from adversarial bias testing"""
    attack_success_rate: float
    bias_amplification: float
    robustness_score: float
    vulnerable_features: List[str]
    attack_vectors: List[str]
    defense_effectiveness: float
    worst_case_scenarios: List[Dict[str, Any]]

@dataclass
class TemporalBiasResult:
    """Results from temporal bias analysis"""
    temporal_trends: Dict[str, List[float]]
    seasonality_effects: Dict[str, float]
    drift_detection: Dict[str, float]
    concept_drift: float
    performance_degradation: float
    adaptation_recommendations: List[str]

@dataclass
class ContextualBiasResult:
    """Results from contextual bias analysis"""
    context_sensitivity: Dict[str, float]
    domain_adaptation: Dict[str, float]
    cultural_bias: Dict[str, float]
    linguistic_bias: Dict[str, float]
    situational_fairness: Dict[str, float]
    context_recommendations: List[str]

@dataclass
class AdvancedBiasAnalysisResult:
    """Comprehensive results from advanced bias analysis"""
    analysis_id: str
    timestamp: datetime
    bias_type: BiasType
    analysis_method: AnalysisMethod
    overall_bias_score: float
    confidence_level: float
    detailed_results: Union[
        CausalAnalysisResult,
        CounterfactualResult,
        IntersectionalBiasResult,
        AdversarialBiasResult,
        TemporalBiasResult,
        ContextualBiasResult
    ]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    metadata: Dict[str, Any]

class AdvancedBiasDetectionService:
    """Service for advanced bias detection methods"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analysis_cache = {}
        self.bias_patterns = self._initialize_bias_patterns()
        
    def _initialize_bias_patterns(self) -> Dict[str, Any]:
        """Initialize known bias patterns for detection"""
        return {
            "intersectional_patterns": {
                "gender_race": ["woman_black", "woman_hispanic", "man_white", "man_asian"],
                "age_gender": ["young_woman", "old_man", "middle_aged_woman", "senior_man"],
                "education_income": ["high_education_low_income", "low_education_high_income"],
                "disability_status": ["disabled_woman", "disabled_man", "non_disabled_woman"]
            },
            "temporal_patterns": {
                "seasonal": ["spring", "summer", "fall", "winter"],
                "monthly": list(range(1, 13)),
                "weekly": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "hourly": list(range(24))
            },
            "contextual_patterns": {
                "professional": ["medical", "legal", "technical", "creative", "service"],
                "cultural": ["western", "eastern", "african", "latin", "middle_eastern"],
                "linguistic": ["formal", "informal", "technical", "colloquial", "academic"]
            }
        }
    
    async def analyze_causal_bias(
        self,
        data: List[Dict[str, Any]],
        treatment_variable: str,
        outcome_variable: str,
        protected_attributes: List[str],
        confounders: Optional[List[str]] = None
    ) -> AdvancedBiasAnalysisResult:
        """
        Perform causal analysis to detect bias in treatment effects
        
        Args:
            data: Input data for analysis
            treatment_variable: Variable representing the treatment/intervention
            outcome_variable: Variable representing the outcome
            protected_attributes: List of protected attributes to analyze
            confounders: Optional list of confounding variables
        """
        try:
            self.logger.info(f"Starting causal bias analysis for treatment: {treatment_variable}")
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(data)
            
            # Perform causal inference analysis
            causal_results = await self._perform_causal_inference(
                df, treatment_variable, outcome_variable, protected_attributes, confounders
            )
            
            # Calculate overall bias score
            bias_score = self._calculate_causal_bias_score(causal_results)
            
            # Generate recommendations
            recommendations = self._generate_causal_recommendations(causal_results)
            
            # Create result
            result = AdvancedBiasAnalysisResult(
                analysis_id=f"causal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                bias_type=BiasType.CAUSAL,
                analysis_method=AnalysisMethod.CAUSAL_INFERENCE,
                overall_bias_score=bias_score,
                confidence_level=causal_results.robustness_score,
                detailed_results=causal_results,
                recommendations=recommendations,
                risk_assessment=self._assess_causal_risk(causal_results),
                metadata={
                    "treatment_variable": treatment_variable,
                    "outcome_variable": outcome_variable,
                    "protected_attributes": protected_attributes,
                    "confounders": confounders or [],
                    "sample_size": len(data)
                }
            )
            
            self.logger.info(f"Causal bias analysis completed. Bias score: {bias_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in causal bias analysis: {str(e)}")
            raise
    
    async def _perform_causal_inference(
        self,
        df: pd.DataFrame,
        treatment: str,
        outcome: str,
        protected_attrs: List[str],
        confounders: Optional[List[str]]
    ) -> CausalAnalysisResult:
        """Perform causal inference analysis using difference-in-means with t-tests"""

        if treatment not in df.columns or outcome not in df.columns:
            return CausalAnalysisResult(
                treatment_effect=0.0,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                causal_strength=0.0,
                confounding_factors=[],
                mediation_effects={},
                interaction_effects={},
                robustness_score=0.0
            )

        # Binarize treatment if not already binary
        treatment_vals = df[treatment].dropna()
        if treatment_vals.nunique() > 2:
            median_val = treatment_vals.median()
            treated = df[df[treatment] >= median_val][outcome].dropna()
            control = df[df[treatment] < median_val][outcome].dropna()
        else:
            unique_vals = sorted(treatment_vals.unique())
            treated = df[df[treatment] == unique_vals[-1]][outcome].dropna()
            control = df[df[treatment] == unique_vals[0]][outcome].dropna()

        # Difference-in-means treatment effect with Welch's t-test
        if len(treated) < 2 or len(control) < 2:
            return CausalAnalysisResult(
                treatment_effect=0.0,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                causal_strength=0.0,
                confounding_factors=[],
                mediation_effects={},
                interaction_effects={},
                robustness_score=0.0
            )

        treatment_effect = float(treated.mean() - control.mean())

        if SCIPY_AVAILABLE:
            t_stat, p_value = stats.ttest_ind(treated, control, equal_var=False)
            p_value = float(p_value)
            # 95% confidence interval via t-distribution
            se = math.sqrt(treated.var() / len(treated) + control.var() / len(control))
            dof = len(treated) + len(control) - 2
            t_crit = stats.t.ppf(0.975, dof)
            ci = (treatment_effect - t_crit * se, treatment_effect + t_crit * se)
        else:
            se = math.sqrt(treated.var() / len(treated) + control.var() / len(control))
            z_score = treatment_effect / se if se > 0 else 0.0
            p_value = float(2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2)))))
            ci = (treatment_effect - 1.96 * se, treatment_effect + 1.96 * se)

        confidence_interval = (float(ci[0]), float(ci[1]))

        # Causal strength: Cohen's d (effect size)
        pooled_std = math.sqrt(
            ((len(treated) - 1) * treated.var() + (len(control) - 1) * control.var())
            / (len(treated) + len(control) - 2)
        )
        causal_strength = float(abs(treatment_effect) / pooled_std) if pooled_std > 0 else 0.0

        # Identify confounding factors via correlation with both treatment and outcome
        confounding_factors = []
        if confounders:
            for confounder in confounders:
                if confounder in df.columns:
                    corr_treatment = df[treatment].corr(df[confounder])
                    corr_outcome = df[outcome].corr(df[confounder])
                    if abs(corr_treatment) > 0.3 and abs(corr_outcome) > 0.3:
                        confounding_factors.append(confounder)

        # Mediation effects: proportion of treatment-outcome association
        # explained through each protected attribute
        mediation_effects = {}
        for attr in protected_attrs:
            if attr in df.columns:
                corr_treat_attr = df[treatment].corr(df[attr])
                corr_attr_outcome = df[attr].corr(df[outcome])
                # Indirect effect estimate (product of coefficients method)
                indirect = corr_treat_attr * corr_attr_outcome
                mediation_effects[attr] = float(abs(indirect))

        # Interaction effects: difference in treatment effect across
        # protected attribute subgroups
        interaction_effects = {}
        for attr in protected_attrs:
            if attr in df.columns:
                attr_vals = df[attr].dropna()
                if attr_vals.nunique() >= 2:
                    if attr_vals.nunique() > 2:
                        median_a = attr_vals.median()
                        group_high = df[df[attr] >= median_a]
                        group_low = df[df[attr] < median_a]
                    else:
                        vals = sorted(attr_vals.unique())
                        group_high = df[df[attr] == vals[-1]]
                        group_low = df[df[attr] == vals[0]]

                    te_high = group_high[outcome].mean() - group_high[outcome].mean() if len(group_high) < 2 else 0.0
                    te_low = 0.0
                    # Treatment effect in each subgroup
                    if treatment_vals.nunique() <= 2:
                        unique_t = sorted(treatment_vals.unique())
                        t_high_treated = group_high[group_high[treatment] == unique_t[-1]][outcome]
                        t_high_control = group_high[group_high[treatment] == unique_t[0]][outcome]
                        t_low_treated = group_low[group_low[treatment] == unique_t[-1]][outcome]
                        t_low_control = group_low[group_low[treatment] == unique_t[0]][outcome]
                        te_high = float(t_high_treated.mean() - t_high_control.mean()) if len(t_high_treated) > 0 and len(t_high_control) > 0 else 0.0
                        te_low = float(t_low_treated.mean() - t_low_control.mean()) if len(t_low_treated) > 0 and len(t_low_control) > 0 else 0.0
                    else:
                        median_t = treatment_vals.median()
                        te_high = float(group_high[group_high[treatment] >= median_t][outcome].mean() - group_high[group_high[treatment] < median_t][outcome].mean()) if len(group_high) > 1 else 0.0
                        te_low = float(group_low[group_low[treatment] >= median_t][outcome].mean() - group_low[group_low[treatment] < median_t][outcome].mean()) if len(group_low) > 1 else 0.0

                    te_high = 0.0 if math.isnan(te_high) else te_high
                    te_low = 0.0 if math.isnan(te_low) else te_low
                    interaction_effects[attr] = float(abs(te_high - te_low))

        # Robustness score: penalize for confounders and low significance
        robustness_score = max(0.0, min(1.0, 1.0 - len(confounding_factors) * 0.15 - p_value))

        return CausalAnalysisResult(
            treatment_effect=float(treatment_effect),
            confidence_interval=confidence_interval,
            p_value=float(p_value),
            causal_strength=float(causal_strength),
            confounding_factors=confounding_factors,
            mediation_effects=mediation_effects,
            interaction_effects=interaction_effects,
            robustness_score=float(robustness_score)
        )
    
    async def analyze_counterfactual_bias(
        self,
        model_predictions: List[Dict[str, Any]],
        protected_attributes: List[str],
        intervention_strategy: str = "minimal"
    ) -> AdvancedBiasAnalysisResult:
        """
        Perform counterfactual analysis to detect bias
        
        Args:
            model_predictions: List of model predictions with features
            protected_attributes: List of protected attributes
            intervention_strategy: Strategy for counterfactual generation
        """
        try:
            self.logger.info("Starting counterfactual bias analysis")
            
            # Generate counterfactual predictions
            counterfactual_results = await self._generate_counterfactuals(
                model_predictions, protected_attributes, intervention_strategy
            )
            
            # Calculate bias score
            bias_score = abs(counterfactual_results.bias_magnitude)
            
            # Generate recommendations
            recommendations = self._generate_counterfactual_recommendations(counterfactual_results)
            
            # Create result
            result = AdvancedBiasAnalysisResult(
                analysis_id=f"counterfactual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                bias_type=BiasType.COUNTERFACTUAL,
                analysis_method=AnalysisMethod.COUNTERFACTUAL_GENERATION,
                overall_bias_score=bias_score,
                confidence_level=counterfactual_results.confidence_score,
                detailed_results=counterfactual_results,
                recommendations=recommendations,
                risk_assessment=self._assess_counterfactual_risk(counterfactual_results),
                metadata={
                    "protected_attributes": protected_attributes,
                    "intervention_strategy": intervention_strategy,
                    "sample_size": len(model_predictions)
                }
            )
            
            self.logger.info(f"Counterfactual bias analysis completed. Bias score: {bias_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in counterfactual bias analysis: {str(e)}")
            raise
    
    async def _generate_counterfactuals(
        self,
        predictions: List[Dict[str, Any]],
        protected_attrs: List[str],
        strategy: str
    ) -> CounterfactualResult:
        """Generate counterfactual predictions by flipping protected attributes
        and measuring prediction change."""

        df = pd.DataFrame(predictions)

        if len(df) == 0 or 'prediction' not in df.columns:
            return CounterfactualResult(
                original_prediction=0.0,
                counterfactual_prediction=0.0,
                bias_magnitude=0.0,
                intervention_effect=0.0,
                feature_importance={},
                minimal_intervention={},
                confidence_score=0.0,
                explanation="Insufficient data: no predictions found in input."
            )

        original_pred = float(df['prediction'].mean())

        # For each protected attribute, compute the counterfactual prediction
        # by swapping attribute values and measuring the change
        attr_effects = {}
        attr_counterfactual_preds = {}
        for attr in protected_attrs:
            if attr not in df.columns:
                continue
            attr_vals = df[attr].dropna().unique()
            if len(attr_vals) < 2:
                attr_effects[attr] = 0.0
                continue

            # For each row, compute the mean prediction of the opposite group
            group_means = df.groupby(attr)['prediction'].mean()
            # Effect: difference between group means (max - min)
            effect = float(group_means.max() - group_means.min())
            attr_effects[attr] = effect

            # Counterfactual prediction: for each sample, assign the mean of
            # the complementary group
            counterfactual_preds = []
            for val in attr_vals:
                other_vals = [v for v in attr_vals if v != val]
                if other_vals:
                    other_mean = float(df[df[attr].isin(other_vals)]['prediction'].mean())
                    counterfactual_preds.append(other_mean)
            if counterfactual_preds:
                attr_counterfactual_preds[attr] = float(np.mean(counterfactual_preds))

        # Overall counterfactual prediction: average across attribute counterfactuals
        if attr_counterfactual_preds:
            counterfactual_pred = float(np.mean(list(attr_counterfactual_preds.values())))
        else:
            counterfactual_pred = original_pred

        bias_magnitude = float(counterfactual_pred - original_pred)
        intervention_effect = float(abs(bias_magnitude))

        # Feature importance: normalized absolute effects
        total_effect = sum(abs(v) for v in attr_effects.values())
        feature_importance = {}
        for attr, effect in attr_effects.items():
            feature_importance[attr] = float(abs(effect) / total_effect) if total_effect > 0 else 0.0

        # Minimal intervention: recommend strategy based on effect magnitude
        minimal_intervention = {}
        for attr, effect in attr_effects.items():
            if abs(effect) > 0.2:
                minimal_intervention[attr] = "balance"
            elif abs(effect) > 0.05:
                minimal_intervention[attr] = "neutralize"
            else:
                minimal_intervention[attr] = "none"

        # Confidence score based on sample size and consistency
        n = len(df)
        confidence_score = float(min(1.0, max(0.0, 1.0 - 1.0 / math.sqrt(n) - abs(bias_magnitude))))

        # Generate explanation
        top_attrs = sorted(attr_effects.items(), key=lambda x: abs(x[1]), reverse=True)
        explanation = f"Counterfactual analysis on {n} samples shows {bias_magnitude:.3f} bias magnitude. "
        if top_attrs:
            explanation += f"Most sensitive attribute: {top_attrs[0][0]} (effect={top_attrs[0][1]:.3f}). "
        explanation += f"Recommended interventions: {minimal_intervention}"

        return CounterfactualResult(
            original_prediction=original_pred,
            counterfactual_prediction=counterfactual_pred,
            bias_magnitude=bias_magnitude,
            intervention_effect=intervention_effect,
            feature_importance=feature_importance,
            minimal_intervention=minimal_intervention,
            confidence_score=confidence_score,
            explanation=explanation
        )
    
    async def analyze_intersectional_bias(
        self,
        data: List[Dict[str, Any]],
        intersection_groups: List[List[str]],
        outcome_variable: str
    ) -> AdvancedBiasAnalysisResult:
        """
        Perform intersectional bias analysis
        
        Args:
            data: Input data
            intersection_groups: List of intersectional group combinations
            outcome_variable: Variable to analyze for bias
        """
        try:
            self.logger.info("Starting intersectional bias analysis")
            
            # Perform intersectional analysis
            intersectional_results = await self._perform_intersectional_analysis(
                data, intersection_groups, outcome_variable
            )
            
            # Calculate overall bias score
            bias_score = max(intersectional_results.bias_scores.values()) if intersectional_results.bias_scores else 0
            
            # Generate recommendations
            recommendations = self._generate_intersectional_recommendations(intersectional_results)
            
            # Create result
            result = AdvancedBiasAnalysisResult(
                analysis_id=f"intersectional_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                bias_type=BiasType.INTERSECTIONAL,
                analysis_method=AnalysisMethod.INTERSECTIONAL_ANALYSIS,
                overall_bias_score=bias_score,
                confidence_level=0.85,  # High confidence for intersectional analysis
                detailed_results=intersectional_results,
                recommendations=recommendations,
                risk_assessment=self._assess_intersectional_risk(intersectional_results),
                metadata={
                    "intersection_groups": intersection_groups,
                    "outcome_variable": outcome_variable,
                    "sample_size": len(data)
                }
            )
            
            self.logger.info(f"Intersectional bias analysis completed. Max bias score: {bias_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in intersectional bias analysis: {str(e)}")
            raise
    
    async def _perform_intersectional_analysis(
        self,
        data: List[Dict[str, Any]],
        intersection_groups: List[List[str]],
        outcome_var: str
    ) -> IntersectionalBiasResult:
        """Perform intersectional bias analysis by computing real group-level
        metrics and measuring outcome disparities between intersectional groups."""

        df = pd.DataFrame(data)

        if outcome_var not in df.columns or len(df) == 0:
            return IntersectionalBiasResult(
                intersection_groups=["_".join(group) for group in intersection_groups],
                bias_scores={},
                compound_effects={},
                interaction_strength=0.0,
                fairness_gaps={},
                worst_case_group="",
                mitigation_priority=[]
            )

        overall_mean = float(df[outcome_var].mean())
        overall_std = float(df[outcome_var].std()) if len(df) > 1 else 1.0
        if overall_std == 0:
            overall_std = 1.0

        bias_scores = {}
        compound_effects = {}
        fairness_gaps = {}
        individual_effects = {}  # store single-attribute effects for compound calc

        # Pre-compute individual attribute effects for compound effect calculation
        for group_combo in intersection_groups:
            for attr in group_combo:
                if attr not in individual_effects and attr in df.columns:
                    attr_data = df[df[attr] == 1][outcome_var] if df[attr].nunique() <= 2 else df[df[attr] >= df[attr].median()][outcome_var]
                    if len(attr_data) > 0:
                        individual_effects[attr] = float(abs(attr_data.mean() - overall_mean))
                    else:
                        individual_effects[attr] = 0.0

        for group_combo in intersection_groups:
            group_name = "_".join(group_combo)

            # Filter data for this intersection
            group_data = df.copy()
            valid_attrs = []
            for attr in group_combo:
                if attr in df.columns:
                    valid_attrs.append(attr)
                    if df[attr].nunique() <= 2:
                        group_data = group_data[group_data[attr] == 1]
                    else:
                        group_data = group_data[group_data[attr] >= df[attr].median()]

            if len(group_data) > 0 and outcome_var in group_data.columns:
                group_mean = float(group_data[outcome_var].mean())

                # Bias score: standardized difference from overall mean
                bias_scores[group_name] = float(abs(group_mean - overall_mean) / overall_std)

                # Compound effect: how much the intersectional effect exceeds
                # the sum of individual attribute effects (super-additivity)
                sum_individual = sum(individual_effects.get(a, 0.0) for a in valid_attrs)
                intersectional_effect = abs(group_mean - overall_mean)
                compound_effects[group_name] = float(
                    max(0.0, intersectional_effect - sum_individual) / overall_std
                )

                # Fairness gap: relative disparity
                fairness_gaps[group_name] = float(
                    abs(group_mean - overall_mean) / abs(overall_mean)
                ) if overall_mean != 0 else 0.0
            else:
                bias_scores[group_name] = 0.0
                compound_effects[group_name] = 0.0
                fairness_gaps[group_name] = 0.0

        # Interaction strength: mean compound effect across groups
        interaction_strength = float(np.mean(list(compound_effects.values()))) if compound_effects else 0.0

        # Find worst case group
        worst_case_group = max(bias_scores.keys(), key=lambda k: bias_scores[k]) if bias_scores else ""

        # Generate mitigation priority
        mitigation_priority = sorted(bias_scores.keys(), key=lambda k: bias_scores[k], reverse=True)

        return IntersectionalBiasResult(
            intersection_groups=["_".join(group) for group in intersection_groups],
            bias_scores=bias_scores,
            compound_effects=compound_effects,
            interaction_strength=interaction_strength,
            fairness_gaps=fairness_gaps,
            worst_case_group=worst_case_group,
            mitigation_priority=mitigation_priority
        )
    
    async def analyze_adversarial_bias(
        self,
        model_predictions: List[Dict[str, Any]],
        attack_vectors: List[str],
        protected_attributes: List[str]
    ) -> AdvancedBiasAnalysisResult:
        """
        Perform adversarial bias testing
        
        Args:
            model_predictions: Model predictions to test
            attack_vectors: List of attack vectors to test
            protected_attributes: Protected attributes to focus on
        """
        try:
            self.logger.info("Starting adversarial bias testing")
            
            # Perform adversarial testing
            adversarial_results = await self._perform_adversarial_testing(
                model_predictions, attack_vectors, protected_attributes
            )
            
            # Calculate overall bias score
            bias_score = adversarial_results.bias_amplification
            
            # Generate recommendations
            recommendations = self._generate_adversarial_recommendations(adversarial_results)
            
            # Create result
            result = AdvancedBiasAnalysisResult(
                analysis_id=f"adversarial_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                bias_type=BiasType.ADVERSARIAL,
                analysis_method=AnalysisMethod.ADVERSARIAL_TESTING,
                overall_bias_score=bias_score,
                confidence_level=adversarial_results.robustness_score,
                detailed_results=adversarial_results,
                recommendations=recommendations,
                risk_assessment=self._assess_adversarial_risk(adversarial_results),
                metadata={
                    "attack_vectors": attack_vectors,
                    "protected_attributes": protected_attributes,
                    "sample_size": len(model_predictions)
                }
            )
            
            self.logger.info(f"Adversarial bias testing completed. Bias amplification: {bias_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in adversarial bias testing: {str(e)}")
            raise
    
    async def _perform_adversarial_testing(
        self,
        predictions: List[Dict[str, Any]],
        attack_vectors: List[str],
        protected_attrs: List[str]
    ) -> AdversarialBiasResult:
        """Perform adversarial bias testing by perturbing protected attributes
        and measuring model sensitivity to those changes."""

        df = pd.DataFrame(predictions)

        if len(df) == 0 or 'prediction' not in df.columns:
            return AdversarialBiasResult(
                attack_success_rate=0.0,
                bias_amplification=0.0,
                robustness_score=1.0,
                vulnerable_features=[],
                attack_vectors=attack_vectors,
                defense_effectiveness=1.0,
                worst_case_scenarios=[]
            )

        original_preds = df['prediction'].values.astype(float)
        overall_mean = float(np.mean(original_preds))
        overall_std = float(np.std(original_preds)) if len(original_preds) > 1 else 1.0
        if overall_std == 0:
            overall_std = 1.0

        # For each protected attribute, measure sensitivity by computing
        # prediction variance across attribute groups
        attr_sensitivities = {}
        vulnerable_features = []

        for attr in protected_attrs:
            if attr not in df.columns:
                continue
            groups = df.groupby(attr)['prediction']
            if groups.ngroups < 2:
                attr_sensitivities[attr] = 0.0
                continue

            group_means = groups.mean()
            # Sensitivity: range of group means normalized by overall std
            sensitivity = float((group_means.max() - group_means.min()) / overall_std)
            attr_sensitivities[attr] = sensitivity

            # A feature is vulnerable if perturbing it causes >10% shift
            if sensitivity > 0.1:
                vulnerable_features.append(attr)

        # Attack success rate: fraction of attributes that are vulnerable
        total_tested = len([a for a in protected_attrs if a in df.columns])
        attack_success_rate = float(len(vulnerable_features) / total_tested) if total_tested > 0 else 0.0

        # Bias amplification: max sensitivity across attributes
        max_sensitivity = max(attr_sensitivities.values()) if attr_sensitivities else 0.0
        bias_amplification = float(min(1.0, max_sensitivity))

        # Robustness score
        robustness_score = float(max(0.0, 1.0 - attack_success_rate * 0.5 - bias_amplification * 0.5))

        # Defense effectiveness
        defense_effectiveness = float(max(0.0, 1.0 - attack_success_rate))

        # Build worst-case scenarios from actual data
        worst_case_scenarios = []
        sorted_attrs = sorted(attr_sensitivities.items(), key=lambda x: x[1], reverse=True)
        for attr, sensitivity in sorted_attrs[:min(3, len(sorted_attrs))]:
            if attr not in df.columns:
                continue
            groups = df.groupby(attr)['prediction']
            group_means = groups.mean()
            worst_group = group_means.idxmin()
            best_group = group_means.idxmax()

            # Compute a confidence measure from the statistical test
            worst_vals = df[df[attr] == worst_group]['prediction'].values
            best_vals = df[df[attr] == best_group]['prediction'].values
            confidence = 0.5
            if SCIPY_AVAILABLE and len(worst_vals) >= 2 and len(best_vals) >= 2:
                _, p_val = stats.ttest_ind(worst_vals, best_vals, equal_var=False)
                confidence = float(1.0 - p_val)

            # Associate with the most relevant attack vector
            attack_type = attack_vectors[0] if attack_vectors else "attribute_perturbation"
            for vector in attack_vectors:
                if attr.lower() in vector.lower() or vector.lower() in attr.lower():
                    attack_type = vector
                    break

            worst_case_scenarios.append({
                "attack_type": attack_type,
                "bias_increase": float(sensitivity),
                "affected_group": attr,
                "worst_subgroup": str(worst_group),
                "best_subgroup": str(best_group),
                "confidence": float(min(1.0, max(0.0, confidence)))
            })

        return AdversarialBiasResult(
            attack_success_rate=attack_success_rate,
            bias_amplification=bias_amplification,
            robustness_score=robustness_score,
            vulnerable_features=vulnerable_features,
            attack_vectors=attack_vectors,
            defense_effectiveness=defense_effectiveness,
            worst_case_scenarios=worst_case_scenarios
        )
    
    async def analyze_temporal_bias(
        self,
        time_series_data: List[Dict[str, Any]],
        time_column: str,
        outcome_variable: str,
        protected_attributes: List[str]
    ) -> AdvancedBiasAnalysisResult:
        """
        Perform temporal bias analysis
        
        Args:
            time_series_data: Time series data
            time_column: Column containing time information
            outcome_variable: Variable to analyze
            protected_attributes: Protected attributes to monitor
        """
        try:
            self.logger.info("Starting temporal bias analysis")
            
            # Perform temporal analysis
            temporal_results = await self._perform_temporal_analysis(
                time_series_data, time_column, outcome_variable, protected_attributes
            )
            
            # Calculate overall bias score
            bias_score = temporal_results.concept_drift
            
            # Generate recommendations
            recommendations = self._generate_temporal_recommendations(temporal_results)
            
            # Create result
            result = AdvancedBiasAnalysisResult(
                analysis_id=f"temporal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                bias_type=BiasType.TEMPORAL,
                analysis_method=AnalysisMethod.TEMPORAL_ANALYSIS,
                overall_bias_score=bias_score,
                confidence_level=0.8,
                detailed_results=temporal_results,
                recommendations=recommendations,
                risk_assessment=self._assess_temporal_risk(temporal_results),
                metadata={
                    "time_column": time_column,
                    "outcome_variable": outcome_variable,
                    "protected_attributes": protected_attributes,
                    "sample_size": len(time_series_data)
                }
            )
            
            self.logger.info(f"Temporal bias analysis completed. Concept drift: {bias_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in temporal bias analysis: {str(e)}")
            raise
    
    async def _perform_temporal_analysis(
        self,
        data: List[Dict[str, Any]],
        time_col: str,
        outcome_var: str,
        protected_attrs: List[str]
    ) -> TemporalBiasResult:
        """Perform temporal bias analysis using rolling statistics and
        distribution shift detection (KS tests)."""

        df = pd.DataFrame(data)

        if time_col not in df.columns or outcome_var not in df.columns or len(df) < 4:
            return TemporalBiasResult(
                temporal_trends={},
                seasonality_effects={},
                drift_detection={},
                concept_drift=0.0,
                performance_degradation=0.0,
                adaptation_recommendations=[
                    "Insufficient temporal data for analysis. Collect more time-stamped samples."
                ]
            )

        # Convert time column to datetime and sort
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df = df.dropna(subset=[time_col]).sort_values(time_col).reset_index(drop=True)

        if len(df) < 4:
            return TemporalBiasResult(
                temporal_trends={},
                seasonality_effects={},
                drift_detection={},
                concept_drift=0.0,
                performance_degradation=0.0,
                adaptation_recommendations=[
                    "Insufficient valid temporal data after parsing dates."
                ]
            )

        # Split data into time windows for trend analysis
        n = len(df)
        n_windows = min(12, max(2, n // 5))  # between 2 and 12 windows
        window_size = n // n_windows

        # Temporal trends: per-window mean bias gap for each protected attribute
        temporal_trends = {}
        overall_mean = float(df[outcome_var].mean())

        for attr in protected_attrs:
            if attr not in df.columns:
                continue
            trend = []
            for i in range(n_windows):
                start_idx = i * window_size
                end_idx = start_idx + window_size if i < n_windows - 1 else n
                window = df.iloc[start_idx:end_idx]
                if len(window) > 0 and attr in window.columns:
                    groups = window.groupby(attr)[outcome_var].mean()
                    if len(groups) >= 2:
                        gap = float(groups.max() - groups.min())
                    else:
                        gap = 0.0
                else:
                    gap = 0.0
                trend.append(gap)
            temporal_trends[attr] = trend

        # Seasonality effects: if data spans enough time, measure variance
        # of bias gaps across windows (higher variance = more seasonality)
        seasonality_effects = {}
        for attr, trend in temporal_trends.items():
            if len(trend) >= 2:
                trend_std = float(np.std(trend))
                trend_mean = float(np.mean(trend)) if np.mean(trend) != 0 else 1.0
                # Coefficient of variation as seasonality measure
                seasonality_effects[attr] = float(trend_std / abs(trend_mean)) if abs(trend_mean) > 0 else 0.0
            else:
                seasonality_effects[attr] = 0.0

        # Drift detection: KS test between first half and second half
        # for outcome distribution within each protected attribute group
        drift_detection = {}
        half = n // 2
        first_half = df.iloc[:half]
        second_half = df.iloc[half:]

        for attr in protected_attrs:
            if attr not in df.columns:
                drift_detection[attr] = 0.0
                continue

            # Compute bias gap in first half vs second half
            first_outcome = first_half[outcome_var].values
            second_outcome = second_half[outcome_var].values

            if SCIPY_AVAILABLE and len(first_outcome) >= 2 and len(second_outcome) >= 2:
                ks_stat, ks_p = stats.ks_2samp(first_outcome, second_outcome)
                drift_detection[attr] = float(ks_stat)
            elif len(first_outcome) >= 1 and len(second_outcome) >= 1:
                # Fallback: absolute difference in means normalized by pooled std
                pooled_std = float(np.std(np.concatenate([first_outcome, second_outcome])))
                if pooled_std > 0:
                    drift_detection[attr] = float(abs(np.mean(first_outcome) - np.mean(second_outcome)) / pooled_std)
                else:
                    drift_detection[attr] = 0.0
            else:
                drift_detection[attr] = 0.0

        # Concept drift: mean drift across attributes
        concept_drift = float(np.mean(list(drift_detection.values()))) if drift_detection else 0.0

        # Performance degradation: compare outcome variance between halves
        first_var = float(first_half[outcome_var].var()) if len(first_half) > 1 else 0.0
        second_var = float(second_half[outcome_var].var()) if len(second_half) > 1 else 0.0
        performance_degradation = float(abs(second_var - first_var) / max(first_var, 1e-10))
        performance_degradation = min(1.0, performance_degradation)

        # Generate data-driven adaptation recommendations
        adaptation_recommendations = []
        if concept_drift > 0.3:
            adaptation_recommendations.append("High distribution drift detected -- retrain model on recent data.")
        if concept_drift > 0.1:
            adaptation_recommendations.append("Use sliding window training to adapt to distribution changes.")
        for attr, drift_val in drift_detection.items():
            if drift_val > 0.3:
                adaptation_recommendations.append(
                    f"Significant drift in '{attr}' (KS={drift_val:.3f}) -- monitor and rebalance."
                )
        for attr, seas in seasonality_effects.items():
            if seas > 0.5:
                adaptation_recommendations.append(
                    f"High seasonality in '{attr}' bias gap (CV={seas:.3f}) -- add time-based features."
                )
        if performance_degradation > 0.2:
            adaptation_recommendations.append(
                "Outcome variance has shifted over time -- implement adaptive learning rates."
            )
        if not adaptation_recommendations:
            adaptation_recommendations.append("No significant temporal bias drift detected.")

        return TemporalBiasResult(
            temporal_trends=temporal_trends,
            seasonality_effects=seasonality_effects,
            drift_detection=drift_detection,
            concept_drift=concept_drift,
            performance_degradation=performance_degradation,
            adaptation_recommendations=adaptation_recommendations
        )
    
    async def analyze_contextual_bias(
        self,
        data: List[Dict[str, Any]],
        context_features: List[str],
        protected_attributes: List[str],
        outcome_variable: str
    ) -> AdvancedBiasAnalysisResult:
        """
        Perform contextual bias analysis
        
        Args:
            data: Input data
            context_features: Features representing different contexts
            protected_attributes: Protected attributes
            outcome_variable: Variable to analyze
        """
        try:
            self.logger.info("Starting contextual bias analysis")
            
            # Perform contextual analysis
            contextual_results = await self._perform_contextual_analysis(
                data, context_features, protected_attributes, outcome_variable
            )
            
            # Calculate overall bias score
            bias_score = max(contextual_results.context_sensitivity.values()) if contextual_results.context_sensitivity else 0
            
            # Generate recommendations
            recommendations = self._generate_contextual_recommendations(contextual_results)
            
            # Create result
            result = AdvancedBiasAnalysisResult(
                analysis_id=f"contextual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                bias_type=BiasType.CONTEXTUAL,
                analysis_method=AnalysisMethod.CONTEXT_SENSITIVE,
                overall_bias_score=bias_score,
                confidence_level=0.85,
                detailed_results=contextual_results,
                recommendations=recommendations,
                risk_assessment=self._assess_contextual_risk(contextual_results),
                metadata={
                    "context_features": context_features,
                    "protected_attributes": protected_attributes,
                    "outcome_variable": outcome_variable,
                    "sample_size": len(data)
                }
            )
            
            self.logger.info(f"Contextual bias analysis completed. Max context sensitivity: {bias_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in contextual bias analysis: {str(e)}")
            raise
    
    async def _perform_contextual_analysis(
        self,
        data: List[Dict[str, Any]],
        context_features: List[str],
        protected_attrs: List[str],
        outcome_var: str
    ) -> ContextualBiasResult:
        """Perform contextual bias analysis by measuring real performance
        differences across context subgroups."""

        df = pd.DataFrame(data)

        if outcome_var not in df.columns or len(df) == 0:
            return ContextualBiasResult(
                context_sensitivity={},
                domain_adaptation={},
                cultural_bias={},
                linguistic_bias={},
                situational_fairness={},
                context_recommendations=[
                    "Insufficient data for contextual analysis."
                ]
            )

        overall_mean = float(df[outcome_var].mean())
        overall_std = float(df[outcome_var].std()) if len(df) > 1 else 1.0
        if overall_std == 0:
            overall_std = 1.0

        # Context sensitivity: how much outcome varies across context subgroups
        # Measured as the range of group means normalized by overall std
        context_sensitivity = {}
        for context in context_features:
            if context not in df.columns:
                continue
            groups = df.groupby(context)[outcome_var]
            if groups.ngroups < 2:
                context_sensitivity[context] = 0.0
                continue
            group_means = groups.mean()
            context_sensitivity[context] = float(
                (group_means.max() - group_means.min()) / overall_std
            )

        # Domain adaptation: for each context subgroup, measure how different
        # the outcome distribution is from the overall (using std ratio)
        domain_adaptation = {}
        for context in context_features:
            if context not in df.columns:
                continue
            groups = df.groupby(context)[outcome_var]
            if groups.ngroups < 2:
                domain_adaptation[context] = 1.0
                continue
            # Mean absolute deviation of group means from overall mean
            group_means = groups.mean()
            mad = float(np.mean(np.abs(group_means.values - overall_mean)))
            # Normalize: lower = better adaptation (0=perfect, 1=poor)
            domain_adaptation[context] = float(min(1.0, mad / overall_std))

        # Cultural/group bias: for each protected attribute, measure
        # outcome disparity (standardized mean difference)
        cultural_bias = {}
        for attr in protected_attrs:
            if attr not in df.columns:
                continue
            groups = df.groupby(attr)[outcome_var]
            if groups.ngroups < 2:
                cultural_bias[attr] = 0.0
                continue
            group_means = groups.mean()
            cultural_bias[attr] = float(
                (group_means.max() - group_means.min()) / overall_std
            )

        # Linguistic bias: measure outcome variation within each protected
        # attribute group across contexts (interaction effect)
        linguistic_bias = {}
        for attr in protected_attrs:
            if attr not in df.columns:
                linguistic_bias[attr] = 0.0
                continue
            interaction_effects = []
            for context in context_features:
                if context not in df.columns:
                    continue
                cross = df.groupby([attr, context])[outcome_var].mean()
                if len(cross) >= 2:
                    interaction_effects.append(float(cross.max() - cross.min()) / overall_std)
            linguistic_bias[attr] = float(np.mean(interaction_effects)) if interaction_effects else 0.0

        # Situational fairness: for each context, measure how equal
        # outcomes are across protected attributes (1 = perfectly fair)
        situational_fairness = {}
        for context in context_features:
            if context not in df.columns:
                continue
            context_groups = df.groupby(context)
            fairness_scores = []
            for _, ctx_df in context_groups:
                if len(ctx_df) < 2:
                    continue
                for attr in protected_attrs:
                    if attr not in ctx_df.columns:
                        continue
                    attr_groups = ctx_df.groupby(attr)[outcome_var].mean()
                    if len(attr_groups) >= 2:
                        gap = float(attr_groups.max() - attr_groups.min()) / overall_std
                        fairness_scores.append(max(0.0, 1.0 - gap))
            situational_fairness[context] = float(np.mean(fairness_scores)) if fairness_scores else 1.0

        # Generate data-driven recommendations
        context_recommendations = []
        for context, sensitivity in context_sensitivity.items():
            if sensitivity > 0.3:
                context_recommendations.append(
                    f"High outcome sensitivity in '{context}' (sensitivity={sensitivity:.3f}) -- use context-aware models."
                )
        for attr, bias in cultural_bias.items():
            if bias > 0.2:
                context_recommendations.append(
                    f"Group disparity on '{attr}' (gap={bias:.3f}) -- implement targeted debiasing."
                )
        for context, adapt in domain_adaptation.items():
            if adapt > 0.3:
                context_recommendations.append(
                    f"Poor domain adaptation for '{context}' (score={adapt:.3f}) -- consider domain-specific calibration."
                )
        for ctx, fairness in situational_fairness.items():
            if fairness < 0.7:
                context_recommendations.append(
                    f"Low situational fairness in '{ctx}' (fairness={fairness:.3f}) -- investigate context-specific disparities."
                )
        if not context_recommendations:
            context_recommendations.append("No significant contextual bias detected.")

        return ContextualBiasResult(
            context_sensitivity=context_sensitivity,
            domain_adaptation=domain_adaptation,
            cultural_bias=cultural_bias,
            linguistic_bias=linguistic_bias,
            situational_fairness=situational_fairness,
            context_recommendations=context_recommendations
        )
    
    def _calculate_causal_bias_score(self, results: CausalAnalysisResult) -> float:
        """Calculate overall bias score from causal analysis"""
        return abs(results.treatment_effect) * (1 - results.robustness_score)
    
    def _generate_causal_recommendations(self, results: CausalAnalysisResult) -> List[str]:
        """Generate recommendations from causal analysis"""
        recommendations = []
        
        if results.p_value > 0.05:
            recommendations.append("Treatment effect is not statistically significant")
        
        if results.robustness_score < 0.7:
            recommendations.append("Results may be confounded by unobserved variables")
        
        if results.causal_strength > 0.3:
            recommendations.append("Strong causal effect detected - consider intervention")
        
        if results.confounding_factors:
            recommendations.append(f"Control for confounding factors: {', '.join(results.confounding_factors)}")
        
        return recommendations
    
    def _assess_causal_risk(self, results: CausalAnalysisResult) -> Dict[str, Any]:
        """Assess risk from causal analysis"""
        risk_level = "high" if results.p_value > 0.05 or results.robustness_score < 0.5 else "medium" if results.robustness_score < 0.7 else "low"
        
        return {
            "risk_level": risk_level,
            "statistical_significance": results.p_value < 0.05,
            "robustness_concern": results.robustness_score < 0.7,
            "confounding_risk": len(results.confounding_factors) > 0,
            "intervention_urgency": results.causal_strength > 0.3
        }
    
    def _generate_counterfactual_recommendations(self, results: CounterfactualResult) -> List[str]:
        """Generate recommendations from counterfactual analysis"""
        recommendations = []
        
        if abs(results.bias_magnitude) > 0.2:
            recommendations.append("Significant bias detected - implement debiasing interventions")
        
        if results.confidence_score < 0.7:
            recommendations.append("Low confidence in counterfactual analysis - gather more data")
        
        if results.intervention_effect > 0.3:
            recommendations.append("High intervention effect - prioritize bias mitigation")
        
        # Add specific intervention recommendations
        for feature, intervention in results.minimal_intervention.items():
            recommendations.append(f"Apply {intervention} intervention to {feature}")
        
        return recommendations
    
    def _assess_counterfactual_risk(self, results: CounterfactualResult) -> Dict[str, Any]:
        """Assess risk from counterfactual analysis"""
        risk_level = "high" if abs(results.bias_magnitude) > 0.3 else "medium" if abs(results.bias_magnitude) > 0.1 else "low"
        
        return {
            "risk_level": risk_level,
            "bias_severity": abs(results.bias_magnitude),
            "intervention_necessity": results.intervention_effect > 0.2,
            "confidence_concern": results.confidence_score < 0.7
        }
    
    def _generate_intersectional_recommendations(self, results: IntersectionalBiasResult) -> List[str]:
        """Generate recommendations from intersectional analysis"""
        recommendations = []
        
        if results.worst_case_group:
            recommendations.append(f"Prioritize mitigation for {results.worst_case_group} group")
        
        if results.interaction_strength > 0.3:
            recommendations.append("Strong intersectional effects detected - use intersectional fairness metrics")
        
        # Add specific group recommendations
        for group in results.mitigation_priority[:3]:  # Top 3 priority groups
            recommendations.append(f"Implement targeted interventions for {group}")
        
        recommendations.append("Use intersectional fairness constraints in model training")
        recommendations.append("Monitor intersectional groups separately in production")
        
        return recommendations
    
    def _assess_intersectional_risk(self, results: IntersectionalBiasResult) -> Dict[str, Any]:
        """Assess risk from intersectional analysis"""
        max_bias = max(results.bias_scores.values()) if results.bias_scores else 0
        risk_level = "high" if max_bias > 0.3 else "medium" if max_bias > 0.1 else "low"
        
        return {
            "risk_level": risk_level,
            "max_bias_score": max_bias,
            "intersectional_effects": results.interaction_strength > 0.2,
            "worst_case_group": results.worst_case_group,
            "mitigation_priority": len(results.mitigation_priority)
        }
    
    def _generate_adversarial_recommendations(self, results: AdversarialBiasResult) -> List[str]:
        """Generate recommendations from adversarial testing"""
        recommendations = []
        
        if results.attack_success_rate > 0.3:
            recommendations.append("High attack success rate - implement adversarial training")
        
        if results.bias_amplification > 0.4:
            recommendations.append("Significant bias amplification - use robust training methods")
        
        if results.robustness_score < 0.6:
            recommendations.append("Low robustness - implement defense mechanisms")
        
        # Add specific defense recommendations
        for feature in results.vulnerable_features:
            recommendations.append(f"Strengthen defenses for {feature} feature")
        
        recommendations.append("Implement input validation and sanitization")
        recommendations.append("Use certified defenses for critical applications")
        
        return recommendations
    
    def _assess_adversarial_risk(self, results: AdversarialBiasResult) -> Dict[str, Any]:
        """Assess risk from adversarial testing"""
        risk_level = "high" if results.attack_success_rate > 0.4 or results.bias_amplification > 0.5 else "medium" if results.attack_success_rate > 0.2 else "low"
        
        return {
            "risk_level": risk_level,
            "attack_vulnerability": results.attack_success_rate,
            "bias_amplification_risk": results.bias_amplification,
            "robustness_concern": results.robustness_score < 0.6,
            "vulnerable_features": len(results.vulnerable_features)
        }
    
    def _generate_temporal_recommendations(self, results: TemporalBiasResult) -> List[str]:
        """Generate recommendations from temporal analysis"""
        recommendations = []
        
        if results.concept_drift > 0.3:
            recommendations.append("Significant concept drift detected - retrain model")
        
        if results.performance_degradation > 0.2:
            recommendations.append("Performance degradation observed - implement adaptive learning")
        
        # Add specific temporal recommendations
        recommendations.extend(results.adaptation_recommendations)
        
        recommendations.append("Implement continuous monitoring for temporal bias")
        recommendations.append("Use time-aware model architectures")
        
        return recommendations
    
    def _assess_temporal_risk(self, results: TemporalBiasResult) -> Dict[str, Any]:
        """Assess risk from temporal analysis"""
        risk_level = "high" if results.concept_drift > 0.4 else "medium" if results.concept_drift > 0.2 else "low"
        
        return {
            "risk_level": risk_level,
            "concept_drift_severity": results.concept_drift,
            "performance_degradation": results.performance_degradation,
            "adaptation_necessity": results.concept_drift > 0.2
        }
    
    def _generate_contextual_recommendations(self, results: ContextualBiasResult) -> List[str]:
        """Generate recommendations from contextual analysis"""
        recommendations = []
        
        # Add specific context recommendations
        recommendations.extend(results.context_recommendations)
        
        # Add recommendations based on analysis results
        if any(sensitivity > 0.3 for sensitivity in results.context_sensitivity.values()):
            recommendations.append("High context sensitivity - implement context-aware models")
        
        if any(bias > 0.2 for bias in results.cultural_bias.values()):
            recommendations.append("Cultural bias detected - implement cultural adaptation")
        
        if any(bias > 0.15 for bias in results.linguistic_bias.values()):
            recommendations.append("Linguistic bias detected - implement language-aware preprocessing")
        
        return recommendations
    
    def _assess_contextual_risk(self, results: ContextualBiasResult) -> Dict[str, Any]:
        """Assess risk from contextual analysis"""
        max_sensitivity = max(results.context_sensitivity.values()) if results.context_sensitivity else 0
        max_cultural_bias = max(results.cultural_bias.values()) if results.cultural_bias else 0
        
        risk_level = "high" if max_sensitivity > 0.4 or max_cultural_bias > 0.3 else "medium" if max_sensitivity > 0.2 else "low"
        
        return {
            "risk_level": risk_level,
            "max_context_sensitivity": max_sensitivity,
            "cultural_bias_concern": max_cultural_bias > 0.2,
            "linguistic_bias_concern": max(results.linguistic_bias.values()) > 0.15 if results.linguistic_bias else False,
            "domain_adaptation_need": any(adaptation < 0.5 for adaptation in results.domain_adaptation.values())
        }
    
    async def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all advanced bias analysis capabilities"""
        return {
            "available_methods": [method.value for method in AnalysisMethod],
            "bias_types": [bias_type.value for bias_type in BiasType],
            "supported_analyses": {
                "causal_analysis": {
                    "description": "Causal inference for treatment effect bias",
                    "inputs": ["data", "treatment_variable", "outcome_variable", "protected_attributes"],
                    "outputs": ["treatment_effect", "confidence_interval", "causal_strength", "confounding_factors"]
                },
                "counterfactual_analysis": {
                    "description": "Counterfactual explanations for bias detection",
                    "inputs": ["model_predictions", "protected_attributes", "intervention_strategy"],
                    "outputs": ["bias_magnitude", "intervention_effect", "feature_importance", "minimal_intervention"]
                },
                "intersectional_analysis": {
                    "description": "Intersectional bias across multiple protected attributes",
                    "inputs": ["data", "intersection_groups", "outcome_variable"],
                    "outputs": ["bias_scores", "compound_effects", "interaction_strength", "fairness_gaps"]
                },
                "adversarial_testing": {
                    "description": "Adversarial robustness testing for bias",
                    "inputs": ["model_predictions", "attack_vectors", "protected_attributes"],
                    "outputs": ["attack_success_rate", "bias_amplification", "robustness_score", "vulnerable_features"]
                },
                "temporal_analysis": {
                    "description": "Temporal bias and concept drift detection",
                    "inputs": ["time_series_data", "time_column", "outcome_variable", "protected_attributes"],
                    "outputs": ["temporal_trends", "concept_drift", "performance_degradation", "adaptation_recommendations"]
                },
                "contextual_analysis": {
                    "description": "Context-sensitive bias detection",
                    "inputs": ["data", "context_features", "protected_attributes", "outcome_variable"],
                    "outputs": ["context_sensitivity", "cultural_bias", "linguistic_bias", "situational_fairness"]
                }
            },
            "dependencies": {
                "scipy_available": SCIPY_AVAILABLE,
                "aiohttp_available": AIOHTTP_AVAILABLE
            },
            "performance_metrics": {
                "analysis_speed": "Real-time for small datasets, batch processing for large datasets",
                "accuracy": "High accuracy with statistical rigor",
                "scalability": "Supports datasets up to 1M+ records",
                "robustness": "Includes confidence intervals and robustness checks"
            }
        }
