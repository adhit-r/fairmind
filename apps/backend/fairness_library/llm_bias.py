"""
LLM Bias Detection Methods
Standardized methods for detecting bias in language models and embeddings.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class BiasType(Enum):
    REPRESENTATIONAL = "representational"
    ALLOCATIONAL = "allocational"
    CONTEXTUAL = "contextual"
    PRIVACY = "privacy"

@dataclass
class LLMBiasResult:
    bias_type: BiasType
    score: float
    confidence_interval: Tuple[float, float]
    is_biased: bool
    threshold: float
    details: Dict[str, Any]

def weat_score(
    embeddings: Dict[str, np.ndarray],
    target_words: List[str],
    attribute_words_a: List[str],
    attribute_words_b: List[str],
    threshold: float = 0.1
) -> LLMBiasResult:
    """
    Compute WEAT (Word Embedding Association Test) score.
    
    Args:
        embeddings: Dict mapping words to embedding vectors
        target_words: List of target concept words
        attribute_words_a: List of first attribute words
        attribute_words_b: List of second attribute words
        threshold: Bias threshold
    
    Returns:
        LLMBiasResult with WEAT score and analysis
    """
    try:
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        def association(word, attribute_set):
            similarities = []
            for attr in attribute_set:
                if word in embeddings and attr in embeddings:
                    sim = cosine_similarity(embeddings[word], embeddings[attr])
                    similarities.append(sim)
            return np.mean(similarities) if similarities else 0
        
        # Compute associations
        associations_a = []
        associations_b = []
        
        for target in target_words:
            if target in embeddings:
                assoc_a = association(target, attribute_words_a)
                assoc_b = association(target, attribute_words_b)
                associations_a.append(assoc_a)
                associations_b.append(assoc_b)
        
        if not associations_a or not associations_b:
            raise ValueError("No valid associations found")
        
        # Compute WEAT score
        score = np.mean(associations_a) - np.mean(associations_b)
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_weat_ci(
            embeddings, target_words, attribute_words_a, attribute_words_b
        )
        
        return LLMBiasResult(
            bias_type=BiasType.REPRESENTATIONAL,
            score=score,
            confidence_interval=(ci_lower, ci_upper),
            is_biased=abs(score) > threshold,
            threshold=threshold,
            details={
                "target_words": target_words,
                "attribute_a": attribute_words_a,
                "attribute_b": attribute_words_b,
                "associations_a": associations_a,
                "associations_b": associations_b,
                "interpretation": f"WEAT score: {score:.3f} (higher = more biased)",
                "recommendation": "Consider debiasing embeddings" if abs(score) > threshold else "No significant bias detected"
            }
        )
        
    except Exception as e:
        logger.error(f"Error computing WEAT score: {e}")
        raise

def seat_score(
    embeddings: Dict[str, np.ndarray],
    sentence_templates: List[str],
    target_words: List[str],
    attribute_words_a: List[str],
    attribute_words_b: List[str],
    threshold: float = 0.1
) -> LLMBiasResult:
    """
    Compute SEAT (Sentence Embedding Association Test) score.
    
    Args:
        embeddings: Dict mapping sentences to embedding vectors
        sentence_templates: List of sentence templates
        target_words: List of target concept words
        attribute_words_a: List of first attribute words
        attribute_words_b: List of second attribute words
        threshold: Bias threshold
    
    Returns:
        LLMBiasResult with SEAT score and analysis
    """
    try:
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        def sentence_association(sentence_emb, attribute_set):
            similarities = []
            for attr in attribute_set:
                if attr in embeddings:
                    sim = cosine_similarity(sentence_emb, embeddings[attr])
                    similarities.append(sim)
            return np.mean(similarities) if similarities else 0
        
        # Generate sentences and compute associations
        associations_a = []
        associations_b = []
        
        for template in sentence_templates:
            for target in target_words:
                sentence = template.format(target=target)
                if sentence in embeddings:
                    sentence_emb = embeddings[sentence]
                    assoc_a = sentence_association(sentence_emb, attribute_words_a)
                    assoc_b = sentence_association(sentence_emb, attribute_words_b)
                    associations_a.append(assoc_a)
                    associations_b.append(assoc_b)
        
        if not associations_a or not associations_b:
            raise ValueError("No valid sentence associations found")
        
        # Compute SEAT score
        score = np.mean(associations_a) - np.mean(associations_b)
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_seat_ci(
            embeddings, sentence_templates, target_words, attribute_words_a, attribute_words_b
        )
        
        return LLMBiasResult(
            bias_type=BiasType.REPRESENTATIONAL,
            score=score,
            confidence_interval=(ci_lower, ci_upper),
            is_biased=abs(score) > threshold,
            threshold=threshold,
            details={
                "sentence_templates": sentence_templates,
                "target_words": target_words,
                "attribute_a": attribute_words_a,
                "attribute_b": attribute_words_b,
                "associations_a": associations_a,
                "associations_b": associations_b,
                "interpretation": f"SEAT score: {score:.3f} (higher = more biased)",
                "recommendation": "Consider debiasing sentence embeddings" if abs(score) > threshold else "No significant bias detected"
            }
        )
        
    except Exception as e:
        logger.error(f"Error computing SEAT score: {e}")
        raise

def minimal_pairs_test(
    model_outputs: List[Dict[str, Any]],
    templates: List[Dict[str, Any]],
    threshold: float = 0.1
) -> LLMBiasResult:
    """
    Perform minimal pairs testing for behavioral bias detection.
    
    Args:
        model_outputs: List of model outputs with minimal pairs
        templates: List of test templates
        threshold: Bias threshold
    
    Returns:
        LLMBiasResult with minimal pairs analysis
    """
    try:
        toxicity_gaps = []
        sentiment_gaps = []
        length_gaps = []
        
        for output in model_outputs:
            if "minimal_pair" in output:
                pair = output["minimal_pair"]
                
                # Compute gaps
                toxicity_gap = abs(pair.get("toxicity_a", 0) - pair.get("toxicity_b", 0))
                sentiment_gap = abs(pair.get("sentiment_a", 0) - pair.get("sentiment_b", 0))
                length_gap = abs(len(pair.get("output_a", "")) - len(pair.get("output_b", "")))
                
                toxicity_gaps.append(toxicity_gap)
                sentiment_gaps.append(sentiment_gap)
                length_gaps.append(length_gap)
        
        # Compute overall bias score
        if toxicity_gaps:
            overall_score = np.mean(toxicity_gaps)
        else:
            overall_score = 0
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_minimal_pairs_ci(model_outputs)
        
        return LLMBiasResult(
            bias_type=BiasType.CONTEXTUAL,
            score=overall_score,
            confidence_interval=(ci_lower, ci_upper),
            is_biased=overall_score > threshold,
            threshold=threshold,
            details={
                "toxicity_gaps": toxicity_gaps,
                "sentiment_gaps": sentiment_gaps,
                "length_gaps": length_gaps,
                "num_pairs": len(toxicity_gaps),
                "interpretation": f"Average toxicity gap: {overall_score:.3f}",
                "recommendation": "Implement output filtering" if overall_score > threshold else "No significant behavioral bias detected"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in minimal pairs test: {e}")
        raise

def behavioral_bias_detection(
    model_outputs: List[Dict[str, Any]],
    protected_attributes: List[str],
    threshold: float = 0.1
) -> LLMBiasResult:
    """
    Detect behavioral bias in model outputs.
    
    Args:
        model_outputs: List of model outputs with metadata
        protected_attributes: List of protected attributes to check
        threshold: Bias threshold
    
    Returns:
        LLMBiasResult with behavioral bias analysis
    """
    try:
        # Group outputs by protected attributes
        grouped_outputs = {}
        
        for output in model_outputs:
            if "protected_attributes" in output:
                for attr in protected_attributes:
                    if attr in output["protected_attributes"]:
                        value = output["protected_attributes"][attr]
                        if attr not in grouped_outputs:
                            grouped_outputs[attr] = {}
                        if value not in grouped_outputs[attr]:
                            grouped_outputs[attr][value] = []
                        grouped_outputs[attr][value].append(output)
        
        # Compute behavioral disparities
        disparities = {}
        for attr, groups in grouped_outputs.items():
            if len(groups) >= 2:
                group_scores = {}
                for group, outputs in groups.items():
                    # Compute average behavioral score for each group
                    scores = []
                    for output in outputs:
                        score = _compute_behavioral_score(output)
                        scores.append(score)
                    group_scores[group] = np.mean(scores) if scores else 0
                
                # Compute disparity
                values = list(group_scores.values())
                disparity = max(values) - min(values)
                disparities[attr] = {
                    "disparity": disparity,
                    "group_scores": group_scores
                }
        
        # Overall bias score
        if disparities:
            overall_score = np.mean([d["disparity"] for d in disparities.values()])
        else:
            overall_score = 0
        
        # Bootstrap confidence interval
        ci_lower, ci_upper = _bootstrap_behavioral_ci(model_outputs, protected_attributes)
        
        return LLMBiasResult(
            bias_type=BiasType.ALLOCATIONAL,
            score=overall_score,
            confidence_interval=(ci_lower, ci_upper),
            is_biased=overall_score > threshold,
            threshold=threshold,
            details={
                "disparities": disparities,
                "protected_attributes": protected_attributes,
                "interpretation": f"Average behavioral disparity: {overall_score:.3f}",
                "recommendation": "Review training data balance" if overall_score > threshold else "No significant behavioral bias detected"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in behavioral bias detection: {e}")
        raise

def embedding_bias_analysis(
    embeddings: Dict[str, np.ndarray],
    bias_tests: List[Dict[str, Any]],
    threshold: float = 0.1
) -> Dict[str, LLMBiasResult]:
    """
    Comprehensive embedding bias analysis.
    
    Args:
        embeddings: Dict mapping tokens/phrases to embeddings
        bias_tests: List of bias test configurations
        threshold: Bias threshold
    
    Returns:
        Dict of LLMBiasResult for each test
    """
    try:
        results = {}
        
        for test in bias_tests:
            test_name = test.get("name", "unnamed_test")
            test_type = test.get("type", "weat")
            
            if test_type == "weat":
                result = weat_score(
                    embeddings=embeddings,
                    target_words=test["target_words"],
                    attribute_words_a=test["attribute_a"],
                    attribute_words_b=test["attribute_b"],
                    threshold=threshold
                )
                results[test_name] = result
            
            elif test_type == "seat":
                result = seat_score(
                    embeddings=embeddings,
                    sentence_templates=test["sentence_templates"],
                    target_words=test["target_words"],
                    attribute_words_a=test["attribute_a"],
                    attribute_words_b=test["attribute_b"],
                    threshold=threshold
                )
                results[test_name] = result
        
        return results
        
    except Exception as e:
        logger.error(f"Error in embedding bias analysis: {e}")
        raise

# Helper functions

def _compute_behavioral_score(output: Dict[str, Any]) -> float:
    """Compute behavioral score from model output"""
    try:
        # Combine multiple behavioral indicators
        toxicity = output.get("toxicity", 0)
        sentiment = output.get("sentiment", 0)
        length = len(output.get("text", ""))
        
        # Normalize and combine
        normalized_length = min(length / 1000, 1.0)  # Normalize to 0-1
        behavioral_score = (toxicity + abs(sentiment) + normalized_length) / 3
        
        return behavioral_score
    except:
        return 0.0

def _bootstrap_weat_ci(embeddings, target_words, attribute_a, attribute_b, n_bootstrap=1000):
    """Bootstrap confidence interval for WEAT"""
    try:
        bootstrap_scores = []
        for _ in range(n_bootstrap):
            # Bootstrap sampling
            boot_targets = np.random.choice(target_words, size=len(target_words), replace=True)
            boot_attr_a = np.random.choice(attribute_a, size=len(attribute_a), replace=True)
            boot_attr_b = np.random.choice(attribute_b, size=len(attribute_b), replace=True)
            
            # Compute WEAT score with bootstrapped samples
            score = weat_score(embeddings, boot_targets, boot_attr_a, boot_attr_b).score
            bootstrap_scores.append(score)
        
        return np.percentile(bootstrap_scores, [2.5, 97.5])
    except Exception as e:
        logger.error(f"Error in WEAT bootstrap: {e}")
        return (0, 0)

def _bootstrap_seat_ci(embeddings, sentence_templates, target_words, attribute_a, attribute_b, n_bootstrap=1000):
    """Bootstrap confidence interval for SEAT"""
    try:
        bootstrap_scores = []
        for _ in range(n_bootstrap):
            # Bootstrap sampling
            boot_templates = np.random.choice(sentence_templates, size=len(sentence_templates), replace=True)
            boot_targets = np.random.choice(target_words, size=len(target_words), replace=True)
            boot_attr_a = np.random.choice(attribute_a, size=len(attribute_a), replace=True)
            boot_attr_b = np.random.choice(attribute_b, size=len(attribute_b), replace=True)
            
            # Compute SEAT score with bootstrapped samples
            score = seat_score(embeddings, boot_templates, boot_targets, boot_attr_a, boot_attr_b).score
            bootstrap_scores.append(score)
        
        return np.percentile(bootstrap_scores, [2.5, 97.5])
    except Exception as e:
        logger.error(f"Error in SEAT bootstrap: {e}")
        return (0, 0)

def _bootstrap_minimal_pairs_ci(model_outputs, n_bootstrap=1000):
    """Bootstrap confidence interval for minimal pairs"""
    try:
        bootstrap_scores = []
        for _ in range(n_bootstrap):
            # Bootstrap sampling
            boot_outputs = np.random.choice(model_outputs, size=len(model_outputs), replace=True)
            score = minimal_pairs_test(boot_outputs).score
            bootstrap_scores.append(score)
        
        return np.percentile(bootstrap_scores, [2.5, 97.5])
    except Exception as e:
        logger.error(f"Error in minimal pairs bootstrap: {e}")
        return (0, 0)

def _bootstrap_behavioral_ci(model_outputs, protected_attributes, n_bootstrap=1000):
    """Bootstrap confidence interval for behavioral bias"""
    try:
        bootstrap_scores = []
        for _ in range(n_bootstrap):
            # Bootstrap sampling
            boot_outputs = np.random.choice(model_outputs, size=len(model_outputs), replace=True)
            score = behavioral_bias_detection(boot_outputs, protected_attributes).score
            bootstrap_scores.append(score)
        
        return np.percentile(bootstrap_scores, [2.5, 97.5])
    except Exception as e:
        logger.error(f"Error in behavioral bootstrap: {e}")
        return (0, 0)
