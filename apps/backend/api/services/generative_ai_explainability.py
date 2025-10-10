"""
Explainability and Bias Detection for Generative AI Models
Implements modern explainability techniques for LLMs, audio, image, and video generation
"""

import json
import numpy as np
import torch
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging
import uuid
import requests
from pathlib import Path
import base64
import io
from PIL import Image
import librosa
import cv2

logger = logging.getLogger(__name__)

class ModelType(Enum):
    LLM = "llm"
    AUDIO_GENERATION = "audio_generation"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    MULTIMODAL = "multimodal"

class ExplainabilityMethod(Enum):
    ATTENTION_VISUALIZATION = "attention_visualization"
    ACTIVATION_PATCHING = "activation_patching"
    CIRCUIT_DISCOVERY = "circuit_discovery"
    CONCEPT_BOTTLENECK = "concept_bottleneck"
    PROMPT_ABLATION = "prompt_ablation"
    GRADIENT_BASED = "gradient_based"
    COUNTERFACTUAL = "counterfactual"
    UNCERTAINTY_QUANTIFICATION = "uncertainty_quantification"

class BiasCategory(Enum):
    DEMOGRAPHIC = "demographic"
    OCCUPATIONAL = "occupational"
    CULTURAL = "cultural"
    GENDER = "gender"
    RACIAL = "racial"
    AGE = "age"
    RELIGIOUS = "religious"
    POLITICAL = "political"
    SOCIOECONOMIC = "socioeconomic"

@dataclass
class ExplainabilityResult:
    """Result of explainability analysis"""
    id: str
    model_id: str
    model_type: ModelType
    method: ExplainabilityMethod
    input_data: Dict[str, Any]
    explanation: Dict[str, Any]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class BiasDetectionResult:
    """Result of bias detection analysis"""
    id: str
    model_id: str
    model_type: ModelType
    bias_category: BiasCategory
    bias_score: float
    bias_indicators: List[str]
    affected_groups: List[str]
    evidence: Dict[str, Any]
    recommendations: List[str]
    severity: str
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class GenerativeAIModel:
    """Represents a generative AI model"""
    id: str
    name: str
    model_type: ModelType
    version: str
    description: str
    capabilities: List[str]
    input_format: str
    output_format: str
    metadata: Dict[str, Any]
    created_at: datetime

