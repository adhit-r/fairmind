"""
Modern Tools Integration API Routes
Exposes integration with latest explainability and bias detection tools
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..services.modern_tools_integration import ModernToolsIntegrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/modern-tools", tags=["Modern Tools Integration"])

# Request/Response Models

class ModelOutput(BaseModel):
    """Model output for tool integration"""
    text: Optional[str] = None
    response: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ToolIntegrationRequest(BaseModel):
    """Request for tool integration"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    selected_tools: Optional[List[str]] = Field(default=None, description="Specific tools to use")
    integration_config: Optional[Dict[str, Any]] = Field(default=None, description="Tool-specific configuration")

class CometLLMRequest(BaseModel):
    """Request for CometLLM integration"""
    prompts: List[str] = Field(..., min_items=1, description="Prompts to analyze")
    responses: List[str] = Field(..., min_items=1, description="Model responses")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class DeepEvalRequest(BaseModel):
    """Request for DeepEval integration"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to evaluate")
    evaluation_criteria: Optional[List[str]] = Field(default=None, description="Specific evaluation criteria")

class ArizePhoenixRequest(BaseModel):
    """Request for Arize Phoenix integration"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to monitor")
    monitoring_config: Optional[Dict[str, Any]] = Field(default=None, description="Monitoring configuration")

class AWSClarifyRequest(BaseModel):
    """Request for AWS Clarify integration"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    sensitive_attributes: List[str] = Field(..., min_items=1, description="Sensitive attributes for bias detection")

class ConfidentAIRequest(BaseModel):
    """Request for Confident AI integration"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    compliance_frameworks: Optional[List[str]] = Field(default=None, description="Compliance frameworks to check")

class TransformerLensRequest(BaseModel):
    """Request for TransformerLens integration"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    analysis_type: str = Field(default="activation_patching", description="Type of analysis to perform")

class BertVizRequest(BaseModel):
    """Request for BertViz integration"""
    model_outputs: List[ModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    visualization_type: str = Field(default="attention_heads", description="Type of visualization to generate")

class ToolIntegrationResponse(BaseModel):
    """Response for tool integration"""
    tool_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str

class ComprehensiveIntegrationResponse(BaseModel):
    """Response for comprehensive tool integration"""
    timestamp: str
    tools_used: List[str]
    results: Dict[str, ToolIntegrationResponse]
    summary: Dict[str, Any]

# API Endpoints

@router.post("/comprehensive-integration", response_model=ComprehensiveIntegrationResponse)
async def comprehensive_tool_integration(
    request: ToolIntegrationRequest,
    background_tasks: BackgroundTasks
):
    """
    Run comprehensive integration with multiple modern tools
    
    Integrates with tools mentioned in the 2025 analysis:
    - CometLLM for prompt tracking
    - DeepEval for LLM evaluation
    - Arize Phoenix for monitoring
    - AWS Clarify for bias detection
    - Confident AI for enterprise compliance
    - TransformerLens for interpretability
    - BertViz for attention visualization
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
                "metadata": output.metadata or {}
            }
            model_outputs.append(output_dict)
        
        # Initialize tools integration service
        async with ModernToolsIntegrationService() as tools_service:
            # Run comprehensive integration
            results = await tools_service.run_comprehensive_tool_integration(
                model_outputs=model_outputs,
                selected_tools=request.selected_tools
            )
            
            # Create summary
            successful_tools = [name for name, result in results.items() if result.success]
            failed_tools = [name for name, result in results.items() if not result.success]
            
            summary = {
                "total_tools": len(results),
                "successful_tools": len(successful_tools),
                "failed_tools": len(failed_tools),
                "success_rate": len(successful_tools) / len(results) if results else 0,
                "tools_used": successful_tools,
                "tools_failed": failed_tools
            }
            
            # Log integration for audit trail
            background_tasks.add_task(
                _log_tool_integration,
                request.selected_tools or list(tools_service.tool_configs.keys()),
                summary["success_rate"]
            )
            
            return ComprehensiveIntegrationResponse(
                timestamp=datetime.now().isoformat(),
                tools_used=successful_tools,
                results=results,
                summary=summary
            )
        
    except Exception as e:
        logger.error(f"Error in comprehensive tool integration: {e}")
        raise HTTPException(status_code=500, detail=f"Tool integration failed: {str(e)}")

