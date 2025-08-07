# Backend API Design & Architecture

## 🏗️ Backend Architecture Overview

The Fairmind v2 backend follows a modern microservices architecture with clear separation of concerns:

- **ML Service**: FastAPI-based Python service for AI/ML operations
- **API Gateway**: Request routing and authentication
- **Database Layer**: Supabase PostgreSQL with ORM
- **Authentication**: Supabase Auth with JWT tokens
- **Real-time**: WebSockets and Server-Sent Events

## 🚀 FastAPI ML Service

### Service Structure

```
apps/ml-service/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── config/
│   ├── __init__.py
│   ├── settings.py        # Environment configuration
│   └── database.py        # Database connection
├── models/
│   ├── __init__.py
│   ├── requests.py        # Pydantic request models
│   ├── responses.py       # Pydantic response models
│   └── schemas.py         # Database schemas
├── services/
│   ├── __init__.py
│   ├── bias_analysis.py   # Bias detection algorithms
│   ├── explainability.py  # SHAP/LIME explanations
│   ├── compliance.py      # NIST compliance scoring
│   ├── monitoring.py      # Model drift detection
│   └── database.py        # Database operations
├── routers/
│   ├── __init__.py
│   ├── analysis.py        # Bias analysis endpoints
│   ├── explanation.py     # Model explanation endpoints
│   ├── compliance.py      # Compliance endpoints
│   └── monitoring.py      # Monitoring endpoints
├── utils/
│   ├── __init__.py
│   ├── auth.py           # Authentication helpers
│   ├── logging.py        # Structured logging
│   └── validators.py     # Data validation
└── tests/
    ├── __init__.py
    ├── test_analysis.py
    ├── test_explanation.py
    └── test_compliance.py
```

### FastAPI Application Setup

```python
# apps/ml-service/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from config.settings import settings
from routers import analysis, explanation, compliance, monitoring
from utils.auth import verify_token
from utils.logging import setup_logging

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Fairmind ML Service...")
    
    # Initialize services
    from services.bias_analysis import BiasAnalysisService
    from services.explainability import ExplainabilityService
    
    app.state.bias_service = BiasAnalysisService()
    app.state.explanation_service = ExplainabilityService()
    
    logger.info("ML Service initialized successfully")
    yield
    
    logger.info("Shutting down ML Service...")

# Create FastAPI application
app = FastAPI(
    title="Fairmind ML Service",
    description="AI Governance and Bias Detection API",
    version="2.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request.headers.get("x-request-id")}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT
    }

# Include routers
app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["Bias Analysis"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    explanation.router,
    prefix="/api/v1/explanation",
    tags=["Model Explanation"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    compliance.router,
    prefix="/api/v1/compliance",
    tags=["Compliance"],
    dependencies=[Depends(verify_token)]
)

app.include_router(
    monitoring.router,
    prefix="/api/v1/monitoring",
    tags=["Monitoring"],
    dependencies=[Depends(verify_token)]
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_config=None  # Use our custom logging config
    )
```

### Configuration Management

```python
# apps/ml-service/config/settings.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_CONNECTIONS: int = 20
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    
    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS & Security
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://app.fairmind.ai"]
    ALLOWED_HOSTS: List[str] = ["localhost", "api.fairmind.ai", "ml-service"]
    
    # ML Configuration
    MODEL_STORAGE_PATH: str = "/app/models"
    DATASET_STORAGE_PATH: str = "/app/datasets"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Performance
    WORKER_PROCESSES: int = 4
    WORKER_CONNECTIONS: int = 1000
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    
    # External Services
    REDIS_URL: Optional[str] = None
    CELERY_BROKER_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Request/Response Models

```python
# apps/ml-service/models/requests.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import pandas as pd

class AnalysisType(str, Enum):
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    INDIVIDUAL_FAIRNESS = "individual_fairness"
    COMPREHENSIVE = "comprehensive"

class ModelType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    RECOMMENDATION = "recommendation"

class BiasAnalysisRequest(BaseModel):
    model_id: str = Field(..., description="Unique identifier for the model")
    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    analysis_type: AnalysisType = Field(default=AnalysisType.COMPREHENSIVE)
    protected_attributes: List[str] = Field(..., description="List of protected/sensitive attributes")
    target_column: str = Field(..., description="Name of the target/outcome variable")
    prediction_column: Optional[str] = Field(default=None, description="Name of the prediction column")
    
    # Analysis parameters
    thresholds: Dict[str, float] = Field(
        default={"demographic_parity": 0.1, "equalized_odds": 0.1},
        description="Bias thresholds for different metrics"
    )
    
    # Advanced options
    enable_intersectional_analysis: bool = Field(default=True)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    bootstrap_samples: int = Field(default=1000, ge=100, le=10000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "550e8400-e29b-41d4-a716-446655440000",
                "dataset_id": "660e8400-e29b-41d4-a716-446655440001",
                "analysis_type": "comprehensive",
                "protected_attributes": ["gender", "race", "age_group"],
                "target_column": "approved",
                "prediction_column": "predicted_approval",
                "thresholds": {
                    "demographic_parity": 0.1,
                    "equalized_odds": 0.1
                },
                "enable_intersectional_analysis": True,
                "confidence_level": 0.95,
                "bootstrap_samples": 1000
            }
        }