class GenerativeAIExplainability:
    """Main explainability and bias detection service for generative AI"""
    
    def __init__(self):
        self.models: Dict[str, GenerativeAIModel] = {}
        self.explainability_results: Dict[str, ExplainabilityResult] = {}
        self.bias_results: Dict[str, BiasDetectionResult] = {}
        
        # Initialize modern tools integration
        self.comet_llm_available = self._check_comet_llm()
        self.deepeval_available = self._check_deepeval()
        self.transformer_lens_available = self._check_transformer_lens()
        
        # Initialize bias detection tools
        self.bias_detection_tools = {
            "weat": self._detect_weat_bias,
            "sentibert": self._detect_sentibert_bias,
            "stereoset": self._detect_stereoset_bias,
            "crowspairs": self._detect_crowspairs_bias,
            "bbq": self._detect_bbq_bias
        }
    
    def _check_comet_llm(self) -> bool:
        """Check if CometLLM is available"""
        try:
            import comet_llm
            return True
        except ImportError:
            logger.warning("CometLLM not available")
            return False
    
    def _check_deepeval(self) -> bool:
        """Check if DeepEval is available"""
        try:
            import deepeval
            return True
        except ImportError:
            logger.warning("DeepEval not available")
            return False
    
    def _check_transformer_lens(self) -> bool:
        """Check if TransformerLens is available"""
        try:
            import transformer_lens
            return True
        except ImportError:
            logger.warning("TransformerLens not available")
            return False
    
    def register_model(self, model_id: str, name: str, model_type: ModelType,
                      version: str, description: str, capabilities: List[str],
                      input_format: str, output_format: str,
                      metadata: Dict[str, Any] = None) -> GenerativeAIModel:
        """Register a generative AI model"""
        
        model = GenerativeAIModel(
            id=model_id,
            name=name,
            model_type=model_type,
            version=version,
            description=description,
            capabilities=capabilities,
            input_format=input_format,
            output_format=output_format,
            metadata=metadata or {},
            created_at=datetime.now()
        )
        
        self.models[model_id] = model
        logger.info(f"Registered model {model_id} of type {model_type.value}")
        
        return model
    
    async def analyze_llm_explainability(self, model_id: str, prompt: str,
                                       method: ExplainabilityMethod,
                                       parameters: Dict[str, Any] = None) -> ExplainabilityResult:
        """Analyze explainability for LLM models"""
        
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        if model.model_type != ModelType.LLM:
            raise ValueError(f"Model {model_id} is not an LLM")
        
        start_time = datetime.now()
        
        try:
            if method == ExplainabilityMethod.ATTENTION_VISUALIZATION:
                explanation = await self._analyze_attention_visualization(model, prompt, parameters)
            elif method == ExplainabilityMethod.ACTIVATION_PATCHING:
                explanation = await self._analyze_activation_patching(model, prompt, parameters)
            elif method == ExplainabilityMethod.CIRCUIT_DISCOVERY:
                explanation = await self._analyze_circuit_discovery(model, prompt, parameters)
            elif method == ExplainabilityMethod.PROMPT_ABLATION:
                explanation = await self._analyze_prompt_ablation(model, prompt, parameters)
            elif method == ExplainabilityMethod.GRADIENT_BASED:
                explanation = await self._analyze_gradient_based(model, prompt, parameters)
            elif method == ExplainabilityMethod.COUNTERFACTUAL:
                explanation = await self._analyze_counterfactual(model, prompt, parameters)
            else:
                raise ValueError(f"Unsupported explainability method: {method}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ExplainabilityResult(
                id=str(uuid.uuid4()),
                model_id=model_id,
                model_type=ModelType.LLM,
                method=method,
                input_data={"prompt": prompt, "parameters": parameters},
                explanation=explanation,
                confidence_score=explanation.get("confidence", 0.0),
                processing_time=processing_time,
                metadata={"model_version": model.version},
                created_at=datetime.now()
            )
            
            self.explainability_results[result.id] = result
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing LLM explainability: {e}")
            raise
    
    async def _analyze_attention_visualization(self, model: GenerativeAIModel, 
                                             prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze attention patterns in LLM"""
        
        # Mock attention visualization (in production, use actual model)
        tokens = prompt.split()
        attention_weights = np.random.rand(len(tokens), len(tokens))
        
        # Normalize attention weights
        attention_weights = attention_weights / attention_weights.sum(axis=1, keepdims=True)
        
        # Find most attended tokens
        max_attention_indices = np.argmax(attention_weights, axis=1)
        most_attended_tokens = [tokens[i] for i in max_attention_indices]
        
        return {
            "attention_weights": attention_weights.tolist(),
            "tokens": tokens,
            "most_attended_tokens": most_attended_tokens,
            "attention_entropy": float(np.mean([-np.sum(weights * np.log(weights + 1e-8)) 
                                              for weights in attention_weights])),
            "confidence": 0.85,
            "visualization_data": {
                "heatmap": attention_weights.tolist(),
                "token_positions": list(range(len(tokens)))
            }
        }
    
    async def _analyze_activation_patching(self, model: GenerativeAIModel, 
                                         prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze causal relationships through activation patching"""
        
        # Mock activation patching analysis
        layers_to_patch = parameters.get("layers", [0, 1, 2, 3, 4])
        patching_results = {}
        
        for layer in layers_to_patch:
            # Simulate patching effect
            original_output = np.random.rand(10)
            patched_output = original_output + np.random.normal(0, 0.1, 10)
            
            patching_results[f"layer_{layer}"] = {
                "original_activation": original_output.tolist(),
                "patched_activation": patched_output.tolist(),
                "effect_size": float(np.mean(np.abs(patched_output - original_output))),
                "causal_importance": float(np.random.rand())
            }
        
        # Find most important layers
        layer_importance = {layer: results["causal_importance"] 
                          for layer, results in patching_results.items()}
        most_important_layer = max(layer_importance, key=layer_importance.get)
        
        return {
            "patching_results": patching_results,
            "most_important_layer": most_important_layer,
            "causal_flow": layer_importance,
            "confidence": 0.78,
            "interpretation": f"Layer {most_important_layer} shows highest causal importance"
        }
    
    async def _analyze_circuit_discovery(self, model: GenerativeAIModel, 
                                       prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Discover neural circuits in LLM"""
        
        # Mock circuit discovery
        circuits = {
            "indirect_object_identification": {
                "components": ["layer_5_attention", "layer_6_mlp"],
                "function": "Identifies indirect objects in sentences",
                "confidence": 0.92,
                "examples": ["John gave Mary the book", "The teacher showed the students the problem"]
            },
            "gender_bias_circuit": {
                "components": ["layer_3_attention", "layer_4_mlp"],
                "function": "Associates gender with certain roles",
                "confidence": 0.67,
                "examples": ["The nurse was caring", "The engineer was technical"]
            },
            "sentiment_analysis": {
                "components": ["layer_7_attention", "layer_8_mlp"],
                "function": "Analyzes sentiment in text",
                "confidence": 0.89,
                "examples": ["This is great!", "I hate this"]
            }
        }
        
        return {
            "discovered_circuits": circuits,
            "circuit_count": len(circuits),
            "confidence": 0.82,
            "interpretation": "Found 3 distinct neural circuits with varying confidence levels"
        }
    
    async def _analyze_prompt_ablation(self, model: GenerativeAIModel, 
                                     prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prompt components through ablation"""
        
        # Split prompt into components
        prompt_components = prompt.split()
        ablation_results = {}
        
        for i, component in enumerate(prompt_components):
            # Create ablated prompt
            ablated_prompt = " ".join(prompt_components[:i] + prompt_components[i+1:])
            
            # Simulate output difference
            original_output_score = np.random.rand()
            ablated_output_score = original_output_score + np.random.normal(0, 0.2)
            
            ablation_results[f"component_{i}"] = {
                "component": component,
                "original_prompt": prompt,
                "ablated_prompt": ablated_prompt,
                "output_difference": float(ablated_output_score - original_output_score),
                "importance": float(abs(ablated_output_score - original_output_score))
            }
        
        # Rank components by importance
        component_importance = {comp: results["importance"] 
                              for comp, results in ablation_results.items()}
        most_important_component = max(component_importance, key=component_importance.get)
        
        return {
            "ablation_results": ablation_results,
            "most_important_component": most_important_component,
            "component_ranking": sorted(component_importance.items(), 
                                      key=lambda x: x[1], reverse=True),
            "confidence": 0.75,
            "interpretation": f"Component {most_important_component} has highest impact on output"
        }
    
    async def _analyze_gradient_based(self, model: GenerativeAIModel, 
                                    prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gradients for explainability"""
        
        # Mock gradient analysis
        tokens = prompt.split()
        gradients = np.random.rand(len(tokens))
        
        # Calculate gradient magnitudes
        gradient_magnitudes = np.abs(gradients)
        
        # Find most influential tokens
        token_influence = list(zip(tokens, gradient_magnitudes))
        token_influence.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "gradients": gradients.tolist(),
            "gradient_magnitudes": gradient_magnitudes.tolist(),
            "token_influence": token_influence,
            "most_influential_tokens": [token for token, _ in token_influence[:3]],
            "confidence": 0.88,
            "interpretation": "Gradient analysis shows token-level influence on model output"
        }
    
    async def _analyze_counterfactual(self, model: GenerativeAIModel, 
                                    prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate counterfactual explanations"""
        
        # Mock counterfactual generation
        counterfactuals = [
            {
                "original": prompt,
                "modified": prompt.replace("he", "she"),
                "change": "gender_pronoun",
                "effect": "Changes gender association in output"
            },
            {
                "original": prompt,
                "modified": prompt.replace("doctor", "nurse"),
                "change": "occupation",
                "effect": "Changes professional context"
            }
        ]
        
        return {
            "counterfactuals": counterfactuals,
            "counterfactual_count": len(counterfactuals),
            "confidence": 0.73,
            "interpretation": "Counterfactual analysis reveals sensitive input-output relationships"
        }
    
    async def detect_llm_bias(self, model_id: str, test_cases: List[Dict[str, Any]],
                            bias_categories: List[BiasCategory]) -> List[BiasDetectionResult]:
        """Detect bias in LLM models"""
        
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        if model.model_type != ModelType.LLM:
            raise ValueError(f"Model {model_id} is not an LLM")
        
        results = []
        
        for category in bias_categories:
            result = await self._detect_category_bias(model, test_cases, category)
            results.append(result)
        
        return results
    
    async def _detect_category_bias(self, model: GenerativeAIModel, 
                                  test_cases: List[Dict[str, Any]], 
                                  category: BiasCategory) -> BiasDetectionResult:
        """Detect bias in a specific category"""
        
        if category == BiasCategory.DEMOGRAPHIC:
            return await self._detect_demographic_bias(model, test_cases)
        elif category == BiasCategory.OCCUPATIONAL:
            return await self._detect_occupational_bias(model, test_cases)
        elif category == BiasCategory.CULTURAL:
            return await self._detect_cultural_bias(model, test_cases)
        elif category == BiasCategory.GENDER:
            return await self._detect_gender_bias(model, test_cases)
        elif category == BiasCategory.RACIAL:
            return await self._detect_racial_bias(model, test_cases)
        else:
            return await self._detect_general_bias(model, test_cases, category)
    
    async def _detect_demographic_bias(self, model: GenerativeAIModel, 
                                     test_cases: List[Dict[str, Any]]) -> BiasDetectionResult:
        """Detect demographic bias"""
        
        # Mock demographic bias detection
        demographic_groups = ["white", "black", "hispanic", "asian", "native_american"]
        bias_scores = {}
        
        for group in demographic_groups:
            # Simulate bias score calculation
            bias_scores[group] = np.random.uniform(0.1, 0.9)
        
        max_bias = max(bias_scores.values())
        min_bias = min(bias_scores.values())
        bias_disparity = max_bias - min_bias
        
        # Determine severity
        if bias_disparity > 0.5:
            severity = "high"
        elif bias_disparity > 0.3:
            severity = "medium"
        else:
            severity = "low"
        
        return BiasDetectionResult(
            id=str(uuid.uuid4()),
            model_id=model.id,
            model_type=ModelType.LLM,
            bias_category=BiasCategory.DEMOGRAPHIC,
            bias_score=bias_disparity,
            bias_indicators=["demographic_parity", "equalized_odds"],
            affected_groups=[group for group, score in bias_scores.items() 
                           if score > max_bias * 0.8],
            evidence={
                "bias_scores": bias_scores,
                "disparity_analysis": {
                    "max_bias": max_bias,
                    "min_bias": min_bias,
                    "disparity": bias_disparity
                }
            },
            recommendations=[
                "Implement demographic parity constraints",
                "Use balanced training data",
                "Apply bias mitigation techniques"
            ],
            severity=severity,
            metadata={"detection_method": "demographic_parity_analysis"},
            created_at=datetime.now()
        )
    
    async def _detect_occupational_bias(self, model: GenerativeAIModel, 
                                      test_cases: List[Dict[str, Any]]) -> BiasDetectionResult:
        """Detect occupational bias"""
        
        # Mock occupational bias detection
        occupations = ["doctor", "nurse", "engineer", "teacher", "lawyer", "artist"]
        gender_associations = {}
        
        for occupation in occupations:
            # Simulate gender association scores
            male_association = np.random.uniform(0.2, 0.8)
            female_association = 1.0 - male_association
            gender_associations[occupation] = {
                "male": male_association,
                "female": female_association
            }
        
        # Calculate bias score
        gender_biases = [abs(assoc["male"] - assoc["female"]) 
                        for assoc in gender_associations.values()]
        avg_bias = np.mean(gender_biases)
        
        return BiasDetectionResult(
            id=str(uuid.uuid4()),
            model_id=model.id,
            model_type=ModelType.LLM,
            bias_category=BiasCategory.OCCUPATIONAL,
            bias_score=avg_bias,
            bias_indicators=["occupational_stereotypes", "gender_associations"],
            affected_groups=["occupations_with_strong_gender_bias"],
            evidence={
                "gender_associations": gender_associations,
                "bias_analysis": {
                    "average_bias": avg_bias,
                    "max_bias": max(gender_biases),
                    "min_bias": min(gender_biases)
                }
            },
            recommendations=[
                "Use gender-neutral occupational descriptions",
                "Implement stereotype debiasing",
                "Train on diverse occupational data"
            ],
            severity="medium" if avg_bias > 0.3 else "low",
            metadata={"detection_method": "occupational_stereotype_analysis"},
            created_at=datetime.now()
        )
    
    async def _detect_cultural_bias(self, model: GenerativeAIModel, 
                                  test_cases: List[Dict[str, Any]]) -> BiasDetectionResult:
        """Detect cultural bias"""
        
        # Mock cultural bias detection
        cultures = ["western", "eastern", "african", "latin_american", "middle_eastern"]
        cultural_representations = {}
        
        for culture in cultures:
            # Simulate representation score
            cultural_representations[culture] = np.random.uniform(0.1, 0.9)
        
        # Calculate representation disparity
        max_representation = max(cultural_representations.values())
        min_representation = min(cultural_representations.values())
        disparity = max_representation - min_representation
        
        return BiasDetectionResult(
            id=str(uuid.uuid4()),
            model_id=model.id,
            model_type=ModelType.LLM,
            bias_category=BiasCategory.CULTURAL,
            bias_score=disparity,
            bias_indicators=["cultural_representation", "cultural_stereotypes"],
            affected_groups=[culture for culture, score in cultural_representations.items() 
                           if score < min_representation * 1.5],
            evidence={
                "cultural_representations": cultural_representations,
                "disparity_analysis": {
                    "max_representation": max_representation,
                    "min_representation": min_representation,
                    "disparity": disparity
                }
            },
            recommendations=[
                "Include diverse cultural perspectives in training",
                "Implement cultural sensitivity checks",
                "Use culturally balanced datasets"
            ],
            severity="high" if disparity > 0.6 else "medium" if disparity > 0.3 else "low",
            metadata={"detection_method": "cultural_representation_analysis"},
            created_at=datetime.now()
        )
    
    async def _detect_gender_bias(self, model: GenerativeAIModel, 
                                test_cases: List[Dict[str, Any]]) -> BiasDetectionResult:
        """Detect gender bias"""
        
        # Mock gender bias detection using WEAT-like approach
        male_words = ["he", "him", "his", "man", "men", "male", "masculine"]
        female_words = ["she", "her", "hers", "woman", "women", "female", "feminine"]
        
        # Simulate association scores
        male_associations = np.random.uniform(0.3, 0.8, len(male_words))
        female_associations = np.random.uniform(0.2, 0.7, len(female_words))
        
        # Calculate WEAT score
        weat_score = np.mean(male_associations) - np.mean(female_associations)
        
        return BiasDetectionResult(
            id=str(uuid.uuid4()),
            model_id=model.id,
            model_type=ModelType.LLM,
            bias_category=BiasCategory.GENDER,
            bias_score=abs(weat_score),
            bias_indicators=["weat_score", "gender_associations"],
            affected_groups=["gender_groups"],
            evidence={
                "weat_score": weat_score,
                "male_associations": male_associations.tolist(),
                "female_associations": female_associations.tolist(),
                "association_analysis": {
                    "male_mean": np.mean(male_associations),
                    "female_mean": np.mean(female_associations),
                    "difference": weat_score
                }
            },
            recommendations=[
                "Implement gender-neutral language",
                "Use balanced gender representations",
                "Apply gender debiasing techniques"
            ],
            severity="high" if abs(weat_score) > 0.5 else "medium" if abs(weat_score) > 0.3 else "low",
            metadata={"detection_method": "weat_analysis"},
            created_at=datetime.now()
        )
    
    async def _detect_racial_bias(self, model: GenerativeAIModel, 
                                test_cases: List[Dict[str, Any]]) -> BiasDetectionResult:
        """Detect racial bias"""
        
        # Mock racial bias detection
        racial_groups = ["white", "black", "asian", "hispanic", "native_american"]
        sentiment_scores = {}
        
        for group in racial_groups:
            # Simulate sentiment association scores
            sentiment_scores[group] = np.random.uniform(0.2, 0.8)
        
        # Calculate bias disparity
        max_sentiment = max(sentiment_scores.values())
        min_sentiment = min(sentiment_scores.values())
        disparity = max_sentiment - min_sentiment
        
        return BiasDetectionResult(
            id=str(uuid.uuid4()),
            model_id=model.id,
            model_type=ModelType.LLM,
            bias_category=BiasCategory.RACIAL,
            bias_score=disparity,
            bias_indicators=["racial_sentiment_bias", "racial_stereotypes"],
            affected_groups=[group for group, score in sentiment_scores.items() 
                           if score < min_sentiment * 1.3],
            evidence={
                "sentiment_scores": sentiment_scores,
                "disparity_analysis": {
                    "max_sentiment": max_sentiment,
                    "min_sentiment": min_sentiment,
                    "disparity": disparity
                }
            },
            recommendations=[
                "Implement racial bias mitigation",
                "Use racially balanced training data",
                "Apply fairness constraints"
            ],
            severity="high" if disparity > 0.5 else "medium" if disparity > 0.3 else "low",
            metadata={"detection_method": "racial_sentiment_analysis"},
            created_at=datetime.now()
        )
    
    async def _detect_general_bias(self, model: GenerativeAIModel, 
                                 test_cases: List[Dict[str, Any]], 
                                 category: BiasCategory) -> BiasDetectionResult:
        """Detect general bias for unspecified categories"""
        
        # Mock general bias detection
        bias_score = np.random.uniform(0.1, 0.8)
        
        return BiasDetectionResult(
            id=str(uuid.uuid4()),
            model_id=model.id,
            model_type=ModelType.LLM,
            bias_category=category,
            bias_score=bias_score,
            bias_indicators=["general_bias_indicators"],
            affected_groups=["affected_groups"],
            evidence={
                "bias_analysis": {
                    "score": bias_score,
                    "category": category.value
                }
            },
            recommendations=[
                "Implement bias mitigation techniques",
                "Use diverse training data",
                "Apply fairness constraints"
            ],
            severity="high" if bias_score > 0.6 else "medium" if bias_score > 0.3 else "low",
            metadata={"detection_method": "general_bias_analysis"},
            created_at=datetime.now()
        )
    
    # Bias detection tool implementations
    async def _detect_weat_bias(self, model: GenerativeAIModel, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bias using WEAT (Word Embedding Association Test)"""
        # Mock WEAT implementation
        return {
            "weat_score": np.random.uniform(-1, 1),
            "p_value": np.random.uniform(0, 0.05),
            "effect_size": np.random.uniform(0, 1),
            "interpretation": "WEAT analysis shows potential bias"
        }
    
    async def _detect_sentibert_bias(self, model: GenerativeAIModel, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bias using SentiBERT"""
        # Mock SentiBERT implementation
        return {
            "sentiment_bias_score": np.random.uniform(0, 1),
            "bias_direction": np.random.choice(["positive", "negative"]),
            "confidence": np.random.uniform(0.7, 0.95)
        }
    
    async def _detect_stereoset_bias(self, model: GenerativeAIModel, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bias using StereoSet"""
        # Mock StereoSet implementation
        return {
            "stereotype_score": np.random.uniform(0, 1),
            "anti_stereotype_score": np.random.uniform(0, 1),
            "neutral_score": np.random.uniform(0, 1),
            "bias_score": np.random.uniform(0, 1)
        }
    
    async def _detect_crowspairs_bias(self, model: GenerativeAIModel, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bias using CrowS-Pairs"""
        # Mock CrowS-Pairs implementation
        return {
            "bias_score": np.random.uniform(0, 1),
            "stereotype_accuracy": np.random.uniform(0.5, 0.9),
            "anti_stereotype_accuracy": np.random.uniform(0.3, 0.8)
        }
    
    async def _detect_bbq_bias(self, model: GenerativeAIModel, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bias using BBQ (Bias Benchmark for QA)"""
        # Mock BBQ implementation
        return {
            "bias_score": np.random.uniform(0, 1),
            "ambiguous_accuracy": np.random.uniform(0.4, 0.8),
            "disambiguated_accuracy": np.random.uniform(0.6, 0.9)
        }
    
    def get_explainability_summary(self, model_id: str) -> Dict[str, Any]:
        """Get explainability summary for a model"""
        model_results = [result for result in self.explainability_results.values() 
                        if result.model_id == model_id]
        
        if not model_results:
            return {"message": "No explainability results found for this model"}
        
        # Group by method
        method_results = {}
        for result in model_results:
            method = result.method.value
            if method not in method_results:
                method_results[method] = []
            method_results[method].append(result)
        
        # Calculate statistics
        total_analyses = len(model_results)
        avg_confidence = np.mean([result.confidence_score for result in model_results])
        avg_processing_time = np.mean([result.processing_time for result in model_results])
        
        return {
            "model_id": model_id,
            "total_analyses": total_analyses,
            "average_confidence": avg_confidence,
            "average_processing_time": avg_processing_time,
            "methods_used": list(method_results.keys()),
            "method_results": {
                method: {
                    "count": len(results),
                    "avg_confidence": np.mean([r.confidence_score for r in results]),
                    "latest_analysis": max(results, key=lambda x: x.created_at).created_at.isoformat()
                }
                for method, results in method_results.items()
            }
        }
    
    def get_bias_summary(self, model_id: str) -> Dict[str, Any]:
        """Get bias detection summary for a model"""
        model_results = [result for result in self.bias_results.values() 
                        if result.model_id == model_id]
        
        if not model_results:
            return {"message": "No bias detection results found for this model"}
        
        # Group by category
        category_results = {}
        for result in model_results:
            category = result.bias_category.value
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(result)
        
        # Calculate statistics
        total_detections = len(model_results)
        avg_bias_score = np.mean([result.bias_score for result in model_results])
        high_severity_count = len([r for r in model_results if r.severity == "high"])
        medium_severity_count = len([r for r in model_results if r.severity == "medium"])
        low_severity_count = len([r for r in model_results if r.severity == "low"])
        
        return {
            "model_id": model_id,
            "total_detections": total_detections,
            "average_bias_score": avg_bias_score,
            "severity_distribution": {
                "high": high_severity_count,
                "medium": medium_severity_count,
                "low": low_severity_count
            },
            "categories_detected": list(category_results.keys()),
            "category_results": {
                category: {
                    "count": len(results),
                    "avg_bias_score": np.mean([r.bias_score for r in results]),
                    "severity_distribution": {
                        "high": len([r for r in results if r.severity == "high"]),
                        "medium": len([r for r in results if r.severity == "medium"]),
                        "low": len([r for r in results if r.severity == "low"])
                    }
                }
                for category, results in category_results.items()
            }
        }

