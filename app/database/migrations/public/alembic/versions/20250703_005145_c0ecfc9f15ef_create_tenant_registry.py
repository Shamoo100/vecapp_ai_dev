"""create_tenant_registry

Revision ID: c0ecfc9f15ef
Revises: 
Create Date: 2025-07-03 00:51:45.359235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0ecfc9f15ef'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """create_tenant_registry"""
    # Create tenant_registry table in public schema
    op.create_table('tenant_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_name', sa.String(length=100), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('schema_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_name'),
        sa.UniqueConstraint('schema_name')
    )


def downgrade() -> None:
    """create_tenant_registry"""
    # Drop tenant_registry table
    op.drop_table('tenant_registry')