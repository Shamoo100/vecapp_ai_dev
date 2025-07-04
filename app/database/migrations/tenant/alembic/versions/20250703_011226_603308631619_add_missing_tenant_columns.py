"""add_missing_tenant_columns

Revision ID: 603308631619
Revises: e81ba2ab0262
Create Date: 2025-07-03 01:12:26.756338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '603308631619'
down_revision: Union[str, None] = 'e81ba2ab0262'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """add_missing_tenant_columns"""
    # Add missing columns to tenants table
    op.add_column('tenants', sa.Column('tenant_type', sa.String(length=50), nullable=True))
    op.add_column('tenants', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    
    # Contact Information
    op.add_column('tenants', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('phone', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('website', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('social_links', postgresql.JSONB(), nullable=True))
    
    # Location Details
    op.add_column('tenants', sa.Column('tenant_address', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('tenant_city', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('tenant_state', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('tenant_country', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('tenant_country_code', sa.String(length=10), nullable=True))
    op.add_column('tenants', sa.Column('zip', sa.String(length=10), nullable=True))
    op.add_column('tenants', sa.Column('landmark', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('tenant_timezone', sa.String(length=255), nullable=True))
    
    # Church Specific Fields
    op.add_column('tenants', sa.Column('parish_name', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('branch', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('logo_url', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('tenant_head', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tenants', sa.Column('tenant_status', sa.String(length=255), nullable=True))
    
    # Configuration
    op.add_column('tenants', sa.Column('adult_consent', sa.Integer(), nullable=False, server_default=sa.text('16')))
    op.add_column('tenants', sa.Column('member_data_retention_period', sa.Integer(), nullable=False, server_default=sa.text('30')))
    op.add_column('tenants', sa.Column('team_deletion_grace_period', sa.Integer(), nullable=False, server_default=sa.text('30')))
    op.add_column('tenants', sa.Column('group_deletion_grace_period', sa.Integer(), nullable=False, server_default=sa.text('30')))
    
    # Timestamps
    op.add_column('tenants', sa.Column('tenant_date_created', sa.Date(), nullable=True))
    
    # Update constraints
    op.alter_column('tenants', 'domain', nullable=False)
    op.alter_column('tenants', 'registry_id', nullable=False)
    op.alter_column('tenants', 'tenant_name', type_=sa.String(length=255))
    
    # Add unique constraint for domain
    op.create_unique_constraint('tenant_domain_unique', 'tenants', ['domain'])


def downgrade() -> None:
    """add_missing_tenant_columns"""
    # Drop unique constraint
    op.drop_constraint('tenant_domain_unique', 'tenants', type_='unique')
    
    # Revert column changes
    op.alter_column('tenants', 'domain', nullable=True)
    op.alter_column('tenants', 'registry_id', nullable=True)
    
    # Drop added columns in reverse order
    op.drop_column('tenants', 'tenant_date_created')
    op.drop_column('tenants', 'group_deletion_grace_period')
    op.drop_column('tenants', 'team_deletion_grace_period')
    op.drop_column('tenants', 'member_data_retention_period')
    op.drop_column('tenants', 'adult_consent')
    op.drop_column('tenants', 'tenant_status')
    op.drop_column('tenants', 'tenant_head')
    op.drop_column('tenants', 'logo_url')
    op.drop_column('tenants', 'branch')
    op.drop_column('tenants', 'parish_name')
    op.drop_column('tenants', 'tenant_timezone')
    op.drop_column('tenants', 'landmark')
    op.drop_column('tenants', 'zip')
    op.drop_column('tenants', 'tenant_country_code')
    op.drop_column('tenants', 'tenant_country')
    op.drop_column('tenants', 'tenant_state')
    op.drop_column('tenants', 'tenant_city')
    op.drop_column('tenants', 'tenant_address')
    op.drop_column('tenants', 'social_links')
    op.drop_column('tenants', 'website')
    op.drop_column('tenants', 'phone')
    op.drop_column('tenants', 'email')
    op.drop_column('tenants', 'is_active')
    op.drop_column('tenants', 'tenant_type')