# OntServe Ontology Editor Integration Plan

## Overview
Adapting the proethica ontology editor to work with OntServer's hybrid storage architecture, replacing Neo4j with lightweight pgvector-based semantic search while maintaining full compatibility for future proethica consumption.

## Architecture Comparison & Integration Strategy

### Proethica Original Architecture
- **Storage**: Pure database-driven (SQLAlchemy)
- **Visualization**: Neo4j graph database (high overhead)
- **Features**: TTL editor, entity cards, BFO validation, hierarchical visualization
- **Authentication**: Integrated with Flask-Login
- **Entity Types**: Roles, Conditions, Resources, Actions, Events, Capabilities

### OntServe Hybrid Architecture (Target)
- **Storage**: File system ground truth (.ttl files) + PostgreSQL metadata/search
- **Visualization**: pgvector semantic search + D3.js/vis.js (lightweight)
- **Models**: Ontology, OntologyVersion, OntologyEntity, SearchHistory
- **Search**: Vector embeddings with cosine similarity
- **Import Status**: ✅ BFO, ✅ PROV-O, ✅ proethica-intermediate

### Integration Benefits
1. **Performance**: Replace Neo4j overhead with pgvector semantic search
2. **Scalability**: File-based ground truth with database indexing
3. **Compatibility**: Maintain API compatibility for proethica consumption
4. **Existing Data**: Leverage already imported foundation ontologies

## Implementation Phases

### Phase 1: Core Editor Infrastructure ✅ PARTIALLY COMPLETE
- [x] Database models (Ontology, OntologyVersion, OntologyEntity)
- [x] File storage with versioning support
- [x] Basic web templates structure
- [x] Import system for foundation ontologies
- [ ] Adapt proethica editor templates to OntServe structure
- [ ] Create editor API endpoints

### Phase 2: Entity Management & Visualization
- [ ] Port proethica's entity extraction service to work with OntServe models
- [ ] Implement semantic search using pgvector instead of Neo4j
- [ ] Create entity relationship visualization using D3.js/vis.js
- [ ] Add hierarchical tree view for ontology classes
- [ ] Implement entity cards interface (roles, conditions, resources, etc.)

### Phase 3: Editor Interface
- [ ] Adapt proethica's TTL editor with CodeMirror
- [ ] Implement save functionality with commit messages
- [ ] Add validation panel (BFO compliance, PROV-O validation)
- [ ] Create version history viewer and diff functionality
- [ ] Add entity preview and editing capabilities

### Phase 4: Advanced Features
- [ ] Implement search and filtering across entities
- [ ] Add export capabilities (TTL, RDF/XML, JSON-LD)
- [ ] Create import/merge functionality for ontologies
- [ ] Add collaborative editing features
- [ ] Implement custom validation rules

### Phase 5: ProEthica Integration
- [ ] Create MCP server for ontology operations
- [ ] Implement API endpoints for proethica consumption
- [ ] Add authentication integration hooks
- [ ] Create shared configuration system
- [ ] Document integration protocols

## File Structure (Updated)
```
OntServe/
├── storage/
│   ├── ontologies/           # File storage for .ttl files
│   │   ├── bfo/
│   │   │   ├── current.ttl
│   │   │   ├── metadata.json
│   │   │   └── versions/
│   │   ├── prov-o/
│   │   │   ├── current.ttl
│   │   │   ├── metadata.json
│   │   │   └── versions/
│   │   └── proethica-intermediate/
│   │       ├── current.ttl
│   │       ├── metadata.json
│   │       └── versions/
├── web/
│   ├── templates/
│   │   ├── editor.html        # Main editor interface
│   │   ├── visualize.html     # Visualization interface
│   │   ├── entities.html      # Entity management
│   │   └── versions.html      # Version history
│   ├── static/
│   │   ├── js/
│   │   │   ├── editor.js      # CodeMirror integration
│   │   │   ├── visualize.js   # D3.js/vis.js visualization
│   │   │   └── entities.js    # Entity management
│   │   └── css/
│   │       └── editor.css     # Editor styling
│   └── models.py              # ✅ Database models (complete)
└── editor/                    # New editor module
    ├── __init__.py
    ├── routes.py              # Editor API endpoints
    ├── services.py            # Entity extraction & validation
    └── utils.py               # Helper functions
```

