"""create_base_tables

Revision ID: c4fd5f3bf58a
Revises: 
Create Date: 2025-06-10 12:31:43.568506+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4fd5f3bf58a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    #create tenant table
    op.create_table(
        'church_branch',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('tenant_name', sa.String(255), nullable=False),
        sa.Column('tenant_type', sa.String(50)),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(255)),
        sa.Column('website', sa.String(255)),
        sa.Column('social_links', postgresql.JSONB()),
        sa.Column('tenant_address', sa.String(255)),
        sa.Column('tenant_city', sa.String(255)),
        sa.Column('tenant_state', sa.String(255)),
        sa.Column('tenant_country', sa.String(255)),
        sa.Column('tenant_country_code', sa.String(10)),
        sa.Column('zip', sa.String(10)),
        sa.Column('landmark', sa.String(255)),
        sa.Column('tenant_timezone', sa.String(255)),
        sa.Column('parish_name', sa.String(255)),
        sa.Column('branch', sa.String(255)),
        sa.Column('logo_url', sa.String(255)),
        sa.Column('tenant_head', postgresql.UUID(as_uuid=True)),
        sa.Column('tenant_status', sa.String(255)),
        sa.Column('adult_consent', sa.Integer(), nullable=False, server_default=sa.text('16')),
        sa.Column('member_data_retention_period', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('team_deletion_grace_period', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('group_deletion_grace_period', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('tenant_date_created', sa.Date()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('domain', name='church_branch_domain_unique')
    )
    

    #create visitor table
    op.create_table(
        'visitor',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(20), nullable=False),
        sa.Column('first_name', sa.String(50), nullable=False),
        sa.Column('last_name', sa.String(50), nullable=False),
        sa.Column('gender', sa.Enum('Male', 'Female', 'Other', name='gender_enum'), nullable=False),
        sa.Column('race', sa.String(50), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('marital_status', sa.Enum('Single', 'Married', 'Divorced', 'Widowed', name='marital_status_enum'), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('preferred_communication_method', sa.Enum('Email', 'Phone', 'SMS', 'Mail', name='communication_method_enum'), nullable=False),
        sa.Column('best_contact_time', sa.String(50), nullable=False),
        sa.Column('receive_devotionals', sa.Boolean(), nullable=False),
        sa.Column('occupation', sa.String(100), nullable=False),
        sa.Column('relocated', sa.Boolean(), nullable=False),
        sa.Column('how_heard', sa.String(100), nullable=False),
        sa.Column('joining_church_consideration', sa.Boolean(), nullable=False),
        sa.Column('joining_church_contact_time', sa.String(50), nullable=False),
        sa.Column('prayer_request', sa.Text(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('email', 'phone', name='uix_visitor_contact'),
        sa.Index('idx_visitor_name', 'first_name', 'last_name'),
        sa.ForeignKeyConstraint(['tenant_id'], ['church_branch.id'], name='fk_visitor_tenant')
    )

    #family member table
    op.create_table(
        'family_member',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('visitor_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(50), nullable=False),
        sa.Column('last_name', sa.String(50), nullable=False),
        sa.Column('gender', sa.Enum('Male', 'Female', 'Other', name='gender_enum'), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('family_relationship', sa.Enum('Spouse', 'Child', 'Parent', 'Sibling', 'Other', name='family_relationship_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('email', 'phone', name='uix_family_contact'),
        sa.Index('idx_family_relationship', 'family_relationship'),
        sa.ForeignKeyConstraint(['visitor_id'], ['visitor.id'], name='fk_family_member_visitor')        
    )

    #notes table
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_assignee_id', sa.Integer(), nullable=True),
        sa.Column('recipient_id', sa.Integer(), nullable=True),
        sa.Column('recipient_fam_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('notes_body', sa.String(), nullable=True),
        sa.Column('note_link', sa.String(), nullable=True),
        sa.Column('note_photos', sa.String(), nullable=True),
        sa.Column('file_attachment', sa.String(), nullable=True),
        sa.Column('is_edited', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='fk_notes_task'),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name='fk_notes_person'),
        sa.ForeignKeyConstraint(['task_assignee_id'], ['task_assignees.id'], name='fk_notes_task_assignee'),
        sa.ForeignKeyConstraint(['recipient_id'], ['recipients.id'], name='fk_notes_recipient'),
        sa.ForeignKeyConstraint(['recipient_fam_id'], ['recipient_families.id'], name='fk_notes_recipient_family')
    )

    #ai_notes table
    op.create_table(
        
    )

    #ai_recommendation_log table
    op.create_table(
        'ai_recommendation_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fam_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('module_name', sa.String(50), nullable=True),
        sa.Column('recommended_entity_type', sa.String(50), nullable=True),
        sa.Column('recommended_entity_id', sa.String(50), nullable=True),
        sa.Column('recommendation_score', sa.Integer(), nullable=True),
        sa.Column('recommendation_tier', sa.String(25), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name='fk_ai_recommendation_person'),
        sa.ForeignKeyConstraint(['fam_id'], ['families.id'], name='fk_ai_recommendation_family')
    )

    #ai_feedback_analysis table
    op.create_table(
        'ai_feedback_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_category', sa.String(100)),
        sa.Column('tone', sa.String(25)),
        sa.Column('suggested_action', sa.Text()),
        sa.Column('feedback_text', sa.Text()),
        sa.Column('confidence_score', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name='fk_ai_feedback_person')
    )

    #ai_suppression_log table
    op.create_table(
        'ai_suppression_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fam_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('module_name', sa.String(50), nullable=True),
        sa.Column('suppressed_entity_type', sa.String(50), nullable=True),
        sa.Column('suppressed_entity_id', sa.String(50), nullable=True),
        sa.Column('suppression_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name='fk_ai_suppression_person'),
        sa.ForeignKeyConstraint(['fam_id'], ['families.id'], name='fk_ai_suppression_family')
    )

    #ai_decision_audit
    op.create_table(
        'ai_decision_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=True),
        sa.Column('rule_description', sa.Text(), nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('triggered', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name='fk_ai_decision_person')
    )

def downgrade():
    op.drop_table('tenant')
    op.drop_table('visitor')
    op.drop_table('family_member')
    op.drop_table('notes')
    op.drop_table('ai_notes')
    op.drop_table('ai_recommendation_log')
    op.drop_table('ai_feedback_analysis')
    op.drop_table('ai_suppression_log')
    op.drop_table('ai_decision_audit')
