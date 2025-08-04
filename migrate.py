#!/usr/bin/env python3
"""
Simple migration wrapper for VecApp AI.
This script provides a consistent interface for all migrations.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Forward all arguments to the main migration script."""
    script_path = Path(__file__).parent / "app" / "database" / "migrations" / "migrate.py"
    
    # Forward all arguments to the main migration script
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]
    
    # Run the command
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()