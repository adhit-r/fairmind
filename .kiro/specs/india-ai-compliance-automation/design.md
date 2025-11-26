# Design Document

## Overview

This design extends FairMind's existing evidence-based compliance system to provide comprehensive India-specific AI compliance automation. The system will integrate with India's Digital Personal Data Protection (DPDP) Act 2023, NITI Aayog's Responsible AI principles, MeitY guidelines, and emerging Indian AI regulations.

The design leverages FairMind's existing `ComplianceReportingService` architecture while adding:
- India-specific regulatory frameworks and technical controls
- Automated evidence collection for Indian compliance requirements
- Integration with leading compliance tools (OneTrust, Securiti.ai, Sprinto)
- India-specific bias detection for caste, religion, language, and regional demographics
- AI-powered compliance automation using LLMs for gap analysis and policy generation
- Comprehensive compliance dashboard with audit-ready reporting

This positions FairMind as the leading AI governance platform for the Indian market, addressing a critical gap in localized compliance tooling.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FairMind Frontend                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         India Compliance Dashboard Component              │  │
│  │  - Framework Selection  - Evidence Viewer                 │  │
│  │  - Compliance Score     - Gap Analysis                    │  │
│  │  - Trend Charts         - Report Export                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API Layer                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         India Compliance Routes                           │  │
│  │  /api/v1/compliance/india/check                          │  │
│  │  /api/v1/compliance/india/frameworks                     │  │
│  │  /api/v1/compliance/india/evidence                       │  │
│  │  /api/v1/compliance/india/bias-detection                 │  │
│  │  /api/v1/compliance/india/report                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │    IndiaComplianceService (extends ComplianceService)     │  │
│  │  - Framework Management  - Evidence Collection           │  │
│  │  - Compliance Checking   - Gap Analysis                  │  │
│  │  - Report Generation     - AI-Powered Automation         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         IndiaBiasDetectionService                         │  │
│  │  - Caste-based bias      - Religious bias                │  │
│  │  - Linguistic bias       - Regional bias                 │  │
│  │  - Intersectional bias   - Fairness metrics              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         IndiaEvidenceCollectionService                    │  │
│  │  - Data localization     - Consent management            │  │
│  │  - Language support      - Cross-border transfer         │  │
│  │  - Grievance mechanism   - Security controls             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         ComplianceIntegrationService                      │  │
│  │  - OneTrust connector    - Securiti.ai connector         │  │
│  │  - Sprinto connector     - Custom API connector          │  │
│  │  - MLflow connector      - Cloud provider connector      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         AIComplianceAutomationService                     │  │
│  │  - LLM-based gap analysis    - Policy generation         │  │
│  │  - Remediation suggestions   - Compliance Q&A (RAG)      │  │
│  │  - Regulatory monitoring     - Risk prediction           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Layer                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Supabase PostgreSQL Database                            │  │
│  │  - india_compliance_evidence                             │  │
│  │  - india_compliance_results                              │  │
│  │  - india_bias_test_results                               │  │
│  │  - india_compliance_reports                              │  │
│  │  - integration_credentials                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Vector Database (for RAG)                               │  │
│  │  - Indian regulatory documents embeddings                │  │
│  │  - DPDP Act, NITI Aayog guidelines, MeitY docs          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  External Integrations                           │
│  - OneTrust API      - Securiti.ai API    - Sprinto API        │
│  - MLflow API        - AWS/Azure/GCP APIs                       │
│  - OpenAI/Anthropic  - Supabase Vector Store                   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Compliance Check Request**: User initiates compliance check via dashboard
2. **Evidence Collection**: System collects evidence from integrations and technical controls
3. **Framework Evaluation**: Evaluates evidence against India-specific requirements
4. **Bias Detection**: Runs India-specific bias tests on AI models
5. **Gap Analysis**: AI-powered analysis identifies compliance gaps
6. **Report Generation**: Creates audit-ready compliance report
7. **Dashboard Update**: Real-time updates to compliance dashboard

## Components and Interfaces

### 1. IndiaComplianceService

**Purpose**: Core service managing India-specific compliance checking and reporting

**Key Methods**:

```python
class IndiaComplianceService:
    """Service for India-specific AI compliance"""
    
    async def check_dpdp_compliance(
        self,
        system_data: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> ComplianceResult:
        """Check DPDP Act 2023 compliance"""
        
    async def check_niti_aayog_compliance(
        self,
        system_data: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> ComplianceResult:
        """Check NITI Aayog AI principles compliance"""
        
    async def check_meity_compliance(
        self,
        system_data: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> ComplianceResult:
        """Check MeitY guidelines compliance"""
        
    async def generate_india_compliance_report(
        self,
        system_id: str,
        frameworks: List[IndiaFramework]
    ) -> ComplianceReport:
        """Generate comprehensive India compliance report"""
        
    async def get_compliance_trends(
        self,
        system_id: str,
        timeframe: str
    ) -> TrendData:
        """Get compliance trends over time"""
```

