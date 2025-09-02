"""Add CURRENT_TIMESTAMP defaults to datetime columns

Revision ID: add_timestamp_defaults
Revises: fix_module_name_nullable
Create Date: 2025-08-23 01:52:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_timestamp_defaults'
down_revision = 'fix_module_name_nullable'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add CURRENT_TIMESTAMP defaults to created_at and updated_at columns."""
    
    tables_to_fix = [
        'ai_fam',
        'ai_notes', 
        'ai_recommendation_log',
        'ai_suppression_log',
        'ai_task',
        'ai_decision_audit',
        'ai_feedback',
        'reports',
        'auth',
        'user_types',
        'user_statuses',
        'tenants'
    ]
    
    for table_name in tables_to_fix:
        # Add default CURRENT_TIMESTAMP to created_at
        op.alter_column(
            table_name,
            'created_at',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        )
        
        # Add default CURRENT_TIMESTAMP to updated_at
        op.alter_column(
            table_name,
            'updated_at',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        )

def downgrade() -> None:
    """Remove CURRENT_TIMESTAMP defaults from datetime columns."""
    
    tables_to_revert = [
        'ai_fam',
        'ai_notes',
        'ai_recommendation_log', 
        'ai_suppression_log',
        'ai_task',
        'ai_decision_audit',
        'ai_feedback',
        'reports',
        'auth',
        'user_types',
        'user_statuses',
        'tenants'
    ]
    
    for table_name in tables_to_revert:
        op.alter_column(
            table_name,
            'created_at',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=None
        )
        
        op.alter_column(
            table_name,
            'updated_at',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=None
        )