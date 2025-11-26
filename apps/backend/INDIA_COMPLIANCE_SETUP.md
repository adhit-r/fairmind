# India Compliance Automation - Setup Guide

This document describes the database schema and Pydantic models for India-specific AI compliance automation.

## Overview

The India Compliance Automation feature extends FairMind's compliance system with:
- India-specific regulatory frameworks (DPDP Act 2023, NITI Aayog principles, MeitY guidelines)
- Automated evidence collection for Indian compliance requirements
- India-specific bias detection for caste, religion, language, and regional demographics
- Integration with leading compliance tools
- AI-powered compliance automation

## Database Schema

### Migration File
- **Location**: `apps/backend/migrations/002_india_compliance_schema.sql`
- **Tables Created**: 5 main tables with comprehensive indexing

### Tables

#### 1. india_compliance_evidence
Stores evidence collected for compliance controls.

**Columns**:
- `id` (UUID): Primary key
- `system_id` (VARCHAR): System identifier
- `control_id` (VARCHAR): Control identifier (e.g., "DL_001", "CM_001")
- `evidence_type` (VARCHAR): Type of evidence (e.g., "data_location", "consent_record")
- `evidence_data` (JSONB): Evidence data payload
- `evidence_hash` (VARCHAR): SHA-256 hash for integrity verification
- `collected_at` (TIMESTAMP): When evidence was collected
- `source` (VARCHAR): Source of evidence (e.g., "onetrust", "manual", "automated")
- `metadata` (JSONB): Additional metadata
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Record update timestamp

**Indexes**:
- `system_id` - for querying by system
- `control_id` - for querying by control
- `collected_at` - for time-based queries
- `source` - for filtering by source

#### 2. india_compliance_results
Stores compliance check results for each framework.

**Columns**:
- `id` (UUID): Primary key
- `system_id` (VARCHAR): System identifier
- `user_id` (VARCHAR): User who ran the check
- `framework` (ENUM): Framework checked (dpdp_act_2023, niti_aayog_principles, meity_guidelines, digital_india_act)
- `overall_score` (FLOAT): Overall compliance score (0-100)
- `status` (ENUM): Compliance status (compliant, non_compliant, pending, under_review, partial)
- `requirements_met` (INTEGER): Number of requirements met
- `total_requirements` (INTEGER): Total requirements in framework
- `evidence_count` (INTEGER): Number of evidence items collected
- `results` (JSONB): Detailed results by requirement
- `gaps` (JSONB): Identified compliance gaps
- `timestamp` (TIMESTAMP): When check was performed
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Record update timestamp

**Indexes**:
- `system_id` - for querying by system
- `user_id` - for querying by user
- `framework` - for filtering by framework
- `status` - for filtering by status
- `timestamp` - for time-based queries

#### 3. india_bias_test_results
Stores results of India-specific bias detection tests.

**Columns**:
- `id` (UUID): Primary key
- `test_id` (VARCHAR): Unique test identifier
- `system_id` (VARCHAR): System identifier
- `user_id` (VARCHAR): User who ran the test
- `model_id` (VARCHAR): Model tested
- `bias_type` (ENUM): Type of bias (caste_bias, religious_bias, linguistic_bias, regional_bias, gender_bias, intersectional_bias)
- `bias_detected` (BOOLEAN): Whether bias was detected
- `severity` (ENUM): Bias severity (critical, high, medium, low)
- `affected_groups` (JSONB): Groups affected by bias
- `fairness_metrics` (JSONB): Fairness metrics (demographic_parity, equal_opportunity, equalized_odds, predictive_parity)
- `recommendations` (JSONB): Mitigation recommendations
- `timestamp` (TIMESTAMP): When test was performed
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Record update timestamp

**Indexes**:
- `system_id` - for querying by system
- `user_id` - for querying by user
- `model_id` - for querying by model
- `bias_type` - for filtering by bias type
- `timestamp` - for time-based queries

#### 4. india_compliance_reports
Stores generated compliance reports.

**Columns**:
- `id` (UUID): Primary key
- `report_id` (VARCHAR): Unique report identifier
- `system_id` (VARCHAR): System identifier
- `user_id` (VARCHAR): User who generated the report
- `frameworks` (JSONB): Frameworks included in report
- `overall_score` (FLOAT): Overall compliance score
- `report_data` (JSONB): Complete report data
- `generated_at` (TIMESTAMP): When report was generated
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Record update timestamp

**Indexes**:
- `system_id` - for querying by system
- `user_id` - for querying by user
- `generated_at` - for time-based queries

#### 5. integration_credentials
Stores encrypted credentials for external integrations.

