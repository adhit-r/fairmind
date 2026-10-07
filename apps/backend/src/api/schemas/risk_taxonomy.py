"""Pydantic schemas for the risk taxonomy data model (Issue #157)."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Taxonomy ---


class RiskTaxonomyBase(BaseModel):
    key: str = Field(..., description="Stable key, e.g. 'ibm', 'mit', 'oecd'")
    name: str
    version: str = "1.0"
    description: str = ""
    source_uri: Optional[str] = None
    is_active: bool = True


class RiskTaxonomyCreate(RiskTaxonomyBase):
    pass


class RiskTaxonomyRead(RiskTaxonomyBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Category ---


class RiskCategoryBase(BaseModel):
    taxonomy_id: str
    key: str = Field(..., description="e.g. 'fairness', 'robustness'")
    name: str
    description: str = ""
    sort_order: int = 0


class RiskCategoryCreate(RiskCategoryBase):
    pass


class RiskCategoryRead(RiskCategoryBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Factor ---


class RiskFactorBase(BaseModel):
    category_id: str
    key: str
    name: str
    description: str = ""
    guidance: list[str] = Field(
        default_factory=list,
        description="Mitigation guidance strings (stored as guidance_json).",
    )
    sort_order: int = 0


class RiskFactorCreate(RiskFactorBase):
    pass


class RiskFactorRead(RiskFactorBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Template ---


class RiskAssessmentTemplateBase(BaseModel):
    taxonomy_id: str
    name: str
    version: str = "1.0"
    description: str = ""
    structure: dict[str, Any] = Field(
        default_factory=lambda: {"sections": []},
        description="Questionnaire structure (stored as structure_json).",
    )
    is_active: bool = True


class RiskAssessmentTemplateCreate(RiskAssessmentTemplateBase):
    pass


class RiskAssessmentTemplateRead(RiskAssessmentTemplateBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
