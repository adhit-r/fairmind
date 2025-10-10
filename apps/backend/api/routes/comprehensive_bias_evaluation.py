"""
Comprehensive Bias Evaluation Pipeline API Routes
Exposes the multi-layered bias evaluation approach from the 2025 analysis
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..services.comprehensive_bias_evaluation_pipeline import (
    ComprehensiveBiasEvaluationPipeline,
    EvaluationPhase,
    BiasRiskLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/comprehensive-evaluation", tags=["Comprehensive Bias Evaluation"])

# Initialize the comprehensive evaluation pipeline
evaluation_pipeline = ComprehensiveBiasEvaluationPipeline()

# Request/Response Models

class ModelOutput(BaseModel):
    """Model output for comprehensive evaluation"""
    text: Optional[str] = None
    response: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    protected_attributes: Optional[Dict[str, Any]] = None

class ComprehensiveEvaluationRequest(BaseModel):
    """Request for comprehensive bias evaluation"""
    model_id: str = Field(..., description="Unique identifier for the model")
    model_type: str = Field(..., description="Type of model (llm, image_gen, audio_gen, video_gen)")
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to evaluate")
    evaluation_config: Optional[Dict[str, Any]] = Field(default=None, description="Optional evaluation configuration")
    phases_to_run: Optional[List[str]] = Field(default=None, description="Specific phases to run")

class EvaluationPhaseRequest(BaseModel):
    """Request for specific evaluation phase"""
    model_id: str = Field(..., description="Model identifier")
    model_type: str = Field(..., description="Model type")
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to evaluate")
    phase: str = Field(..., description="Evaluation phase to run")
    phase_config: Optional[Dict[str, Any]] = Field(default=None, description="Phase-specific configuration")

class EvaluationConfigurationRequest(BaseModel):
    """Request to configure evaluation pipeline"""
    phase: str = Field(..., description="Phase to configure")
    config: Dict[str, Any] = Field(..., description="Configuration for the phase")

class ComprehensiveEvaluationResponse(BaseModel):
    """Response for comprehensive evaluation"""
    evaluation_id: str
    model_id: str
    model_type: str
    start_time: str
    end_time: str
    phases_completed: List[str]
    overall_risk: str
    bias_summary: Dict[str, Any]
    recommendations: List[str]
    compliance_status: Dict[str, Any]
    next_evaluation_due: str
    results: Dict[str, Any]

class EvaluationHistoryResponse(BaseModel):
    """Response for evaluation history"""
    evaluations: List[Dict[str, Any]]
    total_count: int
    limit: int

# API Endpoints

@router.post("/run-comprehensive", response_model=ComprehensiveEvaluationResponse)
async def run_comprehensive_evaluation(
    request: ComprehensiveEvaluationRequest,
    background_tasks: BackgroundTasks
):
    """
    Run comprehensive bias evaluation pipeline
    
    Implements the multi-layered approach from the 2025 analysis:
    1. Pre-deployment comprehensive testing
    2. Real-time monitoring simulation
    3. Post-deployment auditing
    4. Human-in-the-loop evaluation
    5. Continuous learning adaptation
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "response": output.response,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Prepare evaluation configuration
        evaluation_config = request.evaluation_config or {}
        if request.phases_to_run:
            # Configure which phases to run
            for phase in evaluation_config:
                if phase in request.phases_to_run:
                    evaluation_config[phase]["enabled"] = True
                else:
                    evaluation_config[phase]["enabled"] = False
        
        # Run comprehensive evaluation
        report = await evaluation_pipeline.run_comprehensive_evaluation(
            model_id=request.model_id,
            model_type=request.model_type,
            model_outputs=model_outputs,
            evaluation_config=evaluation_config
        )
        
        # Log evaluation for audit trail
        background_tasks.add_task(
            _log_comprehensive_evaluation,
            request.model_id,
            request.model_type,
            report.overall_risk.value,
            len(request.model_outputs)
        )
        
        # Convert to response format
        return ComprehensiveEvaluationResponse(
            evaluation_id=report.evaluation_id,
            model_id=report.model_id,
            model_type=report.model_type,
            start_time=report.start_time,
            end_time=report.end_time,
            phases_completed=[phase.value for phase in report.phases_completed],
            overall_risk=report.overall_risk.value,
            bias_summary=report.bias_summary,
            recommendations=report.recommendations,
            compliance_status=report.compliance_status,
            next_evaluation_due=report.next_evaluation_due,
            results={
                phase: {
                    "phase": result.phase.value,
                    "timestamp": result.timestamp,
                    "success": result.success,
                    "bias_detected": result.bias_detected,
                    "risk_level": result.risk_level.value,
                    "metrics": result.metrics,
                    "recommendations": result.recommendations,
                    "alerts": result.alerts,
                    "details": result.details
                }
                for phase, result in report.results.items()
            }
        )
        
    except Exception as e:
        logger.error(f"Error in comprehensive evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Comprehensive evaluation failed: {str(e)}")

