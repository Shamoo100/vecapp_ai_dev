"""remove foreign key constraints

Revision ID: 1836cef801cc
Revises: add_recommendation_columns
Create Date: 2025-08-22 23:19:23.258476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1836cef801cc'
down_revision: Union[str, None] = 'add_recommendation_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove foreign key constraints from AI models"""
    
    # Remove foreign key constraints from ai_notes
    with op.batch_alter_table('ai_notes', schema=None) as batch_op:
        # Add new tracking columns
        batch_op.add_column(sa.Column('scenario_type', sa.String(length=50), nullable=True, comment='Type of scenario (e.g., family_new, individual_visit)'))
        batch_op.add_column(sa.Column('generation_source', sa.String(length=100), nullable=True, comment='Source system/agent that generated this note'))
        batch_op.add_column(sa.Column('quality_score', sa.Float(), nullable=True, comment='AI quality assessment score'))
        
        # Update column comments to reflect no FK constraints
        batch_op.alter_column('task_id',
               existing_type=sa.INTEGER(),
               comment='Reference to ai_task.id (no FK constraint)',
               existing_nullable=True)
        batch_op.alter_column('recipient_id',
               existing_type=sa.UUID(),
               comment='Reference to ai_person.id (no FK constraint)',
               existing_nullable=True)
        batch_op.alter_column('recipient_family_id',
               existing_type=sa.UUID(),
               comment='Reference to ai_fam.id (no FK constraint)',
               existing_nullable=True)
        
        # Drop foreign key constraints (with error handling)
        try:
            batch_op.drop_constraint('ai_notes_task_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist
        try:
            batch_op.drop_constraint('ai_notes_recipient_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist
        try:
            batch_op.drop_constraint('ai_notes_recipient_family_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist

    # Remove foreign key constraints from ai_recommendation_log
    with op.batch_alter_table('ai_recommendation_log', schema=None) as batch_op:
        # Update column comments
        batch_op.alter_column('person_id',
               existing_type=sa.UUID(),
               comment='Reference to ai_person.id (no FK constraint)',
               existing_nullable=True)
        batch_op.alter_column('note_id',
               existing_type=sa.INTEGER(),
               comment='Reference to ai_notes.id (no FK constraint)',
               existing_nullable=True)
        batch_op.alter_column('task_id',
               existing_type=sa.INTEGER(),
               comment='Reference to ai_task.id (no FK constraint)',
               existing_nullable=True)
        
        # Drop foreign key constraints (with error handling)
        try:
            batch_op.drop_constraint('ai_recommendation_log_person_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist
        try:
            batch_op.drop_constraint('ai_recommendation_log_note_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist
        try:
            batch_op.drop_constraint('ai_recommendation_log_task_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist

    # Remove foreign key constraints from ai_suppression_log
    with op.batch_alter_table('ai_suppression_log', schema=None) as batch_op:
        # Add new columns for enhanced suppression tracking
        batch_op.add_column(sa.Column('suppressed_entity_type', sa.String(length=50), nullable=False, comment='Type: recommendation, note, task, etc.'))
        batch_op.add_column(sa.Column('suppression_type', sa.String(length=50), nullable=False, comment='manual, automatic, policy, etc.'))
        batch_op.add_column(sa.Column('suppressed_by_user_id', sa.UUID(), nullable=True, comment='User who initiated suppression'))
        batch_op.add_column(sa.Column('auto_suppression_rule', sa.String(length=100), nullable=True, comment='Rule that triggered auto-suppression'))
        batch_op.add_column(sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional suppression context'))
        
        # Update column comments
        batch_op.alter_column('person_id',
               existing_type=sa.UUID(),
               comment='Reference to ai_person.id (no FK constraint)',
               existing_nullable=False)
        
        # Drop foreign key constraints (with error handling)
        try:
            batch_op.drop_constraint('ai_suppression_log_person_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist

    # Remove foreign key constraints from ai_task
    with op.batch_alter_table('ai_task', schema=None) as batch_op:
        # Update column comments
        batch_op.alter_column('recipient_person_id',
               existing_type=sa.UUID(),
               comment='Reference to ai_person.id (no FK constraint)',
               existing_nullable=True)
        batch_op.alter_column('recipient_family_id',
               existing_type=sa.UUID(),
               comment='Reference to ai_fam.id (no FK constraint)',
               existing_nullable=True)
        
        # Drop foreign key constraints (with error handling)
        try:
            batch_op.drop_constraint('ai_task_recipient_person_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist
        try:
            batch_op.drop_constraint('ai_task_recipient_family_id_fkey', type_='foreignkey')
        except Exception:
            pass  # Constraint may not exist


def downgrade() -> None:
    """Restore foreign key constraints"""
    # Note: This is a simplified downgrade
    # In practice, you'd need to restore all constraints and remove added columns
    # For now, we'll leave this empty as restoring FKs requires careful data validation
    pass