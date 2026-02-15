import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from apps.backend.domain.compliance.services.compliance_automation_service import ComplianceAutomationService
from apps.backend.database.models import ComplianceSchedule, Model

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session

@pytest.fixture
def service():
    with patch('apps.backend.domain.compliance.services.compliance_automation_service.inject') as mock_inject:
        # Mock injected services
        mock_report_generator = AsyncMock()
        mock_model_test = AsyncMock()
        
        def side_effect(service_type):
            if str(service_type) == "<class 'domain.reports.services.report_generator_service.ReportGeneratorService'>":
                return mock_report_generator
            if str(service_type) == "<class 'domain.models.services.model_test_service.ModelTestService'>":
                return mock_model_test
            return MagicMock()
            
        mock_inject.side_effect = side_effect
        
        service = ComplianceAutomationService()
        service.report_generator = mock_report_generator
        service.model_test_service = mock_model_test
        return service

@pytest.mark.asyncio
async def test_generate_automated_report(service, mock_db_session):
    # Setup
    schedule_id = "test-schedule-id"
    schedule = ComplianceSchedule(
        id=schedule_id,
        framework="Test Framework",
        is_active=True,
        recipients=["test@example.com"]
    )
    
    model = Model(
        id="test-model-id",
        name="Test Model",
        version="1.0",
        model_type="classifier",
        fairness_score=0.9,
        bias_score=0.1
    )
    
    # Mock DB queries
    mock_db_session.query.return_value.filter.return_value.first.return_value = schedule
    mock_db_session.query.return_value.all.return_value = [model]
    
    # Mock report generator
    service.report_generator.generate_compliance_certificate.return_value = "/tmp/report.pdf"
    
    # Mock db_manager context manager
    with patch('apps.backend.domain.compliance.services.compliance_automation_service.db_manager.get_session') as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = mock_db_session
        
        # Execute
        await service.generate_automated_report(schedule_id)
        
        # Verify
        service.report_generator.generate_compliance_certificate.assert_called_once()
        assert schedule.last_run is not None

@pytest.mark.asyncio
async def test_check_compliance_violations(service, mock_db_session):
    # Setup
    model_id = "test-model-id"
    
    # Mock model test service to return low score
    service.model_test_service.run_bias_test.return_value = {
        "score": 0.5, # Below 0.8 threshold
        "metrics": {}
    }
    
    # Execute
    violations = await service.check_compliance_violations(mock_db_session, model_id)
    
    # Verify
    assert len(violations) == 1
    assert violations[0].model_id == model_id
    assert violations[0].violation_type == "Low Fairness Score"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
