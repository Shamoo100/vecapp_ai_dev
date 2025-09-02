"""Add missing columns to ai_recommendation_log

Revision ID: add_recommendation_columns
Revises: 4b82477c8a2d
Create Date: 2025-01-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_recommendation_columns'
down_revision = '4b82477c8a2d'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add missing columns to ai_recommendation_log table."""
    # # Change id from UUID to Integer (if needed)
    # op.execute("ALTER TABLE ai_recommendation_log ALTER COLUMN id TYPE INTEGER USING (ROW_NUMBER() OVER())")
    # op.execute("ALTER TABLE ai_recommendation_log ALTER COLUMN id SET DEFAULT nextval('ai_recommendation_log_id_seq')")
    
    # Add missing columns
    op.add_column('ai_recommendation_log', sa.Column('text', sa.Text(), nullable=False, server_default=''))
    op.add_column('ai_recommendation_log', sa.Column('section', sa.String(100), nullable=True))
    op.add_column('ai_recommendation_log', sa.Column('priority', sa.String(20), nullable=False, server_default='normal'))
    op.add_column('ai_recommendation_log', sa.Column('confidence', sa.Float(), nullable=True))
    op.add_column('ai_recommendation_log', sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('ai_recommendation_log', sa.Column('scenario_type', sa.String(50), nullable=True))
    op.add_column('ai_recommendation_log', sa.Column('source', sa.String(100), nullable=True, server_default='followup_note_agent'))
    op.add_column('ai_recommendation_log', sa.Column('model_version', sa.String(50), nullable=True))
    op.add_column('ai_recommendation_log', sa.Column('suggested_by', sa.String(20), nullable=False, server_default='ai'))
    op.add_column('ai_recommendation_log', sa.Column('suppressed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('ai_recommendation_log', sa.Column('suppress_reason', sa.Text(), nullable=True))
    op.add_column('ai_recommendation_log', sa.Column('meta', postgresql.JSONB(), nullable=True))
    
    # Remove server defaults after adding columns
    op.alter_column('ai_recommendation_log', 'text', server_default=None)
    op.alter_column('ai_recommendation_log', 'priority', server_default=None)
    op.alter_column('ai_recommendation_log', 'source', server_default=None)
    op.alter_column('ai_recommendation_log', 'suggested_by', server_default=None)
    op.alter_column('ai_recommendation_log', 'suppressed', server_default=None)

def downgrade() -> None:
    """Remove added columns from ai_recommendation_log table."""
    op.drop_column('ai_recommendation_log', 'meta')
    op.drop_column('ai_recommendation_log', 'suppress_reason')
    op.drop_column('ai_recommendation_log', 'suppressed')
    op.drop_column('ai_recommendation_log', 'suggested_by')
    op.drop_column('ai_recommendation_log', 'model_version')
    op.drop_column('ai_recommendation_log', 'source')
    op.drop_column('ai_recommendation_log', 'scenario_type')
    op.drop_column('ai_recommendation_log', 'tags')
    op.drop_column('ai_recommendation_log', 'confidence')
    op.drop_column('ai_recommendation_log', 'priority')
    op.drop_column('ai_recommendation_log', 'section')
    op.drop_column('ai_recommendation_log', 'text')