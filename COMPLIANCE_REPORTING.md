# Compliance & Reporting - Implementation Guide

## Overview

The **Compliance & Reporting** module provides comprehensive regulatory compliance checking, automated audit report generation, fairness documentation, and stakeholder dashboards for AI systems.

## Features

### 1. Regulatory Compliance Checks
- **EU AI Act** - European Union Artificial Intelligence Act compliance
- **GDPR** - General Data Protection Regulation for AI systems
- **ISO/IEC 42001** - AI Management System Standard
- **NIST AI RMF** - NIST AI Risk Management Framework
- **IEEE 7000** - Model Process for Addressing Ethical Concerns

### 2. Automated Audit Reports
- Comprehensive compliance assessment across multiple frameworks
- Executive summaries for stakeholders
- Detailed requirement-by-requirement analysis
- Prioritized recommendations
- Downloadable reports in multiple formats

### 3. Fairness Documentation Generation
- Model information and metadata
- Fairness assessment results
- Bias mitigation strategies
- Monitoring plans
- Stakeholder communication plans

### 4. Stakeholder Dashboards
- Executive-level compliance overview
- Key performance indicators
- Compliance trends and analytics
- Action items and priorities
- Framework-specific scores

## Architecture

### Backend Components

#### 1. Compliance Reporting Service
**Location:** `/apps/backend/api/services/compliance_reporting_service.py`

**Key Classes:**
- `ComplianceReportingService` - Main service class
- `RegulatoryFramework` - Enum of supported frameworks
- `RiskLevel` - AI system risk levels (EU AI Act)
- `ComplianceStatus` - Compliance status enum

**Key Methods:**
```python
async def check_compliance(framework, system_data) -> Dict
async def generate_audit_report(system_id, system_data, frameworks) -> Dict
async def generate_fairness_documentation(model_data, bias_test_results) -> Dict
async def generate_stakeholder_dashboard_data(system_id, compliance_results) -> Dict
```

#### 2. API Routes
**Location:** `/apps/backend/api/routes/compliance_reporting.py`

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/compliance/frameworks` | GET | List all supported frameworks |
| `/api/v1/compliance/frameworks/{framework}/requirements` | GET | Get framework requirements |
| `/api/v1/compliance/check` | POST | Check compliance against a framework |
| `/api/v1/compliance/audit-report` | POST | Generate comprehensive audit report |
| `/api/v1/compliance/fairness-documentation` | POST | Generate fairness documentation |
| `/api/v1/compliance/stakeholder-dashboard` | POST | Get stakeholder dashboard data |
| `/api/v1/compliance/risk-levels` | GET | Get AI risk level definitions |
| `/api/v1/compliance/assess-risk` | POST | Assess AI system risk level |
| `/api/v1/compliance/compliance-templates` | GET | Get compliance documentation templates |

### Frontend Components

#### 1. Compliance Dashboard
**Location:** `/apps/frontend-new/src/app/(dashboard)/compliance-dashboard/page.tsx`

**Features:**
- Framework selection
- Real-time compliance checking
- Visual compliance score indicators
- Detailed requirements table
- Recommendations panel
- Export functionality

#### 2. Audit Reports
**Location:** `/apps/frontend-new/src/app/(dashboard)/audit-reports/page.tsx`

**Features:**
- Report generation form
- Multi-framework assessment
- Executive summary display
- Detailed compliance results
- Prioritized recommendations
- Report download

#### 3. Fairness Documentation
**Location:** `/apps/frontend-new/src/app/(dashboard)/fairness-documentation/page.tsx`

**Features:**
- Model information input
- Fairness assessment display
- Mitigation strategies
- Monitoring plan
- Stakeholder communication plan
- Documentation export

#### 4. Stakeholder Dashboard
**Location:** `/apps/frontend-new/src/app/(dashboard)/stakeholder-dashboard/page.tsx`

**Features:**
- Executive-level metrics
- Compliance trends
- Framework-specific scores
- Action items timeline
- Executive summary
- Real-time updates

## Usage Examples

### 1. Check Compliance Against EU AI Act

```python
import requests

