"""
Database models for OntServe Web Application

Uses SQLAlchemy with pgvector extension for semantic search.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid

db = SQLAlchemy()


class Ontology(db.Model):
    """Main ontology model for storing ontology information."""
    
    __tablename__ = 'ontologies'
    
    id = db.Column(db.Integer, primary_key=True)
    ontology_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)  # TTL content
    format = db.Column(db.String(50), default='turtle')
    
    # Metadata
    source_url = db.Column(db.String(500))
    source_file = db.Column(db.String(500))
    triple_count = db.Column(db.Integer)
    class_count = db.Column(db.Integer)
    property_count = db.Column(db.Integer)
    
    # JSON metadata field for flexible storage
    meta_data = db.Column(db.JSON, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = db.relationship('OntologyVersion', back_populates='ontology', 
                              cascade='all, delete-orphan')
    entities = db.relationship('OntologyEntity', back_populates='ontology',
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Ontology {self.ontology_id}: {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ontology to dictionary representation."""
        return {
            'id': self.id,
            'ontology_id': self.ontology_id,
            'name': self.name,
            'description': self.description,
            'format': self.format,
            'source_url': self.source_url,
            'source_file': self.source_file,
            'triple_count': self.triple_count,
            'class_count': self.class_count,
            'property_count': self.property_count,
            'meta_data': self.meta_data if self.meta_data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'version_count': len(self.versions)
        }


class OntologyVersion(db.Model):
    """Version tracking for ontologies."""
    
    __tablename__ = 'ontology_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    ontology_id = db.Column(db.Integer, db.ForeignKey('ontologies.id'), nullable=False)
    version = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    commit_message = db.Column(db.Text)
    
    # Version metadata
    triple_count = db.Column(db.Integer)
    changes_summary = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(255))  # Username if auth is added
    
    # Relationships
    ontology = db.relationship('Ontology', back_populates='versions')
    
    # Unique constraint on ontology_id + version
    __table_args__ = (
        db.UniqueConstraint('ontology_id', 'version', name='uq_ontology_version'),
    )
    
    def __repr__(self):
        return f'<OntologyVersion {self.version} for Ontology {self.ontology_id}>'


class OntologyEntity(db.Model):
    """
    Extracted entities from ontologies with embeddings for semantic search.
    
    Stores classes, properties, and individuals with their vector embeddings.
    """
    
    __tablename__ = 'ontology_entities'
    
    id = db.Column(db.Integer, primary_key=True)
    ontology_id = db.Column(db.Integer, db.ForeignKey('ontologies.id'), nullable=False)
    
    # Entity information
    entity_type = db.Column(db.String(50), nullable=False)  # class, property, individual
    uri = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(255))
    comment = db.Column(db.Text)
    
    # Hierarchical information
    parent_uri = db.Column(db.Text)  # For subclass/subproperty relationships
    
    # Additional metadata
    domain = db.Column(db.JSON)  # For properties
    range = db.Column(db.JSON)   # For properties
    properties = db.Column(db.JSON)  # For individuals
    
    # Vector embedding for semantic search (384 dimensions for all-MiniLM-L6-v2)
    embedding = db.Column(Vector(384))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ontology = db.relationship('Ontology', back_populates='entities')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_entity_type', 'entity_type'),
        Index('idx_entity_label', 'label'),
        Index('idx_ontology_entity', 'ontology_id', 'entity_type'),
        # Vector similarity index will be created separately
    )
    
    def __repr__(self):
        return f'<OntologyEntity {self.entity_type}: {self.label or self.uri}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        return {
            'id': self.id,
            'ontology_id': self.ontology_id,
            'entity_type': self.entity_type,
            'uri': self.uri,
            'label': self.label,
            'comment': self.comment,
            'parent_uri': self.parent_uri,
            'domain': self.domain,
            'range': self.range,
            'properties': self.properties
        }
    
    @classmethod
    def search_similar(cls, query_embedding: List[float], 
                      limit: int = 10, 
                      entity_type: Optional[str] = None,
                      ontology_id: Optional[int] = None) -> List['OntologyEntity']:
        """
        Search for similar entities using vector similarity.
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            entity_type: Filter by entity type
            ontology_id: Filter by ontology
            
        Returns:
            List of similar entities ordered by similarity
        """
        query = cls.query
        
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        if ontology_id:
            query = query.filter_by(ontology_id=ontology_id)
        
        # Use pgvector's <-> operator for cosine distance
        results = query.order_by(
            cls.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()
        
        return results


class SearchHistory(db.Model):
    """Track search queries for analytics and improvement."""
    
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50))  # text, sparql, semantic
    results_count = db.Column(db.Integer)
    execution_time = db.Column(db.Float)  # in seconds
    
    # User tracking (if auth is added)
    user_id = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SearchHistory {self.query_type}: {self.query[:50]}...>'


def init_db(app):
    """
    Initialize the database with the Flask app.
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create vector similarity index if it doesn't exist
        try:
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_entity_embedding_vector 
                ON ontology_entities 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """))
            db.session.commit()
        except Exception as e:
            app.logger.warning(f"Could not create vector index: {e}")
            db.session.rollback()