@router.post("/comet-llm", response_model=ToolIntegrationResponse)
async def integrate_comet_llm(request: CometLLMRequest):
    """
    Integrate with CometLLM for prompt tracking and visualization
    """
    try:
        async with ModernToolsIntegrationService() as tools_service:
            result = await tools_service.integrate_comet_llm(
                prompts=request.prompts,
                responses=request.responses,
                metadata=request.metadata
            )
            return ToolIntegrationResponse(**asdict(result))
        
    except Exception as e:
        logger.error(f"Error integrating with CometLLM: {e}")
        raise HTTPException(status_code=500, detail=f"CometLLM integration failed: {str(e)}")

@router.post("/deepeval", response_model=ToolIntegrationResponse)
async def integrate_deepeval(request: DeepEvalRequest):
    """
    Integrate with DeepEval for LLM evaluation
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
                "metadata": output.metadata or {}
            }
            model_outputs.append(output_dict)
        
        async with ModernToolsIntegrationService() as tools_service:
            result = await tools_service.integrate_deepeval(
                model_outputs=model_outputs,
                evaluation_criteria=request.evaluation_criteria
            )
            return ToolIntegrationResponse(**asdict(result))
        
    except Exception as e:
        logger.error(f"Error integrating with DeepEval: {e}")
        raise HTTPException(status_code=500, detail=f"DeepEval integration failed: {str(e)}")

@router.post("/arize-phoenix", response_model=ToolIntegrationResponse)
async def integrate_arize_phoenix(request: ArizePhoenixRequest):
    """
    Integrate with Arize AI Phoenix for real-time monitoring
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
                "metadata": output.metadata or {}
            }
            model_outputs.append(output_dict)
        
        async with ModernToolsIntegrationService() as tools_service:
            result = await tools_service.integrate_arize_phoenix(
                model_outputs=model_outputs,
                monitoring_config=request.monitoring_config
            )
            return ToolIntegrationResponse(**asdict(result))
        
    except Exception as e:
        logger.error(f"Error integrating with Arize Phoenix: {e}")
        raise HTTPException(status_code=500, detail=f"Arize Phoenix integration failed: {str(e)}")

@router.post("/aws-clarify", response_model=ToolIntegrationResponse)
async def integrate_aws_clarify(request: AWSClarifyRequest):
    """
    Integrate with AWS SageMaker Clarify for automated bias detection
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
                "metadata": output.metadata or {}
            }
            model_outputs.append(output_dict)
        
        async with ModernToolsIntegrationService() as tools_service:
            result = await tools_service.integrate_aws_clarify(
                model_outputs=model_outputs,
                sensitive_attributes=request.sensitive_attributes
            )
            return ToolIntegrationResponse(**asdict(result))
        
    except Exception as e:
        logger.error(f"Error integrating with AWS Clarify: {e}")
        raise HTTPException(status_code=500, detail=f"AWS Clarify integration failed: {str(e)}")

@router.post("/confident-ai", response_model=ToolIntegrationResponse)
async def integrate_confident_ai(request: ConfidentAIRequest):
    """
    Integrate with Confident AI for enterprise-grade bias detection
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
                "metadata": output.metadata or {}
            }
            model_outputs.append(output_dict)
        
        async with ModernToolsIntegrationService() as tools_service:
            result = await tools_service.integrate_confident_ai(
                model_outputs=model_outputs,
                compliance_frameworks=request.compliance_frameworks
            )
            return ToolIntegrationResponse(**asdict(result))
        
    except Exception as e:
        logger.error(f"Error integrating with Confident AI: {e}")
        raise HTTPException(status_code=500, detail=f"Confident AI integration failed: {str(e)}")

@router.post("/transformer-lens", response_model=ToolIntegrationResponse)
async def integrate_transformer_lens(request: TransformerLensRequest):
    """
    Integrate with TransformerLens for mechanistic interpretability
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
                "metadata": output.metadata or {}
            }
            model_outputs.append(output_dict)
        
        async with ModernToolsIntegrationService() as tools_service:
            result = await tools_service.integrate_transformer_lens(
                model_outputs=model_outputs,
                analysis_type=request.analysis_type
            )
            return ToolIntegrationResponse(**asdict(result))
        
    except Exception as e:
        logger.error(f"Error integrating with TransformerLens: {e}")
        raise HTTPException(status_code=500, detail=f"TransformerLens integration failed: {str(e)}")

@router.post("/bertviz", response_model=ToolIntegrationResponse)
async def integrate_bertviz(request: BertVizRequest):
    """
    Integrate with BertViz for attention visualization
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
                "metadata": output.metadata or {}
            }
            model_outputs.append(output_dict)
        
        async with ModernToolsIntegrationService() as tools_service:
            result = await tools_service.integrate_bertviz(
                model_outputs=model_outputs,
                visualization_type=request.visualization_type
            )
            return ToolIntegrationResponse(**asdict(result))
        
    except Exception as e:
        logger.error(f"Error integrating with BertViz: {e}")
        raise HTTPException(status_code=500, detail=f"BertViz integration failed: {str(e)}")

