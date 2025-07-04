"""create_tenant_tables

Revision ID: e81ba2ab0262
Revises: 
Create Date: 2025-07-03 01:00:00.016994

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e81ba2ab0262'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """create_tenant_tables"""
    # Create tenants table first (no dependencies)
    op.create_table('tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_name', sa.String(length=255), nullable=False),
        sa.Column('tenant_type', sa.String(length=50), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        
        # Contact Information
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('social_links', postgresql.JSONB(), nullable=True),
        
        # Location Details
        sa.Column('tenant_address', sa.String(length=255), nullable=True),
        sa.Column('tenant_city', sa.String(length=255), nullable=True),
        sa.Column('tenant_state', sa.String(length=255), nullable=True),
        sa.Column('tenant_country', sa.String(length=255), nullable=True),
        sa.Column('tenant_country_code', sa.String(length=10), nullable=True),
        sa.Column('zip', sa.String(length=10), nullable=True),
        sa.Column('landmark', sa.String(length=255), nullable=True),
        sa.Column('tenant_timezone', sa.String(length=255), nullable=True),
        
        # Church Specific Fields
        sa.Column('parish_name', sa.String(length=255), nullable=True),
        sa.Column('branch', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=255), nullable=True),
        sa.Column('tenant_head', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tenant_status', sa.String(length=255), nullable=True),
        
        # Configuration
        sa.Column('adult_consent', sa.Integer(), nullable=False, server_default=sa.text('16')),
        sa.Column('member_data_retention_period', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('team_deletion_grace_period', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('group_deletion_grace_period', sa.Integer(), nullable=False, server_default=sa.text('30')),
        
        # Registry Reference
        sa.Column('registry_id', sa.Integer(), nullable=False),
        
        # Timestamps
        sa.Column('tenant_date_created', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain', name='tenant_domain_unique')
    )
    
    # Create person table
    op.create_table('person',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('user_type_id', sa.Integer(), nullable=True),
        sa.Column('fam_id', sa.Integer(), nullable=True),
        sa.Column('bulk_upload_history_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('middle_name', sa.String(), nullable=True),
        sa.Column('maiden_name', sa.String(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('dob', sa.String(), nullable=True),
        sa.Column('marital_status', sa.String(), nullable=True),
        sa.Column('race', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_person_fam_id'), 'person', ['fam_id'], unique=False)
    op.create_index(op.f('ix_person_id'), 'person', ['id'], unique=False)
    op.create_index(op.f('ix_person_tenant_id'), 'person', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_person_user_type_id'), 'person', ['user_type_id'], unique=False)
    
    # Create visitors table
    op.create_table('visitors',
        sa.Column('visitor_id', sa.Integer(), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=20), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.PrimaryKeyConstraint('visitor_id'),
        sa.UniqueConstraint('email', 'phone', name='uix_visitor_contact')
    )
    op.create_index('idx_visitor_name', 'visitors', ['first_name', 'last_name'], unique=False)
    
    # Create family_members table
    op.create_table('family_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visitor_id', sa.Integer(), nullable=False),
        sa.Column('relationship', sa.Enum('SPOUSE', 'CHILD', 'PARENT', 'SIBLING', 'OTHER', name='relationshiptype'), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['visitor_id'], ['visitors.visitor_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ai_decision_audit table
    op.create_table('ai_decision_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision_type', sa.String(length=50), nullable=False),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('final_decision', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ai_feedback_analysis table
    op.create_table('ai_feedback_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('analysis_result', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create notes table
    op.create_table('notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_type', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create reports table
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('report_name', sa.String(length=200), nullable=False),
        sa.Column('report_data', sa.Text(), nullable=True),
        sa.Column('generated_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ai_recommendation_log table
    op.create_table('ai_recommendation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_type', sa.String(length=100), nullable=False),
        sa.Column('recommendation_text', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create suppression_log table
    op.create_table('suppression_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('suppression_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('suppressed_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """create_tenant_tables"""
    # Drop tables in reverse order (to handle foreign key dependencies)
    op.drop_table('reports')
    op.drop_table('notes')
    op.drop_table('ai_feedback_analysis')
    op.drop_table('suppression_log')
    op.drop_table('ai_recommendation_log')
    op.drop_table('ai_decision_audit')
    op.drop_table('family_members')
    op.drop_index('idx_visitor_name', table_name='visitors')
    op.drop_table('visitors')
    op.drop_index(op.f('ix_person_user_type_id'), table_name='person')
    op.drop_index(op.f('ix_person_tenant_id'), table_name='person')
    op.drop_index(op.f('ix_person_id'), table_name='person')
    op.drop_index(op.f('ix_person_fam_id'), table_name='person')
    op.drop_table('person')
    op.drop_table('tenants')