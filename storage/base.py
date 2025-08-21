"""
Abstract base class for storage backends.

Defines the interface that all storage implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class StorageBackend(ABC):
    """
    Abstract base class for ontology storage backends.
    
    All storage implementations must inherit from this class and
    implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the storage backend.
        
        Args:
            config: Configuration dictionary for the backend
        """
        self.config = config or {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """
        Initialize the storage backend.
        
        This method should set up any necessary connections,
        create directories, etc.
        """
        pass
    
    @abstractmethod
    def store(self, ontology_id: str, content: str, 
              metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            content: The ontology content (typically TTL format)
            metadata: Optional metadata about the ontology
            
        Returns:
            Dictionary containing storage result information
            
        Raises:
            StorageError: If storage fails
        """
        pass
    
    @abstractmethod
    def retrieve(self, ontology_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            version: Optional version to retrieve (None for latest)
            
        Returns:
            Dictionary containing:
                - content: The ontology content
                - metadata: Metadata about the ontology
                - version: Version identifier
                
        Raises:
            StorageError: If retrieval fails or ontology not found
        """
        pass
    
    @abstractmethod
    def exists(self, ontology_id: str) -> bool:
        """
        Check if an ontology exists.
        
        Args:
            ontology_id: Unique identifier for the ontology
            
        Returns:
            True if the ontology exists, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, ontology_id: str, version: Optional[str] = None) -> bool:
        """
        Delete an ontology or specific version.
        
        Args:
            ontology_id: Unique identifier for the ontology
            version: Optional version to delete (None to delete all)
            
        Returns:
            True if deletion was successful
            
        Raises:
            StorageError: If deletion fails
        """
        pass
    
    @abstractmethod
    def list_ontologies(self, filter_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        List available ontologies.
        
        Args:
            filter_criteria: Optional filtering criteria
            
        Returns:
            List of ontology metadata dictionaries
        """
        pass
    
    @abstractmethod
    def list_versions(self, ontology_id: str) -> List[Dict[str, Any]]:
        """
        List available versions of an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            
        Returns:
            List of version metadata dictionaries
            
        Raises:
            StorageError: If ontology not found
        """
        pass
    
    @abstractmethod
    def get_metadata(self, ontology_id: str, 
                    version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            version: Optional version (None for latest)
            
        Returns:
            Metadata dictionary
            
        Raises:
            StorageError: If ontology not found
        """
        pass
    
    @abstractmethod
    def update_metadata(self, ontology_id: str, metadata: Dict[str, Any],
                       version: Optional[str] = None) -> bool:
        """
        Update metadata for an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            metadata: New metadata to merge with existing
            version: Optional version to update (None for latest)
            
        Returns:
            True if update was successful
            
        Raises:
            StorageError: If update fails or ontology not found
        """
        pass
    
    def create_version(self, ontology_id: str, content: str,
                      version_info: Dict[str, Any] = None) -> str:
        """
        Create a new version of an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            content: The new version content
            version_info: Optional version metadata
            
        Returns:
            Version identifier for the new version
            
        Raises:
            StorageError: If version creation fails
        """
        # Default implementation: store with timestamp as version
        version = datetime.now().isoformat()
        metadata = version_info or {}
        metadata['version'] = version
        metadata['created_at'] = version
        
        self.store(f"{ontology_id}:{version}", content, metadata)
        return version
    
    def backup(self, ontology_id: str, backup_path: str) -> bool:
        """
        Create a backup of an ontology.
        
        Args:
            ontology_id: Unique identifier for the ontology
            backup_path: Path where backup should be stored
            
        Returns:
            True if backup was successful
            
        Raises:
            StorageError: If backup fails
        """
        # Default implementation
        try:
            data = self.retrieve(ontology_id)
            import json
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            raise StorageError(f"Backup failed: {str(e)}")
    
    def restore(self, ontology_id: str, backup_path: str) -> bool:
        """
        Restore an ontology from backup.
        
        Args:
            ontology_id: Unique identifier for the ontology
            backup_path: Path to backup file
            
        Returns:
            True if restoration was successful
            
        Raises:
            StorageError: If restoration fails
        """
        # Default implementation
        try:
            import json
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            self.store(ontology_id, data['content'], data.get('metadata'))
            return True
        except Exception as e:
            raise StorageError(f"Restoration failed: {str(e)}")
    
    def close(self):
        """
        Close any open connections or resources.
        
        Subclasses should override this if they need cleanup.
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