# Prepare system data with evidence
system_data = {
    "name": "Credit Scoring Model",
    "description": "AI-powered credit risk assessment",
    "risk_level": "high",
    "evidence_EU_AI_1": [{"quality": 0.9, "description": "Risk classification completed"}],
    "evidence_EU_AI_2": [{"quality": 0.85, "description": "Transparency measures implemented"}],
    # ... more evidence
}

# Check compliance
response = requests.post(
    "http://localhost:8000/api/v1/compliance/check",
    json={
        "framework": "eu_ai_act",
        "system_data": system_data
    }
)

result = response.json()
print(f"Compliance Score: {result['compliance_score']}%")
print(f"Status: {result['overall_status']}")
```

### 2. Generate Audit Report

```python
import requests

# Generate comprehensive audit report
response = requests.post(
    "http://localhost:8000/api/v1/compliance/audit-report",
    json={
        "system_id": "SYS-001",
        "system_data": system_data,
        "frameworks": ["eu_ai_act", "gdpr", "iso_iec_42001"]
    }
)

report = response.json()
print(f"Report ID: {report['report_id']}")
print(f"Overall Score: {report['overall_compliance_score']}%")
```

### 3. Generate Fairness Documentation

```python
import requests

model_data = {
    "name": "Recommendation Engine",
    "version": "2.0",
    "type": "recommendation",
    "purpose": "Product recommendations"
}

bias_test_results = {
    "metrics": ["Statistical Parity", "Equal Opportunity"],
    "protected_attributes": ["gender", "age"],
    "scores": {
        "statistical_parity": 0.85,
        "equal_opportunity": 0.82
    },
    "bias_detected": True
}

response = requests.post(
    "http://localhost:8000/api/v1/compliance/fairness-documentation",
    json={
        "model_data": model_data,
        "bias_test_results": bias_test_results
    }
)

documentation = response.json()
print(f"Document ID: {documentation['document_id']}")
```

### 4. Assess System Risk Level

```python
import requests

system_info = {
    "id": "SYS-001",
    "purpose": "employment screening",
    "domain": "human resources"
}

response = requests.post(
    "http://localhost:8000/api/v1/compliance/assess-risk",
    json=system_info
)

assessment = response.json()
print(f"Risk Level: {assessment['risk_level']}")
print(f"Reasoning: {assessment['reasoning']}")
```

## Frontend Usage

### Accessing the Pages

1. **Compliance Dashboard**: Navigate to `/compliance-dashboard`
2. **Audit Reports**: Navigate to `/audit-reports`
3. **Fairness Documentation**: Navigate to `/fairness-documentation`
4. **Stakeholder Dashboard**: Navigate to `/stakeholder-dashboard`

### Workflow Example

1. **Risk Assessment**
   - Determine your AI system's risk level
   - Understand applicable requirements

2. **Compliance Check**
   - Select relevant regulatory framework
   - Provide system data and evidence
   - Review compliance results

3. **Generate Audit Report**
   - Input system information
   - Select frameworks to assess
   - Generate comprehensive report
   - Download for stakeholders

4. **Create Fairness Documentation**
   - Enter model details
   - Include bias test results
   - Generate documentation
   - Export for review

5. **Monitor via Dashboard**
   - Track overall compliance
   - Monitor trends
   - Address action items
   - Share with stakeholders

## Regulatory Frameworks

### EU AI Act

**Risk Levels:**
- **Unacceptable Risk**: Prohibited AI systems
- **High Risk**: Strict requirements apply
- **Limited Risk**: Transparency obligations
- **Minimal Risk**: No specific obligations

**Key Requirements:**
- Risk classification
- Transparency information
- Human oversight
- Data governance
- Technical documentation
- Record keeping
- Accuracy & robustness
- Cybersecurity

### GDPR

**Key Requirements:**
- Lawful processing basis
- Data minimization
- Automated decision-making safeguards
- Data Protection Impact Assessment (DPIA)
- Right to explanation

### ISO/IEC 42001

**Key Requirements:**
- AI management system
- Risk management
- Personnel competence

### NIST AI RMF

**Functions:**
- Govern
- Map
- Measure
- Manage

### IEEE 7000

**Focus:**
- Value-based design
- Ethical considerations

## Evidence Management

### Evidence Structure

```python
evidence = {
    "evidence_EU_AI_1": [
        {
            "quality": 0.9,  # 0.0 to 1.0
            "description": "Risk classification completed",
            "document_ref": "DOC-001",
            "date": "2024-01-15"
        }
    ]
}
```

### Quality Scoring

- **0.8 - 1.0**: Compliant (comprehensive evidence)
- **0.5 - 0.8**: Partially Compliant (some gaps)
- **0.0 - 0.5**: Non-Compliant (insufficient evidence)

## Best Practices

### 1. Regular Assessments
- Conduct compliance checks quarterly
- Update evidence continuously
- Track compliance trends

### 2. Documentation
- Maintain comprehensive evidence
- Document all mitigation strategies
- Keep audit trail

### 3. Stakeholder Communication
- Share dashboard with executives
- Provide regular updates
- Address recommendations promptly

### 4. Risk Management
- Assess risk level early
- Implement appropriate controls
- Monitor high-risk systems closely

### 5. Continuous Improvement
- Act on recommendations
- Update processes based on findings
- Stay current with regulations

## Integration with Existing Features

### Bias Detection
- Use bias test results in fairness documentation
- Link compliance to bias metrics
- Track fairness over time

### Model Registry
- Associate compliance reports with models
- Track compliance history
- Version control for documentation

### Monitoring
- Alert on compliance threshold breaches
- Track compliance metrics
- Automated reporting

## Customization

### Adding New Frameworks

1. Update `RegulatoryFramework` enum
2. Add requirements in service
3. Update frontend framework list

```python
class RegulatoryFramework(str, Enum):
    # ... existing frameworks
    NEW_FRAMEWORK = "new_framework"

