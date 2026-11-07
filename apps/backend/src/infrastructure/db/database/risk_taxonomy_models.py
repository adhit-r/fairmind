"""
Risk taxonomy data model for AI risk assessment (Issue #157).

Framework-agnostic taxonomy: IBM AI Risk Atlas, MIT AI Risk Repository,
OECD, or custom taxonomies can coexist without a redesign.

Tables: risk_taxonomies, risk_categories, risk_factors,
risk_assessment_templates.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .connection import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RiskTaxonomy(Base):
    """A named risk framework (e.g. IBM AI Risk Atlas, MIT AI Risk Repository).

    Framework-agnostic: adding OECD or a custom taxonomy is a new row,
    not a schema change.
    """

    __tablename__ = "risk_taxonomies"

    id = Column(String, primary_key=True, default=_new_id)
    key = Column(String, nullable=False, unique=True, index=True)
    # e.g. "ibm", "mit", "oecd", "custom"
    name = Column(String, nullable=False)
    version = Column(String, nullable=False, default="1.0")
    description = Column(Text, nullable=False, default="")
    source_uri = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    categories = relationship(
        "RiskCategory", back_populates="taxonomy", cascade="all, delete-orphan"
    )
    templates = relationship(
        "RiskAssessmentTemplate",
        back_populates="taxonomy",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<RiskTaxonomy(key={self.key}, version={self.version})>"


class RiskCategory(Base):
    """A top-level risk dimension within a taxonomy.

    Covers: fairness, explainability, robustness, privacy, security,
    accountability, hallucination (plus taxonomy-specific extras).
    """

    __tablename__ = "risk_categories"
    __table_args__ = (
        UniqueConstraint("taxonomy_id", "key", name="uq_risk_category_taxonomy_key"),
    )

    id = Column(String, primary_key=True, default=_new_id)
    taxonomy_id = Column(
        String, ForeignKey("risk_taxonomies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    key = Column(String, nullable=False, index=True)
    # e.g. "fairness", "robustness", "hallucination"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False, default="")
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    taxonomy = relationship("RiskTaxonomy", back_populates="categories")
    factors = relationship(
        "RiskFactor", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RiskCategory(key={self.key}, taxonomy_id={self.taxonomy_id})>"


class RiskFactor(Base):
    """A sub-dimension of a risk category (e.g. fairness -> data bias,
    representation disparity, outcome disparity)."""

    __tablename__ = "risk_factors"
    __table_args__ = (
        UniqueConstraint("category_id", "key", name="uq_risk_factor_category_key"),
    )

    id = Column(String, primary_key=True, default=_new_id)
    category_id = Column(
        String, ForeignKey("risk_categories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    key = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False, default="")
    # JSON-encoded list of mitigations/guidance strings; stored as TEXT for
    # SQLite/PostgreSQL portability (matches governance_models.py convention).
    guidance_json = Column(Text, nullable=False, default="[]")
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("RiskCategory", back_populates="factors")

    @property
    def guidance(self) -> list[str]:
        """Parsed guidance list, exposed so Pydantic from_attributes can read it."""
        return json.loads(self.guidance_json or "[]")

    def __repr__(self) -> str:
        return f"<RiskFactor(key={self.key}, category_id={self.category_id})>"


class RiskAssessmentTemplate(Base):
    """Questionnaire structure for assessing a system against a taxonomy.

    `structure_json` is a JSON-encoded object, e.g.:
    {"sections": [{"title": ..., "questions": [{"id": ..., "text": ...,
    "factor_key": ..., "weight": ...}]}]}
    """

    __tablename__ = "risk_assessment_templates"
    __table_args__ = (
        UniqueConstraint(
            "taxonomy_id", "version", name="uq_risk_template_taxonomy_version"
        ),
    )

    id = Column(String, primary_key=True, default=_new_id)
    taxonomy_id = Column(
        String, ForeignKey("risk_taxonomies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name = Column(String, nullable=False)
    version = Column(String, nullable=False, default="1.0")
    description = Column(Text, nullable=False, default="")
    structure_json = Column(Text, nullable=False, default='{"sections": []}')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    taxonomy = relationship("RiskTaxonomy", back_populates="templates")

    @property
    def structure(self) -> dict[str, Any]:
        """Parsed structure dict, exposed so Pydantic from_attributes can read it."""
        return json.loads(self.structure_json or '{"sections": []}')

    def __repr__(self) -> str:
        return (
            f"<RiskAssessmentTemplate(name={self.name}, version={self.version})>"
        )
