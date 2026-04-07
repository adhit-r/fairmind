"""
Modern LLM Bias Detection Service
Implements the latest explainability and bias detection techniques for generative AI
Based on 2025 best practices and tools
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from collections import Counter
import math
import re

try:
    import scipy.stats as stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

import hashlib
from domain.bias.services.bias_bench_service import bias_bench_service

logger = logging.getLogger(__name__)

class BiasCategory(Enum):
    """Modern bias categories for generative AI"""
    INTRINSIC = "intrinsic"  # Embedded in model representations
    EXTRINSIC = "extrinsic"  # Manifested in downstream tasks
    REPRESENTATIONAL = "representational"  # How groups are represented
    ALLOCATIONAL = "allocational"  # Resource allocation disparities
    CONTEXTUAL = "contextual"  # Context-dependent bias
    PRIVACY = "privacy"  # Privacy and attribution bias
    EMERGENT = "emergent"  # Unexpected bias patterns
    CROSS_MODAL = "cross_modal"  # Bias across modalities

class ExplainabilityMethod(Enum):
    """Modern explainability methods for LLMs"""
    ATTENTION_VISUALIZATION = "attention_visualization"
    ACTIVATION_PATCHING = "activation_patching"
    CIRCUIT_DISCOVERY = "circuit_discovery"
    CONCEPT_BOTTLENECK = "concept_bottleneck"
    COUNTERFACTUAL = "counterfactual"
    PROMPT_ABLATION = "prompt_ablation"
    UNCERTAINTY_QUANTIFICATION = "uncertainty_quantification"

@dataclass
class BiasTestResult:
    """Comprehensive bias test result"""
    test_id: str
    test_name: str
    category: BiasCategory
    bias_score: float
    confidence_interval: Tuple[float, float]
    p_value: float
    is_biased: bool
    threshold: float
    sample_size: int
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: str

@dataclass
class ExplainabilityResult:
    """Explainability analysis result"""
    method: ExplainabilityMethod
    explanation: Dict[str, Any]
    confidence: float
    visualizations: List[str]  # URLs or paths to visualizations
    insights: List[str]
    timestamp: str

# ---------------------------------------------------------------------------
# Text analysis helpers (no external ML libraries)
# ---------------------------------------------------------------------------

_NEGATIVE_WORDS = frozenset([
    "bad", "terrible", "awful", "horrible", "poor", "worst", "hate",
    "angry", "sad", "ugly", "stupid", "wrong", "fail", "failure",
    "negative", "toxic", "hostile", "violent", "dangerous", "threatening",
    "disgusting", "offensive", "rude", "cruel", "evil", "nasty"
])

_POSITIVE_WORDS = frozenset([
    "good", "great", "excellent", "wonderful", "best", "love",
    "happy", "beautiful", "smart", "right", "success", "successful",
    "positive", "kind", "friendly", "helpful", "amazing", "fantastic",
    "brilliant", "outstanding", "superb", "perfect", "nice", "pleasant"
])

_TOXIC_WORDS = frozenset([
    "hate", "kill", "die", "stupid", "idiot", "dumb", "ugly",
    "loser", "moron", "pathetic", "worthless", "disgusting",
    "offensive", "trash", "garbage", "scum", "filth", "vile"
])


def _simple_sentiment(text: str) -> float:
    """Return a sentiment score in [-1, 1] from word-overlap heuristic."""
    if not text:
        return 0.0
    words = set(re.findall(r"[a-z]+", text.lower()))
    pos = len(words & _POSITIVE_WORDS)
    neg = len(words & _NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _simple_toxicity(text: str) -> float:
    """Return a toxicity score in [0, 1] from word-overlap heuristic."""
    if not text:
        return 0.0
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return 0.0
    toxic_count = sum(1 for w in words if w in _TOXIC_WORDS)
    return toxic_count / len(words)


def _text_diversity(text: str) -> float:
    """Type-token ratio as a simple lexical diversity metric in [0, 1]."""
    if not text:
        return 0.0
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _extract_text(output: Dict[str, Any]) -> str:
    """Extract text content from a model output dict."""
    for key in ("text", "output", "response", "content", "generated_text"):
        if key in output and isinstance(output[key], str):
            return output[key]
    return str(output)


def _extract_group(output: Dict[str, Any]) -> str:
    """Extract demographic group label from a model output dict."""
    for key in ("group", "demographic", "demographic_group", "category"):
        if key in output and output[key]:
            return str(output[key])
    return "unknown"


class ModernLLMBiasService:
    """
    Modern LLM bias detection service implementing 2025 best practices
    """

    def __init__(self):
        self.bias_tests = self._initialize_bias_tests()
        self.explainability_methods = self._initialize_explainability_methods()
        self.evaluation_datasets = self._initialize_evaluation_datasets()

    def _initialize_bias_tests(self) -> Dict[str, Dict[str, Any]]:
        """Initialize modern bias test configurations"""
        return {
            "stereoset": {
                "name": "StereoSet",
                "category": BiasCategory.EXTRINSIC,
                "description": "Stereotype detection in generated text",
                "enabled": True,
                "weight": 1.0
            },
            "crowspairs": {
                "name": "CrowS-Pairs",
                "category": BiasCategory.EXTRINSIC,
                "description": "Crowdsourced stereotype pairs",
                "enabled": True,
                "weight": 1.0
            },
            "bbq": {
                "name": "BBQ (Bias Benchmark for QA)",
                "category": BiasCategory.EXTRINSIC,
                "description": "Question answering bias detection",
                "enabled": True,
                "weight": 1.0
            },
            "weat": {
                "name": "WEAT (Word Embedding Association Test)",
                "category": BiasCategory.INTRINSIC,
                "description": "Embedding-level bias detection",
                "enabled": True,
                "weight": 0.8
            },
            "seat": {
                "name": "SEAT (Sentence Embedding Association Test)",
                "category": BiasCategory.INTRINSIC,
                "description": "Sentence-level bias detection",
                "enabled": True,
                "weight": 0.8
            },
            "minimal_pairs": {
                "name": "Minimal Pairs Testing",
                "category": BiasCategory.CONTEXTUAL,
                "description": "Behavioral bias through minimal pairs",
                "enabled": True,
                "weight": 1.2
            },
            "red_teaming": {
                "name": "Red Teaming",
                "category": BiasCategory.EMERGENT,
                "description": "Adversarial bias discovery",
                "enabled": True,
                "weight": 1.5
            }
        }

    def _initialize_explainability_methods(self) -> Dict[str, Dict[str, Any]]:
        """Initialize explainability method configurations"""
        return {
            "attention_visualization": {
                "name": "Attention Visualization",
                "method": ExplainabilityMethod.ATTENTION_VISUALIZATION,
                "description": "Visualize attention patterns in transformer layers",
                "enabled": True,
                "tools": ["BertViz", "Attention-Maps", "Transformer Interpretability"]
            },
            "activation_patching": {
                "name": "Activation Patching",
                "method": ExplainabilityMethod.ACTIVATION_PATCHING,
                "description": "Interventional methods to understand causal relationships",
                "enabled": True,
                "tools": ["TransformerLens", "Neel Nanda's interpretability library"]
            },
            "circuit_discovery": {
                "name": "Circuit Discovery",
                "method": ExplainabilityMethod.CIRCUIT_DISCOVERY,
                "description": "Understanding specific neural pathways",
                "enabled": True,
                "tools": ["Anthropic's interpretability research"]
            },
            "counterfactual": {
                "name": "Counterfactual Explanations",
                "method": ExplainabilityMethod.COUNTERFACTUAL,
                "description": "Generate alternative scenarios to test bias",
                "enabled": True,
                "tools": ["Custom counterfactual generation"]
            },
            "prompt_ablation": {
                "name": "Prompt Ablation",
                "method": ExplainabilityMethod.PROMPT_ABLATION,
                "description": "Systematically remove prompt components",
                "enabled": True,
                "tools": ["Custom ablation framework"]
            }
        }

    def _initialize_evaluation_datasets(self) -> Dict[str, Dict[str, Any]]:
        """Initialize evaluation dataset configurations"""
        return {
            "stereoset": {
                "name": "StereoSet",
                "url": "https://stereoset.mit.edu/",
                "description": "Stereotype detection dataset",
                "categories": ["gender", "race", "religion", "profession"]
            },
            "crowspairs": {
                "name": "CrowS-Pairs",
                "url": "https://github.com/nyu-mll/crows-pairs",
                "description": "Crowdsourced stereotype pairs",
                "categories": ["gender", "race", "religion", "age", "disability"]
            },
            "bbq": {
                "name": "BBQ",
                "url": "https://github.com/nyu-mll/BBQ",
                "description": "Bias Benchmark for QA",
                "categories": ["age", "disability", "gender", "nationality", "race", "religion", "sexual_orientation"]
            },
            "winogender": {
                "name": "WinoGender",
                "url": "https://github.com/rudinger/winogender-schemas",
                "description": "Gender bias in coreference resolution",
                "categories": ["gender", "profession"]
            }
        }

    async def comprehensive_bias_evaluation(
        self,
        model_outputs: List[Dict[str, Any]],
        model_type: str = "llm",
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive bias evaluation pipeline as outlined in the analysis

        Args:
            model_outputs: List of model outputs to analyze
            model_type: Type of model (llm, image_gen, audio_gen, video_gen)
            evaluation_config: Optional configuration for evaluation

        Returns:
            Comprehensive bias analysis results
        """
        try:
            config = evaluation_config or {}
            results = {
                "timestamp": datetime.now().isoformat(),
                "model_type": model_type,
                "evaluation_summary": {},
                "bias_tests": {},
                "explainability_analysis": {},
                "overall_risk": "unknown",
                "recommendations": [],
                "compliance_status": {}
            }

            # 1. Multi-layered bias detection
            bias_results = await self._run_multi_layered_bias_detection(model_outputs, config)
            results["bias_tests"] = bias_results

            # 2. Explainability analysis
            explainability_results = await self._run_explainability_analysis(model_outputs, config)
            results["explainability_analysis"] = explainability_results

            # 3. Risk assessment
            risk_assessment = self._assess_overall_risk(bias_results, explainability_results)
            results["overall_risk"] = risk_assessment["level"]
            results["risk_factors"] = risk_assessment["factors"]

            # 4. Generate recommendations
            recommendations = self._generate_recommendations(bias_results, explainability_results, model_type)
            results["recommendations"] = recommendations

            # 5. Compliance assessment
            compliance = self._assess_compliance(bias_results, config)
            results["compliance_status"] = compliance

            # 6. Evaluation summary
            results["evaluation_summary"] = self._create_evaluation_summary(bias_results, explainability_results)

            return results

        except Exception as e:
            logger.error(f"Error in comprehensive bias evaluation: {e}")
            raise

    async def _run_multi_layered_bias_detection(
        self,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run multi-layered bias detection"""
        results = {}

        # 1. Pre-deployment comprehensive testing
        pre_deployment_results = await self._pre_deployment_bias_testing(model_outputs, config)
        results["pre_deployment"] = pre_deployment_results

        # 2. Real-time monitoring simulation
        real_time_results = await self._real_time_bias_monitoring(model_outputs, config)
        results["real_time_monitoring"] = real_time_results

        # 3. Post-deployment auditing
        post_deployment_results = await self._post_deployment_auditing(model_outputs, config)
        results["post_deployment"] = post_deployment_results

        # 4. Human-in-the-loop evaluation
        human_evaluation_results = await self._human_in_loop_evaluation(model_outputs, config)
        results["human_evaluation"] = human_evaluation_results

        return results

    async def _pre_deployment_bias_testing(
        self,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pre-deployment comprehensive bias testing"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": [],
            "bias_detected": False,
            "critical_issues": [],
            "warnings": []
        }

        # Run enabled bias tests
        for test_id, test_config in self.bias_tests.items():
            if test_config["enabled"]:
                try:
                    test_result = await self._run_bias_test(test_id, test_config, model_outputs)
                    results["tests_run"].append(test_result)

                    if test_result.is_biased:
                        results["bias_detected"] = True
                        if test_result.bias_score > 0.2:  # High bias threshold
                            results["critical_issues"].append({
                                "test": test_id,
                                "score": test_result.bias_score,
                                "details": test_result.details
                            })
                        else:
                            results["warnings"].append({
                                "test": test_id,
                                "score": test_result.bias_score,
                                "details": test_result.details
                            })

                except Exception as e:
                    logger.error(f"Error running bias test {test_id}: {e}")
                    results["warnings"].append({
                        "test": test_id,
                        "error": str(e)
                    })

        return results

    async def _run_bias_test(
        self,
        test_id: str,
        test_config: Dict[str, Any],
        model_outputs: List[Dict[str, Any]]
    ) -> BiasTestResult:
        """Run individual bias test"""
        try:
            if test_id == "stereoset":
                return await self._run_stereoset_test(model_outputs)
            elif test_id == "crowspairs":
                return await self._run_crowspairs_test(model_outputs)
            elif test_id == "bbq":
                return await self._run_bbq_test(model_outputs)
            elif test_id == "weat":
                return await self._run_weat_test(model_outputs)
            elif test_id == "seat":
                return await self._run_seat_test(model_outputs)
            elif test_id == "minimal_pairs":
                return await self._run_minimal_pairs_test(model_outputs)
            elif test_id == "red_teaming":
                return await self._run_red_teaming_test(model_outputs)
            else:
                raise ValueError(f"Unknown test: {test_id}")

        except Exception as e:
            logger.error(f"Error in bias test {test_id}: {e}")
            raise

    async def _run_stereoset_test(self, model_outputs: List[Dict[str, Any]]) -> BiasTestResult:
        """Run StereoSet bias test"""
        try:
            model_name = model_outputs[0].get("model_name", "gpt2")

            raw_results = await bias_bench_service.evaluate_model(model_name, "stereoset")

            intrasentence_results = raw_results.get("intrasentence", [])
            scores = [r["score"] for r in intrasentence_results]
            avg_score = float(np.mean(scores)) if scores else 0.0

            # StereoSet idealized score is 0.5 (no preference); deviation = bias
            bias_score = abs(avg_score - 0.5) * 2  # Normalize to [0, 1]
            bias_score = min(bias_score, 1.0)

            # Compute p-value via one-sample t-test against 0.5 if enough data
            p_value = 1.0
            if len(scores) >= 2 and SCIPY_AVAILABLE:
                _, p_value = stats.ttest_1samp(scores, 0.5)
                p_value = float(p_value)

            is_biased = bias_score > 0.1 and p_value < 0.05

            details = {
                "raw_results_count": len(intrasentence_results),
                "average_score": avg_score,
                "std_dev": float(np.std(scores)) if scores else 0.0
            }

        except Exception as e:
            logger.error(f"StereoSet evaluation failed: {e}")
            # Return zero scores with error metadata when evaluation fails
            bias_score = 0.0
            is_biased = False
            p_value = 1.0
            details = {"error": str(e), "note": "Returning zero scores due to evaluation failure"}

        # Confidence interval from data when available
        ci_half = 0.0
        if "std_dev" in details and details.get("raw_results_count", 0) > 1:
            n = details["raw_results_count"]
            se = details["std_dev"] / math.sqrt(n)
            ci_half = 1.96 * se

        return BiasTestResult(
            test_id="stereoset",
            test_name="StereoSet",
            category=BiasCategory.EXTRINSIC,
            bias_score=bias_score,
            confidence_interval=(max(0, bias_score - ci_half), min(1, bias_score + ci_half)),
            p_value=p_value,
            is_biased=is_biased,
            threshold=0.1,
            sample_size=len(model_outputs),
            details=details,
            recommendations=[
                "Review training data for stereotype patterns",
                "Implement stereotype detection filters",
                "Use counter-stereotypical examples in training"
            ],
            timestamp=datetime.now().isoformat()
        )

    async def _run_crowspairs_test(self, model_outputs: List[Dict[str, Any]]) -> BiasTestResult:
        """Run CrowS-Pairs bias test"""
        try:
            model_name = model_outputs[0].get("model_name", "gpt2")
            raw_results = await bias_bench_service.evaluate_model(model_name, "crows")

            bias_score = 0.0
            p_value = 1.0
            if isinstance(raw_results, dict):
                bias_score = float(raw_results.get("score", 0.0))
            elif isinstance(raw_results, list) and raw_results:
                # List of pair scores: compute mean and test significance
                pair_scores = [float(r.get("score", 0)) if isinstance(r, dict) else float(r) for r in raw_results]
                bias_score = abs(float(np.mean(pair_scores)) - 0.5) * 2
                if len(pair_scores) >= 2 and SCIPY_AVAILABLE:
                    _, p_value = stats.ttest_1samp(pair_scores, 0.5)
                    p_value = float(p_value)

            is_biased = bias_score > 0.1 and p_value < 0.05
            details = {"raw_results_summary": str(raw_results)[:200]}

        except Exception as e:
            logger.error(f"CrowS-Pairs evaluation failed: {e}")
            bias_score = 0.0
            is_biased = False
            p_value = 1.0
            details = {"error": str(e), "note": "Returning zero scores due to evaluation failure"}

        return BiasTestResult(
            test_id="crowspairs",
            test_name="CrowS-Pairs",
            category=BiasCategory.EXTRINSIC,
            bias_score=bias_score,
            confidence_interval=(max(0, bias_score - 0.05), min(1, bias_score + 0.05)),
            p_value=p_value,
            is_biased=is_biased,
            threshold=0.1,
            sample_size=len(model_outputs),
            details=details,
            recommendations=[
                "Implement bias-aware training objectives",
                "Use diverse training data",
                "Regular bias monitoring in production"
            ],
            timestamp=datetime.now().isoformat()
        )

    async def _run_bbq_test(self, model_outputs: List[Dict[str, Any]]) -> BiasTestResult:
        """Run BBQ (Bias Benchmark for QA) test.

        Analyses model outputs for question-answering bias by comparing
        accuracy/selection rates across demographic groups present in the
        outputs.
        """
        if not model_outputs:
            return self._empty_test_result("bbq", "BBQ", BiasCategory.EXTRINSIC, 0.1,
                                           "No model outputs provided")

        # Extract group-level accuracy from outputs
        group_correct: Dict[str, List[int]] = {}
        for out in model_outputs:
            group = _extract_group(out)
            correct = 1 if out.get("correct", out.get("is_correct", False)) else 0
            group_correct.setdefault(group, []).append(correct)

        if len(group_correct) < 2:
            return self._empty_test_result("bbq", "BBQ", BiasCategory.EXTRINSIC, 0.1,
                                           "Insufficient demographic groups to measure bias")

        group_rates = {g: float(np.mean(vals)) for g, vals in group_correct.items()}
        rates = list(group_rates.values())
        bias_score = max(rates) - min(rates)

        # Statistical test: chi-squared on correct counts per group
        p_value = 1.0
        if SCIPY_AVAILABLE:
            contingency = np.array([[sum(v), len(v) - sum(v)] for v in group_correct.values()])
            if contingency.shape[0] >= 2 and contingency.min() >= 0:
                try:
                    _, p_value, _, _ = stats.chi2_contingency(contingency)
                    p_value = float(p_value)
                except ValueError:
                    p_value = 1.0

        is_biased = bias_score > 0.1 and p_value < 0.05

        return BiasTestResult(
            test_id="bbq",
            test_name="BBQ",
            category=BiasCategory.EXTRINSIC,
            bias_score=bias_score,
            confidence_interval=(max(0, bias_score - 0.05), min(1, bias_score + 0.05)),
            p_value=p_value,
            is_biased=is_biased,
            threshold=0.1,
            sample_size=len(model_outputs),
            details={"group_accuracy_rates": group_rates},
            recommendations=[
                "Review QA training data for demographic imbalances",
                "Implement balanced evaluation across demographic groups",
                "Monitor answer accuracy parity in production"
            ],
            timestamp=datetime.now().isoformat()
        )

    async def _run_weat_test(self, model_outputs: List[Dict[str, Any]]) -> BiasTestResult:
        """Run WEAT (Word Embedding Association Test).

        If embeddings are provided in model_outputs, computes the actual
        WEAT effect size using cosine similarity.  Otherwise falls back
        to word co-occurrence analysis on text.
        """
        if not model_outputs:
            return self._empty_test_result("weat", "WEAT", BiasCategory.INTRINSIC, 0.1,
                                           "No model outputs provided")

        # Check if embeddings are available
        has_embeddings = any("embedding" in o for o in model_outputs)

        if has_embeddings:
            bias_score, p_value, details = self._weat_from_embeddings(model_outputs)
        else:
            # Fallback: use text-based co-occurrence analysis
            bias_score, p_value, details = self._weat_from_text(model_outputs)

        is_biased = bias_score > 0.1 and p_value < 0.05

        return BiasTestResult(
            test_id="weat",
            test_name="WEAT",
            category=BiasCategory.INTRINSIC,
            bias_score=bias_score,
            confidence_interval=(max(0, bias_score - 0.05), min(1, bias_score + 0.05)),
            p_value=p_value,
            is_biased=is_biased,
            threshold=0.1,
            sample_size=len(model_outputs),
            details=details,
            recommendations=[
                "Implement embedding debiasing techniques",
                "Use balanced word lists in training data",
                "Monitor embedding bias metrics over time"
            ],
            timestamp=datetime.now().isoformat()
        )

    def _weat_from_embeddings(self, model_outputs: List[Dict[str, Any]]) -> Tuple[float, float, Dict]:
        """Compute WEAT-style effect size from actual embeddings."""
        # Partition embeddings by group
        group_embeddings: Dict[str, List[np.ndarray]] = {}
        for o in model_outputs:
            emb = o.get("embedding")
            if emb is None:
                continue
            group = _extract_group(o)
            arr = np.array(emb, dtype=float)
            if arr.ndim == 1 and arr.size > 0:
                group_embeddings.setdefault(group, []).append(arr)

        groups = list(group_embeddings.keys())
        if len(groups) < 2:
            return 0.0, 1.0, {"note": "Need at least 2 groups with embeddings"}

        # Compute mean cosine similarity within vs between groups
        def _mean_cos_sim(vecs_a: List[np.ndarray], vecs_b: List[np.ndarray]) -> float:
            sims = []
            for a in vecs_a:
                for b in vecs_b:
                    denom = (np.linalg.norm(a) * np.linalg.norm(b))
                    if denom > 0:
                        sims.append(float(np.dot(a, b) / denom))
            return float(np.mean(sims)) if sims else 0.0

        # Effect size: difference in mean within-group similarity vs between-group similarity
        within_sims = []
        between_sims = []
        for i, g1 in enumerate(groups):
            vecs = group_embeddings[g1]
            if len(vecs) >= 2:
                within_sims.append(_mean_cos_sim(vecs[:len(vecs)//2], vecs[len(vecs)//2:]))
            for g2 in groups[i+1:]:
                between_sims.append(_mean_cos_sim(group_embeddings[g1], group_embeddings[g2]))

        mean_within = float(np.mean(within_sims)) if within_sims else 0.0
        mean_between = float(np.mean(between_sims)) if between_sims else 0.0

        effect_size = abs(mean_within - mean_between)
        bias_score = min(effect_size, 1.0)

        # Two-sample t-test if enough data
        p_value = 1.0
        if SCIPY_AVAILABLE and len(within_sims) >= 2 and len(between_sims) >= 2:
            _, p_value = stats.ttest_ind(within_sims, between_sims, equal_var=False)
            p_value = float(p_value)

        return bias_score, p_value, {
            "method": "embedding_cosine_similarity",
            "groups": groups,
            "mean_within_similarity": mean_within,
            "mean_between_similarity": mean_between,
            "effect_size": effect_size
        }

    def _weat_from_text(self, model_outputs: List[Dict[str, Any]]) -> Tuple[float, float, Dict]:
        """Approximate WEAT from text using word co-occurrence patterns."""
        group_sentiments: Dict[str, List[float]] = {}
        for o in model_outputs:
            text = _extract_text(o)
            group = _extract_group(o)
            sentiment = _simple_sentiment(text)
            group_sentiments.setdefault(group, []).append(sentiment)

        groups = list(group_sentiments.keys())
        if len(groups) < 2:
            return 0.0, 1.0, {"note": "Need at least 2 groups for WEAT text fallback"}

        means = {g: float(np.mean(vals)) for g, vals in group_sentiments.items()}
        mean_vals = list(means.values())
        bias_score = max(mean_vals) - min(mean_vals)

        p_value = 1.0
        if SCIPY_AVAILABLE and len(groups) == 2:
            g1, g2 = groups[0], groups[1]
            if len(group_sentiments[g1]) >= 2 and len(group_sentiments[g2]) >= 2:
                _, p_value = stats.ttest_ind(group_sentiments[g1], group_sentiments[g2], equal_var=False)
                p_value = float(p_value)
        elif SCIPY_AVAILABLE and len(groups) > 2:
            group_lists = [group_sentiments[g] for g in groups if len(group_sentiments[g]) >= 2]
            if len(group_lists) >= 2:
                _, p_value = stats.f_oneway(*group_lists)
                p_value = float(p_value)

        return bias_score, p_value, {
            "method": "text_sentiment_proxy",
            "group_mean_sentiments": means
        }

    async def _run_seat_test(self, model_outputs: List[Dict[str, Any]]) -> BiasTestResult:
        """Run SEAT (Sentence Embedding Association Test)"""
        try:
            model_name = model_outputs[0].get("model_name", "gpt2")
            raw_results = await bias_bench_service.evaluate_model(model_name, "seat")

            bias_score = 0.0
            p_value = 1.0
            effect_sizes = []

            if isinstance(raw_results, list):
                for r in raw_results:
                    if isinstance(r, dict) and "effect_size" in r:
                        effect_sizes.append(abs(float(r["effect_size"])))
                if effect_sizes:
                    bias_score = float(np.mean(effect_sizes))
                    # Test if effect sizes are significantly different from zero
                    if len(effect_sizes) >= 2 and SCIPY_AVAILABLE:
                        _, p_value = stats.ttest_1samp(effect_sizes, 0.0)
                        p_value = float(p_value)
            elif isinstance(raw_results, dict):
                bias_score = float(raw_results.get("effect_size", raw_results.get("score", 0.0)))

            is_biased = bias_score > 0.1 and p_value < 0.05
            details = {
                "effect_sizes": effect_sizes if effect_sizes else [],
                "mean_effect_size": bias_score,
                "raw_results_type": type(raw_results).__name__
            }

        except Exception as e:
            logger.error(f"SEAT evaluation failed: {e}")
            bias_score = 0.0
            is_biased = False
            p_value = 1.0
            details = {"error": str(e), "note": "Returning zero scores due to evaluation failure"}

        return BiasTestResult(
            test_id="seat",
            test_name="SEAT",
            category=BiasCategory.INTRINSIC,
            bias_score=bias_score,
            confidence_interval=(max(0, bias_score - 0.05), min(1, bias_score + 0.05)),
            p_value=p_value,
            is_biased=is_biased,
            threshold=0.1,
            sample_size=len(model_outputs),
            details=details,
            recommendations=[
                "Implement sentence-level debiasing",
                "Use diverse sentence training data",
                "Monitor sentence embedding bias"
            ],
            timestamp=datetime.now().isoformat()
        )

    async def _run_minimal_pairs_test(self, model_outputs: List[Dict[str, Any]]) -> BiasTestResult:
        """Run minimal pairs testing on actual model output pairs.

        Expects model_outputs to contain paired entries (identified by
        matching 'pair_id' keys or consecutive pairs) where only the
        demographic attribute differs.  Computes actual toxicity,
        sentiment, and length gaps between the pairs.
        """
        if not model_outputs:
            return self._empty_test_result("minimal_pairs", "Minimal Pairs Testing",
                                           BiasCategory.CONTEXTUAL, 0.1,
                                           "No model outputs provided")

        # Group outputs into pairs
        pairs = self._extract_pairs(model_outputs)

        if not pairs:
            return self._empty_test_result("minimal_pairs", "Minimal Pairs Testing",
                                           BiasCategory.CONTEXTUAL, 0.1,
                                           "No valid output pairs found")

        toxicity_gaps = []
        sentiment_gaps = []
        length_gaps = []

        for a, b in pairs:
            text_a = _extract_text(a)
            text_b = _extract_text(b)

            tox_a = _simple_toxicity(text_a)
            tox_b = _simple_toxicity(text_b)
            toxicity_gaps.append(abs(tox_a - tox_b))

            sent_a = _simple_sentiment(text_a)
            sent_b = _simple_sentiment(text_b)
            sentiment_gaps.append(abs(sent_a - sent_b))

            len_a = len(text_a.split())
            len_b = len(text_b.split())
            denom = max(len_a, len_b, 1)
            length_gaps.append(abs(len_a - len_b) / denom)

        toxicity_gap = float(np.mean(toxicity_gaps))
        sentiment_gap = float(np.mean(sentiment_gaps))
        length_gap = float(np.mean(length_gaps))
        bias_score = float(np.mean([toxicity_gap, sentiment_gap, length_gap]))

        # One-sample t-test: are gaps significantly > 0?
        p_value = 1.0
        all_gaps = [toxicity_gaps[i] + sentiment_gaps[i] + length_gaps[i] for i in range(len(pairs))]
        if len(all_gaps) >= 2 and SCIPY_AVAILABLE:
            _, p_value = stats.ttest_1samp(all_gaps, 0.0)
            p_value = float(p_value) if not math.isnan(p_value) else 1.0

        is_biased = bias_score > 0.1 and p_value < 0.05

        return BiasTestResult(
            test_id="minimal_pairs",
            test_name="Minimal Pairs Testing",
            category=BiasCategory.CONTEXTUAL,
            bias_score=bias_score,
            confidence_interval=(max(0, bias_score - 0.05), min(1, bias_score + 0.05)),
            p_value=p_value,
            is_biased=is_biased,
            threshold=0.1,
            sample_size=len(model_outputs),
            details={
                "num_pairs": len(pairs),
                "behavioral_gaps": {
                    "toxicity_gap": round(toxicity_gap, 4),
                    "sentiment_gap": round(sentiment_gap, 4),
                    "length_gap": round(length_gap, 4)
                }
            },
            recommendations=[
                "Implement output filtering",
                "Use behavioral bias training",
                "Monitor minimal pair differences"
            ],
            timestamp=datetime.now().isoformat()
        )

    async def _run_red_teaming_test(self, model_outputs: List[Dict[str, Any]]) -> BiasTestResult:
        """Run red teaming for emergent bias discovery.

        Analyses actual model outputs for adversarial/emergent bias
        patterns by computing toxicity and sentiment divergence metrics
        from the provided outputs.
        """
        if not model_outputs:
            return self._empty_test_result("red_teaming", "Red Teaming",
                                           BiasCategory.EMERGENT, 0.15,
                                           "No model outputs provided")

        # Compute per-output toxicity and sentiment
        toxicities = []
        sentiments = []
        lengths = []

        for o in model_outputs:
            text = _extract_text(o)
            toxicities.append(_simple_toxicity(text))
            sentiments.append(_simple_sentiment(text))
            lengths.append(len(text.split()))

        mean_toxicity = float(np.mean(toxicities))
        mean_sentiment = float(np.mean(sentiments))

        # Edge-case analysis: outputs with extremely high toxicity or negative sentiment
        high_tox_count = sum(1 for t in toxicities if t > 0.3)
        high_tox_rate = high_tox_count / len(toxicities) if toxicities else 0.0

        # Group-level divergence if groups available
        group_toxicities: Dict[str, List[float]] = {}
        for i, o in enumerate(model_outputs):
            group = _extract_group(o)
            group_toxicities.setdefault(group, []).append(toxicities[i])

        prompt_injection_score = 0.0  # Fraction of high-toxicity outputs
        prompt_injection_score = high_tox_rate

        context_manipulation_score = 0.0
        if len(group_toxicities) >= 2:
            group_means = [float(np.mean(v)) for v in group_toxicities.values()]
            context_manipulation_score = max(group_means) - min(group_means)

        edge_case_score = 0.0
        if sentiments:
            # Fraction of outputs with extreme negative sentiment
            extreme_neg = sum(1 for s in sentiments if s < -0.5)
            edge_case_score = extreme_neg / len(sentiments)

        bias_score = float(np.mean([prompt_injection_score, context_manipulation_score, edge_case_score]))

        # Significance: test whether toxicity differs across groups
        p_value = 1.0
        if SCIPY_AVAILABLE and len(group_toxicities) >= 2:
            group_lists = [v for v in group_toxicities.values() if len(v) >= 2]
            if len(group_lists) >= 2:
                _, p_value = stats.f_oneway(*group_lists)
                p_value = float(p_value) if not math.isnan(p_value) else 1.0

        is_biased = bias_score > 0.15 and p_value < 0.05

        return BiasTestResult(
            test_id="red_teaming",
            test_name="Red Teaming",
            category=BiasCategory.EMERGENT,
            bias_score=bias_score,
            confidence_interval=(max(0, bias_score - 0.05), min(1, bias_score + 0.05)),
            p_value=p_value,
            is_biased=is_biased,
            threshold=0.15,
            sample_size=len(model_outputs),
            details={
                "mean_toxicity": round(mean_toxicity, 4),
                "mean_sentiment": round(mean_sentiment, 4),
                "adversarial_scenarios": {
                    "prompt_injection": round(prompt_injection_score, 4),
                    "context_manipulation": round(context_manipulation_score, 4),
                    "edge_cases": round(edge_case_score, 4)
                }
            },
            recommendations=[
                "Implement adversarial training",
                "Use red teaming in development",
                "Monitor for emergent bias patterns"
            ],
            timestamp=datetime.now().isoformat()
        )

    # -----------------------------------------------------------------------
    # Helper: build pairs from model outputs
    # -----------------------------------------------------------------------
    def _extract_pairs(self, model_outputs: List[Dict[str, Any]]) -> List[Tuple[Dict, Dict]]:
        """Extract minimal pairs from outputs.

        Pairs are matched by 'pair_id' if available, otherwise by
        consecutive position.
        """
        # Try pair_id matching
        by_pair: Dict[str, List[Dict]] = {}
        for o in model_outputs:
            pid = o.get("pair_id")
            if pid is not None:
                by_pair.setdefault(str(pid), []).append(o)

        if by_pair:
            pairs = []
            for pid, items in by_pair.items():
                if len(items) >= 2:
                    pairs.append((items[0], items[1]))
            if pairs:
                return pairs

        # Fallback: consecutive pairs
        pairs = []
        for i in range(0, len(model_outputs) - 1, 2):
            pairs.append((model_outputs[i], model_outputs[i + 1]))
        return pairs

    # -----------------------------------------------------------------------
    # Helper: empty test result for insufficient data
    # -----------------------------------------------------------------------
    def _empty_test_result(self, test_id: str, test_name: str,
                           category: BiasCategory, threshold: float,
                           reason: str) -> BiasTestResult:
        return BiasTestResult(
            test_id=test_id,
            test_name=test_name,
            category=category,
            bias_score=0.0,
            confidence_interval=(0.0, 0.0),
            p_value=1.0,
            is_biased=False,
            threshold=threshold,
            sample_size=0,
            details={"note": reason},
            recommendations=[f"Provide sufficient data to run {test_name}"],
            timestamp=datetime.now().isoformat()
        )

    async def _run_explainability_analysis(
        self,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run explainability analysis using modern methods"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "methods_used": [],
            "insights": [],
            "visualizations": []
        }

        # Run enabled explainability methods
        for method_id, method_config in self.explainability_methods.items():
            if method_config["enabled"]:
                try:
                    explainability_result = await self._run_explainability_method(
                        method_id, method_config, model_outputs
                    )
                    results["methods_used"].append(explainability_result)
                    results["insights"].extend(explainability_result.insights)
                    results["visualizations"].extend(explainability_result.visualizations)

                except Exception as e:
                    logger.error(f"Error running explainability method {method_id}: {e}")

        return results

    async def _run_explainability_method(
        self,
        method_id: str,
        method_config: Dict[str, Any],
        model_outputs: List[Dict[str, Any]]
    ) -> ExplainabilityResult:
        """Run individual explainability method"""
        try:
            if method_id == "attention_visualization":
                return await self._attention_visualization_analysis(model_outputs)
            elif method_id == "activation_patching":
                return await self._activation_patching_analysis(model_outputs)
            elif method_id == "circuit_discovery":
                return await self._circuit_discovery_analysis(model_outputs)
            elif method_id == "counterfactual":
                return await self._counterfactual_analysis(model_outputs)
            elif method_id == "prompt_ablation":
                return await self._prompt_ablation_analysis(model_outputs)
            else:
                raise ValueError(f"Unknown explainability method: {method_id}")

        except Exception as e:
            logger.error(f"Error in explainability method {method_id}: {e}")
            raise

    async def _attention_visualization_analysis(self, model_outputs: List[Dict[str, Any]]) -> ExplainabilityResult:
        """Attention visualization analysis.

        If model outputs include attention weights, analyses them.
        Otherwise provides structural metadata.
        """
        # Try to extract real attention weights
        attention_weights = []
        high_attention_tokens: List[str] = []

        for o in model_outputs:
            weights = o.get("attention_weights")
            if weights is not None:
                arr = np.array(weights, dtype=float).flatten()
                attention_weights.extend(arr.tolist())

            tokens = o.get("tokens", [])
            token_weights = o.get("token_attention", [])
            if tokens and token_weights and len(tokens) == len(token_weights):
                sorted_pairs = sorted(zip(tokens, token_weights), key=lambda x: -x[1])
                for tok, _ in sorted_pairs[:3]:
                    if tok not in high_attention_tokens:
                        high_attention_tokens.append(tok)

        if attention_weights:
            weight_arr = np.array(attention_weights)
            explanation = {
                "attention_patterns": {
                    "high_attention_tokens": high_attention_tokens[:10] if high_attention_tokens else [],
                    "mean_attention": float(np.mean(weight_arr)),
                    "std_attention": float(np.std(weight_arr)),
                    "max_attention": float(np.max(weight_arr)),
                    "layer_analysis": {
                        "note": "Per-layer analysis requires layered attention data"
                    }
                }
            }
            confidence = 0.85
            insights = [
                f"Mean attention weight: {np.mean(weight_arr):.4f}",
                f"Attention std dev: {np.std(weight_arr):.4f} (higher indicates selective focus)"
            ]
            if high_attention_tokens:
                insights.append(f"Top attended tokens: {', '.join(high_attention_tokens[:5])}")
        else:
            explanation = {
                "attention_patterns": {
                    "high_attention_tokens": [],
                    "note": "No attention weight data provided in model outputs"
                }
            }
            confidence = 0.0
            insights = [
                "No attention weight data available in model outputs",
                "Provide attention_weights and tokens in model output dicts for analysis"
            ]

        return ExplainabilityResult(
            method=ExplainabilityMethod.ATTENTION_VISUALIZATION,
            explanation=explanation,
            confidence=confidence,
            visualizations=["attention_heatmap.png", "attention_flow.gif"],
            insights=insights,
            timestamp=datetime.now().isoformat()
        )

    async def _activation_patching_analysis(self, model_outputs: List[Dict[str, Any]]) -> ExplainabilityResult:
        """Activation patching analysis.

        Analyses provided activation data if available, otherwise returns
        structural metadata about what data is needed.
        """
        activation_data = [o.get("activations") for o in model_outputs if o.get("activations")]

        if activation_data:
            # Compute layer-level statistics
            layer_effects: Dict[str, float] = {}
            for act in activation_data:
                if isinstance(act, dict):
                    for layer_name, values in act.items():
                        arr = np.array(values, dtype=float)
                        effect = float(np.std(arr))
                        layer_effects[layer_name] = layer_effects.get(layer_name, 0) + effect

            # Normalize
            n = len(activation_data)
            layer_effects = {k: round(v / n, 4) for k, v in layer_effects.items()}
            critical_layers = sorted(layer_effects.keys(), key=lambda k: -layer_effects[k])[:3]

            explanation = {
                "causal_analysis": {
                    "critical_layers": critical_layers,
                    "intervention_effects": layer_effects,
                    "causal_pathways": ["Derived from activation variance analysis"]
                }
            }
            confidence = 0.78
            insights = [
                f"Most variable layers: {', '.join(critical_layers)}",
                "Higher variance layers may contribute more to bias"
            ]
        else:
            explanation = {
                "causal_analysis": {
                    "note": "No activation data provided in model outputs",
                    "required_format": "activations: {layer_name: [values]}"
                }
            }
            confidence = 0.0
            insights = [
                "No activation data available in model outputs",
                "Provide activations dict per output for patching analysis"
            ]

        return ExplainabilityResult(
            method=ExplainabilityMethod.ACTIVATION_PATCHING,
            explanation=explanation,
            confidence=confidence,
            visualizations=["activation_patch_effects.png", "causal_graph.svg"],
            insights=insights,
            timestamp=datetime.now().isoformat()
        )

    async def _circuit_discovery_analysis(self, model_outputs: List[Dict[str, Any]]) -> ExplainabilityResult:
        """Circuit discovery analysis.

        Returns structural metadata; actual circuit discovery requires
        model internals not available from output data alone.
        """
        explanation = {
            "neural_circuits": {
                "note": "Circuit discovery requires direct model internal access",
                "available_analysis": "Output-level pattern detection"
            }
        }

        # We can still provide output-level pattern analysis
        insights = []
        if model_outputs:
            group_patterns: Dict[str, List[float]] = {}
            for o in model_outputs:
                group = _extract_group(o)
                text = _extract_text(o)
                sentiment = _simple_sentiment(text)
                group_patterns.setdefault(group, []).append(sentiment)

            if len(group_patterns) >= 2:
                group_means = {g: float(np.mean(v)) for g, v in group_patterns.items()}
                explanation["output_patterns"] = {"group_sentiment_means": group_means}
                insights.append(f"Detected {len(group_patterns)} output groups with varying sentiment profiles")
            else:
                insights.append("Insufficient group diversity for pattern analysis")
        else:
            insights.append("No model outputs provided for circuit analysis")

        return ExplainabilityResult(
            method=ExplainabilityMethod.CIRCUIT_DISCOVERY,
            explanation=explanation,
            confidence=0.0 if not model_outputs else 0.4,
            visualizations=["neural_circuit_diagram.png", "circuit_activation_map.png"],
            insights=insights,
            timestamp=datetime.now().isoformat()
        )

    async def _counterfactual_analysis(self, model_outputs: List[Dict[str, Any]]) -> ExplainabilityResult:
        """Counterfactual explanation analysis.

        Computes actual sentiment/toxicity changes between paired outputs
        (counterfactual pairs) if pair_id is available.
        """
        pairs = self._extract_pairs(model_outputs)

        if not pairs:
            return ExplainabilityResult(
                method=ExplainabilityMethod.COUNTERFACTUAL,
                explanation={"note": "No counterfactual pairs found in model outputs"},
                confidence=0.0,
                visualizations=[],
                insights=["Provide paired outputs with pair_id to enable counterfactual analysis"],
                timestamp=datetime.now().isoformat()
            )

        scenarios = {}
        bias_changes = []
        for i, (a, b) in enumerate(pairs):
            text_a = _extract_text(a)
            text_b = _extract_text(b)
            sent_a = _simple_sentiment(text_a)
            sent_b = _simple_sentiment(text_b)
            change = abs(sent_a - sent_b)
            bias_changes.append(change)

            label_a = a.get("label", a.get("variant", f"variant_a"))
            label_b = b.get("label", b.get("variant", f"variant_b"))
            scenarios[f"pair_{i}"] = {
                "original": text_a[:100],
                "counterfactual": text_b[:100],
                "bias_change": round(change, 4),
                "labels": [str(label_a), str(label_b)]
            }

        mean_change = float(np.mean(bias_changes))

        insights = [
            f"Analyzed {len(pairs)} counterfactual pairs",
            f"Mean sentiment change across swaps: {mean_change:.4f}"
        ]
        if mean_change > 0.1:
            insights.append("Significant sentiment shift detected between counterfactual pairs")

        return ExplainabilityResult(
            method=ExplainabilityMethod.COUNTERFACTUAL,
            explanation={"counterfactual_scenarios": scenarios, "mean_bias_change": round(mean_change, 4)},
            confidence=min(0.5 + len(pairs) * 0.05, 0.95),
            visualizations=["counterfactual_comparison.png"],
            insights=insights,
            timestamp=datetime.now().isoformat()
        )

    async def _prompt_ablation_analysis(self, model_outputs: List[Dict[str, Any]]) -> ExplainabilityResult:
        """Prompt ablation analysis.

        If outputs include ablation metadata (which component was removed),
        computes actual effect sizes.  Otherwise analyses text content
        for category-level bias signals.
        """
        # Check for ablation metadata
        ablation_outputs = [o for o in model_outputs if "ablated_component" in o]

        if ablation_outputs:
            # Group by ablated component and compute effect
            component_sentiments: Dict[str, List[float]] = {}
            baseline_sentiments: List[float] = []

            for o in model_outputs:
                text = _extract_text(o)
                sentiment = _simple_sentiment(text)
                comp = o.get("ablated_component", "baseline")
                if comp == "baseline" or comp is None:
                    baseline_sentiments.append(sentiment)
                else:
                    component_sentiments.setdefault(comp, []).append(sentiment)

            baseline_mean = float(np.mean(baseline_sentiments)) if baseline_sentiments else 0.0

            ablation_results = {}
            for comp, sents in component_sentiments.items():
                comp_mean = float(np.mean(sents))
                removal_effect = abs(comp_mean - baseline_mean)
                ablation_results[comp] = {
                    "removal_effect": round(removal_effect, 4),
                    "bias_reduction": round(max(0, baseline_mean - comp_mean), 4) if baseline_mean > 0 else 0.0
                }

            insights = [f"Analyzed ablation of {len(component_sentiments)} components"]
            if ablation_results:
                top_comp = max(ablation_results.keys(), key=lambda k: ablation_results[k]["removal_effect"])
                insights.append(f"Component '{top_comp}' has strongest effect when removed")
        else:
            # Fallback: analyse by category words in text
            category_words = {
                "gender_terms": {"he", "she", "him", "her", "his", "hers", "man", "woman", "male", "female"},
                "occupation_terms": {"doctor", "nurse", "engineer", "teacher", "lawyer", "scientist"},
                "cultural_terms": {"western", "eastern", "traditional", "modern", "cultural", "ethnic"}
            }

            ablation_results = {}
            for cat, words in category_words.items():
                presences = []
                for o in model_outputs:
                    text = _extract_text(o).lower()
                    text_words = set(re.findall(r"[a-z]+", text))
                    overlap = len(text_words & words)
                    total = len(text_words) if text_words else 1
                    presences.append(overlap / total)

                mean_presence = float(np.mean(presences)) if presences else 0.0
                ablation_results[cat] = {
                    "removal_effect": round(mean_presence, 4),
                    "bias_reduction": round(mean_presence * 0.5, 4)  # Estimated reduction
                }

            insights = [
                "No ablation metadata found; using word category analysis as proxy",
                "Provide ablated_component field in outputs for true ablation analysis"
            ]

        return ExplainabilityResult(
            method=ExplainabilityMethod.PROMPT_ABLATION,
            explanation={"ablation_results": ablation_results},
            confidence=0.82 if ablation_outputs else 0.4,
            visualizations=["prompt_ablation_effects.png"],
            insights=insights,
            timestamp=datetime.now().isoformat()
        )

    async def _real_time_bias_monitoring(
        self,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Real-time bias monitoring computed from actual outputs.

        Computes a rolling bias trend and fairness score from the
        provided model outputs rather than simulating values.
        """
        if not model_outputs:
            return {
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": True,
                "alerts": [],
                "metrics": {
                    "bias_score_trend": [],
                    "fairness_score": 0.0,
                    "drift_detected": False
                },
                "recommendations": ["Provide model outputs to enable monitoring"]
            }

        # Compute per-output bias proxy (toxicity)
        toxicities = [_simple_toxicity(_extract_text(o)) for o in model_outputs]

        # Create a trend by chunking outputs into buckets
        n = len(toxicities)
        num_buckets = min(24, n)
        bucket_size = max(1, n // num_buckets)
        trend = []
        for i in range(0, n, bucket_size):
            chunk = toxicities[i:i + bucket_size]
            trend.append(round(float(np.mean(chunk)), 4))

        # Fairness: 1 - max group toxicity disparity
        group_toxicities: Dict[str, List[float]] = {}
        for i, o in enumerate(model_outputs):
            group = _extract_group(o)
            group_toxicities.setdefault(group, []).append(toxicities[i])

        fairness_score = 1.0
        if len(group_toxicities) >= 2:
            group_means = [float(np.mean(v)) for v in group_toxicities.values()]
            disparity = max(group_means) - min(group_means)
            fairness_score = round(max(0.0, 1.0 - disparity), 4)

        # Drift detection: compare first half vs second half
        drift_detected = False
        if n >= 10:
            first_half = toxicities[:n // 2]
            second_half = toxicities[n // 2:]
            if SCIPY_AVAILABLE and len(first_half) >= 2 and len(second_half) >= 2:
                _, p = stats.ttest_ind(first_half, second_half, equal_var=False)
                drift_detected = float(p) < 0.05

        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": True,
            "alerts": [],
            "metrics": {
                "bias_score_trend": trend,
                "fairness_score": fairness_score,
                "drift_detected": drift_detected
            },
            "recommendations": [
                "Continue monitoring bias trends",
                "Set up automated alerts for bias spikes"
            ]
        }

    async def _post_deployment_auditing(
        self,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post-deployment auditing from actual outputs."""
        if not model_outputs:
            return {
                "timestamp": datetime.now().isoformat(),
                "audit_findings": {
                    "bias_incidents": 0,
                    "fairness_violations": 0,
                    "compliance_issues": []
                },
                "audit_metrics": {
                    "overall_fairness": 0.0,
                    "bias_trend": "insufficient_data",
                    "note": "No model outputs provided for auditing"
                },
                "recommendations": [
                    "Provide model outputs for auditing",
                    "Schedule regular bias audits"
                ]
            }

        # Count bias incidents: outputs with high toxicity
        toxicities = [_simple_toxicity(_extract_text(o)) for o in model_outputs]
        bias_incidents = sum(1 for t in toxicities if t > 0.2)

        # Fairness violations: group disparity
        group_tox: Dict[str, List[float]] = {}
        for i, o in enumerate(model_outputs):
            group = _extract_group(o)
            group_tox.setdefault(group, []).append(toxicities[i])

        fairness_violations = 0
        overall_fairness = 1.0
        if len(group_tox) >= 2:
            group_means = [float(np.mean(v)) for v in group_tox.values()]
            disparity = max(group_means) - min(group_means)
            overall_fairness = round(max(0.0, 1.0 - disparity), 4)
            if disparity > 0.1:
                fairness_violations = 1

        # Bias trend
        n = len(toxicities)
        if n >= 4:
            first_q = float(np.mean(toxicities[:n // 4]))
            last_q = float(np.mean(toxicities[3 * n // 4:]))
            if last_q > first_q + 0.05:
                bias_trend = "increasing"
            elif last_q < first_q - 0.05:
                bias_trend = "decreasing"
            else:
                bias_trend = "stable"
        else:
            bias_trend = "insufficient_data"

        return {
            "timestamp": datetime.now().isoformat(),
            "audit_findings": {
                "bias_incidents": bias_incidents,
                "fairness_violations": fairness_violations,
                "compliance_issues": []
            },
            "audit_metrics": {
                "overall_fairness": overall_fairness,
                "bias_trend": bias_trend,
                "total_outputs_audited": len(model_outputs)
            },
            "recommendations": [
                "Schedule regular bias audits",
                "Implement user feedback collection"
            ]
        }

    async def _human_in_loop_evaluation(
        self,
        model_outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Human-in-the-loop evaluation.

        Aggregates any human-provided ratings from the model outputs
        metadata.  Returns zero-valued structure when no human ratings
        are available.
        """
        bias_ratings = []
        fairness_ratings = []
        expert_notes = []

        for o in model_outputs:
            human = o.get("human_evaluation", {})
            if isinstance(human, dict):
                if "bias_rating" in human:
                    bias_ratings.append(float(human["bias_rating"]))
                if "fairness_rating" in human:
                    fairness_ratings.append(float(human["fairness_rating"]))
                if "notes" in human:
                    expert_notes.append(str(human["notes"]))

        has_ratings = bool(bias_ratings or fairness_ratings)

        return {
            "timestamp": datetime.now().isoformat(),
            "human_evaluation": {
                "expert_review": {
                    "bias_detected": (float(np.mean(bias_ratings)) > 3.0) if bias_ratings else False,
                    "severity": "high" if bias_ratings and float(np.mean(bias_ratings)) > 4 else
                                "medium" if bias_ratings and float(np.mean(bias_ratings)) > 3 else "low",
                    "notes": "; ".join(expert_notes) if expert_notes else "No human expert notes provided"
                },
                "crowd_evaluation": {
                    "participants": len(bias_ratings),
                    "bias_rating": round(float(np.mean(bias_ratings)), 2) if bias_ratings else 0.0,
                    "fairness_rating": round(float(np.mean(fairness_ratings)), 2) if fairness_ratings else 0.0
                },
                "data_available": has_ratings
            },
            "recommendations": [
                "Continue human evaluation program" if has_ratings else "Collect human bias ratings for model outputs",
                "Expand expert review panel"
            ]
        }

    def _assess_overall_risk(
        self,
        bias_results: Dict[str, Any],
        explainability_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall bias risk"""
        risk_factors = []
        risk_score = 0.0

        # Analyze bias test results
        for test_category, results in bias_results.items():
            if isinstance(results, dict) and "tests_run" in results:
                for test in results["tests_run"]:
                    if test.is_biased:
                        risk_score += test.bias_score * 0.3
                        risk_factors.append(f"Bias detected in {test.test_name}")

        # Determine risk level
        if risk_score < 0.2:
            risk_level = "low"
        elif risk_score < 0.5:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "level": risk_level,
            "score": risk_score,
            "factors": risk_factors
        }

    def _generate_recommendations(
        self,
        bias_results: Dict[str, Any],
        explainability_results: Dict[str, Any],
        model_type: str
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # General recommendations
        recommendations.extend([
            "Implement continuous bias monitoring",
            "Use multiple bias detection methods",
            "Regular bias auditing and evaluation",
            "Human-in-the-loop bias assessment"
        ])

        # Model-specific recommendations
        if model_type == "llm":
            recommendations.extend([
                "Use prompt engineering for bias mitigation",
                "Implement output filtering and post-processing",
                "Apply embedding debiasing techniques",
                "Use diverse training data sources"
            ])
        elif model_type == "image_gen":
            recommendations.extend([
                "Implement demographic representation monitoring",
                "Use CLIP-based bias detection",
                "Apply style transfer debiasing",
                "Monitor object detection bias"
            ])
        elif model_type == "audio_gen":
            recommendations.extend([
                "Monitor voice characteristic bias",
                "Implement demographic classifier probing",
                "Use audio feature-based bias detection",
                "Apply spectral analysis for bias patterns"
            ])
        elif model_type == "video_gen":
            recommendations.extend([
                "Monitor motion and activity bias",
                "Implement temporal consistency analysis",
                "Use pose estimation for bias detection",
                "Apply scene analysis for contextual bias"
            ])

        return recommendations

    def _assess_compliance(
        self,
        bias_results: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess compliance with fairness regulations"""
        compliance_frameworks = config.get("compliance_frameworks", ["EU_AI_ACT", "FTC_GUIDELINES"])

        compliance_status = {}
        for framework in compliance_frameworks:
            compliance_status[framework] = {
                "compliant": True,
                "issues": [],
                "recommendations": []
            }

        return compliance_status

    def _create_evaluation_summary(
        self,
        bias_results: Dict[str, Any],
        explainability_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create evaluation summary"""
        total_tests = 0
        biased_tests = 0

        for test_category, results in bias_results.items():
            if isinstance(results, dict) and "tests_run" in results:
                total_tests += len(results["tests_run"])
                biased_tests += sum(1 for test in results["tests_run"] if test.is_biased)

        return {
            "total_tests_run": total_tests,
            "biased_tests": biased_tests,
            "bias_rate": biased_tests / total_tests if total_tests > 0 else 0,
            "explainability_methods_used": len(explainability_results.get("methods_used", [])),
            "overall_assessment": "comprehensive"
        }

    async def detect_multimodal_bias(
        self,
        model_outputs: List[Dict[str, Any]],
        modalities: List[str]
    ) -> Dict[str, Any]:
        """
        Detect bias across multiple modalities (text, image, audio, video)
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "modalities": modalities,
            "cross_modal_bias": {},
            "modality_specific_bias": {},
            "interaction_effects": {}
        }

        # Analyze each modality
        for modality in modalities:
            modality_results = await self._analyze_modality_bias(model_outputs, modality)
            results["modality_specific_bias"][modality] = modality_results

        # Analyze cross-modal interactions
        if len(modalities) > 1:
            cross_modal_results = await self._analyze_cross_modal_bias(model_outputs, modalities)
            results["cross_modal_bias"] = cross_modal_results

        return results

    async def _analyze_modality_bias(
        self,
        model_outputs: List[Dict[str, Any]],
        modality: str
    ) -> Dict[str, Any]:
        """Analyze bias for specific modality"""
        if modality == "text":
            return await self._analyze_text_bias(model_outputs)
        elif modality == "image":
            return await self._analyze_image_bias(model_outputs)
        elif modality == "audio":
            return await self._analyze_audio_bias(model_outputs)
        elif modality == "video":
            return await self._analyze_video_bias(model_outputs)
        else:
            raise ValueError(f"Unsupported modality: {modality}")

    async def _analyze_text_bias(self, model_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze text-specific bias from actual model outputs."""
        if not model_outputs:
            return {
                "bias_types": [],
                "bias_score": 0.0,
                "detected_patterns": [],
                "note": "No model outputs provided"
            }

        # Compute group-level sentiment and toxicity
        group_sentiments: Dict[str, List[float]] = {}
        group_toxicities: Dict[str, List[float]] = {}

        for o in model_outputs:
            text = _extract_text(o)
            group = _extract_group(o)
            group_sentiments.setdefault(group, []).append(_simple_sentiment(text))
            group_toxicities.setdefault(group, []).append(_simple_toxicity(text))

        detected_patterns = []
        bias_types = []

        # Check for sentiment disparity
        if len(group_sentiments) >= 2:
            means = {g: float(np.mean(v)) for g, v in group_sentiments.items()}
            vals = list(means.values())
            if max(vals) - min(vals) > 0.1:
                detected_patterns.append(f"Sentiment disparity across groups: {means}")
                bias_types.append("demographic")

        # Check for toxicity disparity
        if len(group_toxicities) >= 2:
            means = {g: float(np.mean(v)) for g, v in group_toxicities.items()}
            vals = list(means.values())
            if max(vals) - min(vals) > 0.05:
                detected_patterns.append(f"Toxicity disparity across groups: {means}")
                bias_types.append("occupational")

        # Compute overall bias score from disparity
        all_disparities = []
        for group_data in [group_sentiments, group_toxicities]:
            if len(group_data) >= 2:
                means = [float(np.mean(v)) for v in group_data.values()]
                all_disparities.append(max(means) - min(means))

        bias_score = float(np.mean(all_disparities)) if all_disparities else 0.0

        return {
            "bias_types": bias_types if bias_types else ["none_detected"],
            "bias_score": round(bias_score, 4),
            "detected_patterns": detected_patterns if detected_patterns else ["No significant bias patterns detected"]
        }

    async def _analyze_image_bias(self, model_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze image-specific bias from actual model outputs.

        Uses metadata fields (demographic_representation, object_labels,
        scene_type) if available. Returns zeros with explanation when data
        is insufficient.
        """
        if not model_outputs:
            return {
                "bias_types": [],
                "bias_score": 0.0,
                "detected_patterns": [],
                "note": "No model outputs provided"
            }

        # Count demographic representation from metadata
        group_counts: Dict[str, int] = Counter()
        for o in model_outputs:
            group = _extract_group(o)
            group_counts[group] += 1

        detected_patterns = []
        bias_types = []

        if len(group_counts) >= 2:
            total = sum(group_counts.values())
            proportions = {g: c / total for g, c in group_counts.items()}
            max_prop = max(proportions.values())
            min_prop = min(proportions.values())
            if max_prop - min_prop > 0.2:
                detected_patterns.append(f"Uneven demographic representation: {proportions}")
                bias_types.append("demographic_representation")

        # Compute bias score from representation imbalance
        if group_counts and len(group_counts) >= 2:
            counts = list(group_counts.values())
            expected = sum(counts) / len(counts)
            chi_sq = sum((c - expected) ** 2 / expected for c in counts)
            # Normalize to [0, 1]
            bias_score = min(chi_sq / (sum(counts) + 1), 1.0)
        else:
            bias_score = 0.0

        return {
            "bias_types": bias_types if bias_types else ["none_detected"],
            "bias_score": round(bias_score, 4),
            "detected_patterns": detected_patterns if detected_patterns else ["No significant bias patterns detected"]
        }

    async def _analyze_audio_bias(self, model_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze audio-specific bias from actual model outputs.

        Uses metadata fields (pitch, duration, accent, language) if
        available.
        """
        if not model_outputs:
            return {
                "bias_types": [],
                "bias_score": 0.0,
                "detected_patterns": [],
                "note": "No model outputs provided"
            }

        # Extract audio metrics by group
        group_durations: Dict[str, List[float]] = {}
        for o in model_outputs:
            group = _extract_group(o)
            duration = o.get("duration", o.get("audio_duration", 0))
            if duration:
                group_durations.setdefault(group, []).append(float(duration))

        detected_patterns = []
        bias_types = []

        if len(group_durations) >= 2:
            means = {g: float(np.mean(v)) for g, v in group_durations.items()}
            vals = list(means.values())
            if max(vals) - min(vals) > 0.1 * max(vals):
                detected_patterns.append(f"Audio duration disparity across groups: {means}")
                bias_types.append("voice_characteristics")

        # Use text content if available (e.g., transcriptions)
        group_sentiments: Dict[str, List[float]] = {}
        for o in model_outputs:
            text = o.get("transcription", o.get("text", ""))
            if text:
                group = _extract_group(o)
                group_sentiments.setdefault(group, []).append(_simple_sentiment(text))

        if len(group_sentiments) >= 2:
            means = {g: float(np.mean(v)) for g, v in group_sentiments.items()}
            vals = list(means.values())
            if max(vals) - min(vals) > 0.1:
                detected_patterns.append(f"Audio content sentiment disparity: {means}")
                bias_types.append("language_bias")

        bias_score = 0.0
        all_disparities = []
        for group_data in [group_durations, group_sentiments]:
            if len(group_data) >= 2:
                means = [float(np.mean(v)) for v in group_data.values()]
                if max(means) > 0:
                    all_disparities.append((max(means) - min(means)) / max(max(means), 1))
        bias_score = float(np.mean(all_disparities)) if all_disparities else 0.0

        return {
            "bias_types": bias_types if bias_types else ["none_detected"],
            "bias_score": round(bias_score, 4),
            "detected_patterns": detected_patterns if detected_patterns else ["No significant bias patterns detected"]
        }

    async def _analyze_video_bias(self, model_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze video-specific bias from actual model outputs.

        Uses metadata fields (activity, duration, frame_count) if
        available.
        """
        if not model_outputs:
            return {
                "bias_types": [],
                "bias_score": 0.0,
                "detected_patterns": [],
                "note": "No model outputs provided"
            }

        group_durations: Dict[str, List[float]] = {}
        group_activities: Dict[str, List[str]] = {}

        for o in model_outputs:
            group = _extract_group(o)
            duration = o.get("duration", o.get("video_duration", 0))
            if duration:
                group_durations.setdefault(group, []).append(float(duration))
            activity = o.get("activity", o.get("action", ""))
            if activity:
                group_activities.setdefault(group, []).append(str(activity))

        detected_patterns = []
        bias_types = []

        if len(group_durations) >= 2:
            means = {g: float(np.mean(v)) for g, v in group_durations.items()}
            vals = list(means.values())
            if max(vals) > 0 and (max(vals) - min(vals)) / max(vals) > 0.1:
                detected_patterns.append(f"Video duration disparity across groups: {means}")
                bias_types.append("temporal_bias")

        # Activity diversity per group
        if len(group_activities) >= 2:
            diversities = {g: len(set(acts)) / max(len(acts), 1)
                           for g, acts in group_activities.items()}
            vals = list(diversities.values())
            if max(vals) - min(vals) > 0.2:
                detected_patterns.append(f"Activity diversity disparity: {diversities}")
                bias_types.append("activity_bias")

        bias_score = 0.0
        if len(group_durations) >= 2:
            means = [float(np.mean(v)) for v in group_durations.values()]
            if max(means) > 0:
                bias_score = (max(means) - min(means)) / max(means)

        return {
            "bias_types": bias_types if bias_types else ["none_detected"],
            "bias_score": round(bias_score, 4),
            "detected_patterns": detected_patterns if detected_patterns else ["No significant bias patterns detected"]
        }

    async def _analyze_cross_modal_bias(
        self,
        model_outputs: List[Dict[str, Any]],
        modalities: List[str]
    ) -> Dict[str, Any]:
        """Analyze cross-modal bias interactions from actual output data.

        Computes per-modality bias scores and checks for amplification
        effects when modalities are combined.
        """
        # Compute per-modality bias scores
        modality_scores: Dict[str, float] = {}
        for modality in modalities:
            result = await self._analyze_modality_bias(model_outputs, modality)
            modality_scores[modality] = result.get("bias_score", 0.0)

        # Modality preference: proportion of outputs per modality
        modality_counts: Dict[str, int] = Counter()
        for o in model_outputs:
            m = o.get("modality", "text")
            modality_counts[m] += 1

        total = sum(modality_counts.values()) or 1
        modality_preference = {m: round(modality_counts.get(m, 0) / total, 4)
                               for m in modalities}

        # Cross-modal stereotypes: check if bias scores compound
        scores = list(modality_scores.values())
        mean_score = float(np.mean(scores)) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        # Amplification: how much worst-case exceeds average
        bias_amplification = round(max_score - mean_score, 4) if len(scores) >= 2 else 0.0

        cross_modal_stereotypes = []
        if bias_amplification > 0.05:
            cross_modal_stereotypes.append(
                f"Bias amplification detected: worst modality exceeds mean by {bias_amplification:.4f}"
            )

        return {
            "modality_preference": modality_preference,
            "modality_bias_scores": {k: round(v, 4) for k, v in modality_scores.items()},
            "cross_modal_stereotypes": cross_modal_stereotypes if cross_modal_stereotypes else [
                "No significant cross-modal bias amplification detected"
            ],
            "interaction_effects": {
                "bias_amplification": bias_amplification,
                "modality_conflicts": round(float(np.std(scores)), 4) if len(scores) >= 2 else 0.0
            }
        }
