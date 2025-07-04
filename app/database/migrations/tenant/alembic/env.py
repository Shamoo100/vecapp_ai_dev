from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
from dotenv import load_dotenv
import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import tenant-specific models
from app.database.models.base import Base
from app.database.models.visitor import Visitor, FamilyMember
from app.database.models.tenant import Tenant
from app.database.models.person import Person
from app.database.models.decision_audit import DecisionAudit
from app.database.models.recommendation_log import AIRecommendationLog
from app.database.models.suppression_log import SuppressionLog
from app.database.models.feedback import AIFeedbackAnalysis
from app.database.models.notes import Notes
from app.database.models.reports import Report

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set SQLAlchemy URL from environment variable
config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL"))

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Include all tenant-specific models metadata
target_metadata = Base.metadata

def get_tenant_schema():
    """Get the tenant schema from environment variable."""
    tenant_schema = os.environ.get("TENANT_SCHEMA")
    if not tenant_schema:
        raise ValueError("TENANT_SCHEMA environment variable must be set for tenant migrations")
    return tenant_schema

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode for tenant schema."""
    url = config.get_main_option("sqlalchemy.url")
    tenant_schema = get_tenant_schema()
    
    logger.info(f"Running offline migrations for tenant schema: {tenant_schema}")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=tenant_schema,
        include_schemas=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        # Set search path to tenant schema
        context.execute(text(f"SET search_path TO {tenant_schema}"))
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode for tenant schema."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    tenant_schema = get_tenant_schema()
    
    with connectable.connect() as connection:
        logger.info(f"Running migrations for tenant schema: {tenant_schema}")
        
        # Create schema if it doesn't exist
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant_schema}"))
        connection.commit()
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=tenant_schema,
            include_schemas=True,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            # Set search path to tenant schema
            context.execute(text(f"SET search_path TO {tenant_schema}"))
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()