"""
Dependency Injection Container for FairMind backend.

Provides service registration, resolution, and lifecycle management
with support for singletons, transients, and circular dependency detection.
"""

from typing import Dict, Any, TypeVar, Type, Callable, Optional, Set
from enum import Enum
import inspect
from functools import wraps

from core.exceptions import AppException, ErrorCode


T = TypeVar('T')


class ServiceLifetime(str, Enum):
    """Service lifetime options."""
    SINGLETON = "singleton"  # Single instance shared across the application
    TRANSIENT = "transient"  # New instance created for each request


class CircularDependencyError(AppException):
    """Raised when a circular dependency is detected."""
    
    def __init__(self, dependency_chain: str):
        super().__init__(
            message=f"Circular dependency detected: {dependency_chain}",
            code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details={"dependency_chain": dependency_chain}
        )


class ServiceNotFoundError(AppException):
    """Raised when a service is not registered."""
    
    def __init__(self, service_type: Type):
        super().__init__(
            message=f"Service not registered: {service_type.__name__}",
            code=ErrorCode.NOT_FOUND,
            status_code=500,
            details={"service_type": service_type.__name__}
        )


class ServiceRegistry:
    """Registry for service definitions."""
    
    def __init__(self):
        self.services: Dict[Type, Dict[str, Any]] = {}
    
    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        instance: Optional[T] = None
    ):
        """Register a service."""
        if sum([implementation is not None, factory is not None, instance is not None]) != 1:
            raise ValueError("Exactly one of implementation, factory, or instance must be provided")
        
        self.services[service_type] = {
            "implementation": implementation,
            "factory": factory,
            "instance": instance,
            "lifetime": lifetime
        }
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered."""
        return service_type in self.services
    
    def get_definition(self, service_type: Type) -> Dict[str, Any]:
        """Get service definition."""
        if not self.is_registered(service_type):
            raise ServiceNotFoundError(service_type)
        return self.services[service_type]


class ServiceContainer:
    """
    Dependency Injection container with automatic dependency resolution.
    
    Features:
    - Type-based dependency resolution
    - Singleton and transient lifetimes
    - Circular dependency detection
    - Factory function support
    - Instance registration
    """
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self._singletons: Dict[Type, Any] = {}
        self._resolving: Set[Type] = set()  # Track services being resolved
    
    def register_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None
    ):
        """
        Register a singleton service.
        
        Args:
            service_type: The service interface or class
            implementation: The concrete implementation class
            factory: A factory function to create the service
            instance: An existing instance to use as the singleton
        """
        self.registry.register(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance
        )
    
    def register_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[..., T]] = None
    ):
        """
        Register a transient service (new instance each time).
        
        Args:
            service_type: The service interface or class
            implementation: The concrete implementation class
            factory: A factory function to create the service
        """
        self.registry.register(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve and return a service instance.
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            An instance of the requested service
            
        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
        """
        # Check for circular dependency
        if service_type in self._resolving:
            chain = " -> ".join([t.__name__ for t in self._resolving] + [service_type.__name__])
            raise CircularDependencyError(chain)
        
        definition = self.registry.get_definition(service_type)
        
        # Return existing singleton instance if available
        if definition["lifetime"] == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            # If instance was provided during registration, use it
            if definition["instance"] is not None:
                self._singletons[service_type] = definition["instance"]
                return definition["instance"]
        
        # Track that we're resolving this service
        self._resolving.add(service_type)
        
        try:
            # Create instance
            if definition["factory"] is not None:
                # Use factory function
                instance = self._create_from_factory(definition["factory"])
            elif definition["implementation"] is not None:
                # Use implementation class
                instance = self._create_from_implementation(definition["implementation"])
            else:
                # Should never happen due to registration validation
                raise ValueError(f"No implementation or factory for {service_type.__name__}")
            
            # Store singleton instance
            if definition["lifetime"] == ServiceLifetime.SINGLETON:
                self._singletons[service_type] = instance
            
            return instance
        
        finally:
            # Remove from resolving set
            self._resolving.discard(service_type)
    
    def _create_from_factory(self, factory: Callable) -> Any:
        """Create instance using factory function with dependency injection."""
        sig = inspect.signature(factory)
        
        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty and param.annotation != Any:
                # Try to resolve this parameter type
                if self.registry.is_registered(param.annotation):
                    kwargs[param_name] = self.resolve(param.annotation)
        
        return factory(**kwargs)
    
    def _create_from_implementation(self, implementation: Type) -> Any:
        """Create instance from implementation class with dependency injection."""
        sig = inspect.signature(implementation.__init__)
        
        # Resolve constructor dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty and param.annotation != Any:
                # Try to resolve this parameter type
                if self.registry.is_registered(param.annotation):
                    kwargs[param_name] = self.resolve(param.annotation)
        
        return implementation(**kwargs)
    
    def clear_singletons(self):
        """Clear all singleton instances (useful for testing)."""
        self._singletons.clear()


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def inject(service_type: Type[T]) -> T:
    """
    Decorator/function to inject a service dependency.
    
    Can be used as a function:
        service = inject(MyService)
    
    Or as a default parameter:
        def my_function(service: MyService = inject(MyService)):
            ...
    """
    return get_container().resolve(service_type)


def service(
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    interface: Optional[Type] = None
):
    """
    Decorator to automatically register a service class.
    
    Usage:
        @service(lifetime=ServiceLifetime.SINGLETON)
        class MyService:
            ...
        
        @service(lifetime=ServiceLifetime.SINGLETON, interface=IMyService)
        class MyService(IMyService):
            ...
    """
    def decorator(cls):
        container = get_container()
        service_type = interface if interface else cls
        
        if lifetime == ServiceLifetime.SINGLETON:
            container.register_singleton(service_type, implementation=cls)
        else:
            container.register_transient(service_type, implementation=cls)
        
        return cls
    
    return decorator
