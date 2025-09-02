"""Fix datetime timezone issues

Revision ID: fix_datetime_timezone
Revises: 1836cef801cc
Create Date: 2025-08-22 23:40:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'fix_datetime_timezone'
down_revision = '1836cef801cc'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Convert datetime columns to timezone-aware."""
    
    # Tables that use TimestampMixin and need timezone-aware columns
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
        # Convert created_at to timezone-aware
        op.alter_column(
            table_name,
            'created_at',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False
        )
        
        # Convert updated_at to timezone-aware  
        op.alter_column(
            table_name,
            'updated_at',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False
        )
    
    # Fix AIProcessingMixin columns that are already timezone-aware
    processing_tables = ['ai_notes', 'ai_task']
    for table_name in processing_tables:
        # These should already be timezone-aware, but ensure consistency
        try:
            op.alter_column(
                table_name,
                'processing_started_at',
                type_=sa.DateTime(timezone=True),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=True
            )
            
            op.alter_column(
                table_name,
                'processing_completed_at', 
                type_=sa.DateTime(timezone=True),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=True
            )
        except Exception:
            # Columns might not exist in all tables
            pass

def downgrade() -> None:
    """Revert datetime columns to timezone-naive."""
    
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
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False
        )
        
        op.alter_column(
            table_name,
            'updated_at',
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True), 
            existing_nullable=False
        )