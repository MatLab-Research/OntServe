# OntServe Development Notes

## Project Overview
OntServe is a unified ontology management server designed to consolidate and enhance ontology handling capabilities from OntExtract and proethica. It provides a centralized system for importing, storing, querying, and serving ontologies through multiple interfaces (REST API, MCP, Python library).

## Current Status (2025-01-21)

### ✅ Recently Completed

#### Web Interface Implementation
- **Full-featured Flask web application** with Bootstrap 5 UI
- **Ontology management dashboard** showing all imported ontologies
- **Import functionality** supporting URL, file upload, and text input
- **Ontology detail views** with entity listings and relationship navigation
- **Visual ontology editor** with cytoscape.js for graph visualization
- **Search capabilities** across all ontologies
- **Database integration** with SQLAlchemy models

#### Core Infrastructure
- **OntologyManager** central management system
- **Hybrid storage** supporting both file and database backends
- **PROV-O and BFO importers** with full entity extraction
- **Automatic initialization** of default ontologies (PROV-O, BFO)
- **Comprehensive logging** throughout the system

#### Database Layer
- **SQLAlchemy models** for Ontology, OntologyEntity, and OntologyRelationship
- **Automatic database initialization** with default ontologies
- **Efficient querying** with relationship tracking
- **Metadata storage** including version, description, and import timestamps

### 🔄 Current Work

#### Web Editor Enhancement
- **Interactive graph editing** capabilities (in progress)
- **Entity/relationship CRUD operations** via UI
- **Export functionality** for modified ontologies
- **Version tracking** for changes

#### API Development
- **RESTful endpoints** for programmatic access
- **MCP server integration** for Claude compatibility
- **Authentication layer** for secure access

### 📋 Next Steps

1. **Complete Editor Functionality**
   - Add/edit/delete entities and relationships
   - Save changes back to database
   - Export to various formats (TTL, OWL, JSON-LD)

2. **MCP Server Implementation**
   - Port proethica's MCP capabilities
   - Ensure backward compatibility
   - Add OntServe-specific tools

3. **Integration Testing**
   - Test with OntExtract's PROV-O requirements
   - Verify proethica compatibility
   - Performance benchmarking

4. **Advanced Features**
   - Ontology versioning and history
   - Diff/merge capabilities
   - Neo4j graph database preparation
   - WebVOWL integration

## Technical Architecture

### Directory Structure
```
OntServe/
├── core/               # Core management logic
│   └── ontology_manager.py
├── storage/            # Storage backends
│   ├── base.py        # Abstract interface
│   └── file_storage.py # File-based implementation
├── importers/          # Format-specific importers
│   ├── base.py        # Base importer class
│   ├── prov_importer.py
│   └── bfo_importer.py
├── web/               # Flask web application
│   ├── app.py         # Main Flask app
│   ├── models.py      # SQLAlchemy models
│   ├── config.py      # Configuration
│   ├── templates/     # HTML templates
│   └── static/        # CSS, JS, images
└── cache/             # Cached ontology files
```

### Key Components

#### OntologyManager (`core/ontology_manager.py`)
- Central orchestrator for all ontology operations
- Manages importers, storage, and caching
- Provides unified API for ontology access

#### Web Application (`web/app.py`)
- Flask-based web interface
- RESTful API endpoints
- Real-time ontology visualization
- Database-backed persistence

#### Storage System
- **FileStorage**: JSON file-based storage with indexing
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Hybrid**: Automatic fallback and synchronization

#### Importers
- **ProvImporter**: Specialized for PROV-O ontology
- **BFOImporter**: Handles BFO (Basic Formal Ontology)
- **BaseImporter**: Extensible base for custom formats

### Database Schema

```sql
-- Ontologies table
CREATE TABLE ontologies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    namespace VARCHAR(500),
    version VARCHAR(50),
    description TEXT,
    source_url VARCHAR(500),
    raw_content TEXT,
    format VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Ontology entities table
CREATE TABLE ontology_entities (
    id SERIAL PRIMARY KEY,
    ontology_id INTEGER REFERENCES ontologies(id),
    uri VARCHAR(500) NOT NULL,
    name VARCHAR(255),
    type VARCHAR(100),
    label TEXT,
    definition TEXT,
    metadata JSONB,
    UNIQUE(ontology_id, uri)
);

-- Ontology relationships table
CREATE TABLE ontology_relationships (
    id SERIAL PRIMARY KEY,
    ontology_id INTEGER REFERENCES ontologies(id),
    subject_id INTEGER REFERENCES ontology_entities(id),
    predicate VARCHAR(500),
    object_id INTEGER REFERENCES ontology_entities(id),
    metadata JSONB
);
```

### Web Interface Features

#### Dashboard (`/`)
- Overview of all imported ontologies
- Quick stats (entities, relationships, last updated)
- Search bar for cross-ontology queries
- Import button for new ontologies

#### Import Page (`/import`)
- Three import methods: URL, file upload, text input
- Format auto-detection
- Progress indicator for large ontologies
- Error handling with detailed messages

#### Ontology Detail (`/ontology/<name>`)
- Entity listing with type filtering
- Relationship browser
- Metadata display
- Export options
- Link to visual editor

#### Visual Editor (`/ontology/<name>/editor`)
- Interactive graph visualization (cytoscape.js)
- Node = Entity, Edge = Relationship
- Pan, zoom, layout controls
- Click to select and view details
- (Future: Edit capabilities)

#### Search (`/search`)
- Full-text search across all ontologies
- Filter by ontology, entity type
- Results show context and relationships

### Configuration