**Data Models**:

```python
class IndiaFramework(str, Enum):
    DPDP_ACT_2023 = "dpdp_act_2023"
    NITI_AAYOG_PRINCIPLES = "niti_aayog_principles"
    MEITY_GUIDELINES = "meity_guidelines"
    DIGITAL_INDIA_ACT = "digital_india_act"

class ComplianceResult:
    framework: IndiaFramework
    overall_score: float
    status: ComplianceStatus
    requirements_met: int
    total_requirements: int
    evidence_collected: int
    gaps: List[ComplianceGap]
    timestamp: datetime

class ComplianceGap:
    control_id: str
    control_name: str
    category: str
    severity: str  # critical, high, medium, low
    failed_checks: List[str]
    remediation_steps: List[str]
    legal_citation: str
    evidence_id: Optional[str]
```

### 2. IndiaBiasDetectionService

**Purpose**: Detect bias specific to Indian demographics and social structures

**Key Methods**:

```python
class IndiaBiasDetectionService:
    """India-specific bias detection"""
    
    async def detect_caste_bias(
        self,
        model: Any,
        test_data: pd.DataFrame
    ) -> BiasResult:
        """Detect caste-based bias (SC/ST/OBC/General)"""
        
    async def detect_religious_bias(
        self,
        model: Any,
        test_data: pd.DataFrame
    ) -> BiasResult:
        """Detect religious bias across major religions"""
        
    async def detect_linguistic_bias(
        self,
        model: Any,
        test_data: pd.DataFrame
    ) -> BiasResult:
        """Detect bias across Indian languages"""
        
    async def detect_regional_bias(
        self,
        model: Any,
        test_data: pd.DataFrame
    ) -> BiasResult:
        """Detect regional bias (North/South/East/West/Northeast)"""
        
    async def detect_intersectional_bias(
        self,
        model: Any,
        test_data: pd.DataFrame,
        attributes: List[str]
    ) -> BiasResult:
        """Detect intersectional bias across multiple attributes"""
        
    async def calculate_india_fairness_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        sensitive_attributes: Dict[str, np.ndarray]
    ) -> FairnessMetrics:
        """Calculate fairness metrics for Indian demographics"""
```

**Data Models**:

```python
class BiasResult:
    attribute: str  # caste, religion, language, region
    bias_detected: bool
    severity: str
    affected_groups: List[str]
    fairness_metrics: Dict[str, float]
    disparate_impact: float
    recommendations: List[str]

class FairnessMetrics:
    demographic_parity: Dict[str, float]
    equal_opportunity: Dict[str, float]
    equalized_odds: Dict[str, float]
    predictive_parity: Dict[str, float]
```

### 3. IndiaEvidenceCollectionService

**Purpose**: Automated collection of evidence for India-specific compliance controls

**Key Methods**:

```python
class IndiaEvidenceCollectionService:
    """Automated evidence collection for Indian regulations"""
    
    async def collect_data_localization_evidence(
        self,
        system_id: str
    ) -> Evidence:
        """Verify data storage location for DPDP compliance"""
        
    async def collect_consent_management_evidence(
        self,
        system_id: str
    ) -> Evidence:
        """Verify consent mechanisms and records"""
        
    async def collect_language_support_evidence(
        self,
        system_id: str
    ) -> Evidence:
        """Verify support for Indian languages"""
        
    async def collect_cross_border_transfer_evidence(
        self,
        system_id: str
    ) -> Evidence:
        """Verify cross-border data transfer compliance"""
        
    async def collect_grievance_mechanism_evidence(
        self,
        system_id: str
    ) -> Evidence:
        """Verify grievance redressal mechanism"""
        
    async def collect_security_controls_evidence(
        self,
        system_id: str
    ) -> Evidence:
        """Verify security safeguards per DPDP Act"""
```

**Technical Controls**:

```python
INDIA_TECHNICAL_CONTROLS = {
    "DL_001": {
        "name": "Data Localization Check",
        "description": "Verify sensitive personal data stored in India",
        "framework": "DPDP Act Section 16",
        "automated": True
    },
    "CM_001": {
        "name": "Consent Management",
        "description": "Verify valid consent records with withdrawal mechanism",
        "framework": "DPDP Act Section 6",
        "automated": True
    },
    "LS_001": {
        "name": "Language Support",
        "description": "Verify support for scheduled Indian languages",
        "framework": "NITI Aayog Inclusiveness",
        "automated": True
    },
    "DB_001": {
        "name": "Demographic Bias Detection",
        "description": "Test for bias across Indian demographics",
        "framework": "NITI Aayog Equality",
        "automated": True
    },
    "CBT_001": {
        "name": "Cross-Border Transfer",
        "description": "Verify approved country compliance",
        "framework": "DPDP Act Section 16",
        "automated": True
    },
    "GM_001": {
        "name": "Grievance Mechanism",
        "description": "Verify complaint handling system",
        "framework": "NITI Aayog Accountability",
        "automated": True
    }
}
```

