from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, MetaData
from alembic import context
from logging.config import fileConfig
from dotenv import load_dotenv
import os
import logging

# For public schema, we'll define minimal metadata
# This avoids complex imports and focuses on tenant registry only
target_metadata = MetaData()

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

# Metadata is already defined above

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
        compare_type=True,
        compare_server_default=True,
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
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()