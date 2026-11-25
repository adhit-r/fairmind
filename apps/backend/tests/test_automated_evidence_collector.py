"""The collector reports only what is on file: no invented evidence, oversight from the real attestation."""
import asyncio
import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from api.services.automated_evidence_collector import AutomatedEvidenceCollector


def _db():
    engine = create_engine("sqlite://")
    with engine.begin() as c:
        c.execute(text("CREATE TABLE governance_evidence (id TEXT, system_id TEXT, evidence_type TEXT, content_json TEXT, created_at TEXT)"))
    return sessionmaker(bind=engine)()


def test_nothing_on_file_claims_nothing():
    evidence = asyncio.run(AutomatedEvidenceCollector().collect_evidence_for_model("sys-1", db=_db()))
    assert evidence["human_oversight"]["source"] == "not_collected"
    assert not any(v for k, v in evidence["human_oversight"].items() if k != "source")
    assert evidence["training_data_bias"] == {}
    assert evidence["adversarial_tests"] == {}
    assert evidence["performance_drift"]["monitoring_enabled"] is False
    assert evidence["fairness_monitoring"]["enabled"] is False
    assert evidence["dataset_quality"]["source"] == "default"
    assert evidence["model_card"] == {}


def test_oversight_reads_attestation():
    db = _db()
    db.execute(
        text("INSERT INTO governance_evidence VALUES ('ev-1', 'sys-1', 'human_oversight', :c, '2026-11-15')"),
        {"c": json.dumps({"statement": "Credit officer reviews every decline", "attested_by": "a.reviewer"})},
    )
    oversight = asyncio.run(AutomatedEvidenceCollector().collect_evidence_for_model("sys-1", db=db))["human_oversight"]
    assert oversight["source"] == "attestation" and oversight["evidence_id"] == "ev-1"
    assert oversight["review_process"] and oversight["human_override_enabled"]
    assert not oversight["escalation_defined"] and not oversight["operator_training"]
