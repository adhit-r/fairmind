"""
Alembic migration for India compliance tables with indexes and constraints.

This migration creates all necessary indexes and foreign key constraints
for the India compliance automation feature.

Revision ID: 003
Revises: 002
Create Date: 2025-11-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade migration: Create indexes and constraints for India compliance tables.
    """
    
    # ========================================================================
    # India Compliance Evidence Table Indexes
    # ========================================================================
    
    # Create composite index for system_id and control_id lookups
    op.create_index(
        'idx_india_compliance_evidence_system_control',
        'india_compliance_evidence',
        ['system_id', 'control_id'],
        unique=False
    )
    
    # Create index for time-based queries
    op.create_index(
        'idx_india_compliance_evidence_collected_at_desc',
        'india_compliance_evidence',
        [sa.desc('collected_at')],
        unique=False
    )
    
    # Create index for source filtering
    op.create_index(
        'idx_india_compliance_evidence_source_collected',
        'india_compliance_evidence',
        ['source', 'collected_at'],
        unique=False
    )
    
    # ========================================================================
    # India Compliance Results Table Indexes
    # ========================================================================
    
    # Create composite index for system and framework lookups
    op.create_index(
        'idx_india_compliance_results_system_framework',
        'india_compliance_results',
        ['system_id', 'framework'],
        unique=False
    )
    
    # Create composite index for user and status lookups
    op.create_index(
        'idx_india_compliance_results_user_status',
        'india_compliance_results',
        ['user_id', 'status'],
        unique=False
    )
    
    # Create index for time-based queries
    op.create_index(
        'idx_india_compliance_results_timestamp_desc',
        'india_compliance_results',
        [sa.desc('timestamp')],
        unique=False
    )
    
    # Create index for framework and timestamp (for trend analysis)
    op.create_index(
        'idx_india_compliance_results_framework_timestamp',
        'india_compliance_results',
        ['framework', 'timestamp'],
        unique=False
    )
    
    # ========================================================================
    # India Bias Test Results Table Indexes
    # ========================================================================
    
    # Create composite index for system and bias type lookups
    op.create_index(
        'idx_india_bias_test_results_system_bias_type',
        'india_bias_test_results',
        ['system_id', 'bias_type'],
        unique=False
    )
    
    # Create composite index for model and bias type lookups
    op.create_index(
        'idx_india_bias_test_results_model_bias_type',
        'india_bias_test_results',
        ['model_id', 'bias_type'],
        unique=False
    )
    
    # Create index for time-based queries
    op.create_index(
        'idx_india_bias_test_results_timestamp_desc',
        'india_bias_test_results',
        [sa.desc('timestamp')],
        unique=False
    )
    
    # Create index for user and bias type (for user-specific bias reports)
    op.create_index(
        'idx_india_bias_test_results_user_bias_type',
        'india_bias_test_results',
        ['user_id', 'bias_type'],
        unique=False
    )
    
    # ========================================================================
    # India Compliance Reports Table Indexes
    # ========================================================================
    
    # Create composite index for system and user lookups
    op.create_index(
        'idx_india_compliance_reports_system_user',
        'india_compliance_reports',
        ['system_id', 'user_id'],
        unique=False
    )
    
    # Create index for time-based queries
    op.create_index(
        'idx_india_compliance_reports_generated_at_desc',
        'india_compliance_reports',
        [sa.desc('generated_at')],
        unique=False
    )
    
    # ========================================================================
    # Integration Credentials Table Indexes
    # ========================================================================
    
    # Create composite index for user and integration name lookups
    op.create_index(
        'idx_integration_credentials_user_integration',
        'integration_credentials',
        ['user_id', 'integration_name'],
        unique=False
    )
    
    # Create index for status filtering
    op.create_index(
        'idx_integration_credentials_status_updated',
        'integration_credentials',
        ['status', 'updated_at'],
        unique=False
    )


def downgrade() -> None:
    """
    Downgrade migration: Drop all created indexes.
    """
    
    # Drop India Compliance Evidence indexes
    op.drop_index('idx_india_compliance_evidence_system_control', table_name='india_compliance_evidence')
    op.drop_index('idx_india_compliance_evidence_collected_at_desc', table_name='india_compliance_evidence')
    op.drop_index('idx_india_compliance_evidence_source_collected', table_name='india_compliance_evidence')
    
    # Drop India Compliance Results indexes
    op.drop_index('idx_india_compliance_results_system_framework', table_name='india_compliance_results')
    op.drop_index('idx_india_compliance_results_user_status', table_name='india_compliance_results')
    op.drop_index('idx_india_compliance_results_timestamp_desc', table_name='india_compliance_results')
    op.drop_index('idx_india_compliance_results_framework_timestamp', table_name='india_compliance_results')
    
    # Drop India Bias Test Results indexes
    op.drop_index('idx_india_bias_test_results_system_bias_type', table_name='india_bias_test_results')
    op.drop_index('idx_india_bias_test_results_model_bias_type', table_name='india_bias_test_results')
    op.drop_index('idx_india_bias_test_results_timestamp_desc', table_name='india_bias_test_results')
    op.drop_index('idx_india_bias_test_results_user_bias_type', table_name='india_bias_test_results')
    
    # Drop India Compliance Reports indexes
    op.drop_index('idx_india_compliance_reports_system_user', table_name='india_compliance_reports')
    op.drop_index('idx_india_compliance_reports_generated_at_desc', table_name='india_compliance_reports')
    
    # Drop Integration Credentials indexes
    op.drop_index('idx_integration_credentials_user_integration', table_name='integration_credentials')
    op.drop_index('idx_integration_credentials_status_updated', table_name='integration_credentials')
