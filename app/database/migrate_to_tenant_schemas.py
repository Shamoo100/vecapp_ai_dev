#!/usr/bin/env python
"""
Migration script to move data from a single schema database to tenant-specific schemas.

This script should be run after updating the codebase to use the multi-tenant schema approach.
It will identify all tenants in the database and migrate their data to tenant-specific schemas.

Usage:
    python -m app.database.migrate_to_tenant_schemas
"""

import asyncio
import argparse
import logging
from typing import List
from app.config.settings import settings
from app.database.schema_migration import SchemaMigration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('schema_migration')

# Default tables to migrate
DEFAULT_TABLES = [
    'church_branch',
    'person',
    'notes',
    'visitors',
    'family_members',
    'reports',
    'ai_decision_audit',
    'ai_suppression_log',
    'ai_feedback_analysis',
    'ai_decision_audit'
]

async def run_migration(tables: List[str], dry_run: bool = False):
    """Run the migration process for all tenants.
    
    Args:
        tables: List of tables to migrate
        dry_run: If True, only show what would be migrated without making changes
    """
    migrator = SchemaMigration(settings.DATABASE_URL)
    
    # Get all tenant IDs
    logger.info("Identifying tenants in the database...")
    tenant_ids = await migrator.list_tenants()
    
    if not tenant_ids:
        logger.error("No tenants found in the database. Migration aborted.")
        return
    
    logger.info(f"Found {len(tenant_ids)} tenants: {', '.join(tenant_ids)}")
    
    if dry_run:
        logger.info("DRY RUN MODE: No data will be migrated")
        for tenant_id in tenant_ids:
            logger.info(f"Would migrate data for tenant: {tenant_id}")
            for table in tables:
                logger.info(f"  - Table: {table}")
        return
    
    # Migrate data for each tenant
    total_results = {}
    for tenant_id in tenant_ids:
        logger.info(f"Migrating data for tenant: {tenant_id}")
        results = await migrator.migrate_tenant_data(tenant_id, tables)
        total_results[tenant_id] = results
        
        # Log results for this tenant
        for table, count in results.items():
            logger.info(f"  - Migrated {count} rows from table '{table}'")
    
    # Log summary
    logger.info("Migration complete!")
    logger.info("Summary:")
    for tenant_id, results in total_results.items():
        total_rows = sum(results.values())
        logger.info(f"  - Tenant {tenant_id}: {total_rows} total rows migrated")

def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description='Migrate data to tenant-specific schemas')
    parser.add_argument(
        '--tables', 
        nargs='+', 
        default=DEFAULT_TABLES,
        help='List of tables to migrate (default: all known tables)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Show what would be migrated without making changes'
    )
    
    args = parser.parse_args()
    
    # Run the migration
    asyncio.run(run_migration(args.tables, args.dry_run))

if __name__ == '__main__':
    main()