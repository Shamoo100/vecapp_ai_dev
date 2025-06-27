from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Any

Base = declarative_base()

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Create a base class for declarative models
Base = declarative_base()

# Create engine (you might want to move this to a config file)
engine = create_engine("postgresql://user:password@localhost/vecap_db")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

