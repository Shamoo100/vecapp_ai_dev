from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
from dotenv import load_dotenv
import os
import sys
import logging
from pathlib import Path

# Load environment variables
load_dotenv()
# Add project root to python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

#config
config = context.config

# Set SQLAlchemy URL from environment variable
config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger('alembic.env')

# Import ONLY tenant schema models
try:
    from app.database.models.tenant import (
        Base, AIPerson, AIFam, AINotes, AITask, Tenant,
        DecisionAudit, AIFeedback, AIRecommendationLog, 
        SuppressionLog, Report, Auth, UserType, UserStatus, AIAuditLog
    )
    logger.info(f"Successfully imported tenant models: {list(Base.metadata.tables.keys())}")
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    raise

# Use Base.metadata - now contains ONLY tenant models
target_metadata = Base.metadata
print(f"Tenant schema tables: {list(Base.metadata.tables.keys())}")

def get_tenant_schema():
    """Get the tenant schema from environment variable."""
    tenant_schema = os.environ.get("TENANT_SCHEMA")
    if not tenant_schema:
        raise ValueError("TENANT_SCHEMA environment variable must be set for tenant migrations")
    return tenant_schema

def include_object_filter(obj, name, type_, reflected, compare_to):
    """
    Filter function to determine which objects should be included in migrations.
    
    Excludes:
    - Alembic internal tables (alembic_version)
    - Tables from other schemas (unless schema-agnostic)
    - Comment-only changes
    """
    # Always exclude Alembic's internal tables
    if type_ == "table" and name in ["alembic_version"]:
        return False
    
    # For tables, only include those in target schema or schema-agnostic
    if type_ == "table":
        tenant_schema = get_tenant_schema()
        return obj.schema == tenant_schema or obj.schema is None
    
    # Include all other object types (indexes, constraints, etc.)
    return True

def compare_type_filter(context, inspected_column, metadata_column, inspected_type, metadata_type):
    """
    Custom type comparison to ignore comment-only changes.
    """
    # If only the comment differs, don't consider it a change
    if hasattr(inspected_column, 'comment') and hasattr(metadata_column, 'comment'):
        if (inspected_column.comment != metadata_column.comment and 
            str(inspected_type) == str(metadata_type)):
            return False
    
    # Use default comparison for actual type changes
    return None

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
        include_schemas=False,  # CRITICAL: Don't scan other schemas
        compare_type=compare_type_filter,
        compare_server_default=True,
        include_object=include_object_filter
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
            include_schemas=False,  # CRITICAL: Don't scan other schemas
            compare_type=compare_type_filter,
            render_as_batch=True,
            compare_server_default=True,
            include_object=include_object_filter
        )

        with context.begin_transaction():
            # Set search path to tenant schema
            context.execute(text(f"SET search_path TO {tenant_schema}"))
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