### 4. ComplianceIntegrationService

**Purpose**: Integrate with leading compliance and governance tools

**Key Methods**:

```python
class ComplianceIntegrationService:
    """Integration with compliance tools"""
    
    async def integrate_onetrust(
        self,
        api_key: str,
        org_id: str
    ) -> IntegrationStatus:
        """Connect to OneTrust for consent and privacy data"""
        
    async def integrate_securiti(
        self,
        api_key: str,
        tenant_id: str
    ) -> IntegrationStatus:
        """Connect to Securiti.ai for data discovery"""
        
    async def integrate_sprinto(
        self,
        api_key: str
    ) -> IntegrationStatus:
        """Connect to Sprinto for security controls"""
        
    async def pull_evidence_from_integration(
        self,
        integration_name: str,
        evidence_type: str
    ) -> Evidence:
        """Pull evidence from integrated tool"""
        
    async def sync_compliance_status(
        self,
        integration_name: str,
        compliance_result: ComplianceResult
    ) -> bool:
        """Sync compliance status to integrated tool"""
```

**Integration Connectors**:

```python
class OneTrustConnector:
    """OneTrust API connector"""
    
    async def get_consent_records(self) -> List[ConsentRecord]
    async def get_privacy_assessments(self) -> List[Assessment]
    async def get_data_mapping(self) -> DataMap

class SecuritiConnector:
    """Securiti.ai API connector"""
    
    async def get_data_discovery_results(self) -> DiscoveryResults
    async def get_classification_tags(self) -> List[Tag]
    async def get_privacy_automation_evidence(self) -> Evidence

class SprintoConnector:
    """Sprinto API connector"""
    
    async def get_security_controls(self) -> List[Control]
    async def get_audit_evidence(self) -> List[Evidence]
    async def get_compliance_status(self) -> ComplianceStatus
```

### 5. AIComplianceAutomationService

**Purpose**: AI-powered compliance automation and intelligence

**Key Methods**:

```python
class AIComplianceAutomationService:
    """AI-powered compliance automation"""
    
    async def analyze_gaps_with_llm(
        self,
        compliance_result: ComplianceResult,
        system_context: Dict[str, Any]
    ) -> GapAnalysis:
        """Use LLM to analyze compliance gaps and suggest fixes"""
        
    async def generate_remediation_plan(
        self,
        gaps: List[ComplianceGap]
    ) -> RemediationPlan:
        """Generate step-by-step remediation plan"""
        
    async def generate_privacy_policy(
        self,
        system_data: Dict[str, Any],
        framework: IndiaFramework
    ) -> PolicyDocument:
        """Auto-generate DPDP-compliant privacy policy"""
        
    async def answer_compliance_question(
        self,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """Answer compliance questions using RAG over regulations"""
        
    async def predict_compliance_risk(
        self,
        system_changes: Dict[str, Any],
        historical_data: List[ComplianceResult]
    ) -> RiskPrediction:
        """Predict compliance risk based on system changes"""
        
    async def monitor_regulatory_updates(self) -> List[RegulatoryUpdate]:
        """Monitor and alert on Indian regulatory changes"""
```

**RAG Implementation**:

```python
class IndiaComplianceRAG:
    """RAG system for Indian regulations"""
    
    def __init__(self):
        self.vector_store = SupabaseVectorStore()
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model="gpt-4")
        
    async def index_regulatory_documents(self):
        """Index DPDP Act, NITI Aayog, MeitY guidelines"""
        documents = [
            self._load_dpdp_act(),
            self._load_niti_aayog_principles(),
            self._load_meity_guidelines()
        ]
        await self.vector_store.add_documents(documents)
        
    async def query(self, question: str) -> str:
        """Query regulations using RAG"""
        relevant_docs = await self.vector_store.similarity_search(question)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        prompt = f"""Based on Indian AI regulations:
        
Context: {context}

Question: {question}

Provide a detailed answer with legal citations."""
        
        return await self.llm.apredict(prompt)
```

## Data Models

### Database Schema

