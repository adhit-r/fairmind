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
    # No governance system of this name: every requirement must come out Not assessed.
    mock_db_session.execute.return_value.fetchone.return_value = None
    
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
        compliance_data = service.report_generator.generate_compliance_certificate.call_args.kwargs["compliance_data"]
        assert compliance_data["status"] == "Not assessed"
        assert all(r["status"] == "Not assessed" and r["evidence"] is False for r in compliance_data["requirements"])


def _evidence_db(records):
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = ("sys-1", "high")
    db.execute.return_value.fetchall.return_value = records
    return db


def test_requirements_pass_only_on_proven_evidence(service):
    schedule = ComplianceSchedule(id="s", org_id="org-a", framework="EU_AI_ACT")
    now = datetime.utcnow().isoformat()
    fairness = ("e1", "fairness_test", '{"all_checks_pass": true, "rows": 10, "attributes": []}', 0.9, '{"provenance_class": "measured"}', now)
    policy = ("e2", "policy", "{}", 0.9, '{"provenance_class": "manual"}', now)
    out = service._compliance_from_evidence(_evidence_db([fairness, policy]), schedule, "m")
    by_name = {r["name"]: r for r in out["requirements"]}
    assert by_name["Fairness measured"] == {"name": "Fairness measured", "status": "Pass", "evidence": True}
    assert by_name["Human oversight"]["status"] == "Attested"
    assert by_name["Data governance"] == {"name": "Data governance", "status": "Not assessed", "evidence": False}
    assert out["status"] == "Not assessed"


def test_failed_fairness_is_non_compliant(service):
    schedule = ComplianceSchedule(id="s", org_id="org-a", framework="EU_AI_ACT")
    fairness = ("e1", "fairness_test", '{"all_checks_pass": false}', 0.9, '{"provenance_class": "measured"}', datetime.utcnow().isoformat())
    out = service._compliance_from_evidence(_evidence_db([fairness]), schedule, "m")
    assert out["status"] == "Non-Compliant"


def test_reload_schedules_is_idempotent(service, mock_db_session):
    rows = [SimpleNamespace(id="a", frequency="weekly"), SimpleNamespace(id="b", frequency="daily")]
    mock_db_session.query.return_value.filter.return_value.all.return_value = rows
    service.scheduler = MagicMock()
    with patch('domain.compliance.services.compliance_automation_service.db_manager.get_session') as gs:
        gs.return_value.__enter__.return_value = mock_db_session
        assert service.reload_schedules() == 2
    assert [c.kwargs["id"] for c in service.scheduler.add_job.call_args_list] == ["a", "b"]
    assert all(c.kwargs["replace_existing"] is True for c in service.scheduler.add_job.call_args_list)