**Columns**:
- `id` (UUID): Primary key
- `user_id` (VARCHAR): User who configured the integration
- `integration_name` (VARCHAR): Name of integration (onetrust, securiti, sprinto, etc.)
- `credentials` (JSONB): Encrypted credentials
- `status` (ENUM): Integration status (connected, disconnected, error, pending)
- `last_sync` (TIMESTAMP): When integration was last synced
- `created_at` (TIMESTAMP): Record creation timestamp
- `updated_at` (TIMESTAMP): Record update timestamp

**Indexes**:
- `user_id` - for querying by user
- `integration_name` - for filtering by integration
- `status` - for filtering by status

## Pydantic Models

### Location
- **File**: `apps/backend/api/schemas/india_compliance.py`
- **Package**: `api.schemas`

### Enums

#### IndiaFramework
Supported compliance frameworks:
- `DPDP_ACT_2023` - Digital Personal Data Protection Act 2023
- `NITI_AAYOG_PRINCIPLES` - NITI Aayog Responsible AI principles
- `MEITY_GUIDELINES` - Ministry of Electronics and IT guidelines
- `DIGITAL_INDIA_ACT` - Digital India Act (emerging framework)

#### ComplianceStatus
- `COMPLIANT` - All requirements met
- `NON_COMPLIANT` - Requirements not met
- `PENDING` - Check in progress
- `UNDER_REVIEW` - Manual review required
- `PARTIAL` - Some requirements met

#### SeverityLevel
- `CRITICAL` - Immediate action required
- `HIGH` - Should be addressed soon
- `MEDIUM` - Should be addressed
- `LOW` - Can be addressed later

#### BiasType
- `CASTE_BIAS` - Bias across caste categories (SC/ST/OBC/General)
- `RELIGIOUS_BIAS` - Bias across religions
- `LINGUISTIC_BIAS` - Bias across languages
- `REGIONAL_BIAS` - Bias across regions
- `GENDER_BIAS` - Bias across genders
- `INTERSECTIONAL_BIAS` - Combined demographic bias

#### IntegrationStatus
- `CONNECTED` - Integration is active
- `DISCONNECTED` - Integration is inactive
- `ERROR` - Integration has errors
- `PENDING` - Integration pending setup

### Core Models

#### Evidence
Represents compliance evidence.

```python
Evidence(
    id: UUID,
    system_id: str,
    control_id: str,
    evidence_type: str,
    evidence_data: Dict[str, Any],
    evidence_hash: str,
    collected_at: datetime,
    source: Optional[str],
    metadata: Optional[Dict[str, Any]],
    created_at: datetime,
    updated_at: datetime
)
```

#### ComplianceGap
Represents a compliance gap.

```python
ComplianceGap(
    control_id: str,
    control_name: str,
    category: str,
    severity: SeverityLevel,
    failed_checks: List[str],
    remediation_steps: List[str],
    legal_citation: str,
    evidence_id: Optional[UUID]
)
```

#### FairnessMetrics
Represents fairness metrics for bias detection.

```python
FairnessMetrics(
    demographic_parity: Dict[str, float],
    equal_opportunity: Dict[str, float],
    equalized_odds: Dict[str, float],
    predictive_parity: Dict[str, float],
    disparate_impact: float
)
```

#### BiasResult
Represents bias detection results.

```python
BiasResult(
    attribute: str,
    bias_detected: bool,
    severity: SeverityLevel,
    affected_groups: List[str],
    fairness_metrics: FairnessMetrics,
    disparate_impact: float,
    recommendations: List[str]
)
```

#### ComplianceResult
Represents compliance check results.

```python
ComplianceResult(
    id: UUID,
    system_id: str,
    user_id: str,
    framework: IndiaFramework,
    overall_score: float,
    status: ComplianceStatus,
    requirements_met: int,
    total_requirements: int,
    evidence_count: int,
    results: Dict[str, Any],
    gaps: Optional[List[ComplianceGap]],
    timestamp: datetime,
    created_at: datetime,
    updated_at: datetime
)
```

#### ComplianceReport
Represents a compliance report.

```python
ComplianceReport(
    id: UUID,
    report_id: str,
    system_id: str,
    user_id: str,
    frameworks: List[IndiaFramework],
    overall_score: float,
    report_data: Dict[str, Any],
    generated_at: datetime,
    created_at: datetime,
    updated_at: datetime
)
```

#### BiasTestResult
Represents bias test results.

```python
BiasTestResult(
    id: UUID,
    test_id: str,
    system_id: str,
    user_id: str,
    model_id: str,
    bias_type: BiasType,
    bias_detected: bool,
    severity: Optional[SeverityLevel],
    affected_groups: Optional[List[str]],
    fairness_metrics: FairnessMetrics,
    recommendations: Optional[List[str]],
    timestamp: datetime,
    created_at: datetime,
    updated_at: datetime
)
```

