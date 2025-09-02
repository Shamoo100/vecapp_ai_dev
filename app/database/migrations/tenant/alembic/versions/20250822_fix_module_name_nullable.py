"""Fix module_name nullable constraint in ai_recommendation_log

Revision ID: fix_module_name_nullable
Revises: fix_datetime_timezone
Create Date: 2025-08-22 23:55:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'fix_module_name_nullable'
down_revision = 'fix_datetime_timezone'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Make module_name column nullable in ai_recommendation_log."""
    op.alter_column(
        'ai_recommendation_log',
        'module_name',
        existing_type=sa.String(length=50),
        nullable=True,
        existing_comment='Module or context of the recommendation'
    )

def downgrade() -> None:
    """Revert module_name column to not nullable."""
    op.alter_column(
        'ai_recommendation_log',
        'module_name',
        existing_type=sa.String(length=50),
        nullable=False,
        existing_comment='Module or context of the recommendation'
    )