"""
SQLAlchemy ORM models for India Compliance RAG (Retrieval-Augmented Generation)
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .connection import Base


class IndiaRegulatoryDocument(Base):
    """Model for storing regulatory document embeddings for RAG"""
    __tablename__ = "india_regulatory_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_type = Column(String(100), nullable=False, index=True)  # 'dpdp_act', 'niti_aayog', etc.
    section_id = Column(String(255), nullable=False, index=True)     # e.g., 'DPDP_Section_6'
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(VECTOR(1536), nullable=True)                  # OpenAI embedding
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_india_regulatory_documents_type', 'document_type'),
        Index('idx_india_regulatory_documents_section_id', 'section_id'),
        Index('idx_india_regulatory_documents_type_section', 'document_type', 'section_id'),
        Index('idx_india_regulatory_documents_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<IndiaRegulatoryDocument(id={self.id}, document_type={self.document_type}, section_id={self.section_id})>"


class IndiaComplianceRAGContext(Base):
    """Model for storing RAG query context and results"""
    __tablename__ = "india_compliance_rag_context"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    query = Column(Text, nullable=False)
    query_embedding = Column(VECTOR(1536), nullable=True)
    retrieved_documents = Column(JSON, nullable=False)  # Array of document IDs and scores
    generated_response = Column(Text, nullable=False)
    response_quality_score = Column(Float, nullable=True)  # 0-1 score
    feedback = Column(String(50), nullable=True, index=True)  # 'helpful', 'not_helpful', etc.
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_india_compliance_rag_context_user_id', 'user_id'),
        Index('idx_india_compliance_rag_context_created_at', 'created_at'),
        Index('idx_india_compliance_rag_context_feedback', 'feedback'),
    )

    def __repr__(self):
        return f"<IndiaComplianceRAGContext(id={self.id}, user_id={self.user_id}, query_length={len(self.query)})>"