## Database Schema Integration

### Existing OntServe Models (✅ Complete)
```python
class Ontology(db.Model):
    id, ontology_id, name, description, content, format
    source_url, source_file, triple_count, class_count, property_count
    meta_data, created_at, updated_at
    # Relationships: versions, entities

class OntologyVersion(db.Model):
    id, ontology_id, version, content, commit_message
    triple_count, changes_summary, created_at, created_by

class OntologyEntity(db.Model):
    id, ontology_id, entity_type, uri, label, comment
    parent_uri, domain, range, properties
    embedding (Vector(384))  # pgvector for semantic search
```

### Entity Types Mapping
- **ProEthica Entities** → **OntServe entity_type field**
- Roles → 'role'
- Conditions → 'condition'
- Resources → 'resource' 
- Actions → 'action'
- Events → 'event'
- Capabilities → 'capability'
- Classes → 'class'
- Properties → 'property'
- Individuals → 'individual'

## API Endpoints (New)
```
GET    /editor                          # Main editor interface
GET    /editor/ontology/<id>           # Load ontology in editor
POST   /editor/ontology/<id>/save      # Save ontology with version
GET    /editor/ontology/<id>/entities  # Get entities with semantic search
GET    /editor/ontology/<id>/visualize # Visualization interface
GET    /editor/ontology/<id>/versions  # Version history
POST   /editor/ontology/<id>/validate  # Validate ontology content
GET    /api/entities/search            # Semantic search endpoint
```

## Visualization Architecture

### Replace Neo4j with pgvector + D3.js
```javascript
// Semantic search for related entities
async function findRelatedEntities(entityUri) {
    const response = await fetch(`/api/entities/search?similar_to=${entityUri}&limit=10`);
    return response.json();
}

// D3.js force-directed graph
function createVisualization(entities, relationships) {
    const svg = d3.select("#visualization");
    const simulation = d3.forceSimulation(entities)
        .force("link", d3.forceLink(relationships))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width/2, height/2));
}
```

### Hierarchical Tree View
```javascript
// Tree visualization for class hierarchies
function createClassHierarchy(classes) {
    const hierarchy = d3.hierarchy(buildTree(classes));
    const treeLayout = d3.tree().size([height, width]);
    const root = treeLayout(hierarchy);
}
```

## Entity Extraction Service (Adapted)

### From ProEthica Database → OntServe Hybrid
```python
class OntologyEntityService:
    def __init__(self, storage_backend, db_session):
        self.storage = storage_backend
        self.db = db_session
        
    def extract_entities(self, ontology_id: str) -> List[OntologyEntity]:
        # Get TTL content from file storage
        result = self.storage.retrieve(ontology_id)
        ttl_content = result['content']
        
        # Parse with RDFLib (same as proethica)
        graph = Graph()
        graph.parse(data=ttl_content, format='turtle')
        
        # Extract entities and store in database
        entities = []
        for entity_type in ['class', 'property', 'individual']:
            extracted = self._extract_by_type(graph, entity_type)
            entities.extend(extracted)
            
        return entities
        
    def generate_embeddings(self, entities: List[OntologyEntity]):
        # Generate vector embeddings for semantic search
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        for entity in entities:
            text = f"{entity.label} {entity.comment}"
            entity.embedding = model.encode(text).tolist()
```

## BFO Compliance & Validation

### Leverage Existing Foundation Ontologies
```python
class BFOValidator:
    def __init__(self):
        # Load foundation ontologies from OntServe storage
        self.bfo = self._load_ontology('bfo')
        self.prov_o = self._load_ontology('prov-o')
        self.intermediate = self._load_ontology('proethica-intermediate')
        
    def validate_ontology(self, content: str) -> ValidationResult:
        # Validate against BFO patterns and intermediate ontology
        graph = Graph()
        graph.parse(data=content, format='turtle')
        
        warnings = []
        errors = []
        
        # Check BFO compliance
        bfo_warnings = self._check_bfo_compliance(graph)
        warnings.extend(bfo_warnings)
        
        return ValidationResult(errors=errors, warnings=warnings)
```

