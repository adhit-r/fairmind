"""
Modern Tools Integration Service
Integrates with latest explainability and bias detection tools from 2025
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ToolIntegrationResult:
    """Result from external tool integration"""
    tool_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = ""

class ModernToolsIntegrationService:
    """
    Integration service for modern explainability and bias detection tools
    Implements integration with tools mentioned in the 2025 analysis
    """
    
    def __init__(self):
        self.tool_configs = self._initialize_tool_configs()
        self.session = None
        
    def _initialize_tool_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize configurations for modern tools"""
        return {
            "comet_llm": {
                "name": "CometLLM",
                "description": "Comprehensive prompt logging, tracking, and visualization platform",
                "enabled": True,
                "api_endpoint": "https://api.comet.com/v1/llm",
                "features": [
                    "prompt_logging",
                    "response_tracking", 
                    "parameter_monitoring",
                    "visualization",
                    "a_b_testing"
                ],
                "integrations": ["OpenAI", "LangChain", "Hugging Face"]
            },
            "deepeval": {
                "name": "DeepEval",
                "description": "Open-source LLM evaluation framework",
                "enabled": True,
                "api_endpoint": "https://api.deepeval.com/v1",
                "features": [
                    "bias_detection_metrics",
                    "custom_evaluation_criteria",
                    "mlops_integration",
                    "automated_testing"
                ],
                "metrics": ["BiasMetric", "FaithfulnessMetric", "RelevanceMetric"]
            },
            "arize_phoenix": {
                "name": "Arize AI Phoenix",
                "description": "Real-time monitoring for model performance degradation",
                "enabled": True,
                "api_endpoint": "https://api.arize.com/v1/phoenix",
                "features": [
                    "real_time_monitoring",
                    "data_drift_detection",
                    "bias_identification",
                    "performance_analysis"
                ],
                "capabilities": ["demographic_group_analysis", "bias_trend_monitoring"]
            },
            "aws_clarify": {
                "name": "AWS SageMaker Clarify",
                "description": "Automated bias detection during data preparation",
                "enabled": True,
                "api_endpoint": "https://clarify.sagemaker.amazonaws.com/v1",
                "features": [
                    "automated_bias_detection",
                    "visual_reports",
                    "fairness_evaluation",
                    "aws_ecosystem_integration"
                ],
                "metrics": ["demographic_parity", "equalized_odds", "calibration"]
            },
            "confident_ai": {
                "name": "Confident AI",
                "description": "Enterprise-grade bias detection and monitoring",
                "enabled": True,
                "api_endpoint": "https://api.confident-ai.com/v1",
                "features": [
                    "enterprise_compliance",
                    "risk_management",
                    "governance",
                    "real_time_alerts"
                ],
                "compliance": ["GDPR", "CCPA", "EU_AI_ACT"]
            },
            "transformer_lens": {
                "name": "TransformerLens",
                "description": "Mechanistic interpretability for transformer models",
                "enabled": True,
                "api_endpoint": "https://api.transformerlens.com/v1",
                "features": [
                    "activation_patching",
                    "circuit_discovery",
                    "attention_analysis",
                    "causal_intervention"
                ],
                "methods": ["hook_based_analysis", "intervention_studies"]
            },
            "bertviz": {
                "name": "BertViz",
                "description": "Attention visualization for transformer models",
                "enabled": True,
                "api_endpoint": "https://api.bertviz.com/v1",
                "features": [
                    "attention_visualization",
                    "layer_analysis",
                    "head_analysis",
                    "interactive_exploration"
                ],
                "visualizations": ["attention_heads", "attention_flow", "attention_rollout"]
            }
        }

    async def __aenter__(self):
        """Async context manager entry"""
        if AIOHTTP_AVAILABLE:
            self.session = aiohttp.ClientSession()
        else:
            self.session = None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def integrate_comet_llm(
        self,
        prompts: List[str],
        responses: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ToolIntegrationResult:
        """
        Integrate with CometLLM for prompt tracking and visualization
        """
        try:
            config = self.tool_configs["comet_llm"]
            if not config["enabled"]:
                return ToolIntegrationResult(
                    tool_name="comet_llm",
                    success=False,
                    data={},
                    error="CometLLM integration is disabled",
                    timestamp=datetime.now().isoformat()
                )
            
            # CometLLM integration: compute real metrics from provided data
            prompt_lengths = [len(p) for p in prompts]
            response_lengths = [len(r) for r in responses]

            comet_data = {
                "project_id": "fairmind_bias_detection",
                "experiment_id": f"bias_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "prompts": prompts,
                "responses": responses,
                "metadata": metadata or {},
                "parameters": metadata.get("parameters", {}) if metadata else {},
                "metrics": {
                    "prompt_length": prompt_lengths,
                    "response_length": response_lengths,
                    "avg_prompt_length": sum(prompt_lengths) / max(len(prompt_lengths), 1),
                    "avg_response_length": sum(response_lengths) / max(len(response_lengths), 1),
                    "total_prompts": len(prompts)
                },
                "status": "data_logged",
                "note": "CometLLM API not connected; metrics computed locally from provided data"
            }
            
            return ToolIntegrationResult(
                tool_name="comet_llm",
                success=True,
                data=comet_data,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error integrating with CometLLM: {e}")
            return ToolIntegrationResult(
                tool_name="comet_llm",
                success=False,
                data={},
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def integrate_deepeval(
        self,
        model_outputs: List[Dict[str, Any]],
        evaluation_criteria: Optional[List[str]] = None
    ) -> ToolIntegrationResult:
        """
        Integrate with DeepEval for LLM evaluation
        """
        try:
            config = self.tool_configs["deepeval"]
            if not config["enabled"]:
                return ToolIntegrationResult(
                    tool_name="deepeval",
                    success=False,
                    data={},
                    error="DeepEval integration is disabled",
                    timestamp=datetime.now().isoformat()
                )
            
            # DeepEval integration: compute metrics from actual model outputs
            criteria = evaluation_criteria or ["bias", "faithfulness", "relevance"]
            evaluation_results = {}

            for criterion in criteria:
                # Extract relevant scores from model outputs if available
                criterion_scores = [
                    float(output.get(criterion, output.get("score", 0)))
                    for output in model_outputs
                    if criterion in output or "score" in output
                ]

                if criterion_scores:
                    score = sum(criterion_scores) / len(criterion_scores)
                    evaluation_results[criterion] = {
                        "score": score,
                        "details": {
                            "sample_count": len(criterion_scores),
                            "min_score": min(criterion_scores),
                            "max_score": max(criterion_scores)
                        }
                    }
                else:
                    evaluation_results[criterion] = {
                        "score": 0.0,
                        "details": {
                            "sample_count": 0,
                            "note": f"No {criterion} data available in model outputs"
                        }
                    }

            result_scores = [r["score"] for r in evaluation_results.values()]
            overall_score = sum(result_scores) / max(len(result_scores), 1)

            deepeval_data = {
                "evaluation_id": f"deepeval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "model_outputs_count": len(model_outputs),
                "evaluation_criteria": criteria,
                "results": evaluation_results,
                "overall_score": overall_score,
                "status": "evaluated_locally",
                "note": "DeepEval API not connected; metrics computed from provided model outputs"
            }
            
            return ToolIntegrationResult(
                tool_name="deepeval",
                success=True,
                data=deepeval_data,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error integrating with DeepEval: {e}")
            return ToolIntegrationResult(
                tool_name="deepeval",
                success=False,
                data={},
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def integrate_arize_phoenix(
        self,
        model_outputs: List[Dict[str, Any]],
        monitoring_config: Optional[Dict[str, Any]] = None
    ) -> ToolIntegrationResult:
        """
        Integrate with Arize AI Phoenix for real-time monitoring
        """
        try:
            config = self.tool_configs["arize_phoenix"]
            if not config["enabled"]:
                return ToolIntegrationResult(
                    tool_name="arize_phoenix",
                    success=False,
                    data={},
                    error="Arize Phoenix integration is disabled",
                    timestamp=datetime.now().isoformat()
                )
            
            # Arize Phoenix integration: compute monitoring metrics from actual data
            # Extract scores and group labels from model outputs
            all_scores = [float(o.get("score", 0)) for o in model_outputs if "score" in o]
            all_bias = [float(o.get("bias_score", 0)) for o in model_outputs if "bias_score" in o]

            # Group-level analysis from actual outputs
            group_performance = {}
            for output in model_outputs:
                group = output.get("group", "default")
                if group not in group_performance:
                    group_performance[group] = {"scores": [], "bias_scores": []}
                if "score" in output:
                    group_performance[group]["scores"].append(float(output["score"]))
                if "bias_score" in output:
                    group_performance[group]["bias_scores"].append(float(output["bias_score"]))

            demographic_analysis = {}
            for group, data in group_performance.items():
                scores = data["scores"]
                b_scores = data["bias_scores"]
                demographic_analysis[group] = {
                    "accuracy": sum(scores) / max(len(scores), 1) if scores else 0.0,
                    "bias_score": sum(b_scores) / max(len(b_scores), 1) if b_scores else 0.0
                }

            avg_bias = sum(all_bias) / max(len(all_bias), 1) if all_bias else 0.0

            phoenix_data = {
                "monitoring_session_id": f"phoenix_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "data_points": len(model_outputs),
                "monitoring_metrics": {
                    "data_drift_score": 0.0,
                    "performance_degradation": 0.0,
                    "bias_trend": {
                        "current": avg_bias,
                        "trend": "unknown",
                        "change_rate": 0.0
                    },
                    "note": "Arize Phoenix API not connected; metrics computed from provided data"
                },
                "demographic_analysis": {
                    "group_performance": demographic_analysis
                },
                "alerts": [],
                "recommendations": []
            }

            # Generate alerts from actual data
            if avg_bias > 0.2:
                phoenix_data["alerts"].append({
                    "type": "bias_increase",
                    "severity": "critical",
                    "message": f"Bias level ({avg_bias:.3f}) above acceptable threshold (0.2)"
                })
                phoenix_data["recommendations"].append("Review and mitigate detected bias")

            if not all_scores and not all_bias:
                phoenix_data["recommendations"].append(
                    "Provide 'score' and 'bias_score' fields in model outputs for meaningful monitoring"
                )
            
            return ToolIntegrationResult(
                tool_name="arize_phoenix",
                success=True,
                data=phoenix_data,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error integrating with Arize Phoenix: {e}")
            return ToolIntegrationResult(
                tool_name="arize_phoenix",
                success=False,
                data={},
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def integrate_aws_clarify(
        self,
        model_outputs: List[Dict[str, Any]],
        sensitive_attributes: List[str]
    ) -> ToolIntegrationResult:
        """
        Integrate with AWS SageMaker Clarify for automated bias detection
        """
        try:
            config = self.tool_configs["aws_clarify"]
            if not config["enabled"]:
                return ToolIntegrationResult(
                    tool_name="aws_clarify",
                    success=False,
                    data={},
                    error="AWS Clarify integration is disabled",
                    timestamp=datetime.now().isoformat()
                )
            
            # AWS Clarify integration: compute bias metrics from actual model outputs
            clarify_data = {
                "analysis_job_id": f"clarify_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "sensitive_attributes": sensitive_attributes,
                "bias_metrics": {},
                "fairness_metrics": {},
                "status": "analyzed_locally",
                "note": "AWS Clarify API not connected; metrics computed from provided data"
            }

            for attr in sensitive_attributes:
                # Group model outputs by sensitive attribute value
                groups = {}
                for output in model_outputs:
                    attr_val = output.get(attr, output.get("group", "unknown"))
                    groups.setdefault(str(attr_val), []).append(output)

                if len(groups) >= 2:
                    # Compute actual demographic parity from outcome rates
                    group_rates = {}
                    for group_name, group_outputs in groups.items():
                        positive = sum(1 for o in group_outputs
                                      if o.get("outcome", o.get("prediction", 0)) == 1)
                        group_rates[group_name] = positive / max(len(group_outputs), 1)

                    rates = list(group_rates.values())
                    dp_diff = max(rates) - min(rates)

                    clarify_data["bias_metrics"][attr] = {
                        "demographic_parity_difference": dp_diff,
                        "group_rates": group_rates,
                        "groups_analyzed": len(groups)
                    }
                    clarify_data["fairness_metrics"][attr] = {
                        "statistical_parity": 1.0 - dp_diff,
                        "groups_analyzed": len(groups)
                    }
                else:
                    clarify_data["bias_metrics"][attr] = {
                        "demographic_parity_difference": 0.0,
                        "note": f"Insufficient group variation for attribute '{attr}'"
                    }
                    clarify_data["fairness_metrics"][attr] = {
                        "statistical_parity": 1.0,
                        "note": f"Insufficient group variation for attribute '{attr}'"
                    }
            
            return ToolIntegrationResult(
                tool_name="aws_clarify",
                success=True,
                data=clarify_data,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error integrating with AWS Clarify: {e}")
            return ToolIntegrationResult(
                tool_name="aws_clarify",
                success=False,
                data={},
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def integrate_confident_ai(
        self,
        model_outputs: List[Dict[str, Any]],
        compliance_frameworks: Optional[List[str]] = None
    ) -> ToolIntegrationResult:
        """
        Integrate with Confident AI for enterprise-grade bias detection
        """
        try:
            config = self.tool_configs["confident_ai"]
            if not config["enabled"]:
                return ToolIntegrationResult(
                    tool_name="confident_ai",
                    success=False,
                    data={},
                    error="Confident AI integration is disabled",
                    timestamp=datetime.now().isoformat()
                )
            
            frameworks = compliance_frameworks or ["EU_AI_ACT", "FTC_GUIDELINES"]
            
            # Confident AI integration: compute risk and compliance from actual data
            # Analyze model outputs for risk indicators
            all_bias_scores = [float(o.get("bias_score", 0)) for o in model_outputs if "bias_score" in o]
            avg_bias = sum(all_bias_scores) / max(len(all_bias_scores), 1) if all_bias_scores else 0.0

            if avg_bias > 0.5:
                overall_risk_level = "high"
            elif avg_bias > 0.2:
                overall_risk_level = "medium"
            else:
                overall_risk_level = "low"

            risk_factors = []
            if avg_bias > 0.3:
                risk_factors.append(f"Elevated bias detected (avg: {avg_bias:.3f})")
            if len(model_outputs) < 10:
                risk_factors.append("Small sample size limits confidence in risk assessment")
            if not all_bias_scores:
                risk_factors.append("No bias scores provided in model outputs")

            confident_data = {
                "enterprise_session_id": f"confident_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "compliance_frameworks": frameworks,
                "risk_assessment": {
                    "overall_risk_level": overall_risk_level,
                    "risk_score": avg_bias,
                    "risk_factors": risk_factors
                },
                "compliance_status": {},
                "governance_reports": [],
                "real_time_alerts": [],
                "status": "assessed_locally",
                "note": "Confident AI API not connected; risk computed from provided data"
            }

            for framework in frameworks:
                # Compliance determined from actual risk level
                is_compliant = avg_bias < 0.3
                gaps = []
                if not is_compliant:
                    gaps.append(f"Bias score ({avg_bias:.3f}) exceeds compliance threshold")
                if not all_bias_scores:
                    gaps.append("No bias metrics available for compliance assessment")

                confident_data["compliance_status"][framework] = {
                    "compliant": is_compliant,
                    "compliance_score": max(0.0, 1.0 - avg_bias),
                    "gaps": gaps,
                    "recommendations": [
                        "Implement additional bias monitoring",
                        "Update compliance documentation",
                        "Schedule regular audits"
                    ] if gaps else ["Continue current monitoring practices"]
                }
            
            return ToolIntegrationResult(
                tool_name="confident_ai",
                success=True,
                data=confident_data,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error integrating with Confident AI: {e}")
            return ToolIntegrationResult(
                tool_name="confident_ai",
                success=False,
                data={},
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def integrate_transformer_lens(
        self,
        model_outputs: List[Dict[str, Any]],
        analysis_type: str = "activation_patching"
    ) -> ToolIntegrationResult:
        """
        Integrate with TransformerLens for mechanistic interpretability
        """
        try:
            config = self.tool_configs["transformer_lens"]
            if not config["enabled"]:
                return ToolIntegrationResult(
                    tool_name="transformer_lens",
                    success=False,
                    data={},
                    error="TransformerLens integration is disabled",
                    timestamp=datetime.now().isoformat()
                )
            
            # TransformerLens requires a loaded model for real analysis
            try:
                import transformer_lens  # noqa: F401
            except ImportError:
                return ToolIntegrationResult(
                    tool_name="transformer_lens",
                    success=False,
                    data={},
                    error="TransformerLens package not installed. Install with: pip install transformer-lens",
                    timestamp=datetime.now().isoformat()
                )

            return ToolIntegrationResult(
                tool_name="transformer_lens",
                success=False,
                data={"analysis_type": analysis_type},
                error=(
                    "TransformerLens analysis requires a loaded model instance. "
                    "Pass a HookedTransformer model via model_outputs to run real analysis."
                ),
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error integrating with TransformerLens: {e}")
            return ToolIntegrationResult(
                tool_name="transformer_lens",
                success=False,
                data={},
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def integrate_bertviz(
        self,
        model_outputs: List[Dict[str, Any]],
        visualization_type: str = "attention_heads"
    ) -> ToolIntegrationResult:
        """
        Integrate with BertViz for attention visualization
        """
        try:
            config = self.tool_configs["bertviz"]
            if not config["enabled"]:
                return ToolIntegrationResult(
                    tool_name="bertviz",
                    success=False,
                    data={},
                    error="BertViz integration is disabled",
                    timestamp=datetime.now().isoformat()
                )
            
            # BertViz requires actual attention weights from a loaded model
            try:
                import bertviz  # noqa: F401
            except ImportError:
                return ToolIntegrationResult(
                    tool_name="bertviz",
                    success=False,
                    data={},
                    error="BertViz package not installed. Install with: pip install bertviz",
                    timestamp=datetime.now().isoformat()
                )

            bertviz_data = {
                "visualization_id": f"bertviz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "visualization_type": visualization_type,
                "status": "requires_model",
                "error": (
                    "BertViz visualization requires actual attention weights from a loaded model. "
                    "Pass attention tensors via model_outputs to generate real visualizations."
                ),
            }
            
            return ToolIntegrationResult(
                tool_name="bertviz",
                success=True,
                data=bertviz_data,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error integrating with BertViz: {e}")
            return ToolIntegrationResult(
                tool_name="bertviz",
                success=False,
                data={},
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def run_comprehensive_tool_integration(
        self,
        model_outputs: List[Dict[str, Any]],
        selected_tools: Optional[List[str]] = None
    ) -> Dict[str, ToolIntegrationResult]:
        """
        Run comprehensive integration with multiple tools
        """
        try:
            tools_to_run = selected_tools or list(self.tool_configs.keys())
            results = {}
            
            # Run integrations in parallel
            tasks = []
            
            if "comet_llm" in tools_to_run:
                prompts = [output.get("text", "") for output in model_outputs]
                responses = [output.get("response", "") for output in model_outputs]
                tasks.append(self.integrate_comet_llm(prompts, responses))
            
            if "deepeval" in tools_to_run:
                tasks.append(self.integrate_deepeval(model_outputs))
            
            if "arize_phoenix" in tools_to_run:
                tasks.append(self.integrate_arize_phoenix(model_outputs))
            
            if "aws_clarify" in tools_to_run:
                sensitive_attrs = ["gender", "race", "age"]  # Default attributes
                tasks.append(self.integrate_aws_clarify(model_outputs, sensitive_attrs))
            
            if "confident_ai" in tools_to_run:
                tasks.append(self.integrate_confident_ai(model_outputs))
            
            if "transformer_lens" in tools_to_run:
                tasks.append(self.integrate_transformer_lens(model_outputs))
            
            if "bertviz" in tools_to_run:
                tasks.append(self.integrate_bertviz(model_outputs))
            
            # Execute all integrations
            integration_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(integration_results):
                if isinstance(result, Exception):
                    logger.error(f"Tool integration failed: {result}")
                    results[f"tool_{i}"] = ToolIntegrationResult(
                        tool_name="unknown",
                        success=False,
                        data={},
                        error=str(result),
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    results[result.tool_name] = result
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive tool integration: {e}")
            raise

    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available tools and their configurations"""
        return {
            tool_id: {
                "name": config["name"],
                "description": config["description"],
                "enabled": config["enabled"],
                "features": config["features"]
            }
            for tool_id, config in self.tool_configs.items()
        }

    def configure_tool(self, tool_id: str, enabled: bool) -> bool:
        """Configure tool enablement"""
        try:
            if tool_id in self.tool_configs:
                self.tool_configs[tool_id]["enabled"] = enabled
                return True
            return False
        except Exception as e:
            logger.error(f"Error configuring tool {tool_id}: {e}")
            return False
