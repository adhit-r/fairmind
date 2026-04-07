"""
Multimodal Bias Detection Service
Implements bias detection for image, audio, and video generation models
Based on 2025 analysis of explainability and bias detection in generative AI
"""

import asyncio
import json
import logging
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from scipy import stats

logger = logging.getLogger(__name__)

class ModalityType(Enum):
    """Supported modality types"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class MultimodalBiasType(Enum):
    """Multimodal-specific bias types"""
    DEMOGRAPHIC_REPRESENTATION = "demographic_representation"
    OBJECT_DETECTION_BIAS = "object_detection_bias"
    SCENE_BIAS = "scene_bias"
    VOICE_CHARACTERISTICS = "voice_characteristics"
    ACCENT_BIAS = "accent_bias"
    LANGUAGE_BIAS = "language_bias"
    MOTION_BIAS = "motion_bias"
    ACTIVITY_BIAS = "activity_bias"
    TEMPORAL_BIAS = "temporal_bias"
    CROSS_MODAL_STEREOTYPES = "cross_modal_stereotypes"
    MODALITY_PREFERENCE = "modality_preference"

@dataclass
class MultimodalBiasResult:
    """Result from multimodal bias detection"""
    modality: ModalityType
    bias_type: MultimodalBiasType
    bias_score: float
    confidence: float
    is_biased: bool
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: str

# Bias score threshold for flagging bias
_BIAS_THRESHOLD = 0.15

# Minimum number of outputs required for meaningful statistical analysis
_MIN_SAMPLE_SIZE = 5


def _insufficient_data_result(
    modality: ModalityType,
    bias_type: MultimodalBiasType,
    reason: str,
) -> MultimodalBiasResult:
    """Return a zero-score result when model outputs lack required fields."""
    return MultimodalBiasResult(
        modality=modality,
        bias_type=bias_type,
        bias_score=0.0,
        confidence=0.0,
        is_biased=False,
        details={"insufficient_data": True, "reason": reason},
        recommendations=["Provide model outputs with the required metadata fields for analysis"],
        timestamp=datetime.now().isoformat(),
    )


def _extract_demographic_field(
    outputs: List[Dict[str, Any]], field: str
) -> Dict[str, List[Dict[str, Any]]]:
    """Group model outputs by a demographic field value.

    Returns a dict mapping each demographic label to the list of outputs
    that contain that label.
    """
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for output in outputs:
        value = output.get(field) or output.get("demographics", {}).get(field)
        if value is not None:
            groups[str(value)].append(output)
    return dict(groups)


def _compute_representation_ratios(
    observed_counts: Dict[str, int], total: int
) -> Dict[str, float]:
    """Compute observed proportions for each group."""
    if total == 0:
        return {}
    return {group: count / total for group, count in observed_counts.items()}


def _chi_squared_uniformity(observed_counts: Dict[str, int]) -> Tuple[float, float]:
    """Run a chi-squared goodness-of-fit test against uniform distribution.

    Returns (statistic, p_value).
    """
    counts = list(observed_counts.values())
    if len(counts) < 2:
        return 0.0, 1.0
    total = sum(counts)
    expected = [total / len(counts)] * len(counts)
    stat, p_value = stats.chisquare(counts, f_exp=expected)
    return float(stat), float(p_value)


class MultimodalBiasDetectionService:
    """
    Multimodal bias detection service for generative AI models
    """

    def __init__(self):
        self.bias_detectors = self._initialize_bias_detectors()
        self.cross_modal_analyzers = self._initialize_cross_modal_analyzers()

    def _initialize_bias_detectors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize modality-specific bias detectors"""
        return {
            "image": {
                "demographic_detector": {
                    "enabled": True,
                    "description": "Detect demographic representation bias in generated images",
                    "methods": ["face_analysis", "demographic_classification", "representation_analysis"]
                },
                "object_detector": {
                    "enabled": True,
                    "description": "Detect object detection and scene bias",
                    "methods": ["object_detection", "scene_analysis", "context_bias"]
                },
                "style_detector": {
                    "enabled": True,
                    "description": "Detect style and aesthetic bias",
                    "methods": ["style_analysis", "aesthetic_bias", "cultural_bias"]
                }
            },
            "audio": {
                "voice_detector": {
                    "enabled": True,
                    "description": "Detect voice characteristic bias",
                    "methods": ["voice_analysis", "pitch_analysis", "timbre_analysis"]
                },
                "accent_detector": {
                    "enabled": True,
                    "description": "Detect accent and language bias",
                    "methods": ["accent_classification", "language_detection", "pronunciation_analysis"]
                },
                "content_detector": {
                    "enabled": True,
                    "description": "Detect content and semantic bias",
                    "methods": ["content_analysis", "semantic_bias", "topic_bias"]
                }
            },
            "video": {
                "motion_detector": {
                    "enabled": True,
                    "description": "Detect motion and activity bias",
                    "methods": ["motion_analysis", "activity_recognition", "gesture_analysis"]
                },
                "temporal_detector": {
                    "enabled": True,
                    "description": "Detect temporal and sequence bias",
                    "methods": ["temporal_analysis", "sequence_bias", "narrative_bias"]
                },
                "scene_detector": {
                    "enabled": True,
                    "description": "Detect scene and environment bias",
                    "methods": ["scene_analysis", "environment_bias", "setting_bias"]
                }
            }
        }

    def _initialize_cross_modal_analyzers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cross-modal bias analyzers"""
        return {
            "text_image": {
                "enabled": True,
                "description": "Analyze bias between text prompts and generated images",
                "methods": ["prompt_image_alignment", "semantic_consistency", "stereotype_amplification"]
            },
            "text_audio": {
                "enabled": True,
                "description": "Analyze bias between text and audio generation",
                "methods": ["text_audio_alignment", "voice_assignment_bias", "content_consistency"]
            },
            "image_audio": {
                "enabled": True,
                "description": "Analyze bias between image and audio synchronization",
                "methods": ["visual_audio_sync", "multimodal_consistency", "cross_modal_stereotypes"]
            },
            "text_video": {
                "enabled": True,
                "description": "Analyze bias between text prompts and video generation",
                "methods": ["prompt_video_alignment", "temporal_consistency", "narrative_bias"]
            }
        }

    async def detect_image_generation_bias(
        self,
        model_outputs: List[Dict[str, Any]],
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> List[MultimodalBiasResult]:
        """
        Detect bias in image generation models

        Implements techniques from the analysis:
        - Demographic representation analysis
        - Object detection bias
        - Scene and context bias
        - Style and aesthetic bias
        """
        try:
            results = []
            config = analysis_config or {}

            # Demographic representation bias
            if self.bias_detectors["image"]["demographic_detector"]["enabled"]:
                demographic_result = await self._analyze_demographic_representation(model_outputs)
                results.append(demographic_result)

            # Object detection bias
            if self.bias_detectors["image"]["object_detector"]["enabled"]:
                object_result = await self._analyze_object_detection_bias(model_outputs)
                results.append(object_result)

            # Scene bias
            if self.bias_detectors["image"]["style_detector"]["enabled"]:
                scene_result = await self._analyze_scene_bias(model_outputs)
                results.append(scene_result)

            return results

        except Exception as e:
            logger.error(f"Error in image generation bias detection: {e}")
            raise

    async def detect_audio_generation_bias(
        self,
        model_outputs: List[Dict[str, Any]],
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> List[MultimodalBiasResult]:
        """
        Detect bias in audio generation models

        Implements techniques from the analysis:
        - Voice characteristic bias
        - Accent and language bias
        - Content and semantic bias
        """
        try:
            results = []
            config = analysis_config or {}

            # Voice characteristics bias
            if self.bias_detectors["audio"]["voice_detector"]["enabled"]:
                voice_result = await self._analyze_voice_characteristics(model_outputs)
                results.append(voice_result)

            # Accent bias
            if self.bias_detectors["audio"]["accent_detector"]["enabled"]:
                accent_result = await self._analyze_accent_bias(model_outputs)
                results.append(accent_result)

            # Content bias
            if self.bias_detectors["audio"]["content_detector"]["enabled"]:
                content_result = await self._analyze_audio_content_bias(model_outputs)
                results.append(content_result)

            return results

        except Exception as e:
            logger.error(f"Error in audio generation bias detection: {e}")
            raise

    async def detect_video_generation_bias(
        self,
        model_outputs: List[Dict[str, Any]],
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> List[MultimodalBiasResult]:
        """
        Detect bias in video generation models

        Implements techniques from the analysis:
        - Motion and activity bias
        - Temporal and sequence bias
        - Scene and environment bias
        """
        try:
            results = []
            config = analysis_config or {}

            # Motion bias
            if self.bias_detectors["video"]["motion_detector"]["enabled"]:
                motion_result = await self._analyze_motion_bias(model_outputs)
                results.append(motion_result)

            # Temporal bias
            if self.bias_detectors["video"]["temporal_detector"]["enabled"]:
                temporal_result = await self._analyze_temporal_bias(model_outputs)
                results.append(temporal_result)

            # Scene bias
            if self.bias_detectors["video"]["scene_detector"]["enabled"]:
                scene_result = await self._analyze_video_scene_bias(model_outputs)
                results.append(scene_result)

            return results

        except Exception as e:
            logger.error(f"Error in video generation bias detection: {e}")
            raise

    async def detect_cross_modal_bias(
        self,
        model_outputs: List[Dict[str, Any]],
        modalities: List[ModalityType],
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> List[MultimodalBiasResult]:
        """
        Detect cross-modal bias interactions

        Implements cross-modal bias analysis from the analysis:
        - Modality preference analysis
        - Cross-modal stereotype detection
        - Interaction effect analysis
        """
        try:
            results = []
            config = analysis_config or {}

            # Analyze cross-modal interactions
            for i, modality_a in enumerate(modalities):
                for modality_b in modalities[i+1:]:
                    cross_modal_key = f"{modality_a.value}_{modality_b.value}"
                    if cross_modal_key in self.cross_modal_analyzers:
                        analyzer = self.cross_modal_analyzers[cross_modal_key]
                        if analyzer["enabled"]:
                            cross_modal_result = await self._analyze_cross_modal_interaction(
                                model_outputs, modality_a, modality_b, analyzer
                            )
                            results.append(cross_modal_result)

            return results

        except Exception as e:
            logger.error(f"Error in cross-modal bias detection: {e}")
            raise

    # ------------------------------------------------------------------
    # Image bias analysis methods
    # ------------------------------------------------------------------

    async def _analyze_demographic_representation(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze demographic representation in generated images.

        Expects each model output to contain demographic labels such as:
          - "gender", "race", "age" (top-level or nested under "demographics")

        Computes representation ratios and runs a chi-squared goodness-of-fit
        test against a uniform distribution for each demographic dimension.
        """
        demographic_fields = ["gender", "race", "age"]
        dimension_results: Dict[str, Any] = {}
        max_bias_score = 0.0
        total_p_values: List[float] = []
        representation_gaps: List[str] = []

        has_any_data = False

        for field in demographic_fields:
            groups = _extract_demographic_field(model_outputs, field)
            if not groups:
                continue
            has_any_data = True

            counts = {g: len(items) for g, items in groups.items()}
            total = sum(counts.values())
            ratios = _compute_representation_ratios(counts, total)
            dimension_results[field] = ratios

            if total < _MIN_SAMPLE_SIZE or len(counts) < 2:
                continue

            chi2_stat, p_value = _chi_squared_uniformity(counts)
            total_p_values.append(p_value)

            # Bias score: normalized chi-squared effect size (Cramer's V approximation)
            k = len(counts)
            cramers_v = float(np.sqrt(chi2_stat / (total * max(k - 1, 1))))
            max_bias_score = max(max_bias_score, min(cramers_v, 1.0))

            if p_value < 0.05:
                # Identify under-represented groups
                expected_ratio = 1.0 / k
                for group, ratio in ratios.items():
                    if ratio < expected_ratio * 0.5:
                        representation_gaps.append(
                            f"Under-representation of '{group}' in {field} "
                            f"({ratio:.1%} vs expected {expected_ratio:.1%})"
                        )

        if not has_any_data:
            return _insufficient_data_result(
                ModalityType.IMAGE,
                MultimodalBiasType.DEMOGRAPHIC_REPRESENTATION,
                "No demographic labels (gender, race, age) found in model outputs",
            )

        # Confidence based on sample size and number of dimensions analyzed
        n = len(model_outputs)
        confidence = min(1.0, n / 100) * (len(dimension_results) / len(demographic_fields))

        bias_score = float(max_bias_score)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Increase diversity in training data to address representation gaps")
            recommendations.append("Implement demographic balancing in generation pipeline")
        if representation_gaps:
            recommendations.append("Use FairFace or similar tools for ongoing demographic analysis")
        if not recommendations:
            recommendations.append("Continue monitoring demographic representation across outputs")

        return MultimodalBiasResult(
            modality=ModalityType.IMAGE,
            bias_type=MultimodalBiasType.DEMOGRAPHIC_REPRESENTATION,
            bias_score=bias_score,
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "demographic_breakdown": dimension_results,
                "representation_gaps": representation_gaps,
                "sample_size": n,
                "chi_squared_p_values": {
                    field: round(p, 6) for field, p in zip(
                        [f for f in demographic_fields if f in dimension_results],
                        total_p_values,
                    )
                },
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    async def _analyze_object_detection_bias(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze object-demographic co-occurrence patterns in generated images.

        Expects each model output to contain:
          - "objects": list of detected/generated object labels
          - a demographic field (e.g. "gender") at top level or under "demographics"

        Builds a contingency table of object x demographic group and computes
        chi-squared tests for independence to detect stereotypical associations.
        """
        # Build co-occurrence matrix
        demographic_field = "gender"  # primary axis; extend as needed
        co_occurrences: Dict[str, Counter] = defaultdict(Counter)
        total_pairs = 0

        for output in model_outputs:
            objects = output.get("objects", [])
            if not objects:
                continue
            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )
            if demo_value is None:
                continue
            demo_value = str(demo_value)
            for obj in objects:
                obj_label = str(obj) if isinstance(obj, str) else str(obj.get("label", obj.get("name", "")))
                if obj_label:
                    co_occurrences[obj_label][demo_value] += 1
                    total_pairs += 1

        if total_pairs == 0 or not co_occurrences:
            return _insufficient_data_result(
                ModalityType.IMAGE,
                MultimodalBiasType.OBJECT_DETECTION_BIAS,
                "No object-demographic co-occurrence data found in model outputs. "
                "Expected 'objects' list and demographic labels.",
            )

        # All demographic groups across all objects
        all_groups = sorted({g for counts in co_occurrences.values() for g in counts})
        if len(all_groups) < 2:
            return _insufficient_data_result(
                ModalityType.IMAGE,
                MultimodalBiasType.OBJECT_DETECTION_BIAS,
                "Only one demographic group found; need at least two for comparison.",
            )

        # Build contingency table and test each object
        object_associations: Dict[str, Dict[str, float]] = {}
        stereotypical_associations: List[str] = []
        max_cramers_v = 0.0

        # Overall contingency table across all objects
        all_objects = sorted(co_occurrences.keys())
        contingency = []
        for obj in all_objects:
            row = [co_occurrences[obj].get(g, 0) for g in all_groups]
            contingency.append(row)
            row_total = sum(row)
            if row_total > 0:
                object_associations[obj] = {
                    g: round(co_occurrences[obj].get(g, 0) / row_total, 4)
                    for g in all_groups
                }

        contingency_arr = np.array(contingency)
        if contingency_arr.shape[0] >= 2 and contingency_arr.shape[1] >= 2:
            chi2_stat, p_value, dof, _ = stats.chi2_contingency(contingency_arr)
            n_total = contingency_arr.sum()
            k = min(contingency_arr.shape)
            cramers_v = float(np.sqrt(chi2_stat / (n_total * max(k - 1, 1)))) if n_total > 0 else 0.0
            max_cramers_v = min(cramers_v, 1.0)

            if p_value < 0.05:
                # Find which objects show the strongest skew
                for obj, assoc in object_associations.items():
                    values = list(assoc.values())
                    if max(values) > 0.7:
                        dominant = max(assoc, key=assoc.get)
                        stereotypical_associations.append(
                            f"'{obj}' predominantly associated with {demographic_field}='{dominant}' "
                            f"({assoc[dominant]:.0%})"
                        )
        else:
            p_value = 1.0

        bias_score = float(max_cramers_v)
        confidence = min(1.0, total_pairs / 200)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Balance object-person associations in training data")
            recommendations.append("Use CLIP-based analysis for semantic bias monitoring")
        if stereotypical_associations:
            recommendations.append("Review flagged object-demographic associations for stereotypes")
        if not recommendations:
            recommendations.append("Continue monitoring object detection bias patterns")

        return MultimodalBiasResult(
            modality=ModalityType.IMAGE,
            bias_type=MultimodalBiasType.OBJECT_DETECTION_BIAS,
            bias_score=bias_score,
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "object_associations": object_associations,
                "stereotypical_associations": stereotypical_associations,
                "chi_squared_p_value": round(float(p_value), 6),
                "cramers_v": round(max_cramers_v, 4),
                "total_co_occurrences": total_pairs,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    async def _analyze_scene_bias(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze scene-demographic associations in generated images.

        Expects each model output to contain:
          - "scene" or "scene_type": the scene/context label
          - demographic fields at top level or under "demographics"

        Computes scene distribution across demographic groups and tests for
        association using chi-squared test of independence.
        """
        demographic_field = "gender"
        scene_demo_counts: Dict[str, Counter] = defaultdict(Counter)
        scene_counts: Counter = Counter()
        total = 0

        for output in model_outputs:
            scene = output.get("scene") or output.get("scene_type") or output.get("context")
            if scene is None:
                continue
            scene = str(scene)
            scene_counts[scene] += 1
            total += 1

            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )
            if demo_value is not None:
                scene_demo_counts[scene][str(demo_value)] += 1

        if total == 0:
            return _insufficient_data_result(
                ModalityType.IMAGE,
                MultimodalBiasType.SCENE_BIAS,
                "No scene labels found in model outputs. "
                "Expected 'scene', 'scene_type', or 'context' field.",
            )

        # Scene distribution
        scene_distribution = {s: round(c / total, 4) for s, c in scene_counts.items()}

        # Test scene-demographic association if we have demographic data
        all_groups = sorted({g for counts in scene_demo_counts.values() for g in counts})
        cultural_bias: List[str] = []
        bias_score = 0.0
        p_value = 1.0

        if len(scene_demo_counts) >= 2 and len(all_groups) >= 2:
            scenes_sorted = sorted(scene_demo_counts.keys())
            contingency = []
            for scene in scenes_sorted:
                row = [scene_demo_counts[scene].get(g, 0) for g in all_groups]
                contingency.append(row)

            contingency_arr = np.array(contingency)
            if contingency_arr.sum() >= _MIN_SAMPLE_SIZE:
                chi2_stat, p_value, dof, _ = stats.chi2_contingency(contingency_arr)
                n_total = contingency_arr.sum()
                k = min(contingency_arr.shape)
                cramers_v = float(np.sqrt(chi2_stat / (n_total * max(k - 1, 1)))) if n_total > 0 else 0.0
                bias_score = min(cramers_v, 1.0)

                if p_value < 0.05:
                    for scene in scenes_sorted:
                        row_total = sum(scene_demo_counts[scene].values())
                        if row_total > 0:
                            for g in all_groups:
                                ratio = scene_demo_counts[scene].get(g, 0) / row_total
                                if ratio > 0.75:
                                    cultural_bias.append(
                                        f"Scene '{scene}' strongly associated with "
                                        f"{demographic_field}='{g}' ({ratio:.0%})"
                                    )
        else:
            # No demographic cross-tabulation possible; test scene uniformity
            chi2_stat_scene, p_val_scene = _chi_squared_uniformity(dict(scene_counts))
            k = len(scene_counts)
            if total > 0 and k > 1:
                cramers_v = float(np.sqrt(chi2_stat_scene / (total * max(k - 1, 1))))
                bias_score = min(cramers_v, 1.0)
                p_value = p_val_scene

        confidence = min(1.0, total / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Increase cultural and contextual diversity in training data")
            recommendations.append("Implement scene balance monitoring")
        if cultural_bias:
            recommendations.append("Review flagged scene-demographic associations")
        if not recommendations:
            recommendations.append("Continue monitoring scene distribution across outputs")

        return MultimodalBiasResult(
            modality=ModalityType.IMAGE,
            bias_type=MultimodalBiasType.SCENE_BIAS,
            bias_score=float(bias_score),
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "scene_distribution": scene_distribution,
                "cultural_bias": cultural_bias,
                "chi_squared_p_value": round(float(p_value), 6),
                "sample_size": total,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------
    # Audio bias analysis methods
    # ------------------------------------------------------------------

    async def _analyze_voice_characteristics(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze voice characteristic bias in generated audio.

        Expects each model output to contain:
          - numeric voice features: "pitch", "timbre" (or nested under "voice")
          - a demographic field (e.g. "gender") at top level or under "demographics"

        Computes per-group distributions of pitch/timbre and runs
        Kolmogorov-Smirnov tests between group pairs to detect distributional
        differences.
        """
        demographic_field = "gender"
        voice_features = ["pitch", "timbre"]

        # Collect per-group feature values
        group_features: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        total_with_data = 0

        for output in model_outputs:
            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )
            if demo_value is None:
                continue

            demo_value = str(demo_value)
            voice_data = output.get("voice", output)

            has_feature = False
            for feat in voice_features:
                val = voice_data.get(feat)
                if val is not None:
                    try:
                        group_features[demo_value][feat].append(float(val))
                        has_feature = True
                    except (TypeError, ValueError):
                        pass
            if has_feature:
                total_with_data += 1

        if total_with_data < _MIN_SAMPLE_SIZE or len(group_features) < 2:
            return _insufficient_data_result(
                ModalityType.AUDIO,
                MultimodalBiasType.VOICE_CHARACTERISTICS,
                "Insufficient voice characteristic data. Expected numeric 'pitch'/'timbre' "
                "fields and demographic labels in model outputs.",
            )

        # KS tests between all group pairs for each feature
        groups = sorted(group_features.keys())
        ks_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        max_bias_score = 0.0
        bias_patterns: List[str] = []

        for feat in voice_features:
            for i, g1 in enumerate(groups):
                for g2 in groups[i + 1:]:
                    vals1 = group_features[g1].get(feat, [])
                    vals2 = group_features[g2].get(feat, [])
                    if len(vals1) >= 2 and len(vals2) >= 2:
                        ks_stat, p_value = stats.ks_2samp(vals1, vals2)
                        ks_results[feat].append({
                            "groups": [g1, g2],
                            "ks_statistic": round(float(ks_stat), 4),
                            "p_value": round(float(p_value), 6),
                        })
                        max_bias_score = max(max_bias_score, float(ks_stat))
                        if p_value < 0.05:
                            mean1 = float(np.mean(vals1))
                            mean2 = float(np.mean(vals2))
                            bias_patterns.append(
                                f"Significant {feat} difference between {g1} "
                                f"(mean={mean1:.2f}) and {g2} (mean={mean2:.2f}), "
                                f"KS p={p_value:.4f}"
                            )

        # Voice characteristic summary per group
        voice_summary: Dict[str, Dict[str, Any]] = {}
        for group, feats in group_features.items():
            voice_summary[group] = {}
            for feat, vals in feats.items():
                if vals:
                    voice_summary[group][feat] = {
                        "mean": round(float(np.mean(vals)), 4),
                        "std": round(float(np.std(vals)), 4),
                        "count": len(vals),
                    }

        bias_score = min(float(max_bias_score), 1.0)
        confidence = min(1.0, total_with_data / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Balance voice characteristics across demographic contexts")
            recommendations.append("Implement demographic classifier probing for voice generation")
        if bias_patterns:
            recommendations.append("Review flagged distributional differences in voice features")
        if not recommendations:
            recommendations.append("Continue monitoring voice characteristic distributions")

        return MultimodalBiasResult(
            modality=ModalityType.AUDIO,
            bias_type=MultimodalBiasType.VOICE_CHARACTERISTICS,
            bias_score=bias_score,
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "voice_characteristics": voice_summary,
                "ks_test_results": dict(ks_results),
                "bias_patterns": bias_patterns,
                "sample_size": total_with_data,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    async def _analyze_accent_bias(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze accent classification accuracy/distribution across groups.

        Expects each model output to contain:
          - "accent" or "accent_label": the classified/generated accent
          - optionally "confidence_score" for classification confidence
          - a demographic field at top level or under "demographics"

        Tests whether accent distribution is uniform and whether accuracy
        varies across demographic groups.
        """
        accent_counts: Counter = Counter()
        group_accuracy: Dict[str, List[float]] = defaultdict(list)
        demographic_field = "gender"
        total = 0

        for output in model_outputs:
            accent = output.get("accent") or output.get("accent_label")
            if accent is None:
                continue
            accent = str(accent)
            accent_counts[accent] += 1
            total += 1

            # Track accuracy per demographic group if available
            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )
            conf = output.get("confidence_score") or output.get("accuracy")
            if demo_value is not None and conf is not None:
                try:
                    group_accuracy[str(demo_value)].append(float(conf))
                except (TypeError, ValueError):
                    pass

        if total == 0:
            return _insufficient_data_result(
                ModalityType.AUDIO,
                MultimodalBiasType.ACCENT_BIAS,
                "No accent labels found in model outputs. "
                "Expected 'accent' or 'accent_label' field.",
            )

        # Accent distribution
        accent_distribution = {a: round(c / total, 4) for a, c in accent_counts.items()}

        # Chi-squared test for accent uniformity
        chi2_stat, p_value = _chi_squared_uniformity(dict(accent_counts))
        k = len(accent_counts)
        bias_score_dist = 0.0
        if total > 0 and k > 1:
            bias_score_dist = float(np.sqrt(chi2_stat / (total * max(k - 1, 1))))

        # KS test for accuracy differences across demographic groups
        language_bias: List[str] = []
        accuracy_bias_score = 0.0
        accuracy_stats: Dict[str, Dict[str, float]] = {}

        groups = sorted(group_accuracy.keys())
        if len(groups) >= 2:
            for g in groups:
                vals = group_accuracy[g]
                if vals:
                    accuracy_stats[g] = {
                        "mean_accuracy": round(float(np.mean(vals)), 4),
                        "count": len(vals),
                    }

            for i, g1 in enumerate(groups):
                for g2 in groups[i + 1:]:
                    vals1 = group_accuracy[g1]
                    vals2 = group_accuracy[g2]
                    if len(vals1) >= 2 and len(vals2) >= 2:
                        ks_stat, ks_p = stats.ks_2samp(vals1, vals2)
                        accuracy_bias_score = max(accuracy_bias_score, float(ks_stat))
                        if ks_p < 0.05:
                            language_bias.append(
                                f"Accent accuracy differs between {g1} and {g2} "
                                f"(KS={ks_stat:.3f}, p={ks_p:.4f})"
                            )

        bias_score = min(max(bias_score_dist, accuracy_bias_score), 1.0)
        confidence = min(1.0, total / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        if p_value < 0.05 and not language_bias:
            dominant = max(accent_distribution, key=accent_distribution.get)
            language_bias.append(
                f"Non-uniform accent distribution; '{dominant}' dominates at "
                f"{accent_distribution[dominant]:.0%}"
            )

        recommendations = []
        if is_biased:
            recommendations.append("Increase linguistic diversity in training data")
            recommendations.append("Implement accent balance monitoring")
        if language_bias:
            recommendations.append("Review flagged accent distribution imbalances")
        if not recommendations:
            recommendations.append("Continue monitoring accent distribution across outputs")

        return MultimodalBiasResult(
            modality=ModalityType.AUDIO,
            bias_type=MultimodalBiasType.ACCENT_BIAS,
            bias_score=float(bias_score),
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "accent_distribution": accent_distribution,
                "language_bias": language_bias,
                "chi_squared_p_value": round(float(p_value), 6),
                "accuracy_by_group": accuracy_stats,
                "sample_size": total,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    async def _analyze_audio_content_bias(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze content topic distribution across demographic groups in audio.

        Expects each model output to contain:
          - "topic" or "content_topic": the content topic label
          - optionally "sentiment": sentiment label (positive/negative/neutral)
          - a demographic field at top level or under "demographics"

        Tests whether topic and sentiment distributions differ across
        demographic groups using chi-squared tests.
        """
        demographic_field = "gender"
        topic_demo_counts: Dict[str, Counter] = defaultdict(Counter)
        topic_counts: Counter = Counter()
        sentiment_demo_counts: Dict[str, Counter] = defaultdict(Counter)
        sentiment_counts: Counter = Counter()
        total = 0

        for output in model_outputs:
            topic = output.get("topic") or output.get("content_topic")
            sentiment = output.get("sentiment")
            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )

            if topic is not None:
                topic = str(topic)
                topic_counts[topic] += 1
                total += 1
                if demo_value is not None:
                    topic_demo_counts[topic][str(demo_value)] += 1

            if sentiment is not None:
                sentiment = str(sentiment)
                sentiment_counts[sentiment] += 1
                if demo_value is not None:
                    sentiment_demo_counts[sentiment][str(demo_value)] += 1

        if total == 0:
            return _insufficient_data_result(
                ModalityType.AUDIO,
                MultimodalBiasType.LANGUAGE_BIAS,
                "No content topic labels found in model outputs. "
                "Expected 'topic' or 'content_topic' field.",
            )

        # Topic distribution
        topic_distribution = {t: round(c / total, 4) for t, c in topic_counts.items()}
        sentiment_total = sum(sentiment_counts.values())
        sentiment_distribution = (
            {s: round(c / sentiment_total, 4) for s, c in sentiment_counts.items()}
            if sentiment_total > 0
            else {}
        )

        # Test topic-demographic association
        all_groups = sorted({g for counts in topic_demo_counts.values() for g in counts})
        semantic_bias: List[str] = []
        bias_score = 0.0
        p_value = 1.0

        if len(topic_demo_counts) >= 2 and len(all_groups) >= 2:
            topics_sorted = sorted(topic_demo_counts.keys())
            contingency = []
            for topic in topics_sorted:
                row = [topic_demo_counts[topic].get(g, 0) for g in all_groups]
                contingency.append(row)

            contingency_arr = np.array(contingency)
            if contingency_arr.sum() >= _MIN_SAMPLE_SIZE:
                chi2_stat, p_value, dof, _ = stats.chi2_contingency(contingency_arr)
                n_total = contingency_arr.sum()
                k = min(contingency_arr.shape)
                cramers_v = float(np.sqrt(chi2_stat / (n_total * max(k - 1, 1)))) if n_total > 0 else 0.0
                bias_score = min(cramers_v, 1.0)

                if p_value < 0.05:
                    for topic in topics_sorted:
                        row_total = sum(topic_demo_counts[topic].values())
                        if row_total > 0:
                            for g in all_groups:
                                ratio = topic_demo_counts[topic].get(g, 0) / row_total
                                if ratio > 0.75:
                                    semantic_bias.append(
                                        f"Topic '{topic}' strongly associated with "
                                        f"{demographic_field}='{g}' ({ratio:.0%})"
                                    )

        # Also check sentiment-demographic association
        sentiment_groups = sorted({g for counts in sentiment_demo_counts.values() for g in counts})
        if len(sentiment_demo_counts) >= 2 and len(sentiment_groups) >= 2:
            sentiments_sorted = sorted(sentiment_demo_counts.keys())
            sent_contingency = []
            for sent in sentiments_sorted:
                row = [sentiment_demo_counts[sent].get(g, 0) for g in sentiment_groups]
                sent_contingency.append(row)

            sent_arr = np.array(sent_contingency)
            if sent_arr.sum() >= _MIN_SAMPLE_SIZE:
                sent_chi2, sent_p, _, _ = stats.chi2_contingency(sent_arr)
                n_sent = sent_arr.sum()
                k_sent = min(sent_arr.shape)
                sent_cramers = float(np.sqrt(sent_chi2 / (n_sent * max(k_sent - 1, 1)))) if n_sent > 0 else 0.0
                bias_score = max(bias_score, min(sent_cramers, 1.0))
                if sent_p < 0.05:
                    semantic_bias.append("Sentiment distribution differs across demographic groups")

        confidence = min(1.0, total / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Balance content topics across demographic groups")
            recommendations.append("Implement semantic bias monitoring for audio generation")
        if semantic_bias:
            recommendations.append("Review flagged topic-demographic and sentiment associations")
        if not recommendations:
            recommendations.append("Continue monitoring content distribution across outputs")

        return MultimodalBiasResult(
            modality=ModalityType.AUDIO,
            bias_type=MultimodalBiasType.LANGUAGE_BIAS,
            bias_score=float(bias_score),
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "content_analysis": {
                    "topics": topic_distribution,
                    "sentiment": sentiment_distribution,
                },
                "semantic_bias": semantic_bias,
                "chi_squared_p_value": round(float(p_value), 6),
                "sample_size": total,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------
    # Video bias analysis methods
    # ------------------------------------------------------------------

    async def _analyze_motion_bias(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze activity/motion patterns across demographic groups in video.

        Expects each model output to contain:
          - "activity" or "motion_type": the activity/motion label
          - a demographic field at top level or under "demographics"

        Builds activity x demographic contingency tables and tests for
        association bias using chi-squared test of independence.
        """
        demographic_field = "gender"
        activity_demo_counts: Dict[str, Counter] = defaultdict(Counter)
        activity_counts: Counter = Counter()
        total = 0

        for output in model_outputs:
            activity = output.get("activity") or output.get("motion_type") or output.get("action")
            if activity is None:
                continue
            activity = str(activity)
            activity_counts[activity] += 1
            total += 1

            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )
            if demo_value is not None:
                activity_demo_counts[activity][str(demo_value)] += 1

        if total == 0:
            return _insufficient_data_result(
                ModalityType.VIDEO,
                MultimodalBiasType.MOTION_BIAS,
                "No activity/motion labels found in model outputs. "
                "Expected 'activity', 'motion_type', or 'action' field.",
            )

        # Activity distribution per demographic group
        all_groups = sorted({g for counts in activity_demo_counts.values() for g in counts})
        activity_distribution: Dict[str, Dict[str, float]] = {}
        motion_patterns: List[str] = []
        bias_score = 0.0
        p_value = 1.0

        for activity in sorted(activity_demo_counts.keys()):
            row_total = sum(activity_demo_counts[activity].values())
            if row_total > 0:
                activity_distribution[activity] = {
                    g: round(activity_demo_counts[activity].get(g, 0) / row_total, 4)
                    for g in all_groups
                }

        if len(activity_demo_counts) >= 2 and len(all_groups) >= 2:
            activities_sorted = sorted(activity_demo_counts.keys())
            contingency = []
            for activity in activities_sorted:
                row = [activity_demo_counts[activity].get(g, 0) for g in all_groups]
                contingency.append(row)

            contingency_arr = np.array(contingency)
            if contingency_arr.sum() >= _MIN_SAMPLE_SIZE:
                chi2_stat, p_value, dof, _ = stats.chi2_contingency(contingency_arr)
                n_total = contingency_arr.sum()
                k = min(contingency_arr.shape)
                cramers_v = float(np.sqrt(chi2_stat / (n_total * max(k - 1, 1)))) if n_total > 0 else 0.0
                bias_score = min(cramers_v, 1.0)

                if p_value < 0.05:
                    for activity, assoc in activity_distribution.items():
                        values = list(assoc.values())
                        if values and max(values) > 0.75:
                            dominant = max(assoc, key=assoc.get)
                            motion_patterns.append(
                                f"Activity '{activity}' predominantly associated with "
                                f"{demographic_field}='{dominant}' ({assoc[dominant]:.0%})"
                            )
        else:
            # Fall back to uniformity test on activity distribution
            chi2_stat_act, p_val_act = _chi_squared_uniformity(dict(activity_counts))
            k = len(activity_counts)
            if total > 0 and k > 1:
                cramers_v = float(np.sqrt(chi2_stat_act / (total * max(k - 1, 1))))
                bias_score = min(cramers_v, 1.0)
                p_value = p_val_act

        confidence = min(1.0, total / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Balance activities across demographic groups in training data")
            recommendations.append("Use pose estimation for ongoing bias detection")
        if motion_patterns:
            recommendations.append("Review flagged activity-demographic stereotypical patterns")
        if not recommendations:
            recommendations.append("Continue monitoring activity distribution across outputs")

        return MultimodalBiasResult(
            modality=ModalityType.VIDEO,
            bias_type=MultimodalBiasType.MOTION_BIAS,
            bias_score=float(bias_score),
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "activity_distribution": activity_distribution,
                "motion_patterns": motion_patterns,
                "chi_squared_p_value": round(float(p_value), 6),
                "sample_size": total,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    async def _analyze_temporal_bias(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze temporal and sequence bias in generated videos.

        Expects each model output to contain:
          - "temporal_position" or "sequence_order": numeric position in sequence
          - a demographic field at top level or under "demographics"
          - optionally "narrative_role": the role in the narrative

        Tests whether demographic groups are unevenly distributed across
        temporal positions using KS tests.
        """
        demographic_field = "gender"
        group_positions: Dict[str, List[float]] = defaultdict(list)
        narrative_demo_counts: Dict[str, Counter] = defaultdict(Counter)
        total = 0

        for output in model_outputs:
            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )
            if demo_value is None:
                continue
            demo_value = str(demo_value)

            position = output.get("temporal_position") or output.get("sequence_order")
            if position is not None:
                try:
                    group_positions[demo_value].append(float(position))
                    total += 1
                except (TypeError, ValueError):
                    pass

            narrative_role = output.get("narrative_role")
            if narrative_role is not None:
                narrative_demo_counts[str(narrative_role)][demo_value] += 1

        if total < _MIN_SAMPLE_SIZE and not narrative_demo_counts:
            return _insufficient_data_result(
                ModalityType.VIDEO,
                MultimodalBiasType.TEMPORAL_BIAS,
                "Insufficient temporal/sequence data in model outputs. "
                "Expected 'temporal_position', 'sequence_order', or 'narrative_role' fields.",
            )

        bias_manifestations: List[str] = []
        max_bias_score = 0.0

        # KS test on temporal positions across groups
        temporal_stats: Dict[str, Dict[str, float]] = {}
        groups = sorted(group_positions.keys())
        ks_results: List[Dict[str, Any]] = []

        for g in groups:
            vals = group_positions[g]
            if vals:
                temporal_stats[g] = {
                    "mean_position": round(float(np.mean(vals)), 4),
                    "std_position": round(float(np.std(vals)), 4),
                    "count": len(vals),
                }

        for i, g1 in enumerate(groups):
            for g2 in groups[i + 1:]:
                vals1 = group_positions[g1]
                vals2 = group_positions[g2]
                if len(vals1) >= 2 and len(vals2) >= 2:
                    ks_stat, ks_p = stats.ks_2samp(vals1, vals2)
                    ks_results.append({
                        "groups": [g1, g2],
                        "ks_statistic": round(float(ks_stat), 4),
                        "p_value": round(float(ks_p), 6),
                    })
                    max_bias_score = max(max_bias_score, float(ks_stat))
                    if ks_p < 0.05:
                        bias_manifestations.append(
                            f"Temporal positioning differs between {g1} and {g2} "
                            f"(KS={ks_stat:.3f}, p={ks_p:.4f})"
                        )

        # Narrative role association test
        narrative_p_value = 1.0
        all_narrative_groups = sorted({g for counts in narrative_demo_counts.values() for g in counts})
        if len(narrative_demo_counts) >= 2 and len(all_narrative_groups) >= 2:
            roles_sorted = sorted(narrative_demo_counts.keys())
            contingency = []
            for role in roles_sorted:
                row = [narrative_demo_counts[role].get(g, 0) for g in all_narrative_groups]
                contingency.append(row)
            contingency_arr = np.array(contingency)
            if contingency_arr.sum() >= _MIN_SAMPLE_SIZE:
                chi2_stat, narrative_p_value, _, _ = stats.chi2_contingency(contingency_arr)
                n_total = contingency_arr.sum()
                k = min(contingency_arr.shape)
                cramers_v = float(np.sqrt(chi2_stat / (n_total * max(k - 1, 1)))) if n_total > 0 else 0.0
                max_bias_score = max(max_bias_score, min(cramers_v, 1.0))
                if narrative_p_value < 0.05:
                    bias_manifestations.append("Narrative roles unevenly distributed across demographic groups")

        bias_score = min(float(max_bias_score), 1.0)
        confidence = min(1.0, max(total, sum(sum(c.values()) for c in narrative_demo_counts.values())) / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Implement temporal consistency analysis across demographic groups")
            recommendations.append("Monitor narrative bias patterns in video generation")
        if bias_manifestations:
            recommendations.append("Review flagged temporal and narrative role biases")
        if not recommendations:
            recommendations.append("Continue monitoring temporal patterns across outputs")

        return MultimodalBiasResult(
            modality=ModalityType.VIDEO,
            bias_type=MultimodalBiasType.TEMPORAL_BIAS,
            bias_score=bias_score,
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "temporal_patterns": temporal_stats,
                "ks_test_results": ks_results,
                "narrative_role_p_value": round(float(narrative_p_value), 6),
                "bias_manifestations": bias_manifestations,
                "sample_size": total,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    async def _analyze_video_scene_bias(
        self,
        model_outputs: List[Dict[str, Any]]
    ) -> MultimodalBiasResult:
        """Analyze scene and environment bias in generated videos.

        Expects each model output to contain:
          - "environment" or "setting" or "scene": environment/setting label
          - a demographic field at top level or under "demographics"

        Tests for scene-demographic association using chi-squared test.
        """
        demographic_field = "gender"
        env_demo_counts: Dict[str, Counter] = defaultdict(Counter)
        env_counts: Counter = Counter()
        total = 0

        for output in model_outputs:
            env = (
                output.get("environment")
                or output.get("setting")
                or output.get("scene")
            )
            if env is None:
                continue
            env = str(env)
            env_counts[env] += 1
            total += 1

            demo_value = (
                output.get(demographic_field)
                or output.get("demographics", {}).get(demographic_field)
            )
            if demo_value is not None:
                env_demo_counts[env][str(demo_value)] += 1

        if total == 0:
            return _insufficient_data_result(
                ModalityType.VIDEO,
                MultimodalBiasType.SCENE_BIAS,
                "No environment/setting labels found in model outputs. "
                "Expected 'environment', 'setting', or 'scene' field.",
            )

        # Environment distribution
        env_distribution = {e: round(c / total, 4) for e, c in env_counts.items()}

        all_groups = sorted({g for counts in env_demo_counts.values() for g in counts})
        environmental_patterns: List[str] = []
        bias_score = 0.0
        p_value = 1.0

        if len(env_demo_counts) >= 2 and len(all_groups) >= 2:
            envs_sorted = sorted(env_demo_counts.keys())
            contingency = []
            for env in envs_sorted:
                row = [env_demo_counts[env].get(g, 0) for g in all_groups]
                contingency.append(row)

            contingency_arr = np.array(contingency)
            if contingency_arr.sum() >= _MIN_SAMPLE_SIZE:
                chi2_stat, p_value, dof, _ = stats.chi2_contingency(contingency_arr)
                n_total = contingency_arr.sum()
                k = min(contingency_arr.shape)
                cramers_v = float(np.sqrt(chi2_stat / (n_total * max(k - 1, 1)))) if n_total > 0 else 0.0
                bias_score = min(cramers_v, 1.0)

                if p_value < 0.05:
                    for env in envs_sorted:
                        row_total = sum(env_demo_counts[env].values())
                        if row_total > 0:
                            for g in all_groups:
                                ratio = env_demo_counts[env].get(g, 0) / row_total
                                if ratio > 0.75:
                                    environmental_patterns.append(
                                        f"Environment '{env}' strongly associated with "
                                        f"{demographic_field}='{g}' ({ratio:.0%})"
                                    )
        else:
            # Fall back to uniformity test
            chi2_stat_env, p_val_env = _chi_squared_uniformity(dict(env_counts))
            k = len(env_counts)
            if total > 0 and k > 1:
                cramers_v = float(np.sqrt(chi2_stat_env / (total * max(k - 1, 1))))
                bias_score = min(cramers_v, 1.0)
                p_value = p_val_env

        confidence = min(1.0, total / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Balance environmental representation across demographic groups")
            recommendations.append("Implement scene analysis for ongoing bias detection")
        if environmental_patterns:
            recommendations.append("Review flagged environment-demographic associations")
        if not recommendations:
            recommendations.append("Continue monitoring scene distribution across outputs")

        return MultimodalBiasResult(
            modality=ModalityType.VIDEO,
            bias_type=MultimodalBiasType.SCENE_BIAS,
            bias_score=float(bias_score),
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "scene_analysis": env_distribution,
                "environmental_patterns": environmental_patterns,
                "chi_squared_p_value": round(float(p_value), 6),
                "sample_size": total,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------
    # Cross-modal bias analysis
    # ------------------------------------------------------------------

    async def _analyze_cross_modal_interaction(
        self,
        model_outputs: List[Dict[str, Any]],
        modality_a: ModalityType,
        modality_b: ModalityType,
        analyzer: Dict[str, Any]
    ) -> MultimodalBiasResult:
        """Analyze cross-modal bias interactions.

        Expects each model output to contain per-modality bias scores or
        demographic labels, keyed by modality name. For example:
          - "image_demographic": "male", "audio_demographic": "female"
          - "image_bias_score": 0.3, "audio_bias_score": 0.1

        Checks consistency of demographic assignments across modalities and
        tests whether bias scores correlate across modalities.
        """
        key_a = modality_a.value
        key_b = modality_b.value

        # Strategy 1: Check demographic consistency across modalities
        consistent_count = 0
        inconsistent_count = 0
        demographic_field = "gender"

        for output in model_outputs:
            demo_a = (
                output.get(f"{key_a}_demographic")
                or output.get(f"{key_a}_{demographic_field}")
                or (output.get(key_a, {}) or {}).get(demographic_field)
            )
            demo_b = (
                output.get(f"{key_b}_demographic")
                or output.get(f"{key_b}_{demographic_field}")
                or (output.get(key_b, {}) or {}).get(demographic_field)
            )
            if demo_a is not None and demo_b is not None:
                if str(demo_a) == str(demo_b):
                    consistent_count += 1
                else:
                    inconsistent_count += 1

        total_consistency = consistent_count + inconsistent_count

        # Strategy 2: Correlate per-modality bias scores
        scores_a: List[float] = []
        scores_b: List[float] = []

        for output in model_outputs:
            sa = output.get(f"{key_a}_bias_score") or (output.get(key_a, {}) or {}).get("bias_score")
            sb = output.get(f"{key_b}_bias_score") or (output.get(key_b, {}) or {}).get("bias_score")
            if sa is not None and sb is not None:
                try:
                    scores_a.append(float(sa))
                    scores_b.append(float(sb))
                except (TypeError, ValueError):
                    pass

        if total_consistency == 0 and len(scores_a) < _MIN_SAMPLE_SIZE:
            return _insufficient_data_result(
                ModalityType.TEXT,
                MultimodalBiasType.CROSS_MODAL_STEREOTYPES,
                f"Insufficient cross-modal data between {key_a} and {key_b}. "
                f"Expected per-modality demographic labels or bias scores.",
            )

        interaction_effects: List[str] = []
        bias_score = 0.0
        correlation = 0.0
        consistency_ratio = 0.0

        # Consistency-based bias: if assignments are systematically inconsistent,
        # that itself indicates stereotypical cross-modal patterns
        if total_consistency >= _MIN_SAMPLE_SIZE:
            consistency_ratio = consistent_count / total_consistency
            # Deviation from 50/50 chance indicates association
            # Use binomial test: is the consistency ratio significantly different from 0.5?
            binom_p = float(
                stats.binomtest(consistent_count, total_consistency, 0.5).pvalue
            )
            # Bias score from consistency: how far from 0.5
            bias_score = abs(consistency_ratio - 0.5) * 2  # maps [0,0.5] deviation to [0,1]

            if binom_p < 0.05:
                if consistency_ratio > 0.5:
                    interaction_effects.append(
                        f"Cross-modal demographic assignments are significantly consistent "
                        f"between {key_a} and {key_b} ({consistency_ratio:.0%} match rate), "
                        f"suggesting stereotype reinforcement"
                    )
                else:
                    interaction_effects.append(
                        f"Cross-modal demographic assignments are significantly inconsistent "
                        f"between {key_a} and {key_b} ({consistency_ratio:.0%} match rate), "
                        f"suggesting systematic bias"
                    )

        # Correlation-based bias amplification
        stereotype_amplification = 0.0
        if len(scores_a) >= _MIN_SAMPLE_SIZE:
            corr, corr_p = stats.pearsonr(scores_a, scores_b)
            correlation = float(corr)
            stereotype_amplification = max(0.0, correlation)  # positive correlation = amplification

            if corr_p < 0.05 and correlation > 0.3:
                interaction_effects.append(
                    f"Bias scores positively correlated between {key_a} and {key_b} "
                    f"(r={correlation:.3f}, p={corr_p:.4f}), indicating bias amplification"
                )
                bias_score = max(bias_score, min(abs(correlation), 1.0))

        bias_score = min(float(bias_score), 1.0)
        data_points = max(total_consistency, len(scores_a))
        confidence = min(1.0, data_points / 100)
        is_biased = bias_score > _BIAS_THRESHOLD

        recommendations = []
        if is_biased:
            recommendations.append("Monitor cross-modal bias interactions for stereotype amplification")
            recommendations.append("Implement consistency testing across modalities")
        if interaction_effects:
            recommendations.append("Use interaction effect analysis to identify amplification sources")
        if not recommendations:
            recommendations.append("Continue monitoring cross-modal consistency")

        return MultimodalBiasResult(
            modality=ModalityType.TEXT,  # Cross-modal is not a single modality
            bias_type=MultimodalBiasType.CROSS_MODAL_STEREOTYPES,
            bias_score=bias_score,
            confidence=round(confidence, 4),
            is_biased=is_biased,
            details={
                "cross_modal_analysis": {
                    "modality_a": key_a,
                    "modality_b": key_b,
                    "interaction_strength": round(bias_score, 4),
                    "stereotype_amplification": round(stereotype_amplification, 4),
                    "consistency_ratio": round(consistency_ratio, 4) if total_consistency > 0 else None,
                    "correlation": round(correlation, 4) if len(scores_a) >= _MIN_SAMPLE_SIZE else None,
                },
                "interaction_effects": interaction_effects,
                "data_points": data_points,
            },
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
        )

    async def comprehensive_multimodal_analysis(
        self,
        model_outputs: List[Dict[str, Any]],
        modalities: List[ModalityType],
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive multimodal bias analysis

        Combines individual modality analysis with cross-modal analysis
        """
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "modalities": [mod.value for mod in modalities],
                "individual_modality_results": {},
                "cross_modal_results": [],
                "overall_assessment": {},
                "recommendations": []
            }

            # Analyze each modality individually
            for modality in modalities:
                if modality == ModalityType.IMAGE:
                    modality_results = await self.detect_image_generation_bias(
                        model_outputs, analysis_config
                    )
                elif modality == ModalityType.AUDIO:
                    modality_results = await self.detect_audio_generation_bias(
                        model_outputs, analysis_config
                    )
                elif modality == ModalityType.VIDEO:
                    modality_results = await self.detect_video_generation_bias(
                        model_outputs, analysis_config
                    )
                else:
                    continue

                results["individual_modality_results"][modality.value] = [
                    asdict(result) for result in modality_results
                ]

            # Analyze cross-modal interactions
            if len(modalities) > 1:
                cross_modal_results = await self.detect_cross_modal_bias(
                    model_outputs, modalities, analysis_config
                )
                results["cross_modal_results"] = [
                    asdict(result) for result in cross_modal_results
                ]

            # Generate overall assessment
            results["overall_assessment"] = self._generate_overall_assessment(results)

            # Generate comprehensive recommendations
            results["recommendations"] = self._generate_comprehensive_recommendations(results)

            return results

        except Exception as e:
            logger.error(f"Error in comprehensive multimodal analysis: {e}")
            raise

    def _generate_overall_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment from individual results"""
        total_bias_score = 0.0
        total_results = 0
        biased_modalities = []

        # Analyze individual modality results
        for modality, modality_results in results["individual_modality_results"].items():
            modality_bias_scores = [r["bias_score"] for r in modality_results]
            if modality_bias_scores:
                avg_modality_bias = float(np.mean(modality_bias_scores))
                total_bias_score += avg_modality_bias
                total_results += 1

                if avg_modality_bias > _BIAS_THRESHOLD:
                    biased_modalities.append(modality)

        # Analyze cross-modal results
        cross_modal_bias_scores = [r["bias_score"] for r in results["cross_modal_results"]]
        if cross_modal_bias_scores:
            avg_cross_modal_bias = float(np.mean(cross_modal_bias_scores))
            total_bias_score += avg_cross_modal_bias
            total_results += 1

        overall_bias_score = total_bias_score / total_results if total_results > 0 else 0.0

        return {
            "overall_bias_score": overall_bias_score,
            "biased_modalities": biased_modalities,
            "cross_modal_bias_detected": len(results["cross_modal_results"]) > 0,
            "risk_level": "high" if overall_bias_score > 0.2 else "medium" if overall_bias_score > 0.1 else "low"
        }

    def _generate_comprehensive_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations based on all results"""
        recommendations = []

        assessment = results["overall_assessment"]

        if assessment["risk_level"] == "high":
            recommendations.extend([
                "Implement immediate bias mitigation measures",
                "Consider model retraining with balanced data",
                "Deploy with strict monitoring and controls"
            ])
        elif assessment["risk_level"] == "medium":
            recommendations.extend([
                "Implement enhanced bias monitoring",
                "Schedule regular bias audits",
                "Consider post-processing bias correction"
            ])
        else:
            recommendations.extend([
                "Continue current monitoring practices",
                "Schedule regular bias evaluations",
                "Maintain bias detection systems"
            ])

        if assessment["biased_modalities"]:
            recommendations.append(f"Focus bias mitigation on: {', '.join(assessment['biased_modalities'])}")

        if assessment["cross_modal_bias_detected"]:
            recommendations.extend([
                "Implement cross-modal consistency monitoring",
                "Use interaction effect analysis",
                "Monitor for bias amplification across modalities"
            ])

        return recommendations