```sql
-- India compliance evidence table
CREATE TABLE india_compliance_evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id VARCHAR(255) NOT NULL,
    control_id VARCHAR(50) NOT NULL,
    evidence_type VARCHAR(100) NOT NULL,
    evidence_data JSONB NOT NULL,
    evidence_hash VARCHAR(64) NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- India compliance results table
CREATE TABLE india_compliance_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    framework VARCHAR(100) NOT NULL,
    overall_score FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL,
    requirements_met INTEGER NOT NULL,
    total_requirements INTEGER NOT NULL,
    evidence_count INTEGER NOT NULL,
    results JSONB NOT NULL,
    gaps JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- India bias test results table
CREATE TABLE india_bias_test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id VARCHAR(255) UNIQUE NOT NULL,
    system_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    bias_type VARCHAR(100) NOT NULL,
    bias_detected BOOLEAN NOT NULL,
    severity VARCHAR(50),
    affected_groups JSONB,
    fairness_metrics JSONB NOT NULL,
    recommendations JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- India compliance reports table
CREATE TABLE india_compliance_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id VARCHAR(255) UNIQUE NOT NULL,
    system_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    frameworks JSONB NOT NULL,
    overall_score FLOAT NOT NULL,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Integration credentials table
CREATE TABLE integration_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    integration_name VARCHAR(100) NOT NULL,
    credentials JSONB NOT NULL,  -- encrypted
    status VARCHAR(50) NOT NULL,
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Error Handling

### Error Types

```python
class IndiaComplianceError(Exception):
    """Base exception for India compliance errors"""

class FrameworkNotFoundError(IndiaComplianceError):
    """Raised when framework is not supported"""

class EvidenceCollectionError(IndiaComplianceError):
    """Raised when evidence collection fails"""

class IntegrationError(IndiaComplianceError):
    """Raised when external integration fails"""

class BiasDetectionError(IndiaComplianceError):
    """Raised when bias detection fails"""

class AIAutomationError(IndiaComplianceError):
    """Raised when AI automation fails"""
```

### Error Handling Strategy

1. **Graceful Degradation**: If integration fails, fall back to manual evidence upload
2. **Retry Logic**: Exponential backoff for transient failures (3 retries)
3. **Error Logging**: Comprehensive logging with context for debugging
4. **User Notifications**: Clear error messages with remediation steps
5. **Partial Results**: Return partial compliance results if some checks fail

## Testing Strategy

### Unit Tests

```python
# Test India compliance service
def test_dpdp_compliance_check():
    """Test DPDP Act compliance checking"""
    
def test_niti_aayog_compliance_check():
    """Test NITI Aayog principles checking"""
    
def test_evidence_collection():
    """Test automated evidence collection"""
    
def test_bias_detection():
    """Test India-specific bias detection"""

# Test integrations
def test_onetrust_integration():
    """Test OneTrust connector"""
    
def test_securiti_integration():
    """Test Securiti.ai connector"""

# Test AI automation
def test_llm_gap_analysis():
    """Test LLM-based gap analysis"""
    
def test_policy_generation():
    """Test privacy policy generation"""
```

### Integration Tests

```python
def test_end_to_end_compliance_check():
    """Test complete compliance check flow"""
    
def test_evidence_to_report_flow():
    """Test evidence collection to report generation"""
    
def test_integration_sync():
    """Test syncing with external tools"""
```

### Performance Tests

```python
def test_compliance_check_performance():
    """Ensure compliance check completes within 30 seconds"""
    
def test_bias_detection_performance():
    """Ensure bias detection completes within 60 seconds"""
    
def test_concurrent_checks():
    """Test handling multiple concurrent compliance checks"""
```

## Security Considerations

1. **Credential Encryption**: All integration credentials encrypted at rest using AES-256
2. **API Key Management**: Secure storage in environment variables or secrets manager
3. **Data Privacy**: Compliance evidence contains sensitive data - implement RBAC
4. **Audit Logging**: Log all compliance checks and evidence access
5. **Rate Limiting**: Prevent abuse of AI-powered features
6. **Input Validation**: Sanitize all user inputs to prevent injection attacks
7. **HTTPS Only**: All external integrations use HTTPS
8. **Token Expiry**: Implement token refresh for long-lived integrations

## Performance Optimization

1. **Caching**: Cache framework requirements and regulatory documents
2. **Async Operations**: Use async/await for all I/O operations
3. **Batch Processing**: Batch evidence collection from integrations
4. **Database Indexing**: Index on system_id, user_id, timestamp
5. **Vector Store Optimization**: Use HNSW index for fast similarity search
6. **Connection Pooling**: Reuse database and HTTP connections
7. **Lazy Loading**: Load evidence details only when requested

## Deployment Considerations

1. **Environment Variables**: Configure API keys, database URLs via env vars
2. **Database Migrations**: Use Alembic for schema migrations
3. **Vector Store Setup**: Initialize Supabase vector extension
4. **Document Indexing**: Index regulatory documents on first deployment
5. **Health Checks**: Implement health check endpoints for monitoring
6. **Logging**: Structured logging with correlation IDs
7. **Monitoring**: Track compliance check latency, error rates, integration health
