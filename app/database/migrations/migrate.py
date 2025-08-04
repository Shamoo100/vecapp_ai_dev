#!/usr/bin/env python3
"""
Migration management script for VecApp AI.

This script handles both public schema migrations (tenant registry)
and tenant-specific schema migrations with auto-generation support.

Usage:
    # Initialize public schema (run once during setup)
    python app/database/migrations/migrate.py init-public
    
    # Run public schema migrations
    python app/database/migrations/migrate.py upgrade-public
    
    # Generate new public migration (auto-detects changes)
    python app/database/migrations/migrate.py generate-public --message "add new tenant fields"
    
    # Initialize tenant schema
    python app/database/migrations/migrate.py init-tenant --schema demo
    
    # Run tenant schema migrations
    python app/database/migrations/migrate.py upgrade-tenant --schema demo
    
    # Generate new tenant migration (schema-agnostic, auto-detects changes)
    python app/database/migrations/migrate.py generate-tenant --message "add user auth fields"
    
    # Check migration status
    python app/database/migrations/migrate.py status --schema demo
    python app/database/migrations/migrate.py status-public
    
    # Check for pending model changes
    python app/database/migrations/migrate.py check-changes --schema demo
    python app/database/migrations/migrate.py check-changes-public
"""

import os
import sys
import argparse
import subprocess
import logging
import time
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProgressIndicator:
    """Simple progress indicator for long-running operations."""
    
    def __init__(self, message: str):
        self.message = message
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the progress indicator."""
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the progress indicator."""
        self.running = False
        if self.thread:
            self.thread.join()
        print()  # New line after animation
        
    def _animate(self):
        """Animate the progress indicator."""
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while self.running:
            print(f"\r{chars[i % len(chars)]} {self.message}", end="", flush=True)
            time.sleep(0.1)
            i += 1

