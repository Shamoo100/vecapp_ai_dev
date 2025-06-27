from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import asyncio
import os
from dotenv import load_dotenv

# Import your models
from app.database.models.base import Base
from app.database.models.person import Person
from app.database.models.tenant import  ChurchBranch
from app.database.models.visitor import Visitor
from app.database.models.volunteer import Volunteer
# Import other models as needed

# Import tenant context
from app.database.tenant_context import TenantContext

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Set the target metadata
target_metadata = Base.metadata

# Load environment variables
load_dotenv()

# Set SQLAlchemy URL from environment
config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL"))

# Get tenant schema option from command line
tenant_schema = context.get_x_argument(as_dictionary=True).get('tenant')


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    
    # Handle tenant schema if specified
    schema_option = {}
    if tenant_schema:
        schema_option["schema"] = tenant_schema
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **schema_option
    )

    with context.begin_transaction():
        context.run_migrations()


async def get_tenant_schemas():
    """Get all tenant schemas from the database."""
    return await TenantContext.list_tenant_schemas()


def do_run_migrations(connection):
    """Run migrations with the given connection."""
    # If tenant schema specified, run migrations for that schema only
    if tenant_schema:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=tenant_schema,
            include_schemas=True,
            include_name=lambda name, _, **kw: (
                # Include objects in the tenant schema or public schema objects that don't have schema-specific versions
                (kw.get("schema") == tenant_schema) or 
                (kw.get("schema") == "public" and not any(
                    name in target_metadata.tables.get(f"{s}.{name}", {})
                    for s in [tenant_schema]
                ))
            )
        )
        with context.begin_transaction():
            context.run_migrations()
    else:
        # Run migrations for public schema
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="public"
        )
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
