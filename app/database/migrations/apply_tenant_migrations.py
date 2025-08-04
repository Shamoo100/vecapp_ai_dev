#!/usr/bin/env python
"""
Script to apply Alembic migrations to all tenant schemas.

This script should be run after creating a new migration with Alembic.
It will apply the migration to all tenant schemas in the database.

Usage:
    python -m app.database.apply_tenant_migrations [--revision REVISION] [--dry-run]
"""

import asyncio
import argparse
import logging
import subprocess
import sys
from typing import List, Optional

from app.config import settings
from app.database.repositories.tenant_context import TenantContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tenant_migrations')


async def get_tenant_schemas() -> List[str]:
    """Get all tenant schemas from the database."""
    return await TenantContext.list_tenant_schemas()


def apply_migration_to_schema(schema: str, revision: Optional[str] = None, dry_run: bool = False) -> bool:
    """Apply Alembic migration to a specific schema.
    
    Args:
        schema: The tenant schema name
        revision: Specific revision to migrate to (default: head)
        dry_run: If True, only show what would be migrated without making changes
    
    Returns:
        True if migration was successful, False otherwise
    """
    cmd = ["alembic", "-x", f"tenant={schema}" "upgrade"]
    
    # Add revision or default to head
    if revision:
        cmd.append(revision)
    else:
        cmd.append("head")
    
    # Add schema argument
    cmd.extend(["-x", f"tenant={schema}"])
    #cmd.append(f"-x=tenant={schema}")
    
    if dry_run:
        cmd.append("--sql")
        logger.info(f"Would apply migration to schema {schema} with command: {' '.join(cmd)}")
        return True
    
    logger.info(f"Applying migration to schema {schema}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Migration applied to schema {schema}")
        if result.stdout.strip():
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to apply migration to schema {schema}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False


async def run_migrations(revision: Optional[str] = None, dry_run: bool = False):
    """Run migrations for all tenant schemas.
    
    Args:
        revision: Specific revision to migrate to (default: head)
        dry_run: If True, only show what would be migrated without making changes
    """
    # First, apply migration to public schema
    logger.info("Applying migration to public schema...")
    success = apply_migration_to_schema("public", revision, dry_run)
    if not success and not dry_run:
        logger.error("Failed to apply migration to public schema. Aborting.")
        return
    
    # Get all tenant schemas
    logger.info("Identifying tenant schemas...")
    schemas = await get_tenant_schemas()
    
    if not schemas:
        logger.warning("No tenant schemas found.")
        return
    
    logger.info(f"Found {len(schemas)} tenant schemas: {', '.join(schemas)}")
    
    # Apply migration to each tenant schema
    success_count = 0
    for schema in schemas:
        if apply_migration_to_schema(schema, revision, dry_run):
            success_count += 1
    
    # Log summary
    logger.info(f"Migration complete! Successfully applied to {success_count}/{len(schemas)} tenant schemas.")


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description='Apply Alembic migrations to all tenant schemas')
    parser.add_argument(
        '--revision',
        help='Specific revision to migrate to (default: head)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )
    
    args = parser.parse_args()
    
    # Run the migrations
    asyncio.run(run_migrations(args.revision, args.dry_run))


if __name__ == '__main__':
    main()