#### IntegrationCredentials
Represents integration credentials.

```python
IntegrationCredentials(
    id: UUID,
    user_id: str,
    integration_name: str,
    credentials: Dict[str, Any],
    status: IntegrationStatus,
    last_sync: Optional[datetime],
    created_at: datetime,
    updated_at: datetime
)
```

### Request/Response Models

#### ComplianceCheckRequest
Request for compliance check.

```python
ComplianceCheckRequest(
    system_id: str,
    frameworks: List[IndiaFramework],
    include_evidence: bool = True,
    include_gaps: bool = True
)
```

#### ComplianceCheckResponse
Response from compliance check.

```python
ComplianceCheckResponse(
    system_id: str,
    frameworks: List[IndiaFramework],
    results: List[ComplianceResult],
    overall_score: float,
    status: ComplianceStatus,
    timestamp: datetime
)
```

#### BiasDetectionRequest
Request for bias detection.

```python
BiasDetectionRequest(
    system_id: str,
    model_id: str,
    bias_types: List[BiasType],
    test_data: Optional[Dict[str, Any]]
)
```

#### BiasDetectionResponse
Response from bias detection.

```python
BiasDetectionResponse(
    system_id: str,
    model_id: str,
    results: List[BiasResult],
    overall_bias_detected: bool,
    timestamp: datetime
)
```

## Running Migrations

### Using Alembic (Recommended)

```bash
cd apps/backend

# Create a new migration
alembic revision --autogenerate -m "Add India compliance tables"

# Apply migrations
alembic upgrade head
```

### Manual SQL Execution

```bash
# Connect to Supabase PostgreSQL
psql postgresql://user:password@host/database

# Execute migration
\i migrations/002_india_compliance_schema.sql
```

## Usage Examples

### Creating Evidence

```python
from api.schemas import EvidenceCreate, Evidence
from database.india_compliance_models import IndiaComplianceEvidence

evidence = EvidenceCreate(
    system_id="system-123",
    control_id="DL_001",
    evidence_type="data_location",
    evidence_data={
        "storage_location": "India",
        "region": "ap-south-1",
        "verified": True
    },
    source="automated"
)
```

### Creating Compliance Results

```python
from api.schemas import ComplianceResultCreate, ComplianceResult, IndiaFramework, ComplianceStatus

result = ComplianceResultCreate(
    system_id="system-123",
    framework=IndiaFramework.DPDP_ACT_2023,
    overall_score=85.5,
    status=ComplianceStatus.COMPLIANT,
    requirements_met=12,
    total_requirements=14,
    evidence_count=25,
    results={
        "consent_management": {"status": "compliant", "score": 90},
        "data_localization": {"status": "compliant", "score": 95}
    }
)
```

### Creating Bias Test Results

```python
from api.schemas import BiasTestResultCreate, BiasType, SeverityLevel, FairnessMetrics

bias_result = BiasTestResultCreate(
    system_id="system-123",
    model_id="model-456",
    bias_type=BiasType.CASTE_BIAS,
    bias_detected=True,
    severity=SeverityLevel.HIGH,
    affected_groups=["SC", "ST"],
    fairness_metrics=FairnessMetrics(
        demographic_parity={"SC": 0.75, "ST": 0.72, "OBC": 0.88, "General": 0.90},
        equal_opportunity={"SC": 0.70, "ST": 0.68, "OBC": 0.85, "General": 0.88},
        equalized_odds={"SC": 0.68, "ST": 0.65, "OBC": 0.83, "General": 0.86},
        predictive_parity={"SC": 0.72, "ST": 0.70, "OBC": 0.87, "General": 0.89},
        disparate_impact=0.80
    ),
    recommendations=[
        "Rebalance training data for SC/ST categories",
        "Apply algorithmic debiasing techniques",
        "Increase representation of underrepresented groups"
    ]
)
```

## Database Connection

The models use SQLAlchemy with Supabase PostgreSQL. Connection is configured in:
- `apps/backend/config/database.py` - Database configuration
- `apps/backend/database/connection.py` - Connection setup

## Security Considerations

1. **Credential Encryption**: Integration credentials are encrypted at rest
2. **RBAC**: Row-level security for compliance data
3. **Audit Logging**: All compliance checks are logged
4. **Data Privacy**: Sensitive data is protected with appropriate access controls

## Performance Optimization

1. **Indexes**: All frequently queried columns are indexed
2. **Partitioning**: Consider partitioning large tables by date
3. **Caching**: Cache framework definitions and regulatory documents
4. **Connection Pooling**: Use connection pooling for database access

## Next Steps

1. Run the migration to create tables
2. Implement repository classes for data access
3. Create service classes for business logic
4. Implement API routes for compliance endpoints
5. Add integration connectors for external tools
