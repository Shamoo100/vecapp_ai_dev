from sqlalchemy import Column, DateTime, func, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import get_settings
from app.database.repositories.connection import get_db_dependency

settings = get_settings()


# Create engine using DATABASE_URL from settings
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create a base class for declarative models
Base = declarative_base()

# Schema configuration - can be set via environment variable or parameter
DEFAULT_SCHEMA = settings.DB_SCHEMA or 'public'

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
        if schema:
            return {'schema': schema}
        return {}
    
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
            return (schema_dict,) if schema_dict else ()

# Use centralized dependency function
get_db = get_db_dependency

