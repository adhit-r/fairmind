"""
Base interfaces and abstract classes for FairMind backend.

Defines the contracts that all components must follow for consistency
and testability.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime


# Type variables for generic interfaces
T = TypeVar('T')
ID = TypeVar('ID')


class IService(ABC):
    """Base interface for all service classes."""
    
    @abstractmethod
    def __init__(self, *args, **kwargs):
        """Initialize the service with dependencies."""
        pass


class IRepository(ABC, Generic[T, ID]):
    """Base repository interface for data access."""
    
    @abstractmethod
    async def get_by_id(self, id: ID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def update(self, id: ID, entity: T) -> Optional[T]:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete an entity by ID."""
        pass


class ICache(ABC):
    """Base cache interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL in seconds."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass


class IHealthCheck(ABC):
    """Base health check interface."""
    
    @abstractmethod
    async def check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Dict with keys: name, status, message, details
        """
        pass


class IDependencyChecker(ABC):
    """Base dependency checker interface."""
    
    @abstractmethod
    async def check_database(self) -> bool:
        """Check database connectivity."""
        pass
    
    @abstractmethod
    async def check_cache(self) -> bool:
        """Check cache connectivity."""
        pass
    
    @abstractmethod
    async def check_external_service(self, service_name: str) -> bool:
        """Check external service availability."""
        pass


class ILogger(ABC):
    """Base logger interface."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs):
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs):
        """Log error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        pass


class IEventBus(ABC):
    """Base event bus interface for pub/sub messaging."""
    
    @abstractmethod
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event."""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler: callable):
        """Subscribe to an event type."""
        pass


class IStorageProvider(ABC):
    """Base storage provider interface."""
    
    @abstractmethod
    async def upload(self, file_path: str, content: bytes) -> str:
        """Upload file and return storage URL."""
        pass
    
    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        """Download file content."""
        pass
    
    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """Delete file."""
        pass
    
    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass
    
    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files with optional prefix."""
        pass


class BaseModel:
    """Base model class for domain models."""
    
    id: Optional[ID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model from dictionary."""
        return cls(**data)
