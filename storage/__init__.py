"""
Storage backends for OntServe.

Provides different storage strategies:
- File-based storage
- Database storage  
- Hybrid storage with automatic fallback
"""

from .base import StorageBackend, StorageError
from .file_storage import FileStorage

__all__ = [
    'StorageBackend',
    'StorageError',
    'FileStorage'
]
