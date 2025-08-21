"""
PROV-O (W3C Provenance Ontology) importer.

Specialized importer for handling PROV-O ontologies with support for
experiment classification and provenance tracking.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests

try:
    import rdflib
    from rdflib import Graph, Namespace, RDF, RDFS, OWL
    from rdflib.namespace import PROV, FOAF, DCTERMS, XSD
except ImportError:
    raise ImportError("rdflib is required for PROV-O import. Install with: pip install rdflib")

from importers.base import BaseImporter, ImportError


# PROV-O specific namespaces
PROV_NAMESPACES = {
    'prov': PROV,
    'provo': Namespace("http://www.w3.org/ns/prov#"),
    'prov-o': Namespace("http://www.w3.org/ns/prov-o#"),
    'prov-aq': Namespace("http://www.w3.org/ns/prov-aq#"),
    'prov-dc': Namespace("http://www.w3.org/ns/prov-dc#"),
    'prov-dictionary': Namespace("http://www.w3.org/ns/prov-dictionary#"),
    'prov-links': Namespace("http://www.w3.org/ns/prov-links#"),
}

# Standard namespaces
STANDARD_NAMESPACES = {
    'prov': PROV,
    'foaf': FOAF,
    'dcterms': DCTERMS,
    'xsd': XSD,
    'owl': OWL,
    'rdf': RDF,
    'rdfs': RDFS,
    'skos': Namespace("http://www.w3.org/2004/02/skos/core#"),
    'dcat': Namespace("http://www.w3.org/ns/dcat#"),
    'void': Namespace("http://rdfs.org/ns/void#"),
}


class PROVImporter(BaseImporter):
    """
    Specialized importer for PROV-O ontologies.
    
    Provides enhanced support for:
    - PROV-O core concepts (Activity, Entity, Agent)
    - Provenance relationships
    - Experiment classification
    - Temporal tracking
    """
    
    def _initialize(self):
        """Initialize the PROV-O importer."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize namespace manager
        from rdflib.namespace import NamespaceManager
        self.namespace_manager = NamespaceManager(Graph())
        
        # Bind standard namespaces
        for prefix, ns in STANDARD_NAMESPACES.items():
            self.namespace_manager.bind(prefix, ns)
        
        # Bind PROV-specific namespaces
        for prefix, ns in PROV_NAMESPACES.items():
            self.namespace_manager.bind(prefix, ns)
        
        # Set up cache directory
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def import_prov_o(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Import the standard W3C PROV-O ontology.
        
        Args:
            force_refresh: Force re-download even if cached
            
        Returns:
            Dictionary containing import results
        """
        prov_o_ttl_url = "https://www.w3.org/ns/prov.ttl"
        
        self.logger.info("Importing PROV-O ontology...")
        
        result = self.import_from_url(
            prov_o_ttl_url,
            ontology_id="prov-o",
            name="W3C Provenance Ontology (PROV-O)",
            description="The PROV Ontology provides classes, properties, and restrictions for representing provenance information",
            format='turtle',
            force_refresh=force_refresh
        )
        
        # Extract PROV-O specific concepts for experiment classification
        if result.get('success'):
            result['experiment_concepts'] = self._extract_prov_experiment_concepts(result['graph'])
            self.logger.info(f"Extracted {len(result['experiment_concepts'])} PROV-O concepts for experiments")
        
        return result
    
    def import_from_url(self, url: str, ontology_id: Optional[str] = None,
                       name: Optional[str] = None, description: Optional[str] = None,
                       format: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Import an ontology from a URL.
        
        Args:
            url: URL of the ontology to import
            ontology_id: Optional unique identifier for the ontology
            name: Optional human-readable name
            description: Optional description
            format: Optional RDF format (turtle, xml, n3, etc.)
            force_refresh: Force re-download even if cached
            
        Returns:
            Dictionary containing import results
        """
        # Generate ontology ID if not provided
        if not ontology_id:
            ontology_id = self.generate_ontology_id(url)
        
        # Check cache first if not forcing refresh
        if not force_refresh and self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{ontology_id}.ttl")
            metadata_file = os.path.join(self.cache_dir, f"{ontology_id}.json")
            
            if os.path.exists(cache_file) and os.path.exists(metadata_file):
                self.logger.info(f"Loading ontology {ontology_id} from cache")
                return self._load_from_cache(ontology_id)
        
        try:
            # Download ontology
            self.logger.info(f"Downloading ontology from {url}")
            response = requests.get(url, headers={'Accept': 'text/turtle, application/rdf+xml'})
            response.raise_for_status()
            
            # Parse ontology
            g = Graph()
            
            # Auto-detect format if not specified
            if not format:
                format = self.detect_format(response.text, url)
            
            g.parse(data=response.text, format=format)
            self.logger.info(f"Successfully parsed ontology with {len(g)} triples")
            
            # Extract metadata
            metadata = self._extract_metadata(g, url, name, description)
            metadata['ontology_id'] = ontology_id
            metadata['source_url'] = url
            metadata['import_date'] = datetime.now().isoformat()
            metadata['format'] = format
            metadata['triple_count'] = len(g)
            
            # Save to cache if cache directory is set
            if self.cache_dir:
                cache_file = os.path.join(self.cache_dir, f"{ontology_id}.ttl")
                metadata_file = os.path.join(self.cache_dir, f"{ontology_id}.json")
                
                g.serialize(destination=cache_file, format='turtle')
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Store in memory
            self.imported_ontologies[ontology_id] = {
                'graph': g,
                'metadata': metadata,
                'content': g.serialize(format='turtle')
            }
            
            # Optionally save to storage backend
            if self.storage_backend:
                self.storage_backend.store(
                    ontology_id, 
                    g.serialize(format='turtle'),
                    metadata
                )
            
            return {
                'success': True,
                'ontology_id': ontology_id,
                'metadata': metadata,
                'graph': g,
                'message': f"Successfully imported ontology {ontology_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Error importing ontology from {url}: {e}")
            raise ImportError(f"Failed to import ontology from {url}: {str(e)}")
    
    def import_from_file(self, file_path: str, ontology_id: Optional[str] = None,
                        name: Optional[str] = None, description: Optional[str] = None,
                        format: str = 'turtle') -> Dict[str, Any]:
        """
        Import an ontology from a local file.
        
        Args:
            file_path: Path to the ontology file
            ontology_id: Optional unique identifier for the ontology
            name: Optional human-readable name
            description: Optional description
            format: RDF format (turtle, xml, n3, etc.)
            
        Returns:
            Dictionary containing import results
        """
        # Generate ontology ID if not provided
        if not ontology_id:
            ontology_id = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            # Parse ontology
            g = Graph()
            g.parse(file_path, format=format)
            self.logger.info(f"Successfully parsed ontology from {file_path} with {len(g)} triples")
            
            # Extract metadata
            metadata = self._extract_metadata(g, file_path, name, description)
            metadata['ontology_id'] = ontology_id
            metadata['source_file'] = file_path
            metadata['import_date'] = datetime.now().isoformat()
            metadata['format'] = format
            metadata['triple_count'] = len(g)
            
            # Save to cache if cache directory is set
            if self.cache_dir:
                cache_file = os.path.join(self.cache_dir, f"{ontology_id}.ttl")
                metadata_file = os.path.join(self.cache_dir, f"{ontology_id}.json")
                
                g.serialize(destination=cache_file, format='turtle')
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Store in memory
            self.imported_ontologies[ontology_id] = {
                'graph': g,
                'metadata': metadata,
                'content': g.serialize(format='turtle')
            }
            
            # Optionally save to storage backend
            if self.storage_backend:
                self.storage_backend.store(
                    ontology_id,
                    g.serialize(format='turtle'),
                    metadata
                )
            
            return {
                'success': True,
                'ontology_id': ontology_id,
                'metadata': metadata,
                'graph': g,
                'message': f"Successfully imported ontology {ontology_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Error importing ontology from {file_path}: {e}")
            raise ImportError(f"Failed to import ontology from {file_path}: {str(e)}")
    
    def extract_classes(self, ontology_id: str) -> List[Dict[str, Any]]:
        """
        Extract all classes from an imported ontology.
        
        Args:
            ontology_id: ID of the ontology
            
        Returns:
            List of class definitions
        """
        ont_data = self.get_imported_ontology(ontology_id)
        if not ont_data:
            return []
        
        g = ont_data['graph']
        classes = []
        
        for s in g.subjects(RDF.type, OWL.Class):
            class_info = {
                'uri': str(s),
                'label': self._get_label(g, s),
                'comment': self._get_comment(g, s),
                'subclass_of': [str(o) for o in g.objects(s, RDFS.subClassOf)]
            }
            classes.append(class_info)
        
        return classes
    
    def extract_properties(self, ontology_id: str) -> List[Dict[str, Any]]:
        """
        Extract all properties from an imported ontology.
        
        Args:
            ontology_id: ID of the ontology
            
        Returns:
            List of property definitions
        """
        ont_data = self.get_imported_ontology(ontology_id)
        if not ont_data:
            return []
        
        g = ont_data['graph']
        properties = []
        
        # Object properties
        for s in g.subjects(RDF.type, OWL.ObjectProperty):
            prop_info = {
                'uri': str(s),
                'type': 'object_property',
                'label': self._get_label(g, s),
                'comment': self._get_comment(g, s),
                'domain': [str(o) for o in g.objects(s, RDFS.domain)],
                'range': [str(o) for o in g.objects(s, RDFS.range)]
            }
            properties.append(prop_info)
        
        # Datatype properties
        for s in g.subjects(RDF.type, OWL.DatatypeProperty):
            prop_info = {
                'uri': str(s),
                'type': 'datatype_property',
                'label': self._get_label(g, s),
                'comment': self._get_comment(g, s),
                'domain': [str(o) for o in g.objects(s, RDFS.domain)],
                'range': [str(o) for o in g.objects(s, RDFS.range)]
            }
            properties.append(prop_info)
        
        return properties
    
    def extract_individuals(self, ontology_id: str) -> List[Dict[str, Any]]:
        """
        Extract all individuals from an imported ontology.
        
        Args:
            ontology_id: ID of the ontology
            
        Returns:
            List of individual definitions
        """
        ont_data = self.get_imported_ontology(ontology_id)
        if not ont_data:
            return []
        
        g = ont_data['graph']
        individuals = []
        
        # Find all subjects that are instances of classes
        for s, p, o in g.triples((None, RDF.type, None)):
            # Skip if object is a meta-class like owl:Class
            if o in [OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, 
                    RDFS.Class, RDF.Property]:
                continue
            
            individual_info = {
                'uri': str(s),
                'type': str(o),
                'label': self._get_label(g, s),
                'comment': self._get_comment(g, s),
                'properties': {}
            }
            
            # Get all properties of this individual
            for pred, obj in g.predicate_objects(s):
                if pred not in [RDF.type, RDFS.label, RDFS.comment]:
                    individual_info['properties'][str(pred)] = str(obj)
            
            individuals.append(individual_info)
        
        return individuals
    
    def _extract_prov_experiment_concepts(self, graph: Graph) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract PROV-O concepts relevant for experiment classification.
        
        Args:
            graph: RDF graph containing PROV-O ontology
            
        Returns:
            Dictionary of concept categories with their terms
        """
        concepts = {
            'activities': [],
            'entities': [],
            'agents': [],
            'relations': [],
            'qualified_relations': []
        }
        
        # Extract Activity subclasses (for experiment steps/processes)
        for s in graph.subjects(RDFS.subClassOf, PROV.Activity):
            concepts['activities'].append({
                'uri': str(s),
                'label': self._get_label(graph, s),
                'comment': self._get_comment(graph, s),
                'type': 'activity'
            })
        
        # Extract Entity subclasses (for experiment artifacts/data)
        for s in graph.subjects(RDFS.subClassOf, PROV.Entity):
            concepts['entities'].append({
                'uri': str(s),
                'label': self._get_label(graph, s),
                'comment': self._get_comment(graph, s),
                'type': 'entity'
            })
        
        # Extract Agent subclasses (for experiment participants)
        for s in graph.subjects(RDFS.subClassOf, PROV.Agent):
            concepts['agents'].append({
                'uri': str(s),
                'label': self._get_label(graph, s),
                'comment': self._get_comment(graph, s),
                'type': 'agent'
            })
        
        # Extract core PROV properties for relationships
        prov_properties = [
            (PROV.wasGeneratedBy, 'generation'),
            (PROV.used, 'usage'),
            (PROV.wasInformedBy, 'communication'),
            (PROV.wasStartedBy, 'start'),
            (PROV.wasEndedBy, 'end'),
            (PROV.wasInvalidatedBy, 'invalidation'),
            (PROV.wasDerivedFrom, 'derivation'),
            (PROV.wasAttributedTo, 'attribution'),
            (PROV.wasAssociatedWith, 'association'),
            (PROV.actedOnBehalfOf, 'delegation'),
            (PROV.wasInfluencedBy, 'influence')
        ]
        
        for prop_uri, prop_type in prov_properties:
            prop_info = {
                'uri': str(prop_uri),
                'label': self._get_label(graph, prop_uri) or prop_uri.split('#')[-1],
                'comment': self._get_comment(graph, prop_uri),
                'type': prop_type
            }
            concepts['relations'].append(prop_info)
        
        # Add core PROV classes
        core_classes = [
            (PROV.Activity, 'activities'),
            (PROV.Entity, 'entities'),
            (PROV.Agent, 'agents')
        ]
        
        for class_uri, category in core_classes:
            class_info = {
                'uri': str(class_uri),
                'label': self._get_label(graph, class_uri) or class_uri.split('#')[-1],
                'comment': self._get_comment(graph, class_uri),
                'type': category[:-1]  # Remove 's' from plural
            }
            if class_info not in concepts[category]:
                concepts[category].insert(0, class_info)  # Add at beginning
        
        return concepts
    
    def _extract_metadata(self, graph: Graph, source: str,
                         name: Optional[str] = None, 
                         description: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract metadata from an ontology graph.
        
        Args:
            graph: RDF graph
            source: Source URL or file path
            name: Override name
            description: Override description
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            'source': source,
            'name': name or '',
            'description': description or ''
        }
        
        # Try to find ontology declaration
        for s in graph.subjects(RDF.type, OWL.Ontology):
            if not name:
                metadata['name'] = self._get_label(graph, s) or str(s)
            if not description:
                comment = self._get_comment(graph, s)
                if comment:
                    metadata['description'] = comment
            
            # Get version info
            version = next(graph.objects(s, OWL.versionInfo), None)
            if version:
                metadata['version'] = str(version)
            
            # Get other metadata
            for pred, key in [
                (DCTERMS.title, 'title'),
                (DCTERMS.creator, 'creator'),
                (DCTERMS.publisher, 'publisher'),
                (DCTERMS.license, 'license'),
                (DCTERMS.created, 'created'),
                (DCTERMS.modified, 'modified')
            ]:
                value = next(graph.objects(s, pred), None)
                if value:
                    metadata[key] = str(value)
            
            break  # Use first ontology declaration found
        
        # Count classes and properties
        metadata['class_count'] = len(list(graph.subjects(RDF.type, OWL.Class)))
        metadata['property_count'] = (
            len(list(graph.subjects(RDF.type, OWL.ObjectProperty))) +
            len(list(graph.subjects(RDF.type, OWL.DatatypeProperty)))
        )
        
        return metadata
    
    def _get_label(self, graph: Graph, subject: Any) -> Optional[str]:
        """Get rdfs:label for a subject."""
        label = next(graph.objects(subject, RDFS.label), None)
        return str(label) if label else None
    
    def _get_comment(self, graph: Graph, subject: Any) -> Optional[str]:
        """Get rdfs:comment for a subject."""
        comment = next(graph.objects(subject, RDFS.comment), None)
        return str(comment) if comment else None
    
    def _load_from_cache(self, ontology_id: str) -> Optional[Dict[str, Any]]:
        """Load an ontology from cache."""
        if not self.cache_dir:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{ontology_id}.ttl")
        metadata_file = os.path.join(self.cache_dir, f"{ontology_id}.json")
        
        if not os.path.exists(cache_file) or not os.path.exists(metadata_file):
            return None
        
        try:
            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Load graph
            g = Graph()
            g.parse(cache_file, format='turtle')
            
            # Store in memory
            self.imported_ontologies[ontology_id] = {
                'graph': g,
                'metadata': metadata,
                'content': g.serialize(format='turtle')
            }
            
            return {
                'success': True,
                'ontology_id': ontology_id,
                'metadata': metadata,
                'graph': g,
                'message': f"Loaded ontology {ontology_id} from cache"
            }
            
        except Exception as e:
            self.logger.error(f"Error loading ontology {ontology_id} from cache: {e}")
            return None