@router.get("/available-tools")
async def get_available_tools():
    """
    Get list of available tools and their configurations
    """
    try:
        async with ModernToolsIntegrationService() as tools_service:
            return {
                "tools": tools_service.get_available_tools(),
                "total_tools": len(tools_service.tool_configs)
            }
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available tools: {str(e)}")

@router.put("/configure-tool/{tool_id}")
async def configure_tool(tool_id: str, enabled: bool):
    """
    Configure tool enablement
    """
    try:
        async with ModernToolsIntegrationService() as tools_service:
            success = tools_service.configure_tool(tool_id, enabled)
            if success:
                return {
                    "message": f"Tool '{tool_id}' configured successfully",
                    "enabled": enabled
                }
            else:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure tool: {str(e)}")

@router.get("/tool-status")
async def get_tool_status():
    """
    Get status of all tools
    """
    try:
        async with ModernToolsIntegrationService() as tools_service:
            status = {}
            for tool_id, config in tools_service.tool_configs.items():
                status[tool_id] = {
                    "name": config["name"],
                    "enabled": config["enabled"],
                    "description": config["description"]
                }
            return {
                "tools": status,
                "enabled_count": sum(1 for config in tools_service.tool_configs.values() if config["enabled"]),
                "total_count": len(tools_service.tool_configs)
            }
    except Exception as e:
        logger.error(f"Error getting tool status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tool status: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check for the modern tools integration service
    """
    try:
        async with ModernToolsIntegrationService() as tools_service:
            enabled_tools = sum(1 for config in tools_service.tool_configs.values() if config["enabled"])
            return {
                "status": "healthy",
                "service": "modern_tools_integration",
                "timestamp": datetime.now().isoformat(),
                "total_tools": len(tools_service.tool_configs),
                "enabled_tools": enabled_tools
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Background task functions

async def _log_tool_integration(tools_used: List[str], success_rate: float):
    """Log tool integration for audit trail"""
    try:
        logger.info(f"Tool integration completed - Tools: {tools_used}, Success rate: {success_rate:.2f}")
        # Here you could add database logging, metrics collection, etc.
    except Exception as e:
        logger.error(f"Error logging tool integration: {e}")

# Additional utility endpoints

@router.post("/batch-integration")
async def batch_tool_integration(
    requests: List[ToolIntegrationRequest],
    background_tasks: BackgroundTasks
):
    """
    Perform batch tool integration for multiple datasets
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
                    "metadata": output.metadata or {}
                }
                model_outputs.append(output_dict)
            
            # Run integration
            async with ModernToolsIntegrationService() as tools_service:
                result = await tools_service.run_comprehensive_tool_integration(
                    model_outputs=model_outputs,
                    selected_tools=request.selected_tools
                )
                results.append(result)
        
        # Log batch integration
        background_tasks.add_task(
            _log_batch_integration,
            len(requests),
            [len(r) for r in results]
        )
        
        return {
            "batch_results": results,
            "total_integrations": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch tool integration: {e}")
        raise HTTPException(status_code=500, detail=f"Batch integration failed: {str(e)}")

async def _log_batch_integration(count: int, result_counts: List[int]):
    """Log batch integration for audit trail"""
    try:
        logger.info(f"Batch tool integration completed - Count: {count}, Results: {result_counts}")
    except Exception as e:
        logger.error(f"Error logging batch integration: {e}")

@router.get("/integration-history")
async def get_integration_history(limit: int = 10):
    """
    Get recent integration history (placeholder - would integrate with database)
    """
    try:
        # This would typically query a database for integration history
        return {
            "message": "Integration history endpoint - would integrate with database",
            "limit": limit,
            "note": "This is a placeholder implementation"
        }
    except Exception as e:
        logger.error(f"Error getting integration history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get integration history: {str(e)}")