## ProEthica Compatibility Layer

### MCP Server for Ontology Operations
```python
# OntServe/mcp/ontology_server.py
class OntologyMCPServer:
    def __init__(self, ontserver_instance):
        self.ontserver = ontserver_instance
        
    @mcp_tool
    async def get_ontology(self, ontology_id: str) -> dict:
        """Get ontology content and metadata"""
        return self.ontserver.get_ontology(ontology_id)
        
    @mcp_tool  
    async def search_entities(self, query: str, entity_type: str = None) -> list:
        """Semantic search across entities"""
        return self.ontserver.search_entities(query, entity_type)
        
    @mcp_tool
    async def validate_ontology(self, content: str) -> dict:
        """Validate ontology against BFO and other standards"""
        return self.ontserver.validate_ontology(content)
```

## Testing Strategy

### Phase 1: Foundation Testing
```bash
# Test with existing imported ontologies
python -m pytest tests/test_editor_bfo.py
python -m pytest tests/test_editor_prov_o.py
python -m pytest tests/test_editor_proethica.py
```

### Phase 2: Integration Testing
```bash
# Test semantic search performance vs Neo4j
python -m pytest tests/test_semantic_search.py
python -m pytest tests/test_visualization_performance.py
```

### Phase 3: Compatibility Testing
```bash
# Test ProEthica integration
python -m pytest tests/test_proethica_compatibility.py
```

## Migration Path

### For ProEthica Integration
1. **Phase 1**: OntServe provides ontology storage and search APIs
2. **Phase 2**: ProEthica consumes OntServe APIs via MCP server
3. **Phase 3**: Gradual migration of ProEthica ontology operations to OntServe
4. **Phase 4**: ProEthica uses OntServe as primary ontology backend

### Configuration Management
```yaml
# config/integration.yml
proethica_compatibility:
  enabled: true
  mcp_server:
    host: localhost
    port: 8001
  shared_ontologies:
    - bfo
    - prov-o
    - proethica-intermediate
```

## Performance Expectations

### pgvector vs Neo4j Comparison
- **Startup Time**: pgvector ~1s vs Neo4j ~10-30s
- **Memory Usage**: pgvector ~100MB vs Neo4j ~500MB-1GB
- **Query Performance**: Similar for semantic similarity
- **Maintenance**: pgvector integrated with main DB vs separate Neo4j instance

### Scalability Targets
- **Ontologies**: 100+ ontologies
- **Entities**: 10,000+ entities per ontology
- **Search Response**: <100ms for semantic queries
- **Visualization**: <2s to render 1000+ entity graphs

## Next Steps

### Immediate (Week 1)
1. Create editor module structure
2. Adapt proethica templates to OntServe
3. Implement basic entity extraction service
4. Create semantic search endpoints

### Short Term (Weeks 2-3)
1. Implement D3.js visualization components
2. Add TTL editor with validation
3. Create version management interface
4. Test with foundation ontologies

### Medium Term (Month 2)
1. Add entity cards and editing interface
2. Implement collaborative features
3. Create MCP server for proethica integration
4. Performance optimization and testing

## Documentation Requirements

1. **API Documentation**: OpenAPI/Swagger spec for all endpoints
2. **Integration Guide**: How to consume from ProEthica
3. **Visualization Guide**: Using the D3.js components
4. **Entity Management**: Working with the semantic search
5. **Validation Guide**: BFO compliance and custom rules

## Success Metrics

- ✅ Successfully replace Neo4j with pgvector (target: 80% memory reduction)
- ✅ Maintain all proethica editor functionality
- ✅ Achieve <100ms semantic search response times
- ✅ Support 1000+ entity visualizations
- ✅ Full compatibility with existing BFO, PROV-O, proethica-intermediate ontologies
- ✅ Seamless integration path for ProEthica consumption
