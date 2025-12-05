import pytest
import os
from apps.backend.domain.reports.services.report_generator_service import report_generator_service

@pytest.mark.asyncio
async def test_generate_bias_audit_report():
    model_data = {
        "name": "Audit Model",
        "version": "1.0",
        "author": "Auditor"
    }
    bias_results = {
        "overall_score": 0.85,
        "metrics": {"bias_metric": 0.05},
        "recommendations": ["Fix bias"]
    }
    
    filepath = await report_generator_service.generate_bias_audit_report(model_data, bias_results)
    
    assert filepath is not None
    assert os.path.exists(filepath)
    assert filepath.endswith(".pdf")
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)

@pytest.mark.asyncio
async def test_generate_compliance_certificate():
    model_data = {
        "name": "Compliant Model",
        "version": "2.0",
        "author": "Compliance Officer"
    }
    compliance_data = {
        "framework": "EU AI Act",
        "status": "Compliant",
        "requirements": [{"name": "Req1", "status": "Met", "evidence": True}]
    }
    
    filepath = await report_generator_service.generate_compliance_certificate(model_data, compliance_data)
    
    assert filepath is not None
    assert os.path.exists(filepath)
    assert filepath.endswith(".pdf")
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)
