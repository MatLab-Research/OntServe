"""
OntServe Ontology Editor Module

Provides ontology editing, visualization, and management capabilities
adapted from the proethica ontology editor but using OntServe's 
hybrid file+database storage and pgvector semantic search.
"""

from .routes import create_editor_blueprint
from .services import OntologyEntityService, OntologyValidationService
from .utils import EntityTypeMapper, HierarchyBuilder

__version__ = "1.0.0"
__all__ = [
    'create_editor_blueprint',
    'OntologyEntityService', 
    'OntologyValidationService',
    'EntityTypeMapper',
    'HierarchyBuilder'
]
