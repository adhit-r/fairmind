"""
Bias Detection Domain Routes.

Handles LLM and Multimodal bias detection operations.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel

from core.container import inject
from core.exceptions import AppException
from domain.bias_detection.services.bias_detection_service import BiasDetectionService
from domain.bias_detection.services.llm_bias_service import LLMBiasDetectionService, BiasCategory
from domain.bias_detection.services.multimodal_bias_service import MultimodalBiasDetectionService, ModalityType


router = APIRouter(prefix="/api/v1/bias", tags=["bias-detection"])


# Request Models
class BiasAnalysisRequest(BaseModel):
    """Request model for bias analysis."""
    dataset_id: Optional[str] = None
    model_id: Optional[str] = None
    sensitive_attributes: List[str]
    target_column: Optional[str] = None
    model_outputs: Optional[List[Dict[str, Any]]] = None
    category: Optional[BiasCategory] = None
    modalities: Optional[List[ModalityType]] = None


from domain.dataset.services.dataset_service import DatasetService
from database.connection import db_manager
from sqlalchemy import text
import json
from datetime import datetime, timezone
import uuid

@router.post("/analyze/dataset")
async def analyze_dataset_bias(
    request: BiasAnalysisRequest,
    service: BiasDetectionService = Depends(lambda: inject(BiasDetectionService)),
    dataset_service: DatasetService = Depends(lambda: inject(DatasetService))
):
    """
    Analyze bias in a dataset.
    """
    if not request.dataset_id:
        raise HTTPException(status_code=400, detail="dataset_id required")
        
    try:
        # Run analysis
        # Pass dataset_id directly to let service handle DuckDB optimization
        result = await service.analyze_dataset_bias(
            dataset_or_df=request.dataset_id,
            sensitive_attributes=request.sensitive_attributes,
            target_column=request.target_column or "target"
        )
        
        # Persist result if model_id is provided or just as a dataset analysis
        analysis_id = str(uuid.uuid4())
        
        # Save to database
        with db_manager.get_session() as session:
            insert_query = text("""
                INSERT INTO bias_analyses (
                    id, model_id, dataset_id, analysis_type, status,
                    results, metrics, created_at, completed_at
                ) VALUES (
                    :id, :model_id, :dataset_id, :analysis_type, :status,
                    :results, :metrics, :created_at, :completed_at
                )
            """)
            
            # Extract metrics and results
            metrics_data = result.fairness_metrics if hasattr(result, 'fairness_metrics') else {}
            
            # Calculate overall score
            total_checks = 0
            passed_checks = 0
            
            for attr, metrics in metrics_data.items():
                if 'demographic_parity' in metrics:
                    total_checks += 1
                    if metrics['demographic_parity'].get('fair', False):
                        passed_checks += 1
                if 'equality_of_opportunity' in metrics:
                    total_checks += 1
                    if metrics['equality_of_opportunity'].get('fair', False):
                        passed_checks += 1
                if 'statistical_parity' in metrics:
                    total_checks += 1
                    if metrics['statistical_parity'].get('fair', False):
                        passed_checks += 1
            
            overall_score = passed_checks / total_checks if total_checks > 0 else 0.0
            metrics_data['overall_score'] = overall_score

            results_data = {
                "dataset_info": result.dataset_info if hasattr(result, 'dataset_info') else {},
                "data_quality": result.data_quality if hasattr(result, 'data_quality') else {},
                "bias_detection": result.bias_detection if hasattr(result, 'bias_detection') else {},
                "recommendations": result.recommendations if hasattr(result, 'recommendations') else []
            }
            
            session.execute(insert_query, {
                "id": analysis_id,
                "model_id": request.model_id or "unknown", # Handle case where model_id is optional but required by DB
                "dataset_id": request.dataset_id,
                "analysis_type": "dataset_bias",
                "status": "completed",
                "results": json.dumps(results_data),
                "metrics": json.dumps(metrics_data),
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc)
            })
            session.commit()
        
        # Return result with analysis_id
        # We need to convert dataclass to dict and add analysis_id
        result_dict = result.__dict__ if hasattr(result, '__dict__') else result
        if isinstance(result_dict, dict):
             result_dict['analysis_id'] = analysis_id
             
        return result_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/llm")
async def analyze_llm_bias(
    request: BiasAnalysisRequest,
    service: LLMBiasDetectionService = Depends(lambda: inject(LLMBiasDetectionService))
):
    """
    Analyze bias in LLM outputs.
    """
    if not request.model_outputs or not request.category:
        raise HTTPException(status_code=400, detail="model_outputs and category required")
        
    result = await service.detect_bias(
        model_outputs=request.model_outputs,
        category=request.category
    )
    
    return result


@router.post("/analyze/multimodal")
async def analyze_multimodal_bias(
    request: BiasAnalysisRequest,
    service: MultimodalBiasDetectionService = Depends(lambda: inject(MultimodalBiasDetectionService))
):
    """
    Analyze bias in multimodal outputs.
    """
    if not request.model_outputs or not request.modalities:
        raise HTTPException(status_code=400, detail="model_outputs and modalities required")
        
    result = await service.comprehensive_multimodal_analysis(
        model_outputs=request.model_outputs,
        modalities=request.modalities
    )
    
    return result