@router.post("/run-phase")
async def run_evaluation_phase(request: EvaluationPhaseRequest):
    """
    Run a specific evaluation phase
    
    Available phases:
    - pre_deployment: Comprehensive bias testing before deployment
    - real_time_monitoring: Real-time bias monitoring simulation
    - post_deployment_auditing: Post-deployment bias auditing
    - human_in_loop: Human-in-the-loop bias evaluation
    - continuous_learning: Continuous learning adaptation
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "response": output.response,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Validate phase
        try:
            phase_enum = EvaluationPhase(request.phase)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phase: {request.phase}. Valid phases: {[p.value for p in EvaluationPhase]}"
            )
        
        # Run specific phase
        if request.phase == "pre_deployment":
            result = await evaluation_pipeline._run_pre_deployment_evaluation(
                request.model_id, request.model_type, model_outputs, 
                request.phase_config or evaluation_pipeline.evaluation_configs["pre_deployment"]
            )
        elif request.phase == "real_time_monitoring":
            result = await evaluation_pipeline._run_real_time_monitoring(
                request.model_id, request.model_type, model_outputs,
                request.phase_config or evaluation_pipeline.evaluation_configs["real_time_monitoring"]
            )
        elif request.phase == "post_deployment_auditing":
            result = await evaluation_pipeline._run_post_deployment_auditing(
                request.model_id, request.model_type, model_outputs,
                request.phase_config or evaluation_pipeline.evaluation_configs["post_deployment_auditing"]
            )
        elif request.phase == "human_in_loop":
            result = await evaluation_pipeline._run_human_in_loop_evaluation(
                request.model_id, request.model_type, model_outputs,
                request.phase_config or evaluation_pipeline.evaluation_configs["human_in_loop"]
            )
        elif request.phase == "continuous_learning":
            result = await evaluation_pipeline._run_continuous_learning(
                request.model_id, request.model_type, model_outputs,
                request.phase_config or evaluation_pipeline.evaluation_configs["continuous_learning"]
            )
        else:
            raise HTTPException(status_code=400, detail=f"Phase {request.phase} not implemented")
        
        return {
            "phase": result.phase.value,
            "timestamp": result.timestamp,
            "success": result.success,
            "bias_detected": result.bias_detected,
            "risk_level": result.risk_level.value,
            "metrics": result.metrics,
            "recommendations": result.recommendations,
            "alerts": result.alerts,
            "details": result.details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running evaluation phase {request.phase}: {e}")
        raise HTTPException(status_code=500, detail=f"Phase evaluation failed: {str(e)}")

@router.get("/evaluation-history", response_model=EvaluationHistoryResponse)
async def get_evaluation_history(limit: int = 10):
    """
    Get evaluation history
    """
    try:
        history = evaluation_pipeline.get_evaluation_history(limit)
        
        # Convert to response format
        evaluations = []
        for report in history:
            evaluations.append({
                "evaluation_id": report.evaluation_id,
                "model_id": report.model_id,
                "model_type": report.model_type,
                "start_time": report.start_time,
                "end_time": report.end_time,
                "phases_completed": [phase.value for phase in report.phases_completed],
                "overall_risk": report.overall_risk.value,
                "bias_summary": report.bias_summary,
                "recommendations_count": len(report.recommendations),
                "compliance_status": report.compliance_status
            })
        
        return EvaluationHistoryResponse(
            evaluations=evaluations,
            total_count=len(evaluation_pipeline.evaluation_history),
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error getting evaluation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation history: {str(e)}")

@router.get("/evaluation/{evaluation_id}")
async def get_evaluation_by_id(evaluation_id: str):
    """
    Get specific evaluation by ID
    """
    try:
        report = evaluation_pipeline.get_evaluation_by_id(evaluation_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
        return {
            "evaluation_id": report.evaluation_id,
            "model_id": report.model_id,
            "model_type": report.model_type,
            "start_time": report.start_time,
            "end_time": report.end_time,
            "phases_completed": [phase.value for phase in report.phases_completed],
            "overall_risk": report.overall_risk.value,
            "bias_summary": report.bias_summary,
            "recommendations": report.recommendations,
            "compliance_status": report.compliance_status,
            "next_evaluation_due": report.next_evaluation_due,
            "results": {
                phase: {
                    "phase": result.phase.value,
                    "timestamp": result.timestamp,
                    "success": result.success,
                    "bias_detected": result.bias_detected,
                    "risk_level": result.risk_level.value,
                    "metrics": result.metrics,
                    "recommendations": result.recommendations,
                    "alerts": result.alerts,
                    "details": result.details
                }
                for phase, result in report.results.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evaluation {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation: {str(e)}")

@router.get("/available-phases")
async def get_available_phases():
    """
    Get available evaluation phases
    """
    try:
        return {
            "phases": [
                {
                    "name": phase.value,
                    "description": _get_phase_description(phase),
                    "enabled": evaluation_pipeline.evaluation_configs.get(phase.value, {}).get("enabled", True)
                }
                for phase in EvaluationPhase
            ],
            "total_phases": len(EvaluationPhase)
        }
    except Exception as e:
        logger.error(f"Error getting available phases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available phases: {str(e)}")

@router.get("/risk-levels")
async def get_risk_levels():
    """
    Get available risk levels
    """
    try:
        return {
            "risk_levels": [
                {
                    "name": level.value,
                    "description": _get_risk_level_description(level)
                }
                for level in BiasRiskLevel
            ],
            "monitoring_thresholds": evaluation_pipeline.monitoring_thresholds
        }
    except Exception as e:
        logger.error(f"Error getting risk levels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk levels: {str(e)}")

@router.get("/compliance-frameworks")
async def get_compliance_frameworks():
    """
    Get available compliance frameworks
    """
    try:
        return {
            "frameworks": evaluation_pipeline.compliance_frameworks,
            "total_frameworks": len(evaluation_pipeline.compliance_frameworks)
        }
    except Exception as e:
        logger.error(f"Error getting compliance frameworks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance frameworks: {str(e)}")

@router.put("/configure-phase")
async def configure_evaluation_phase(request: EvaluationConfigurationRequest):
    """
    Configure evaluation phase settings
    """
    try:
        if request.phase not in evaluation_pipeline.evaluation_configs:
            raise HTTPException(status_code=404, detail=f"Phase {request.phase} not found")
        
        # Update configuration
        evaluation_pipeline.evaluation_configs[request.phase].update(request.config)
        
        return {
            "message": f"Phase {request.phase} configured successfully",
            "configuration": evaluation_pipeline.evaluation_configs[request.phase]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring phase {request.phase}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure phase: {str(e)}")

@router.get("/pipeline-status")
async def get_pipeline_status():
    """
    Get pipeline status and configuration
    """
    try:
        return {
            "pipeline_status": "active",
            "evaluation_configs": evaluation_pipeline.evaluation_configs,
            "monitoring_thresholds": evaluation_pipeline.monitoring_thresholds,
            "compliance_frameworks": evaluation_pipeline.compliance_frameworks,
            "evaluation_history_count": len(evaluation_pipeline.evaluation_history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check for the comprehensive evaluation pipeline
    """
    try:
        return {
            "status": "healthy",
            "service": "comprehensive_bias_evaluation_pipeline",
            "timestamp": datetime.now().isoformat(),
            "available_phases": len(EvaluationPhase),
            "evaluation_history_count": len(evaluation_pipeline.evaluation_history)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Background task functions

async def _log_comprehensive_evaluation(
    model_id: str, 
    model_type: str, 
    risk_level: str, 
    sample_count: int
):
    """Log comprehensive evaluation for audit trail"""
    try:
        logger.info(f"Comprehensive evaluation completed - Model: {model_id}, Type: {model_type}, Risk: {risk_level}, Samples: {sample_count}")
        # Here you could add database logging, metrics collection, etc.
    except Exception as e:
        logger.error(f"Error logging comprehensive evaluation: {e}")

# Helper functions

def _get_phase_description(phase: EvaluationPhase) -> str:
    """Get description for evaluation phase"""
    descriptions = {
        EvaluationPhase.PRE_DEPLOYMENT: "Comprehensive bias testing before model deployment",
        EvaluationPhase.REAL_TIME_MONITORING: "Real-time bias monitoring and alerting",
        EvaluationPhase.POST_DEPLOYMENT_AUDITING: "Post-deployment bias auditing and compliance checking",
        EvaluationPhase.HUMAN_IN_LOOP: "Human-in-the-loop bias evaluation with expert and crowd input",
        EvaluationPhase.CONTINUOUS_LEARNING: "Continuous learning and adaptation for bias mitigation"
    }
    return descriptions.get(phase, "Unknown phase")

def _get_risk_level_description(level: BiasRiskLevel) -> str:
    """Get description for risk level"""
    descriptions = {
        BiasRiskLevel.LOW: "Low bias risk - model is safe to deploy with standard monitoring",
        BiasRiskLevel.MEDIUM: "Medium bias risk - deploy with enhanced monitoring and regular audits",
        BiasRiskLevel.HIGH: "High bias risk - deploy with strict monitoring and immediate bias mitigation",
        BiasRiskLevel.CRITICAL: "Critical bias risk - do not deploy without addressing bias issues"
    }
    return descriptions.get(level, "Unknown risk level")

# Additional utility endpoints

@router.post("/batch-evaluation")
async def batch_comprehensive_evaluation(
    requests: List[ComprehensiveEvaluationRequest],
    background_tasks: BackgroundTasks
):
    """
    Perform batch comprehensive evaluation for multiple models
    """
    try:
        results = []
        for request in requests:
            # Convert request model outputs
            model_outputs = []
            for output in request.model_outputs:
                output_dict = {
                    "text": output.text,
                    "response": output.response,
                    "image_url": output.image_url,
                    "audio_url": output.audio_url,
                    "video_url": output.video_url,
                    "metadata": output.metadata or {},
                    "protected_attributes": output.protected_attributes or {}
                }
                model_outputs.append(output_dict)
            
            # Run evaluation
            report = await evaluation_pipeline.run_comprehensive_evaluation(
                model_id=request.model_id,
                model_type=request.model_type,
                model_outputs=model_outputs,
                evaluation_config=request.evaluation_config or {}
            )
            results.append(report)
        
        # Log batch evaluation
        background_tasks.add_task(
            _log_batch_evaluation,
            len(requests),
            [r.overall_risk.value for r in results]
        )
        
        return {
            "batch_results": [
                {
                    "evaluation_id": r.evaluation_id,
                    "model_id": r.model_id,
                    "overall_risk": r.overall_risk.value,
                    "phases_completed": len(r.phases_completed)
                }
                for r in results
            ],
            "total_evaluations": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch comprehensive evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")

async def _log_batch_evaluation(count: int, risk_levels: List[str]):
    """Log batch evaluation for audit trail"""
    try:
        logger.info(f"Batch comprehensive evaluation completed - Count: {count}, Risk levels: {risk_levels}")
    except Exception as e:
        logger.error(f"Error logging batch evaluation: {e}")

@router.get("/evaluation-metrics")
async def get_evaluation_metrics():
    """
    Get evaluation metrics and statistics
    """
    try:
        history = evaluation_pipeline.evaluation_history
        
        if not history:
            return {
                "total_evaluations": 0,
                "metrics": {},
                "message": "No evaluation history available"
            }
        
        # Calculate metrics
        risk_distribution = {}
        model_type_distribution = {}
        phases_completed_distribution = {}
        
        for report in history:
            # Risk distribution
            risk = report.overall_risk.value
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            
            # Model type distribution
            model_type = report.model_type
            model_type_distribution[model_type] = model_type_distribution.get(model_type, 0) + 1
            
            # Phases completed distribution
            phases_count = len(report.phases_completed)
            phases_completed_distribution[phases_count] = phases_completed_distribution.get(phases_count, 0) + 1
        
        return {
            "total_evaluations": len(history),
            "metrics": {
                "risk_distribution": risk_distribution,
                "model_type_distribution": model_type_distribution,
                "phases_completed_distribution": phases_completed_distribution,
                "average_phases_per_evaluation": sum(len(r.phases_completed) for r in history) / len(history)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting evaluation metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation metrics: {str(e)}")

