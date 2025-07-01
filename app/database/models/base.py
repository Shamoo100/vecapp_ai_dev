from sqlalchemy import Column, DateTime, func, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Any, Optional
import os

# Create a base class for declarative models
Base = declarative_base()

# Schema configuration - can be set via environment variable or parameter
DEFAULT_SCHEMA = os.getenv('DB_SCHEMA', 'public')

class SchemaConfigMixin:
    """Mixin to provide schema configuration for models."""
    
    @classmethod
    def set_schema(cls, schema: str = None) -> dict:
        """Set the schema for the model's table args.
        
        Args:
            schema: The schema name to use. If None, uses DEFAULT_SCHEMA.
            
        Returns:
            dict: Table args dictionary with schema configuration.
        """
        schema_name = schema or DEFAULT_SCHEMA
        return {'schema': schema_name}
    
    @classmethod
    def get_table_args_with_schema(cls, schema: str = None, additional_args: tuple = None) -> tuple:
        """Get table args with schema configuration.
        
        Args:
            schema: The schema name to use. If None, uses DEFAULT_SCHEMA.
            additional_args: Additional table args (constraints, indexes, etc.)
            
        Returns:
            tuple: Complete table args with schema.
        """
        schema_dict = cls.set_schema(schema)
        
        if additional_args:
            return additional_args + (schema_dict,)
        else:
            return (schema_dict,)
    
    @classmethod
    def configure_schema(cls, schema: str = None):
        """Configure the schema for this model class dynamically.
        
        Args:
            schema: The schema name to use. If None, uses DEFAULT_SCHEMA.
        """
        # Get existing table args if any
        existing_args = getattr(cls, '__table_args__', None)
        
        if existing_args is None:
            # No existing args, just set schema
            cls.__table_args__ = cls.set_schema(schema)
        elif isinstance(existing_args, dict):
            # Existing args is a dict, update schema
            existing_args['schema'] = schema or DEFAULT_SCHEMA
        elif isinstance(existing_args, tuple):
            # Existing args is a tuple, need to reconstruct
            # Find the schema dict and update it, or add it
            args_list = list(existing_args)
            schema_dict_found = False
            
            for i, arg in enumerate(args_list):
                if isinstance(arg, dict) and 'schema' in arg:
                    args_list[i]['schema'] = schema or DEFAULT_SCHEMA
                    schema_dict_found = True
                    break
            
            if not schema_dict_found:
                # Add schema dict to the end
                args_list.append(cls.set_schema(schema))
            
            cls.__table_args__ = tuple(args_list)

# Create engine (you might want to move this to a config file)
engine = create_engine("postgresql://user:password@localhost/vecap_db")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    """Get database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

