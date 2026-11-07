"""Tests for the risk taxonomy data model (Issue #157).

Validates model wiring (SQLite in-memory), schema serialization,
seed idempotency helpers, and migration file presence — without
requiring a live database.
"""

from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent


def test_migration_file_exists():
    migration = BACKEND_ROOT / "migrations" / "014_risk_taxonomy.sql"
    assert migration.exists(), "014_risk_taxonomy.sql must exist"
    sql = migration.read_text()
    for table in (
        "risk_taxonomies",
        "risk_categories",
        "risk_factors",
        "risk_assessment_templates",
    ):
        assert table in sql, f"migration must create {table}"


def test_models_importable():
    from src.infrastructure.db.database import risk_taxonomy_models as m

    assert hasattr(m, "RiskTaxonomy")
    assert hasattr(m, "RiskCategory")
    assert hasattr(m, "RiskFactor")
    assert hasattr(m, "RiskAssessmentTemplate")
    assert m.RiskTaxonomy.__tablename__ == "risk_taxonomies"
    assert m.RiskCategory.__tablename__ == "risk_categories"
    assert m.RiskFactor.__tablename__ == "risk_factors"
    assert m.RiskAssessmentTemplate.__tablename__ == "risk_assessment_templates"


def test_models_persist_sqlite():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.infrastructure.db.database.connection import Base
    from src.infrastructure.db.database import risk_taxonomy_models as m

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    taxonomy = m.RiskTaxonomy(key="test", name="Test Taxonomy")
    session.add(taxonomy)
    session.commit()

    category = m.RiskCategory(
        taxonomy_id=taxonomy.id, key="fairness", name="Fairness"
    )
    session.add(category)
    session.commit()

    factor = m.RiskFactor(
        category_id=category.id,
        key="data_bias",
        name="Data bias",
        guidance_json='["Audit data"]',
    )
    session.add(factor)
    template = m.RiskAssessmentTemplate(
        taxonomy_id=taxonomy.id, name="Baseline", version="1.0"
    )
    session.add(template)
    session.commit()

    assert session.query(m.RiskTaxonomy).count() == 1
    assert session.query(m.RiskCategory).count() == 1
    assert session.query(m.RiskFactor).count() == 1
    assert session.query(m.RiskAssessmentTemplate).count() == 1

    # Cascade: deleting the taxonomy removes children.
    session.delete(taxonomy)
    session.commit()
    assert session.query(m.RiskCategory).count() == 0
    assert session.query(m.RiskFactor).count() == 0
    assert session.query(m.RiskAssessmentTemplate).count() == 0
    session.close()


def test_schemas_roundtrip():
    from src.api.schemas import risk_taxonomy as s

    created = s.RiskFactorCreate(
        category_id="cat-1", key="data_bias", name="Data bias",
        guidance=["Audit data"],
    )
    assert created.guidance == ["Audit data"]

    read = s.RiskTaxonomyRead(
        id="tax-1", key="ibm", name="IBM AI Risk Atlas", version="1.0"
    )
    assert read.key == "ibm"

    template = s.RiskAssessmentTemplateCreate(
        taxonomy_id="tax-1", name="Baseline"
    )
    assert template.structure == {"sections": []}


def test_seed_categories_cover_required_dimensions():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "seed_risk_taxonomy",
        str(BACKEND_ROOT / "scripts" / "seed_risk_taxonomy.py"),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ibm_keys = {key for key, _name, _desc, _factors in module.IBM_CATEGORIES}
    for required in (
        "fairness", "explainability", "robustness", "privacy",
        "security", "accountability", "hallucination", "value_alignment",
    ):
        assert required in ibm_keys, f"IBM seed must cover '{required}'"

    mit_keys = {key for key, _name, _desc, _factors in module.MIT_CATEGORIES}
    for required in (
        "discrimination_toxicity", "privacy_data_governance", "misinformation",
        "malicious_actors_misuse", "human_computer_interaction",
        "socioeconomic_environmental", "ai_safety",
        "transparency_accountability",
    ):
        assert required in mit_keys, f"MIT seed must cover '{required}'"

    assert {t["key"] for t in module.TAXONOMIES} >= {"ibm", "mit"}
