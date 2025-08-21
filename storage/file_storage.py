"""
File-based storage backend implementation.

Stores ontologies as files on the filesystem with JSON metadata.
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from storage.base import StorageBackend, StorageError


class FileStorage(StorageBackend):
    """
    File-based storage implementation.
    
    Stores ontologies as .ttl files and metadata as .json files
    in a structured directory hierarchy.
    """
    
    def _initialize(self):
        """Initialize the file storage backend."""
        # Get storage directory from config
        self.storage_dir = Path(self.config.get(
            'storage_dir', 
            os.path.join(os.getcwd(), 'ontology_storage')
        ))
        
        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.ontologies_dir = self.storage_dir / 'ontologies'
        self.versions_dir = self.storage_dir / 'versions'
        self.metadata_dir = self.storage_dir / 'metadata'
        
        for directory in [self.ontologies_dir, self.versions_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_ontology_path(self, ontology_id: str) -> Path:
        """Get the file path for an ontology."""
        # Sanitize the ID for filesystem use
        safe_id = self._sanitize_id(ontology_id)
        return self.ontologies_dir / f"{safe_id}.ttl"
    
    def _get_metadata_path(self, ontology_id: str) -> Path:
        """Get the metadata file path for an ontology."""
        safe_id = self._sanitize_id(ontology_id)
        return self.metadata_dir / f"{safe_id}.json"
    
    def _get_version_path(self, ontology_id: str, version: str) -> Path:
        """Get the file path for a specific version."""
        safe_id = self._sanitize_id(ontology_id)
        safe_version = self._sanitize_id(version)
        version_dir = self.versions_dir / safe_id
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir / f"{safe_version}.ttl"
    
    def _sanitize_id(self, id_str: str) -> str:
        """Sanitize an ID for filesystem use."""
        # Replace problematic characters
        safe = id_str.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe = safe.replace(' ', '_').replace('.', '_')
        return safe
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def store(self, ontology_id: str, content: str, 
              metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store an ontology to the filesystem.
        
        Args:
            ontology_id: Unique identifier for the ontology
            content: The ontology content (TTL format)
            metadata: Optional metadata about the ontology
            
        Returns:
            Dictionary containing storage result
        """
        try:
            # Get paths
            ontology_path = self._get_ontology_path(ontology_id)
            metadata_path = self._get_metadata_path(ontology_id)
            
            # Prepare metadata
            meta = metadata or {}
            meta.update({
                'ontology_id': ontology_id,
                'stored_at': datetime.now().isoformat(),
                'content_hash': self._compute_hash(content),
                'size_bytes': len(content.encode()),
                'storage_type': 'file'
            })
            
            # Check if this is an update
            is_update = ontology_path.exists()
            
            # If updating, create a version backup
            if is_update:
                existing_content = ontology_path.read_text()
                version = datetime.now().isoformat()
                version_path = self._get_version_path(ontology_id, version)
                version_path.write_text(existing_content)
                
                # Update version list in metadata
                if 'versions' not in meta:
                    meta['versions'] = []
                meta['versions'].append({
                    'version': version,
                    'created_at': version,
                    'hash': self._compute_hash(existing_content)
                })
            
            # Write content
            ontology_path.write_text(content)
            
            # Write metadata
            metadata_path.write_text(json.dumps(meta, indent=2))
            
            return {
                'success': True,
                'ontology_id': ontology_id,
                'path': str(ontology_path),
                'metadata_path': str(metadata_path),
                'is_update': is_update,
                'hash': meta['content_hash']
            }
            
        except Exception as e:
            raise StorageError(f"Failed to store ontology {ontology_id}: {str(e)}")
    
    def retrieve(self, ontology_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve an ontology from the filesystem.
        
        Args:
            ontology_id: Unique identifier for the ontology
            version: Optional version to retrieve
            
        Returns:
            Dictionary containing content and metadata
        """
        try:
            if version:
                # Retrieve specific version
                version_path = self._get_version_path(ontology_id, version)
                if not version_path.exists():
                    raise StorageError(f"Version {version} not found for ontology {ontology_id}")
                content = version_path.read_text()
            else:
                # Retrieve latest version
                ontology_path = self._get_ontology_path(ontology_id)
                if not ontology_path.exists():
                    raise StorageError(f"Ontology {ontology_id} not found")
                content = ontology_path.read_text()
            
            # Load metadata
            metadata_path = self._get_metadata_path(ontology_id)
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text())
            else:
                metadata = {'ontology_id': ontology_id}
            
            return {
                'content': content,
                'metadata': metadata,
                'version': version or 'latest',
                'hash': self._compute_hash(content)
            }
            
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to retrieve ontology {ontology_id}: {str(e)}")
    
    def exists(self, ontology_id: str) -> bool:
        """Check if an ontology exists."""
        ontology_path = self._get_ontology_path(ontology_id)
        return ontology_path.exists()
    
    def delete(self, ontology_id: str, version: Optional[str] = None) -> bool:
        """
        Delete an ontology or specific version.
        
        Args:
            ontology_id: Unique identifier for the ontology
            version: Optional version to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            if version:
                # Delete specific version
                version_path = self._get_version_path(ontology_id, version)
                if version_path.exists():
                    version_path.unlink()
                    return True
                return False
            else:
                # Delete entire ontology
                ontology_path = self._get_ontology_path(ontology_id)
                metadata_path = self._get_metadata_path(ontology_id)
                
                deleted = False
                if ontology_path.exists():
                    ontology_path.unlink()
                    deleted = True
                
                if metadata_path.exists():
                    metadata_path.unlink()
                    deleted = True
                
                # Delete version directory
                safe_id = self._sanitize_id(ontology_id)
                version_dir = self.versions_dir / safe_id
                if version_dir.exists():
                    import shutil
                    shutil.rmtree(version_dir)
                    deleted = True
                
                return deleted
                
        except Exception as e:
            raise StorageError(f"Failed to delete ontology {ontology_id}: {str(e)}")
    
    def list_ontologies(self, filter_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        List available ontologies.
        
        Args:
            filter_criteria: Optional filtering criteria
            
        Returns:
            List of ontology metadata dictionaries
        """
        ontologies = []
        
        # List all .ttl files in ontologies directory
        for ttl_file in self.ontologies_dir.glob("*.ttl"):
            ontology_id = ttl_file.stem
            
            # Load metadata
            metadata_path = self._get_metadata_path(ontology_id)
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text())
            else:
                # Create basic metadata
                metadata = {
                    'ontology_id': ontology_id,
                    'file_path': str(ttl_file),
                    'size_bytes': ttl_file.stat().st_size,
                    'modified_at': datetime.fromtimestamp(
                        ttl_file.stat().st_mtime
                    ).isoformat()
                }
            
            # Apply filters if provided
            if filter_criteria:
                match = True
                for key, value in filter_criteria.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue
            
            ontologies.append(metadata)
        
        return ontologies
    
    def list_versions(self, ontology_id: str) -> List[Dict[str, Any]]:
        """
        List available versions of an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            
        Returns:
            List of version metadata dictionaries
        """
        if not self.exists(ontology_id):
            raise StorageError(f"Ontology {ontology_id} not found")
        
        versions = []
        
        # Check version directory
        safe_id = self._sanitize_id(ontology_id)
        version_dir = self.versions_dir / safe_id
        
        if version_dir.exists():
            for version_file in version_dir.glob("*.ttl"):
                version_id = version_file.stem
                versions.append({
                    'version': version_id,
                    'file_path': str(version_file),
                    'size_bytes': version_file.stat().st_size,
                    'created_at': datetime.fromtimestamp(
                        version_file.stat().st_mtime
                    ).isoformat()
                })
        
        # Add current version
        ontology_path = self._get_ontology_path(ontology_id)
        if ontology_path.exists():
            versions.append({
                'version': 'latest',
                'file_path': str(ontology_path),
                'size_bytes': ontology_path.stat().st_size,
                'created_at': datetime.fromtimestamp(
                    ontology_path.stat().st_mtime
                ).isoformat()
            })
        
        return versions
    
    def get_metadata(self, ontology_id: str, 
                    version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            version: Optional version (ignored for file storage)
            
        Returns:
            Metadata dictionary
        """
        metadata_path = self._get_metadata_path(ontology_id)
        
        if not metadata_path.exists():
            if not self.exists(ontology_id):
                raise StorageError(f"Ontology {ontology_id} not found")
            
            # Return basic metadata
            ontology_path = self._get_ontology_path(ontology_id)
            return {
                'ontology_id': ontology_id,
                'file_path': str(ontology_path),
                'size_bytes': ontology_path.stat().st_size,
                'modified_at': datetime.fromtimestamp(
                    ontology_path.stat().st_mtime
                ).isoformat()
            }
        
        return json.loads(metadata_path.read_text())
    
    def update_metadata(self, ontology_id: str, metadata: Dict[str, Any],
                       version: Optional[str] = None) -> bool:
        """
        Update metadata for an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            metadata: New metadata to merge with existing
            version: Optional version (ignored for file storage)
            
        Returns:
            True if update was successful
        """
        try:
            # Get existing metadata
            existing = self.get_metadata(ontology_id)
            
            # Merge metadata
            existing.update(metadata)
            existing['updated_at'] = datetime.now().isoformat()
            
            # Write updated metadata
            metadata_path = self._get_metadata_path(ontology_id)
            metadata_path.write_text(json.dumps(existing, indent=2))
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to update metadata for {ontology_id}: {str(e)}")
