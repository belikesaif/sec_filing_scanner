# app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry

# Create the registry and declarative base
mapper_registry = registry()
Base = mapper_registry.generate_base()

# Import models explicitly to avoid circular imports
from app.models.filing import Filing
from app.models.metric import Metric

__all__ = ['Base', 'Filing', 'Metric']