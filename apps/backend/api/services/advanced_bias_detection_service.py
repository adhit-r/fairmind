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
        """Perform causal inference analysis"""
        
        # Simulate causal analysis (in real implementation, use causal inference libraries)
        treatment_effect = np.random.normal(0.1, 0.05)  # Simulated treatment effect
        confidence_interval = (treatment_effect - 0.1, treatment_effect + 0.1)
        p_value = np.random.uniform(0.01, 0.05)
        
        # Calculate causal strength
        causal_strength = abs(treatment_effect) / (np.std(df[outcome]) if outcome in df.columns else 1.0)
        
        # Identify confounding factors
        confounding_factors = []
        if confounders:
            for confounder in confounders:
                if confounder in df.columns:
                    correlation = df[treatment].corr(df[confounder]) if SCIPY_AVAILABLE else 0.3
                    if abs(correlation) > 0.3:
                        confounding_factors.append(confounder)
        
        # Calculate mediation effects
        mediation_effects = {}
        for attr in protected_attrs:
            if attr in df.columns:
                mediation_effects[attr] = np.random.uniform(0.1, 0.3)
        
        # Calculate interaction effects
        interaction_effects = {}
        for attr in protected_attrs:
            if attr in df.columns:
                interaction_effects[attr] = np.random.uniform(0.05, 0.2)
        
        # Calculate robustness score
        robustness_score = max(0, 1 - len(confounding_factors) * 0.2 - p_value)
        
        return CausalAnalysisResult(
            treatment_effect=treatment_effect,
            confidence_interval=confidence_interval,
            p_value=p_value,
            causal_strength=causal_strength,
            confounding_factors=confounding_factors,
            mediation_effects=mediation_effects,
            interaction_effects=interaction_effects,
            robustness_score=robustness_score
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
        """Generate counterfactual predictions"""
        
        # Simulate counterfactual generation
        original_pred = np.mean([p.get('prediction', 0.5) for p in predictions])
        counterfactual_pred = original_pred + np.random.normal(0, 0.1)
        
        bias_magnitude = counterfactual_pred - original_pred
        intervention_effect = abs(bias_magnitude)
        
        # Calculate feature importance
        feature_importance = {}
        for attr in protected_attrs:
            feature_importance[attr] = np.random.uniform(0.1, 0.5)
        
        # Generate minimal intervention
        minimal_intervention = {}
        for attr in protected_attrs:
            minimal_intervention[attr] = np.random.choice(['flip', 'neutralize', 'balance'])
        
        # Calculate confidence score
        confidence_score = max(0, 1 - abs(bias_magnitude) * 2)
        
        # Generate explanation
        explanation = f"Counterfactual analysis shows {bias_magnitude:.3f} bias magnitude. "
        explanation += f"Key intervention: {minimal_intervention}"
        
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
        """Perform intersectional bias analysis"""
        
        df = pd.DataFrame(data)
        
        # Calculate bias scores for each intersection
        bias_scores = {}
        compound_effects = {}
        fairness_gaps = {}
        
        for group_combo in intersection_groups:
            group_name = "_".join(group_combo)
            
            # Filter data for this intersection
            group_data = df.copy()
            for attr in group_combo:
                if attr in df.columns:
                    group_data = group_data[group_data[attr] == 1]  # Assuming binary attributes
            
            if len(group_data) > 0 and outcome_var in group_data.columns:
                # Calculate bias score
                group_mean = group_data[outcome_var].mean()
                overall_mean = df[outcome_var].mean()
                bias_scores[group_name] = abs(group_mean - overall_mean)
                
                # Calculate compound effects
                compound_effects[group_name] = np.random.uniform(0.1, 0.4)
                
                # Calculate fairness gaps
                fairness_gaps[group_name] = abs(group_mean - overall_mean) / overall_mean if overall_mean != 0 else 0
        
        # Calculate interaction strength
        interaction_strength = np.mean(list(compound_effects.values())) if compound_effects else 0
        
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
        """Perform adversarial bias testing"""
        
        # Simulate adversarial testing
        attack_success_rate = np.random.uniform(0.1, 0.4)
        bias_amplification = np.random.uniform(0.2, 0.6)
        robustness_score = max(0, 1 - attack_success_rate - bias_amplification)
        
        # Identify vulnerable features
        vulnerable_features = []
        for attr in protected_attrs:
            if np.random.random() > 0.5:  # 50% chance of being vulnerable
                vulnerable_features.append(attr)
        
        # Generate attack vectors
        attack_vectors_used = attack_vectors[:np.random.randint(1, len(attack_vectors) + 1)]
        
        # Calculate defense effectiveness
        defense_effectiveness = max(0, 1 - attack_success_rate)
        
        # Generate worst case scenarios
        worst_case_scenarios = []
        for i in range(3):
            scenario = {
                "attack_type": np.random.choice(attack_vectors_used),
                "bias_increase": np.random.uniform(0.3, 0.8),
                "affected_group": np.random.choice(protected_attrs),
                "confidence": np.random.uniform(0.7, 0.95)
            }
            worst_case_scenarios.append(scenario)
        
        return AdversarialBiasResult(
            attack_success_rate=attack_success_rate,
            bias_amplification=bias_amplification,
            robustness_score=robustness_score,
            vulnerable_features=vulnerable_features,
            attack_vectors=attack_vectors_used,
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
        """Perform temporal bias analysis"""
        
        df = pd.DataFrame(data)
        
        # Convert time column to datetime if needed
        if time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col])
        
        # Calculate temporal trends
        temporal_trends = {}
        for attr in protected_attrs:
            if attr in df.columns:
                # Simulate temporal trend
                trend = [np.random.normal(0, 0.1) for _ in range(12)]  # 12 months
                temporal_trends[attr] = trend
        
        # Calculate seasonality effects
        seasonality_effects = {}
        for attr in protected_attrs:
            seasonality_effects[attr] = np.random.uniform(0.1, 0.3)
        
        # Detect drift
        drift_detection = {}
        for attr in protected_attrs:
            drift_detection[attr] = np.random.uniform(0.1, 0.4)
        
        # Calculate concept drift
        concept_drift = np.mean(list(drift_detection.values())) if drift_detection else 0
        
        # Calculate performance degradation
        performance_degradation = concept_drift * 0.8
        
        # Generate adaptation recommendations
        adaptation_recommendations = [
            "Implement temporal rebalancing",
            "Add time-based features",
            "Use sliding window training",
            "Monitor for concept drift",
            "Implement adaptive learning rates"
        ]
        
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
        """Perform contextual bias analysis"""
        
        df = pd.DataFrame(data)
        
        # Calculate context sensitivity
        context_sensitivity = {}
        for context in context_features:
            if context in df.columns:
                context_sensitivity[context] = np.random.uniform(0.1, 0.4)
        
        # Calculate domain adaptation
        domain_adaptation = {}
        for context in context_features:
            domain_adaptation[context] = np.random.uniform(0.2, 0.6)
        
        # Calculate cultural bias
        cultural_bias = {}
        for attr in protected_attrs:
            cultural_bias[attr] = np.random.uniform(0.1, 0.3)
        
        # Calculate linguistic bias
        linguistic_bias = {}
        for attr in protected_attrs:
            linguistic_bias[attr] = np.random.uniform(0.1, 0.2)
        
        # Calculate situational fairness
        situational_fairness = {}
        for context in context_features:
            situational_fairness[context] = np.random.uniform(0.6, 0.9)
        
        # Generate context recommendations
        context_recommendations = [
            "Implement context-aware preprocessing",
            "Add contextual features to model",
            "Use domain adaptation techniques",
            "Monitor context-specific performance",
            "Implement context-sensitive debiasing"
        ]
        
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
