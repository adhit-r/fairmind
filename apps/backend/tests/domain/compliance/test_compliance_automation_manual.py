import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
try:
    from domain.compliance.services.compliance_automation_service import ComplianceAutomationService
except ModuleNotFoundError as exc:
    pytest.skip(f"compliance automation dependencies unavailable: {exc}", allow_module_level=True)
from types import SimpleNamespace

from database.models import ComplianceSchedule

# There is no Model ORM class in database.models, and importing one broke
# collection for the whole suite. The object below is only ever handed back by a
# mocked session, so a plain stub with the attributes read is enough.
Model = SimpleNamespace

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session

@pytest.fixture
def service():
    with patch('domain.compliance.services.compliance_automation_service.inject') as mock_inject:
        # Mock injected services
        mock_report_generator = AsyncMock()
        
        def side_effect(service_type):
            if str(service_type) == "<class 'domain.reports.services.report_generator_service.ReportGeneratorService'>":
                return mock_report_generator
            return MagicMock()
            
        mock_inject.side_effect = side_effect
        
        service = ComplianceAutomationService()
        service.report_generator = mock_report_generator
        return service

@pytest.mark.asyncio
async def test_generate_automated_report(service, mock_db_session):
    # Setup
    schedule_id = "test-schedule-id"
    schedule = ComplianceSchedule(
        id=schedule_id,
        org_id="org-a",
        framework="Test Framework",
        is_active=True,
        recipients=["test@example.com"]
    )
    
    # Every attribute generate_automated_report reads. A missing one raises
    # inside the method's try block, which swallows it and skips the report.
    model = Model(
        id="test-model-id",
        name="Test Model",
        version="1.0",
        model_type="classifier",
        author="Test Author",
        fairness_score=0.9,
        bias_score=0.1
    )
    
    # Mock DB queries
    mock_db_session.query.return_value.filter.return_value.first.return_value = schedule
    # Models are scoped to the schedule's organisation: query(...).filter(...).all().
    mock_db_session.query.return_value.filter.return_value.all.return_value = [model]
    
    # Mock report generator
    service.report_generator.generate_compliance_certificate.return_value = "/tmp/report.pdf"
    
    # Mock db_manager context manager
    with patch('domain.compliance.services.compliance_automation_service.db_manager.get_session') as mock_get_session, \
            patch('domain.compliance.services.compliance_automation_service.compliance_notifier', AsyncMock()):
        mock_get_session.return_value.__enter__.return_value = mock_db_session
        
        # Execute
        await service.generate_automated_report(schedule_id)
        
        # Verify
        service.report_generator.generate_compliance_certificate.assert_called_once()
        assert schedule.last_run is not None
