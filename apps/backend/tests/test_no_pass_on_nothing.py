"""Checks fail when nothing is on file, and declarations need a value, not just a key."""
import asyncio

from src.application.services.evidence_collection_service import EvidenceCollectionService
from src.domain.compliance.services.compliance_audit_engine import _ctx_has


def test_privacy_and_drift_fail_on_nothing():
    svc = EvidenceCollectionService()
    assert asyncio.run(svc._check_data_privacy({}))["checks"]["pii_detection"] is False
    assert asyncio.run(svc._check_performance_drift({}))["checks"]["accuracy_stable"] is False
    assert asyncio.run(svc._check_data_privacy({"privacy_controls": {"pii_detected": False}}))["checks"]["pii_detection"] is True


def test_audit_declaration_needs_a_value():
    assert not _ctx_has({"model_context": {"human_oversight": ""}}, "human_oversight")
    assert _ctx_has({"model_context": {"human_oversight": "Officer reviews every decline"}}, "human_oversight")
