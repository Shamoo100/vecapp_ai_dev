#!/usr/bin/env python3
"""
Script to check current database tables and drop everything for a fresh start.
"""

import os
from sqlalchemy import create_engine, text

# Set database URL
os.environ['DATABASE_URL'] = 'postgresql://determinastechnologies:postgres@localhost:5432/vecapp_ai'

def check_current_tables():
    """Check what tables currently exist in the database."""
    engine = create_engine(os.environ['DATABASE_URL'])
    
    with engine.connect() as conn:
        # Check all tables in public and demo schemas
        result = conn.execute(text("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname IN ('public', 'demo') 
            ORDER BY schemaname, tablename
        """))
        
        tables = result.fetchall()
        print('Current tables:')
        for schema, table in tables:
            print(f'  {schema}.{table}')
        
        # Check alembic version tables
        result = conn.execute(text("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename = 'alembic_version'
            ORDER BY schemaname
        """))
        
        alembic_tables = result.fetchall()
        print('\nAlembic version tables:')
        for schema, table in alembic_tables:
            print(f'  {schema}.{table}')
            
            # Check version in each alembic table
            version_result = conn.execute(text(f"SELECT version_num FROM {schema}.alembic_version"))
            versions = version_result.fetchall()
            for version, in versions:
                print(f'    Current version: {version}')

def drop_all_tables():
    """Drop all tables and schemas to start fresh."""
    engine = create_engine(os.environ['DATABASE_URL'])
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # Drop demo schema if it exists (CASCADE will drop all tables)
            conn.execute(text("DROP SCHEMA IF EXISTS demo CASCADE"))
            print("Dropped demo schema and all its tables")
            
            # Get all tables in public schema and drop them
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            
            tables = result.fetchall()
            for table, in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS public.{table} CASCADE"))
                print(f"Dropped public.{table}")
            
            # Also drop any remaining schemas that might have tenant data
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'demo_%' OR schema_name = 'demo'
            """))
            
            schemas = result.fetchall()
            for schema, in schemas:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
                print(f"Dropped schema {schema}")
            
            # Commit the transaction
            trans.commit()
            print("\nAll tables dropped successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"Error dropping tables: {e}")
            raise

if __name__ == "__main__":
    print("=== Current Database State ===")
    check_current_tables()
    
    print("\n=== Dropping All Tables ===")
    drop_all_tables()
    
    print("\n=== Database State After Drop ===")
    check_current_tables()