#### Environment Variables
```bash
# Database
ONTSERVE_DATABASE_URL=postgresql://user:pass@localhost/ontserve

# Storage
ONTSERVE_STORAGE_TYPE=hybrid  # file, database, hybrid
ONTSERVE_CACHE_DIR=./cache
ONTSERVE_FILE_DIR=./storage

# Web Server
FLASK_APP=web.app
FLASK_ENV=development
ONTSERVE_PORT=5003

# Logging
ONTSERVE_LOG_LEVEL=INFO
```

#### Running the Web Server
```bash
cd OntServe/web
./run.sh  # Sets up venv and starts Flask
```

### API Endpoints

#### Ontology Management
- `GET /api/ontologies` - List all ontologies
- `POST /api/ontologies` - Import new ontology
- `GET /api/ontologies/<name>` - Get ontology details
- `DELETE /api/ontologies/<name>` - Remove ontology

#### Entity Operations
- `GET /api/ontologies/<name>/entities` - List entities
- `GET /api/ontologies/<name>/entities/<id>` - Get entity details
- `POST /api/ontologies/<name>/entities` - Create entity (future)
- `PUT /api/ontologies/<name>/entities/<id>` - Update entity (future)

#### Relationship Operations
- `GET /api/ontologies/<name>/relationships` - List relationships
- `GET /api/ontologies/<name>/relationships/<id>` - Get relationship
- `POST /api/ontologies/<name>/relationships` - Create relationship (future)

#### Search
- `GET /api/search?q=<query>` - Search across ontologies
- `GET /api/search/entities?q=<query>&type=<type>` - Search entities

### Integration Points

#### OntExtract Integration
- Uses OntServe as library: `from OntServe.core import OntologyManager`
- Accesses PROV-O entities for temporal tracking
- Leverages entity extraction capabilities

#### proethica Integration
- MCP server compatibility maintained
- Database models aligned for easy migration
- API endpoints match existing expectations

#### a-proxy Integration (Future)
- Ethical decision support via ontology queries
- Role-based access control using ontology concepts

### Development Guidelines

#### Adding New Importers
1. Extend `BaseImporter` class
2. Implement `can_import()` and `import_ontology()` methods
3. Register with OntologyManager
4. Add tests in `tests/importers/`

#### Adding New Storage Backends
1. Implement `StorageBackend` interface
2. Handle CRUD operations for ontologies
3. Implement search and query methods
4. Add configuration support

#### Extending Web Interface
1. Add routes in `web/app.py`
2. Create templates in `web/templates/`
3. Add static resources in `web/static/`
4. Update navigation in `base.html`

### Testing

#### Unit Tests
```bash
python -m pytest tests/
```

#### Integration Tests
```bash
python -m pytest tests/integration/
```

#### Web Interface Testing
```bash
# Start test server
cd OntServe/web
flask run --debug

# Run Selenium tests (future)
python -m pytest tests/web/
```

### Performance Considerations

#### Caching Strategy
- In-memory cache for frequently accessed ontologies
- File cache for parsed representations
- Database query result caching
- TTL-based invalidation

#### Optimization Targets
- Ontology load time: < 500ms (cached)
- Entity query: < 50ms
- Relationship traversal: < 100ms
- Search response: < 200ms

### Known Issues

1. **Large Ontology Performance**: Loading very large ontologies (>10MB) can be slow
   - *Solution*: Implement streaming parser and pagination

2. **Circular Dependencies**: Some ontologies have circular references
   - *Solution*: Track visited nodes during traversal

3. **Format Detection**: Auto-detection sometimes fails for unusual formats
   - *Solution*: Allow manual format specification

### Recent Achievements (2025-01-21)

1. **Web Interface Launch**: Full Flask application with modern Bootstrap UI
2. **Database Integration**: SQLAlchemy models with automatic initialization
3. **Import Pipeline**: Support for URL, file, and text imports
4. **Visual Editor**: Interactive graph visualization with cytoscape.js
5. **Search Functionality**: Cross-ontology search capabilities
6. **Default Ontologies**: Automatic PROV-O and BFO initialization

### Immediate Priorities

1. **Complete Editor CRUD**: Enable creating/editing entities via UI
2. **MCP Server**: Port from proethica for Claude integration
3. **API Documentation**: OpenAPI/Swagger specification
4. **Performance Testing**: Benchmark with large ontologies
5. **Integration Tests**: Verify OntExtract/proethica compatibility

### Long-term Vision

- **Ontology Hub**: Central repository for organization's ontologies
- **Version Control**: Git-like versioning for ontology evolution
- **Collaboration**: Multi-user editing with conflict resolution
- **AI Integration**: LLM-powered ontology suggestions and validation
- **Standards Compliance**: Full OWL 2, SHACL, and SKOS support

## Development Commands

### Quick Start
```bash
# Set up and run web server
cd OntServe/web
./run.sh

# Initialize default ontologies
cd OntServe
python initialize_default_ontologies.py

# Test import
python import_prov_o.py
```

### Database Operations
```bash
# Create database
createdb ontserve

# Initialize schema
cd OntServe/web
python -c "from app import db; db.create_all()"

# Import default ontologies
python init_default_ontologies.py
```

### Development Workflow
```bash
# 1. Make changes to code
# 2. Test locally
cd OntServe
python example_usage.py

# 3. Run web interface
cd web
./run.sh

# 4. Check logs
tail -f ontserve_web.log
```

## Contact and Support

This is the centralized ontology management system for the broader platform. For questions about:
- **OntExtract integration**: See OntExtract/CLAUDE.md
- **proethica compatibility**: See proethica/CLAUDE.md
- **General architecture**: See root CLAUDE.md

---
*Last Updated: 2025-01-21*