class ExplanationRequest(BaseModel):
    model_id: str
    instance_id: Optional[str] = None
    instance_data: Optional[Dict[str, Any]] = None
    explanation_type: str = Field(..., regex="^(shap|lime|permutation|global)$")
    feature_names: Optional[List[str]] = None
    num_features: int = Field(default=10, ge=1, le=50)
    
    @validator('instance_data', 'instance_id')
    def validate_instance(cls, v, values):
        instance_id = values.get('instance_id')
        instance_data = values.get('instance_data')
        
        if not instance_id and not instance_data:
            raise ValueError("Either instance_id or instance_data must be provided")
            
        return v

class ComplianceRequest(BaseModel):
    model_id: str
    framework: str = Field(default="nist_ai_rmf", regex="^(nist_ai_rmf|eu_ai_act|iso_23053)$")
    assessment_scope: List[str] = Field(
        default=["bias", "transparency", "robustness", "privacy"],
        description="Areas to assess for compliance"
    )
    
class MonitoringRequest(BaseModel):
    model_id: str
    monitoring_type: str = Field(..., regex="^(drift|performance|bias|data_quality)$")
    reference_period: str = Field(default="30d", regex="^\\d+[dwmy]$")
    current_period: str = Field(default="7d", regex="^\\d+[dwmy]$")
    alert_threshold: float = Field(default=0.05, ge=0.001, le=0.5)
```

```python
# apps/ml-service/models/responses.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class BiasMetric(BaseModel):
    name: str
    value: float
    threshold: float
    status: str = Field(..., regex="^(pass|warning|fail)$")
    confidence_interval: Optional[Dict[str, float]] = None
    description: str

class GroupMetrics(BaseModel):
    group_name: str
    group_size: int
    metrics: Dict[str, float]
    comparison_metrics: Dict[str, float]

class BiasAnalysisResponse(BaseModel):
    analysis_id: str
    model_id: str
    dataset_id: str
    status: str
    
    # Core metrics
    overall_bias_score: float = Field(..., ge=0, le=1)
    compliance_score: float = Field(..., ge=0, le=100)
    
    # Detailed metrics
    demographic_parity: BiasMetric
    equalized_odds: BiasMetric
    individual_fairness: Optional[BiasMetric] = None
    
    # Group-level analysis
    group_metrics: List[GroupMetrics]
    intersectional_analysis: Optional[Dict[str, Any]] = None
    
    # Recommendations
    recommendations: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    
    # Metadata
    analysis_metadata: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "770e8400-e29b-41d4-a716-446655440002",
                "model_id": "550e8400-e29b-41d4-a716-446655440000",
                "dataset_id": "660e8400-e29b-41d4-a716-446655440001",
                "status": "completed",
                "overall_bias_score": 0.15,
                "compliance_score": 78.5,
                "demographic_parity": {
                    "name": "Demographic Parity",
                    "value": 0.12,
                    "threshold": 0.1,
                    "status": "warning",
                    "confidence_interval": {"lower": 0.08, "upper": 0.16},
                    "description": "Difference in positive prediction rates between groups"
                },
                "equalized_odds": {
                    "name": "Equalized Odds",
                    "value": 0.08,
                    "threshold": 0.1,
                    "status": "pass",
                    "confidence_interval": {"lower": 0.05, "upper": 0.11},
                    "description": "Difference in true positive rates between groups"
                },
                "group_metrics": [
                    {
                        "group_name": "Female",
                        "group_size": 5420,
                        "metrics": {"precision": 0.82, "recall": 0.79, "f1": 0.80},
                        "comparison_metrics": {"demographic_parity_diff": -0.12}
                    }
                ],
                "recommendations": [
                    {
                        "type": "data_augmentation",
                        "priority": "high",
                        "description": "Increase representation of underrepresented groups",
                        "implementation": "Collect additional data or use synthetic data generation"
                    }
                ],
                "risk_assessment": {
                    "overall_risk": "medium",
                    "risk_factors": ["demographic_imbalance", "threshold_violations"],
                    "mitigation_urgency": "moderate"
                }
            }
        }

class ExplanationResponse(BaseModel):
    explanation_id: str
    model_id: str
    explanation_type: str
    
    # SHAP values
    shap_values: Optional[Dict[str, Any]] = None
    
    # LIME explanation
    lime_explanation: Optional[Dict[str, Any]] = None
    
    # Feature importance
    feature_importance: List[Dict[str, float]]
    
    # Global explanations
    global_explanations: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime
    metadata: Dict[str, Any]

class ComplianceResponse(BaseModel):
    assessment_id: str
    model_id: str
    framework: str
    overall_score: float
    
    # Detailed scores by category
    bias_score: float
    transparency_score: float
    robustness_score: float
    privacy_score: float
    
    # Recommendations
    recommendations: List[Dict[str, Any]]
    
    # Compliance status
    compliance_status: str = Field(..., regex="^(compliant|non_compliant|conditional)$")
    
    created_at: datetime