def _get_new_framework_requirements(self):
    return [
        {
            "id": "NEW-1",
            "category": "Category",
            "requirement": "Requirement text",
            # ...
        }
    ]
```

### Custom Evidence Types

Extend the evidence structure to include:
- Document references
- Timestamps
- Responsible parties
- Review status

### Custom Report Templates

Add new templates in the templates endpoint:
```python
{
    "id": "custom-template",
    "name": "Custom Template",
    "framework": "custom",
    "sections": [...]
}
```

## Testing

### Backend Tests

```bash
cd apps/backend
pytest tests/test_compliance_reporting.py -v
```

### Frontend Tests

```bash
cd apps/frontend-new
npm test -- compliance
```

### Integration Tests

```bash
# Test full workflow
python scripts/test_compliance_workflow.py
```

## Deployment

### Environment Variables

```bash
# Add to .env
COMPLIANCE_ENABLED=true
COMPLIANCE_FRAMEWORKS=eu_ai_act,gdpr,iso_iec_42001,nist_ai_rmf
AUDIT_RETENTION_DAYS=365
```

### Production Considerations

1. **Data Security**: Encrypt compliance data
2. **Access Control**: Restrict to authorized users
3. **Audit Trail**: Log all compliance activities
4. **Backup**: Regular backups of evidence
5. **Performance**: Cache framework requirements

## Troubleshooting

### Common Issues

1. **Low Compliance Scores**
   - Review evidence quality
   - Ensure all requirements have evidence
   - Update system documentation

2. **Missing Evidence**
   - Check evidence key naming
   - Verify evidence structure
   - Ensure quality scores are set

3. **Report Generation Fails**
   - Validate system data
   - Check framework selection
   - Review error logs

## Future Enhancements

- [ ] Automated evidence collection
- [ ] Integration with document management systems
- [ ] Real-time compliance monitoring
- [ ] Predictive compliance analytics
- [ ] Multi-language support
- [ ] Custom framework builder
- [ ] Compliance workflow automation
- [ ] Integration with external audit tools

## Support

For questions or issues:
- GitHub Issues: [fairmind/issues](https://github.com/adhit-r/fairmind/issues)
- Documentation: [docs/compliance](./docs/compliance)
- Email: support@fairmind.xyz

## License

MIT License - See LICENSE file for details

---

**Last Updated**: 2024-11-23
**Version**: 1.0.0
**Status**: Production Ready
