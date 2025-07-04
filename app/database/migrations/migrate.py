#!/usr/bin/env python3
"""
Migration management script for VecApp AI.

This script handles both public schema migrations (tenant registry)
and tenant-specific schema migrations.

Usage:
    # Initialize public schema (run once during setup)
    python migrate.py init-public
    
    # Run public schema migrations
    python migrate.py upgrade-public
    
    # Initialize tenant schema
    python migrate.py init-tenant --schema demo
    
    # Run tenant schema migrations
    python migrate.py upgrade-tenant --schema demo
    
    # Check migration status
    python migrate.py status --schema demo
    python migrate.py status-public
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class MigrationManager:
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        self.public_dir = self.migrations_dir / "public"
        self.tenant_dir = self.migrations_dir / "tenant"
        
    def run_alembic_command(self, config_path: Path, command: list, env_vars: dict = None):
        """Run an alembic command with the specified config."""
        cmd = ["alembic", "-c", str(config_path)] + command
        
        # Set up environment variables
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
            
        print(f"Running: {' '.join(cmd)}")
        if env_vars:
            print(f"Environment: {env_vars}")
            
        result = subprocess.run(cmd, cwd=self.migrations_dir, env=env, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        if result.returncode != 0:
            print(f"Command failed with exit code {result.returncode}", file=sys.stderr)
            sys.exit(1)
            
        return result
    
    def init_public(self):
        """Initialize public schema migrations."""
        print("Initializing public schema migrations...")
        config_path = self.public_dir / "alembic.ini"
        self.run_alembic_command(config_path, ["upgrade", "head"])
        print("Public schema initialized successfully!")
    
    def upgrade_public(self):
        """Run public schema migrations."""
        print("Running public schema migrations...")
        config_path = self.public_dir / "alembic.ini"
        self.run_alembic_command(config_path, ["upgrade", "head"])
        print("Public schema migrations completed!")
    
    def status_public(self):
        """Check public schema migration status."""
        print("Checking public schema migration status...")
        config_path = self.public_dir / "alembic.ini"
        self.run_alembic_command(config_path, ["current"])
        self.run_alembic_command(config_path, ["history"])
    
    def init_tenant(self, schema_name: str):
        """Initialize tenant schema migrations."""
        print(f"Initializing tenant schema migrations for: {schema_name}")
        config_path = self.tenant_dir / "alembic.ini"
        env_vars = {"TENANT_SCHEMA": schema_name}
        self.run_alembic_command(config_path, ["upgrade", "head"], env_vars)
        print(f"Tenant schema '{schema_name}' initialized successfully!")
    
    def upgrade_tenant(self, schema_name: str):
        """Run tenant schema migrations."""
        print(f"Running tenant schema migrations for: {schema_name}")
        config_path = self.tenant_dir / "alembic.ini"
        env_vars = {"TENANT_SCHEMA": schema_name}
        self.run_alembic_command(config_path, ["upgrade", "head"], env_vars)
        print(f"Tenant schema '{schema_name}' migrations completed!")
    
    def status_tenant(self, schema_name: str):
        """Check tenant schema migration status."""
        print(f"Checking tenant schema migration status for: {schema_name}")
        config_path = self.tenant_dir / "alembic.ini"
        env_vars = {"TENANT_SCHEMA": schema_name}
        self.run_alembic_command(config_path, ["current"], env_vars)
        self.run_alembic_command(config_path, ["history"], env_vars)

def main():
    parser = argparse.ArgumentParser(description="VecApp AI Migration Manager")
    parser.add_argument("command", choices=[
        "init-public", "upgrade-public", "status-public",
        "init-tenant", "upgrade-tenant", "status"
    ], help="Migration command to run")
    parser.add_argument("--schema", help="Tenant schema name (required for tenant commands)")
    
    args = parser.parse_args()
    manager = MigrationManager()
    
    if args.command == "init-public":
        manager.init_public()
    elif args.command == "upgrade-public":
        manager.upgrade_public()
    elif args.command == "status-public":
        manager.status_public()
    elif args.command in ["init-tenant", "upgrade-tenant", "status"]:
        if not args.schema:
            print("Error: --schema is required for tenant commands", file=sys.stderr)
            sys.exit(1)
        
        if args.command == "init-tenant":
            manager.init_tenant(args.schema)
        elif args.command == "upgrade-tenant":
            manager.upgrade_tenant(args.schema)
        elif args.command == "status":
            manager.status_tenant(args.schema)

if __name__ == "__main__":
    main()