class MigrationManager:
    """Enhanced migration manager with auto-generation capabilities."""
    
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        self.public_dir = self.migrations_dir / "public"
        self.tenant_dir = self.migrations_dir / "tenant"
        
    def run_alembic_command(self, config_path: Path, command: list, env_vars: dict = None, show_progress: bool = True):
        """Run an alembic command with the specified config and progress indicator."""
        cmd = ["alembic", "-c", str(config_path)] + command
        
        # Set up environment variables
        env = os.environ.copy()
        
        # Add project root to PYTHONPATH to ensure proper imports
        project_root = Path(__file__).parent.parent.parent.parent
        current_pythonpath = env.get('PYTHONPATH', '')
        if current_pythonpath:
            env['PYTHONPATH'] = f"{project_root}:{current_pythonpath}"
        else:
            env['PYTHONPATH'] = str(project_root)
        
        if env_vars:
            env.update(env_vars)
            
        logger.info(f"Running: {' '.join(cmd)}")
        if env_vars:
            logger.info(f"Environment: {env_vars}")
            
        # Always run from the directory containing the alembic.ini file
        working_dir = config_path.parent
        logger.info(f"Working directory: {working_dir}")
        
        # Determine operation type for progress message
        operation = "migration"
        if "revision" in command or "autogenerate" in command:
            operation = "generating migration"
        elif "upgrade" in command:
            operation = "applying migrations"
        elif "current" in command or "history" in command:
            operation = "checking status"
            show_progress = False  # Don't show progress for quick status checks
        
        # Start progress indicator for long operations
        progress = None
        if show_progress:
            progress = ProgressIndicator(f"🔄 {operation.title()}...")
            progress.start()
        
        try:
            # Use Popen for real-time output
            process = subprocess.Popen(
                cmd, 
                cwd=working_dir, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Print output in real-time
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if progress:
                        progress.stop()
                        progress = None
                    print(output.strip())
                    output_lines.append(output.strip())
            
            # Wait for process to complete
            return_code = process.poll()
            
            if return_code != 0:
                logger.error(f"❌ Command failed with exit code {return_code}")
                sys.exit(1)
            else:
                if "revision" in command or "autogenerate" in command:
                    logger.info("✅ Migration generation completed!")
                elif "upgrade" in command:
                    logger.info("✅ Migration execution completed!")
                    
        finally:
            if progress:
                progress.stop()
        
        return subprocess.CompletedProcess(cmd, return_code, '\n'.join(output_lines), '')
    
    def init_public(self):
        """Initialize public schema migrations."""
        logger.info("🚀 Initializing public schema migrations...")
        config_path = self.public_dir / "alembic.ini"
        self.run_alembic_command(config_path, ["upgrade", "head"])
        logger.info("🎉 Public schema initialized successfully!")
    
    def upgrade_public(self):
        """Run public schema migrations."""
        logger.info("🚀 Running public schema migrations...")
        config_path = self.public_dir / "alembic.ini"
        self.run_alembic_command(config_path, ["upgrade", "head"])
        logger.info("🎉 Public schema migrations completed!")
    
    def status_public(self):
        """Check public schema migration status."""
        logger.info("📊 Checking public schema migration status...")
        config_path = self.public_dir / "alembic.ini"
        self.run_alembic_command(config_path, ["current"], show_progress=False)
        self.run_alembic_command(config_path, ["history"], show_progress=False)
    
    def init_tenant(self, schema_name: str):
        """Initialize tenant schema migrations."""
        logger.info(f"🚀 Initializing tenant schema migrations for: {schema_name}")
        config_path = self.tenant_dir / "alembic.ini"
        env_vars = {"TENANT_SCHEMA": schema_name}
        self.run_alembic_command(config_path, ["upgrade", "head"], env_vars)
        logger.info(f"🎉 Tenant schema '{schema_name}' initialized successfully!")
    
    def upgrade_tenant(self, schema_name: str):
        """Run tenant schema migrations."""
        logger.info(f"🚀 Running tenant schema migrations for: {schema_name}")
        config_path = self.tenant_dir / "alembic.ini"
        env_vars = {"TENANT_SCHEMA": schema_name}
        self.run_alembic_command(config_path, ["upgrade", "head"], env_vars)
        logger.info(f"🎉 Tenant schema '{schema_name}' migrations completed!")
    
    def status_tenant(self, schema_name: str):
        """Check tenant schema migration status."""
        logger.info(f"📊 Checking tenant schema migration status for: {schema_name}")
        config_path = self.tenant_dir / "alembic.ini"
        env_vars = {"TENANT_SCHEMA": schema_name}
        self.run_alembic_command(config_path, ["current"], env_vars, show_progress=False)
        self.run_alembic_command(config_path, ["history"], env_vars, show_progress=False)
    
    # New auto-generation methods
    def generate_public_migration(self, message: str, auto_detect: bool = True):
        """Generate a new public schema migration with auto-detection."""
        try:
            logger.info(f"🔧 Generating public migration: {message}")
            config_path = self.public_dir / "alembic.ini"
            
            if auto_detect:
                # Auto-detect changes from models
                cmd = ["revision", "--autogenerate", "-m", message]
            else:
                # Create empty migration
                cmd = ["revision", "-m", message]
            
            self.run_alembic_command(config_path, cmd)
            logger.info("✅ Public migration generated successfully!")
            logger.info("📝 Please review the generated migration file before applying it.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to generate public migration: {e}")
            return False
    
    def generate_tenant_migration(self, message: str, auto_detect: bool = True, reference_schema: str = "demo"):
        """Generate a new tenant schema migration with auto-detection (schema-agnostic).
        
        Args:
            message: Migration message
            auto_detect: Whether to auto-detect changes
            reference_schema: Schema to use as reference for generation (default: demo)
        """
        try:
            logger.info(f"🔧 Generating schema-agnostic tenant migration: {message}")
            logger.info(f"📋 Using '{reference_schema}' as reference schema for generation")
            config_path = self.tenant_dir / "alembic.ini"
            env_vars = {"TENANT_SCHEMA": reference_schema}
            
            if auto_detect:
                # Auto-detect changes from models
                cmd = ["revision", "--autogenerate", "-m", message]
            else:
                # Create empty migration
                cmd = ["revision", "-m", message]
            
            self.run_alembic_command(config_path, cmd, env_vars)
            logger.info("✅ Schema-agnostic tenant migration generated successfully!")
            logger.info("📝 Please review the generated migration file before applying it.")
            logger.info("🔄 This migration can be applied to any tenant schema.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to generate tenant migration: {e}")
            return False
    
    def check_public_changes(self):
        """Check if there are pending model changes in public schema."""
        try:
            logger.info("Checking for pending public schema changes...")
            config_path = self.public_dir / "alembic.ini"
            
            # Use alembic check command to detect changes
            result = subprocess.run(
                ["alembic", "-c", str(config_path), "check"],
                cwd=config_path.parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ No pending changes detected in public schema")
                return False
            else:
                logger.info("📋 Pending changes detected in public schema:")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return True
                
        except Exception as e:
            logger.warning(f"Could not check for public schema changes: {e}")
            return False
    
    def check_tenant_changes(self, schema_name: str):
        """Check if there are pending model changes in tenant schema."""
        try:
            logger.info(f"Checking for pending tenant schema changes in {schema_name}...")
            config_path = self.tenant_dir / "alembic.ini"
            env_vars = {"TENANT_SCHEMA": schema_name}
            
            # Set up environment
            env = os.environ.copy()
            env.update(env_vars)
            
            # Use alembic check command to detect changes
            result = subprocess.run(
                ["alembic", "-c", str(config_path), "check"],
                cwd=config_path.parent,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"✅ No pending changes detected in tenant schema {schema_name}")
                return False
            else:
                logger.info(f"📋 Pending changes detected in tenant schema {schema_name}:")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return True
                
        except Exception as e:
            logger.warning(f"Could not check for tenant schema changes: {e}")
            return False
    
    def auto_generate_if_needed(self, schema_name: str = None):
        """Auto-generate migrations if model changes are detected."""
        if schema_name:
            # Check tenant schema
            if self.check_tenant_changes(schema_name):
                response = input(f"Pending changes detected in tenant schema {schema_name}. Generate migration? (y/n): ")
                if response.lower() == 'y':
                    message = input("Enter migration message: ") or f"auto-generated changes for tenant schemas"
                    self.generate_tenant_migration(message, reference_schema=schema_name)
        else:
            # Check public schema
            if self.check_public_changes():
                response = input("Pending changes detected in public schema. Generate migration? (y/n): ")
                if response.lower() == 'y':
                    message = input("Enter migration message: ") or "auto-generated public schema changes"
                    self.generate_public_migration(message)

def main():
    parser = argparse.ArgumentParser(description="VecApp AI Migration Manager with Auto-Generation")
    parser.add_argument("command", choices=[
        "init-public", "upgrade-public", "status-public", "generate-public", "check-changes-public",
        "init-tenant", "upgrade-tenant", "status", "generate-tenant", "check-changes", "auto-check"
    ], help="Migration command to run")
    parser.add_argument("--schema", help="Tenant schema name (required for tenant commands except generate-tenant)")
    parser.add_argument("--message", "-m", help="Migration message")
    parser.add_argument("--manual", action="store_true", help="Create empty migration (no auto-detection)")
    parser.add_argument("--reference-schema", default="demo", help="Reference schema for tenant migration generation (default: demo)")
    
    args = parser.parse_args()
    manager = MigrationManager()
    
    # Public schema commands
    if args.command == "init-public":
        manager.init_public()
    elif args.command == "upgrade-public":
        manager.upgrade_public()
    elif args.command == "status-public":
        manager.status_public()
    elif args.command == "generate-public":
        message = args.message or input("Enter migration message: ")
        manager.generate_public_migration(message, not args.manual)
    elif args.command == "check-changes-public":
        manager.check_public_changes()
    
    # Tenant schema commands
    elif args.command in ["init-tenant", "upgrade-tenant", "status", "check-changes"]:
        if not args.schema:
            print("Error: --schema is required for this tenant command", file=sys.stderr)
            sys.exit(1)
        
        if args.command == "init-tenant":
            manager.init_tenant(args.schema)
        elif args.command == "upgrade-tenant":
            manager.upgrade_tenant(args.schema)
        elif args.command == "status":
            manager.status_tenant(args.schema)
        elif args.command == "check-changes":
            manager.check_tenant_changes(args.schema)
    
    # Schema-agnostic tenant migration generation
    elif args.command == "generate-tenant":
        message = args.message or input("Enter migration message: ")
        manager.generate_tenant_migration(message, not args.manual, args.reference_schema)
    
    # Auto-check command
    elif args.command == "auto-check":
        if args.schema:
            manager.auto_generate_if_needed(args.schema)
        else:
            manager.auto_generate_if_needed()

if __name__ == "__main__":
    main()