from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, MetaData
from alembic import context
from logging.config import fileConfig
from dotenv import load_dotenv
import os
import sys
import logging
from pathlib import Path

# Add project root to python Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

# Import ONLY public schema models
try:
    from app.database.models.public import Base, TenantRegistry, ai_rate_limit_log
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    raise

# Use Base.metadata - now contains ONLY TenantRegistry
target_metadata = Base.metadata
print(f"Public schema tables: {list(Base.metadata.tables.keys())}")

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

def include_object_filter(obj, name, type_, reflected, compare_to):
    """
    Filter function to determine which objects should be included in migrations.
    
    Excludes:
    - Alembic internal tables (alembic_version)
    - Tables from other schemas (only include public schema)
    """
    # Always exclude Alembic's internal tables
    if type_ == "table" and name in ["alembic_version"]:
        return False
    
    # For tables, only include those in public schema or schema-agnostic
    if type_ == "table":
        return obj.schema == "public" or obj.schema is None
    
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
    """Run migrations in 'offline' mode for public schema only."""
    url = config.get_main_option("sqlalchemy.url")
    logger.info("Running offline migrations for public schema (tenant registry)")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="public",
        include_schemas=False,  # Don't scan other schemas
        compare_type=compare_type_filter,
        compare_server_default=True,
        include_object=include_object_filter
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode for public schema only."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        logger.info("Running migrations for public schema (tenant registry)")
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="public",
            include_schemas=False,  # Don't scan other schemas
            compare_type=compare_type_filter,
            compare_server_default=True,
            render_as_batch=True,
            include_object=include_object_filter
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()