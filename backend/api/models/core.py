"""
Core data models for the Fairmind API
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ModelPrediction(BaseModel):
    prediction: float
    confidence: float
    model_id: str
    timestamp: datetime

class BiasAnalysisRequest(BaseModel):
    model_id: str
    dataset_id: str
    sensitive_columns: List[str]
    target_column: str
    analysis_type: str = "comprehensive"

class BiasAnalysisResponse(BaseModel):
    analysis_id: str
    model_id: str
    dataset_id: str
    overall_bias_score: float
    bias_metrics: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime
    status: str

class ModelUploadRequest(BaseModel):
    name: str
    description: str
    model_type: str
    version: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    model_type: str
    version: str
    upload_date: datetime
    file_path: str
    file_size: int
    tags: List[str]
    metadata: Dict[str, Any]

class DatasetInfo(BaseModel):
    id: str
    name: str
    description: str
    source: str
    size: int
    columns: List[str]
    upload_date: datetime
    tags: List[str]

class SecurityTestRequest(BaseModel):
    model_id: str
    test_type: str
    parameters: Dict[str, Any] = {}

class SecurityTestResponse(BaseModel):
    test_id: str
    model_id: str
    test_type: str
    results: Dict[str, Any]
    vulnerabilities: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: datetime

class ProvenanceRequest(BaseModel):
    model_id: str
    dataset_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ProvenanceResponse(BaseModel):
    provenance_id: str
    model_id: str
    dataset_id: Optional[str]
    checksum: str
    signature: str
    metadata: Dict[str, Any]
    timestamp: datetime

class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: datetime
    severity: str = "info"
    metadata: Dict[str, Any] = {}

class MetricsSummary(BaseModel):
    total_models: int
    total_datasets: int
    active_analyses: int
    security_score: float
    compliance_score: float
    bias_score: float
    last_updated: datetime

