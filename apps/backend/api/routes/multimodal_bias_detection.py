"""
Multimodal Bias Detection API Routes
Exposes bias detection capabilities for image, audio, and video generation models
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..services.multimodal_bias_detection_service import (
    MultimodalBiasDetectionService,
    ModalityType,
    MultimodalBiasType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/multimodal-bias", tags=["Multimodal Bias Detection"])

# Request/Response Models

class MultimodalModelOutput(BaseModel):
    """Model output for multimodal bias analysis"""
    text: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    protected_attributes: Optional[Dict[str, Any]] = None

class ImageBiasDetectionRequest(BaseModel):
    """Request for image generation bias detection"""
    model_outputs: List[MultimodalModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    analysis_config: Optional[Dict[str, Any]] = Field(default=None, description="Analysis configuration")

class AudioBiasDetectionRequest(BaseModel):
    """Request for audio generation bias detection"""
    model_outputs: List[MultimodalModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    analysis_config: Optional[Dict[str, Any]] = Field(default=None, description="Analysis configuration")

class VideoBiasDetectionRequest(BaseModel):
    """Request for video generation bias detection"""
    model_outputs: List[MultimodalModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    analysis_config: Optional[Dict[str, Any]] = Field(default=None, description="Analysis configuration")

class CrossModalBiasDetectionRequest(BaseModel):
    """Request for cross-modal bias detection"""
    model_outputs: List[MultimodalModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    modalities: List[str] = Field(..., min_items=2, description="Modalities to analyze")
    analysis_config: Optional[Dict[str, Any]] = Field(default=None, description="Analysis configuration")

class ComprehensiveMultimodalRequest(BaseModel):
    """Request for comprehensive multimodal bias analysis"""
    model_outputs: List[MultimodalModelOutput] = Field(..., min_items=1, description="Model outputs to analyze")
    modalities: List[str] = Field(..., min_items=1, description="Modalities to analyze")
    analysis_config: Optional[Dict[str, Any]] = Field(default=None, description="Analysis configuration")

class MultimodalBiasResult(BaseModel):
    """Response for multimodal bias detection"""
    modality: str
    bias_type: str
    bias_score: float
    confidence: float
    is_biased: bool
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: str

class ComprehensiveMultimodalResponse(BaseModel):
    """Response for comprehensive multimodal analysis"""
    timestamp: str
    modalities: List[str]
    individual_modality_results: Dict[str, List[MultimodalBiasResult]]
    cross_modal_results: List[MultimodalBiasResult]
    overall_assessment: Dict[str, Any]
    recommendations: List[str]

# API Endpoints

@router.post("/image-detection", response_model=List[MultimodalBiasResult])
async def detect_image_generation_bias(
    request: ImageBiasDetectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect bias in image generation models
    
    Implements techniques from the 2025 analysis:
    - Demographic representation analysis
    - Object detection bias
    - Scene and context bias
    - Style and aesthetic bias
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Initialize service
        bias_service = MultimodalBiasDetectionService()
        
        # Run image bias detection
        results = await bias_service.detect_image_generation_bias(
            model_outputs=model_outputs,
            analysis_config=request.analysis_config
        )
        
        # Log analysis for audit trail
        background_tasks.add_task(
            _log_multimodal_analysis,
            "image",
            len(model_outputs),
            len([r for r in results if r.is_biased])
        )
        
        # Convert to response format
        return [
            MultimodalBiasResult(
                modality=result.modality.value,
                bias_type=result.bias_type.value,
                bias_score=result.bias_score,
                confidence=result.confidence,
                is_biased=result.is_biased,
                details=result.details,
                recommendations=result.recommendations,
                timestamp=result.timestamp
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error in image generation bias detection: {e}")
        raise HTTPException(status_code=500, detail=f"Image bias detection failed: {str(e)}")

@router.post("/audio-detection", response_model=List[MultimodalBiasResult])
async def detect_audio_generation_bias(
    request: AudioBiasDetectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect bias in audio generation models
    
    Implements techniques from the 2025 analysis:
    - Voice characteristic bias
    - Accent and language bias
    - Content and semantic bias
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Initialize service
        bias_service = MultimodalBiasDetectionService()
        
        # Run audio bias detection
        results = await bias_service.detect_audio_generation_bias(
            model_outputs=model_outputs,
            analysis_config=request.analysis_config
        )
        
        # Log analysis for audit trail
        background_tasks.add_task(
            _log_multimodal_analysis,
            "audio",
            len(model_outputs),
            len([r for r in results if r.is_biased])
        )
        
        # Convert to response format
        return [
            MultimodalBiasResult(
                modality=result.modality.value,
                bias_type=result.bias_type.value,
                bias_score=result.bias_score,
                confidence=result.confidence,
                is_biased=result.is_biased,
                details=result.details,
                recommendations=result.recommendations,
                timestamp=result.timestamp
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error in audio generation bias detection: {e}")
        raise HTTPException(status_code=500, detail=f"Audio bias detection failed: {str(e)}")

@router.post("/video-detection", response_model=List[MultimodalBiasResult])
async def detect_video_generation_bias(
    request: VideoBiasDetectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect bias in video generation models
    
    Implements techniques from the 2025 analysis:
    - Motion and activity bias
    - Temporal and sequence bias
    - Scene and environment bias
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Initialize service
        bias_service = MultimodalBiasDetectionService()
        
        # Run video bias detection
        results = await bias_service.detect_video_generation_bias(
            model_outputs=model_outputs,
            analysis_config=request.analysis_config
        )
        
        # Log analysis for audit trail
        background_tasks.add_task(
            _log_multimodal_analysis,
            "video",
            len(model_outputs),
            len([r for r in results if r.is_biased])
        )
        
        # Convert to response format
        return [
            MultimodalBiasResult(
                modality=result.modality.value,
                bias_type=result.bias_type.value,
                bias_score=result.bias_score,
                confidence=result.confidence,
                is_biased=result.is_biased,
                details=result.details,
                recommendations=result.recommendations,
                timestamp=result.timestamp
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error in video generation bias detection: {e}")
        raise HTTPException(status_code=500, detail=f"Video bias detection failed: {str(e)}")

@router.post("/cross-modal-detection", response_model=List[MultimodalBiasResult])
async def detect_cross_modal_bias(
    request: CrossModalBiasDetectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect cross-modal bias interactions
    
    Implements cross-modal bias analysis from the 2025 analysis:
    - Modality preference analysis
    - Cross-modal stereotype detection
    - Interaction effect analysis
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Validate modalities
        try:
            modalities = [ModalityType(mod) for mod in request.modalities]
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid modality: {e}. Valid modalities: {[m.value for m in ModalityType]}"
            )
        
        # Initialize service
        bias_service = MultimodalBiasDetectionService()
        
        # Run cross-modal bias detection
        results = await bias_service.detect_cross_modal_bias(
            model_outputs=model_outputs,
            modalities=modalities,
            analysis_config=request.analysis_config
        )
        
        # Log analysis for audit trail
        background_tasks.add_task(
            _log_multimodal_analysis,
            f"cross-modal_{'-'.join(request.modalities)}",
            len(model_outputs),
            len([r for r in results if r.is_biased])
        )
        
        # Convert to response format
        return [
            MultimodalBiasResult(
                modality=result.modality.value,
                bias_type=result.bias_type.value,
                bias_score=result.bias_score,
                confidence=result.confidence,
                is_biased=result.is_biased,
                details=result.details,
                recommendations=result.recommendations,
                timestamp=result.timestamp
            )
            for result in results
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cross-modal bias detection: {e}")
        raise HTTPException(status_code=500, detail=f"Cross-modal bias detection failed: {str(e)}")

@router.post("/comprehensive-analysis", response_model=ComprehensiveMultimodalResponse)
async def comprehensive_multimodal_analysis(
    request: ComprehensiveMultimodalRequest,
    background_tasks: BackgroundTasks
):
    """
    Run comprehensive multimodal bias analysis
    
    Combines individual modality analysis with cross-modal analysis
    """
    try:
        # Convert request model outputs
        model_outputs = []
        for output in request.model_outputs:
            output_dict = {
                "text": output.text,
                "image_url": output.image_url,
                "audio_url": output.audio_url,
                "video_url": output.video_url,
                "metadata": output.metadata or {},
                "protected_attributes": output.protected_attributes or {}
            }
            model_outputs.append(output_dict)
        
        # Validate modalities
        try:
            modalities = [ModalityType(mod) for mod in request.modalities]
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid modality: {e}. Valid modalities: {[m.value for m in ModalityType]}"
            )
        
        # Initialize service
        bias_service = MultimodalBiasDetectionService()
        
        # Run comprehensive analysis
        results = await bias_service.comprehensive_multimodal_analysis(
            model_outputs=model_outputs,
            modalities=modalities,
            analysis_config=request.analysis_config
        )
        
        # Log analysis for audit trail
        background_tasks.add_task(
            _log_comprehensive_multimodal_analysis,
            request.modalities,
            len(model_outputs),
            results["overall_assessment"]["risk_level"]
        )
        
        # Convert to response format
        response = ComprehensiveMultimodalResponse(
            timestamp=results["timestamp"],
            modalities=results["modalities"],
            individual_modality_results={},
            cross_modal_results=[],
            overall_assessment=results["overall_assessment"],
            recommendations=results["recommendations"]
        )
        
        # Convert individual modality results
        for modality, modality_results in results["individual_modality_results"].items():
            response.individual_modality_results[modality] = [
                MultimodalBiasResult(**result) for result in modality_results
            ]
        
        # Convert cross-modal results
        response.cross_modal_results = [
            MultimodalBiasResult(**result) for result in results["cross_modal_results"]
        ]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive multimodal analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Comprehensive multimodal analysis failed: {str(e)}")

@router.get("/available-modalities")
async def get_available_modalities():
    """
    Get available modality types for analysis
    """
    try:
        return {
            "modalities": [modality.value for modality in ModalityType],
            "bias_types": [bias_type.value for bias_type in MultimodalBiasType],
            "total_modalities": len(ModalityType),
            "total_bias_types": len(MultimodalBiasType)
        }
    except Exception as e:
        logger.error(f"Error getting available modalities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available modalities: {str(e)}")

@router.get("/bias-detectors")
async def get_bias_detectors():
    """
    Get available bias detectors for each modality
    """
    try:
        bias_service = MultimodalBiasDetectionService()
        return {
            "bias_detectors": bias_service.bias_detectors,
            "cross_modal_analyzers": bias_service.cross_modal_analyzers
        }
    except Exception as e:
        logger.error(f"Error getting bias detectors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bias detectors: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check for the multimodal bias detection service
    """
    try:
        bias_service = MultimodalBiasDetectionService()
        return {
            "status": "healthy",
            "service": "multimodal_bias_detection",
            "timestamp": datetime.now().isoformat(),
            "available_modalities": len(ModalityType),
            "available_bias_types": len(MultimodalBiasType),
            "bias_detectors": len(bias_service.bias_detectors),
            "cross_modal_analyzers": len(bias_service.cross_modal_analyzers)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Background task functions

async def _log_multimodal_analysis(
    modality: str, 
    sample_count: int, 
    biased_count: int
):
    """Log multimodal analysis for audit trail"""
    try:
        logger.info(f"Multimodal bias analysis completed - Modality: {modality}, Samples: {sample_count}, Biased: {biased_count}")
        # Here you could add database logging, metrics collection, etc.
    except Exception as e:
        logger.error(f"Error logging multimodal analysis: {e}")

async def _log_comprehensive_multimodal_analysis(
    modalities: List[str], 
    sample_count: int, 
    risk_level: str
):
    """Log comprehensive multimodal analysis for audit trail"""
    try:
        logger.info(f"Comprehensive multimodal analysis completed - Modalities: {modalities}, Samples: {sample_count}, Risk: {risk_level}")
        # Here you could add database logging, metrics collection, etc.
    except Exception as e:
        logger.error(f"Error logging comprehensive multimodal analysis: {e}")

# Additional utility endpoints

@router.post("/batch-analysis")
async def batch_multimodal_analysis(
    requests: List[ComprehensiveMultimodalRequest],
    background_tasks: BackgroundTasks
):
    """
    Perform batch multimodal bias analysis for multiple datasets
    """
    try:
        results = []
        for request in requests:
            # Convert request model outputs
            model_outputs = []
            for output in request.model_outputs:
                output_dict = {
                    "text": output.text,
                    "image_url": output.image_url,
                    "audio_url": output.audio_url,
                    "video_url": output.video_url,
                    "metadata": output.metadata or {},
                    "protected_attributes": output.protected_attributes or {}
                }
                model_outputs.append(output_dict)
            
            # Validate modalities
            try:
                modalities = [ModalityType(mod) for mod in request.modalities]
            except ValueError as e:
                continue  # Skip invalid requests
            
            # Run analysis
            bias_service = MultimodalBiasDetectionService()
            result = await bias_service.comprehensive_multimodal_analysis(
                model_outputs=model_outputs,
                modalities=modalities,
                analysis_config=request.analysis_config
            )
            results.append(result)
        
        # Log batch analysis
        background_tasks.add_task(
            _log_batch_multimodal_analysis,
            len(requests),
            [r["overall_assessment"]["risk_level"] for r in results]
        )
        
        return {
            "batch_results": results,
            "total_analyses": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch multimodal analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

async def _log_batch_multimodal_analysis(count: int, risk_levels: List[str]):
    """Log batch multimodal analysis for audit trail"""
    try:
        logger.info(f"Batch multimodal analysis completed - Count: {count}, Risk levels: {risk_levels}")
    except Exception as e:
        logger.error(f"Error logging batch multimodal analysis: {e}")