class MonitoringResponse(BaseModel):
    monitoring_id: str
    model_id: str
    monitoring_type: str
    
    # Drift detection results
    drift_detected: bool
    drift_score: float
    drift_threshold: float
    
    # Detailed metrics
    metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    
    # Recommendations
    recommendations: List[str]
    
    created_at: datetime
```

### API Endpoints Implementation

```python
# apps/ml-service/routers/analysis.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
import logging

from models.requests import BiasAnalysisRequest
from models.responses import BiasAnalysisResponse
from services.bias_analysis import BiasAnalysisService
from services.database import DatabaseService
from utils.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/bias", response_model=BiasAnalysisResponse)
async def create_bias_analysis(
    request: BiasAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    bias_service: BiasAnalysisService = Depends(lambda: BiasAnalysisService()),
    db_service: DatabaseService = Depends(lambda: DatabaseService())
):
    """
    Create a new bias analysis for a model
    """
    try:
        # Validate user has access to the model
        model = await db_service.get_model(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check user permissions
        if not await db_service.user_has_model_access(current_user["id"], request.model_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Create analysis record
        analysis_id = await db_service.create_analysis_record(
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            created_by=current_user["id"],
            analysis_type=request.analysis_type,
            parameters=request.dict()
        )
        
        # Queue analysis for background processing
        background_tasks.add_task(
            bias_service.process_analysis,
            analysis_id=analysis_id,
            request=request
        )
        
        return BiasAnalysisResponse(
            analysis_id=analysis_id,
            model_id=request.model_id,
            dataset_id=request.dataset_id,
            status="queued",
            overall_bias_score=0.0,
            compliance_score=0.0,
            demographic_parity=BiasMetric(
                name="Demographic Parity",
                value=0.0,
                threshold=request.thresholds.get("demographic_parity", 0.1),
                status="pending",
                description="Analysis in progress"
            ),
            equalized_odds=BiasMetric(
                name="Equalized Odds",
                value=0.0,
                threshold=request.thresholds.get("equalized_odds", 0.1),
                status="pending",
                description="Analysis in progress"
            ),
            group_metrics=[],
            recommendations=[],
            risk_assessment={},
            analysis_metadata={"request_parameters": request.dict()},
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to create bias analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create analysis")

@router.get("/bias/{analysis_id}", response_model=BiasAnalysisResponse)
async def get_bias_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
    db_service: DatabaseService = Depends(lambda: DatabaseService())
):
    """
    Get bias analysis results by ID
    """
    try:
        analysis = await db_service.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check user permissions
        if not await db_service.user_has_analysis_access(current_user["id"], analysis_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bias analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")

@router.get("/bias/model/{model_id}", response_model=List[BiasAnalysisResponse])
async def get_model_analyses(
    model_id: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db_service: DatabaseService = Depends(lambda: DatabaseService())
):
    """
    Get all bias analyses for a specific model
    """
    try:
        # Check user permissions
        if not await db_service.user_has_model_access(current_user["id"], model_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        analyses = await db_service.get_model_analyses(
            model_id=model_id,
            limit=limit,
            offset=offset,
            status=status
        )
        
        return analyses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model analyses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve analyses")

@router.delete("/bias/{analysis_id}")
async def delete_bias_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
    db_service: DatabaseService = Depends(lambda: DatabaseService())
):
    """
    Delete a bias analysis
    """
    try:
        # Check user permissions
        if not await db_service.user_has_analysis_access(current_user["id"], analysis_id, write=True):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        await db_service.delete_analysis(analysis_id)
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete bias analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete analysis")
```

### Authentication & Authorization

```python
# apps/ml-service/utils/auth.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from config.settings import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthenticationError(Exception):
    pass

class AuthorizationError(Exception):
    pass

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token and return user information
    """
    try:
        token = credentials.credentials
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user information
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token: missing user ID")
        
        # Check token expiration
        exp: int = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            raise AuthenticationError("Token has expired")
        
        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "organization_id": payload.get("organization_id"),
            "permissions": payload.get("permissions", [])
        }
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Get current authenticated user
    """
    return token_data

async def require_permission(permission: str):
    """
    Dependency to require specific permission
    """
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        user_role = current_user.get("role", "user")
        
        # Admin role has all permissions
        if user_role == "admin":
            return current_user
        
        # Check specific permission
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission} required"
            )
        
        return current_user
    
    return permission_checker

# Permission decorators
require_model_read = require_permission("model:read")
require_model_write = require_permission("model:write")
require_analysis_create = require_permission("analysis:create")
require_analysis_read = require_permission("analysis:read")
require_compliance_access = require_permission("compliance:access")
```

This comprehensive backend design provides a robust, scalable, and secure foundation for the Fairmind v2 ML service with proper authentication, authorization, and API design patterns.
