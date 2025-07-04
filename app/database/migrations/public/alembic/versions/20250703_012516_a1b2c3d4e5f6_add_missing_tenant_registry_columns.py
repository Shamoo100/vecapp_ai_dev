"""add_missing_tenant_registry_columns

Revision ID: a1b2c3d4e5f6
Revises: c0ecfc9f15ef
Create Date: 2025-07-03 01:25:16.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c0ecfc9f15ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """add_missing_tenant_registry_columns"""
    # Add missing columns to tenant_registry table
    
    # Add tenant_type column
    op.add_column('tenant_registry', sa.Column('tenant_type', sa.String(length=50), server_default='church'))
    
    # Make domain nullable=False and add unique constraint
    op.alter_column('tenant_registry', 'domain', nullable=False)
    
    # Contact Information
    op.add_column('tenant_registry', sa.Column('email', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('phone', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('website', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('social_links', postgresql.JSONB()))
    
    # Location Details
    op.add_column('tenant_registry', sa.Column('tenant_address', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('tenant_city', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('tenant_state', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('tenant_country', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('tenant_country_code', sa.String(length=10)))
    op.add_column('tenant_registry', sa.Column('zip', sa.String(length=10)))
    op.add_column('tenant_registry', sa.Column('landmark', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('tenant_timezone', sa.String(length=255)))
    
    # Church Specific Fields
    op.add_column('tenant_registry', sa.Column('parish_name', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('branch', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('logo_url', sa.String(length=255)))
    op.add_column('tenant_registry', sa.Column('tenant_head', postgresql.UUID(as_uuid=True)))
    op.add_column('tenant_registry', sa.Column('tenant_status', sa.String(length=255)))
    
    # Configuration
    op.add_column('tenant_registry', sa.Column('adult_consent', sa.Integer(), nullable=False, server_default='16'))
    op.add_column('tenant_registry', sa.Column('member_data_retention_period', sa.Integer(), nullable=False, server_default='30'))
    op.add_column('tenant_registry', sa.Column('team_deletion_grace_period', sa.Integer(), nullable=False, server_default='30'))
    op.add_column('tenant_registry', sa.Column('group_deletion_grace_period', sa.Integer(), nullable=False, server_default='30'))
    
    # Schema Management
    op.add_column('tenant_registry', sa.Column('schema_provisioned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('tenant_registry', sa.Column('migrations_applied', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('tenant_registry', sa.Column('api_key', sa.String(length=255), nullable=False))
    
    # Timestamps
    op.add_column('tenant_registry', sa.Column('tenant_date_created', sa.Date(), server_default=sa.text('CURRENT_DATE')))
    
    # Update constraints
    op.drop_constraint('tenant_registry_tenant_name_key', 'tenant_registry', type_='unique')
    op.create_unique_constraint('tenant_registry_domain_unique', 'tenant_registry', ['domain'])
    op.create_unique_constraint('tenant_registry_schema_unique', 'tenant_registry', ['schema_name'])
    op.create_unique_constraint('tenant_registry_api_key_unique', 'tenant_registry', ['api_key'])


def downgrade() -> None:
    """add_missing_tenant_registry_columns"""
    # Drop unique constraints
    op.drop_constraint('tenant_registry_api_key_unique', 'tenant_registry', type_='unique')
    op.drop_constraint('tenant_registry_schema_unique', 'tenant_registry', type_='unique')
    op.drop_constraint('tenant_registry_domain_unique', 'tenant_registry', type_='unique')
    op.create_unique_constraint('tenant_registry_tenant_name_key', 'tenant_registry', ['tenant_name'])
    
    # Revert domain column
    op.alter_column('tenant_registry', 'domain', nullable=True)
    
    # Drop added columns in reverse order
    op.drop_column('tenant_registry', 'tenant_date_created')
    op.drop_column('tenant_registry', 'api_key')
    op.drop_column('tenant_registry', 'migrations_applied')
    op.drop_column('tenant_registry', 'schema_provisioned')
    op.drop_column('tenant_registry', 'group_deletion_grace_period')
    op.drop_column('tenant_registry', 'team_deletion_grace_period')
    op.drop_column('tenant_registry', 'member_data_retention_period')
    op.drop_column('tenant_registry', 'adult_consent')
    op.drop_column('tenant_registry', 'tenant_status')
    op.drop_column('tenant_registry', 'tenant_head')
    op.drop_column('tenant_registry', 'logo_url')
    op.drop_column('tenant_registry', 'branch')
    op.drop_column('tenant_registry', 'parish_name')
    op.drop_column('tenant_registry', 'tenant_timezone')
    op.drop_column('tenant_registry', 'landmark')
    op.drop_column('tenant_registry', 'zip')
    op.drop_column('tenant_registry', 'tenant_country_code')
    op.drop_column('tenant_registry', 'tenant_country')
    op.drop_column('tenant_registry', 'tenant_state')
    op.drop_column('tenant_registry', 'tenant_city')
    op.drop_column('tenant_registry', 'tenant_address')
    op.drop_column('tenant_registry', 'social_links')
    op.drop_column('tenant_registry', 'website')
    op.drop_column('tenant_registry', 'phone')
    op.drop_column('tenant_registry', 'email')
    op.drop_column('tenant_registry', 'tenant_type')