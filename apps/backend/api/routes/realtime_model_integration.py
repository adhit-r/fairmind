"""
Real-time Model Integration API Routes
Provides endpoints for real-time model integration and bias testing
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ..services.realtime_model_integration_service import (
    RealTimeModelIntegrationService,
    ModelConfig,
    ModelProvider,
    ModelType,
    BiasTestType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/realtime-model-integration", tags=["Real-time Model Integration"])

# Initialize service
realtime_service = RealTimeModelIntegrationService()

# Request/Response Models
class ModelConfigRequest(BaseModel):
    """Request model for configuring a model"""
    provider: str = Field(..., description="Model provider (openai, anthropic, google, cohere, huggingface, local)")
    model_name: str = Field(..., description="Name of the model")
    model_type: str = Field("chat_completion", description="Type of model")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for API calls")
    max_tokens: int = Field(1000, description="Maximum tokens in response")
    temperature: float = Field(0.7, description="Temperature for generation")
    top_p: float = Field(1.0, description="Top-p for generation")
    frequency_penalty: float = Field(0.0, description="Frequency penalty")
    presence_penalty: float = Field(0.0, description="Presence penalty")
    timeout: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")

class BiasTestRequest(BaseModel):
    """Request model for performing bias tests"""
    model_config: ModelConfigRequest = Field(..., description="Model configuration")
    test_type: str = Field(..., description="Type of bias test to perform")
    test_groups: List[str] = Field(..., description="Groups to test for bias")
    custom_prompt: Optional[str] = Field(None, description="Custom test prompt")

class ComprehensiveAnalysisRequest(BaseModel):
    """Request model for comprehensive bias analysis"""
    model_config: ModelConfigRequest = Field(..., description="Model configuration")
    test_groups: List[str] = Field(..., description="Groups to test for bias")
    custom_tests: Optional[List[Dict[str, Any]]] = Field(None, description="Custom test configurations")
    include_all_tests: bool = Field(True, description="Include all available bias tests")

class ConnectionTestRequest(BaseModel):
    """Request model for testing model connection"""
    model_config: ModelConfigRequest = Field(..., description="Model configuration")

class BiasTestResponse(BaseModel):
    """Response model for bias test results"""
    success: bool
    test_type: str
    prompt: str
    model_response: Dict[str, Any]
    bias_score: float
    bias_indicators_found: List[str]
    protected_attributes_affected: List[str]
    confidence_score: float
    explanation: str
    recommendations: List[str]
    timestamp: datetime

class ComprehensiveAnalysisResponse(BaseModel):
    """Response model for comprehensive analysis results"""
    success: bool
    analysis_id: str
    timestamp: datetime
    model_name: str
    provider: str
    tests_performed: List[str]
    overall_bias_score: float
    test_results: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any]

class ConnectionTestResponse(BaseModel):
    """Response model for connection test results"""
    success: bool
    response_time: float
    response: str
    tokens_used: int
    timestamp: datetime

@router.get("/", summary="Get real-time model integration capabilities")
async def get_capabilities():
    """Get summary of real-time model integration capabilities"""
    try:
        providers = await realtime_service.get_supported_providers()
        test_types = await realtime_service.get_bias_test_types()
        
        return {
            "success": True,
            "capabilities": {
                "providers": providers,
                "test_types": test_types
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting capabilities: {str(e)}")

@router.post("/configure-model", summary="Configure a model for real-time integration")
async def configure_model(request: ModelConfigRequest):
    """
    Configure a model for real-time bias testing
    
    This endpoint allows you to configure various model providers
    for real-time bias detection and analysis.
    """
    try:
        # Convert request to ModelConfig
        config = ModelConfig(
            provider=ModelProvider(request.provider),
            model_name=request.model_name,
            model_type=ModelType(request.model_type),
            api_key=request.api_key,
            base_url=request.base_url,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            timeout=request.timeout,
            retry_attempts=request.retry_attempts
        )
        
        success = realtime_service.configure_model(config)
        
        if success:
            return {
                "success": True,
                "message": f"Model {request.model_name} configured successfully",
                "config_key": f"{request.provider}_{request.model_name}",
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to configure model")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Error configuring model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error configuring model: {str(e)}")

@router.post("/test-connection", response_model=ConnectionTestResponse, summary="Test connection to a model")
async def test_connection(request: ConnectionTestRequest):
    """
    Test connection to a configured model
    
    This endpoint tests the connection to a model by sending
    a simple test prompt and measuring response time.
    """
    try:
        # Convert request to ModelConfig
        config = ModelConfig(
            provider=ModelProvider(request.model_config.provider),
            model_name=request.model_config.model_name,
            model_type=ModelType(request.model_config.model_type),
            api_key=request.model_config.api_key,
            base_url=request.model_config.base_url,
            max_tokens=request.model_config.max_tokens,
            temperature=request.model_config.temperature,
            top_p=request.model_config.top_p,
            frequency_penalty=request.model_config.frequency_penalty,
            presence_penalty=request.model_config.presence_penalty,
            timeout=request.model_config.timeout,
            retry_attempts=request.model_config.retry_attempts
        )
        
        async with realtime_service:
            result = await realtime_service.test_model_connection(config)
        
        return ConnectionTestResponse(
            success=result["success"],
            response_time=result.get("response_time", 0),
            response=result.get("response", ""),
            tokens_used=result.get("tokens_used", 0),
            timestamp=result["timestamp"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing connection: {str(e)}")

@router.post("/bias-test", response_model=BiasTestResponse, summary="Perform a single bias test")
async def perform_bias_test(request: BiasTestRequest):
    """
    Perform a single bias test on a model
    
    This endpoint performs a specific type of bias test on a configured model
    using the specified test groups.
    """
    try:
        # Convert request to ModelConfig
        config = ModelConfig(
            provider=ModelProvider(request.model_config.provider),
            model_name=request.model_config.model_name,
            model_type=ModelType(request.model_config.model_type),
            api_key=request.model_config.api_key,
            base_url=request.model_config.base_url,
            max_tokens=request.model_config.max_tokens,
            temperature=request.model_config.temperature,
            top_p=request.model_config.top_p,
            frequency_penalty=request.model_config.frequency_penalty,
            presence_penalty=request.model_config.presence_penalty,
            timeout=request.model_config.timeout,
            retry_attempts=request.model_config.retry_attempts
        )
        
        async with realtime_service:
            result = await realtime_service.perform_bias_test(
                config=config,
                test_type=BiasTestType(request.test_type),
                test_groups=request.test_groups,
                custom_prompt=request.custom_prompt
            )
        
        return BiasTestResponse(
            success=True,
            test_type=result.test_type.value,
            prompt=result.prompt,
            model_response={
                "provider": result.model_response.provider.value,
                "model_name": result.model_response.model_name,
                "response_text": result.model_response.response_text,
                "tokens_used": result.model_response.tokens_used,
                "response_time": result.model_response.response_time,
                "timestamp": result.model_response.timestamp.isoformat(),
                "metadata": result.model_response.metadata
            },
            bias_score=result.bias_score,
            bias_indicators_found=result.bias_indicators_found,
            protected_attributes_affected=result.protected_attributes_affected,
            confidence_score=result.confidence_score,
            explanation=result.explanation,
            recommendations=result.recommendations,
            timestamp=datetime.now()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Error performing bias test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing bias test: {str(e)}")

@router.post("/comprehensive-analysis", response_model=ComprehensiveAnalysisResponse, summary="Perform comprehensive bias analysis")
async def perform_comprehensive_analysis(request: ComprehensiveAnalysisRequest):
    """
    Perform comprehensive bias analysis on a model
    
    This endpoint performs all available bias tests on a configured model
    and provides a comprehensive analysis with recommendations.
    """
    try:
        # Convert request to ModelConfig
        config = ModelConfig(
            provider=ModelProvider(request.model_config.provider),
            model_name=request.model_config.model_name,
            model_type=ModelType(request.model_config.model_type),
            api_key=request.model_config.api_key,
            base_url=request.model_config.base_url,
            max_tokens=request.model_config.max_tokens,
            temperature=request.model_config.temperature,
            top_p=request.model_config.top_p,
            frequency_penalty=request.model_config.frequency_penalty,
            presence_penalty=request.model_config.presence_penalty,
            timeout=request.model_config.timeout,
            retry_attempts=request.model_config.retry_attempts
        )
        
        async with realtime_service:
            result = await realtime_service.perform_comprehensive_bias_analysis(
                config=config,
                test_groups=request.test_groups,
                custom_tests=request.custom_tests
            )
        
        # Convert test results to dict format
        test_results_dict = []
        for test_result in result.test_results:
            test_results_dict.append({
                "test_type": test_result.test_type.value,
                "prompt": test_result.prompt,
                "bias_score": test_result.bias_score,
                "bias_indicators_found": test_result.bias_indicators_found,
                "protected_attributes_affected": test_result.protected_attributes_affected,
                "confidence_score": test_result.confidence_score,
                "explanation": test_result.explanation,
                "recommendations": test_result.recommendations,
                "model_response": {
                    "provider": test_result.model_response.provider.value,
                    "model_name": test_result.model_response.model_name,
                    "response_text": test_result.model_response.response_text,
                    "tokens_used": test_result.model_response.tokens_used,
                    "response_time": test_result.model_response.response_time,
                    "timestamp": test_result.model_response.timestamp.isoformat()
                }
            })
        
        return ComprehensiveAnalysisResponse(
            success=True,
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            model_name=result.model_config.model_name,
            provider=result.model_config.provider.value,
            tests_performed=[test.value for test in result.tests_performed],
            overall_bias_score=result.overall_bias_score,
            test_results=test_results_dict,
            risk_assessment=result.risk_assessment,
            recommendations=result.recommendations,
            metadata=result.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Error performing comprehensive analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing comprehensive analysis: {str(e)}")

@router.get("/providers", summary="Get supported model providers")
async def get_providers():
    """Get list of supported model providers and their availability"""
    try:
        providers = await realtime_service.get_supported_providers()
        return {
            "success": True,
            "providers": providers,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting providers: {str(e)}")

@router.get("/bias-test-types", summary="Get available bias test types")
async def get_bias_test_types():
    """Get list of available bias test types and their configurations"""
    try:
        test_types = await realtime_service.get_bias_test_types()
        return {
            "success": True,
            "test_types": test_types,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting bias test types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting bias test types: {str(e)}")

@router.get("/health", summary="Health check for real-time model integration service")
async def health_check():
    """Health check endpoint for real-time model integration service"""
    try:
        # Test service capabilities
        providers = await realtime_service.get_supported_providers()
        test_types = await realtime_service.get_bias_test_types()
        
        return {
            "success": True,
            "status": "healthy",
            "service": "realtime_model_integration",
            "available_providers": len([p for p in providers["providers"] if p["available"]]),
            "total_providers": len(providers["providers"]),
            "bias_test_types": len(test_types["test_types"]),
            "dependencies": providers["dependencies"],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "service": "realtime_model_integration",
            "error": str(e),
            "timestamp": datetime.now()
        }
