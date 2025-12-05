"""
Route Registry for automatic route discovery and management.

Provides centralized route management with automatic discovery,
validation, and fail-fast error handling.
"""

from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from fastapi import APIRouter, FastAPI
from pathlib import Path
import importlib
import inspect

from core.logging import get_logger
from core.exceptions import AppException, ErrorCode


logger = get_logger(__name__)


@dataclass
class RouteMetadata:
    """Metadata for a registered route."""
    path: str
    methods: Set[str]
    tags: List[str]
    name: str
    handler: Callable
    description: Optional[str] = None
    documented: bool = False
    error_handling: bool = False


@dataclass
class DomainRoutes:
    """Routes for a specific domain."""
    domain: str
    router: APIRouter
    routes: List[RouteMetadata] = field(default_factory=list)


class RouteRegistryError(AppException):
    """Raised when route registration fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Route registry error: {message}",
            code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details=details
        )


class RouteValidator:
    """Validates route configurations."""
    
    @staticmethod
    def validate_route_documentation(route: RouteMetadata) -> List[str]:
        """Validate that route has proper documentation."""
        issues = []
        
        if not route.description:
            issues.append(f"Route {route.path} missing description")
        
        if not route.handler.__doc__:
            issues.append(f"Route handler {route.name} missing docstring")
        
        return issues
    
    @staticmethod
    def validate_route_naming(route: RouteMetadata) -> List[str]:
        """Validate route naming conventions."""
        issues = []
        
        # Check path format
        if not route.path.startswith('/'):
            issues.append(f"Route path {route.path} must start with '/'")
        
        # Check handler naming
        if not route.name or route.name.startswith('_'):
            issues.append(f"Route handler name {route.name} should not start with '_'")
        
        return issues
    
    @staticmethod
    def validate_error_handling(route: RouteMetadata) -> List[str]:
        """Validate that route has error handling."""
        issues = []
        
        # Check if handler has try/except or raises documented exceptions
        source = inspect.getsource(route.handler)
        if 'try:' not in source and 'raise' not in source:
            issues.append(f"Route {route.path} may lack error handling")
        
        return issues


class RouteRegistry:
    """
    Centralized route registry with automatic discovery.
    
    Features:
    - Automatic route discovery from domain modules
    - Route validation and fail-fast error handling
    - Route listing and introspection
    - Domain-based organization
    """
    
    def __init__(self, app: Optional[FastAPI] = None):
        self.app = app
        self.domains: Dict[str, DomainRoutes] = {}
        self.all_routes: List[RouteMetadata] = []
        self.validator = RouteValidator()
    
    def register_domain(
        self,
        domain: str,
        router: APIRouter,
        prefix: str = "",
        tags: Optional[List[str]] = None
    ):
        """
        Register a domain router.
        
        Args:
            domain: Domain name (e.g., 'auth', 'bias_detection')
            router: FastAPI router for the domain
            prefix: URL prefix for the router
            tags: OpenAPI tags
        """
        logger.info(f"Registering domain: {domain}", prefix=prefix)
        
        # Extract route metadata
        routes = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                metadata = RouteMetadata(
                    path=route.path,
                    methods=route.methods,
                    tags=tags or [],
                    name=route.name,
                    handler=route.endpoint,
                    description=route.description if hasattr(route, 'description') else None
                )
                routes.append(metadata)
        
        domain_routes = DomainRoutes(
            domain=domain,
            router=router,
            routes=routes
        )
        
        self.domains[domain] = domain_routes
        self.all_routes.extend(routes)
        
        # Register with FastAPI app if available
        if self.app:
            self.app.include_router(router, prefix=prefix, tags=tags or [domain])
        
        logger.info(f"Domain {domain} registered with {len(routes)} routes")
    
    def discover_routes(self, base_path: Path, fail_fast: bool = True):
        """
        Automatically discover routes from domain modules.
        
        Args:
            base_path: Base path to domain modules
            fail_fast: Whether to fail immediately on discovery errors
        """
        logger.info("Starting route discovery", base_path=str(base_path))
        
        domains_path = base_path / "domain"
        if not domains_path.exists():
            error_msg = f"Domains directory not found: {domains_path}"
            if fail_fast:
                raise RouteRegistryError(error_msg)
            logger.warning(error_msg)
            return
        
        discovered_count = 0
        errors = []
        
        for domain_dir in domains_path.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('_'):
                continue
            
            domain_name = domain_dir.name
            
            try:
                # Try to import routes module
                module_path = f"domain.{domain_name}.routes"
                
                try:
                    module = importlib.import_module(module_path)
                except ModuleNotFoundError:
                    # Try alternate structure (routes.py file)
                    routes_file = domain_dir / "routes.py"
                    if not routes_file.exists():
                        error_msg = f"No routes module found for domain: {domain_name}"
                        if fail_fast:
                            raise RouteRegistryError(error_msg)
                        logger.warning(error_msg)
                        continue
                    
                    module_path = f"domain.{domain_name}.routes"
                    module = importlib.import_module(module_path)
                
                # Look for router object
                if not hasattr(module, 'router'):
                    error_msg = f"No 'router' object found in {module_path}"
                    if fail_fast:
                        raise RouteRegistryError(error_msg)
                    errors.append(error_msg)
                    continue
                
                router = module.router
                prefix = f"/api/v1/{domain_name.replace('_', '-')}"
                
                self.register_domain(
                    domain=domain_name,
                    router=router,
                    prefix=prefix,
                    tags=[domain_name]
                )
                
                discovered_count += 1
                
            except Exception as e:
                error_msg = f"Failed to load routes for domain {domain_name}: {str(e)}"
                if fail_fast:
                    raise RouteRegistryError(error_msg, details={"domain": domain_name, "error": str(e)})
                errors.append(error_msg)
                logger.error(error_msg, domain=domain_name)
        
        logger.info(
            "Route discovery complete",
            discovered=discovered_count,
            errors=len(errors)
        )
        
        if errors and not fail_fast:
            logger.warning("Route discovery had errors", errors=errors)
    
    def validate_all_routes(self) -> Dict[str, List[str]]:
        """
        Validate all registered routes.
        
        Returns:
            Dictionary mapping domain to list of validation issues
        """
        issues_by_domain: Dict[str, List[str]] = {}
        
        for domain_name, domain_routes in self.domains.items():
            domain_issues = []
            
            for route in domain_routes.routes:
                domain_issues.extend(self.validator.validate_route_documentation(route))
                domain_issues.extend(self.validator.validate_route_naming(route))
                # domain_issues.extend(self.validator.validate_error_handling(route))
            
            if domain_issues:
                issues_by_domain[domain_name] = domain_issues
        
        return issues_by_domain
    
    def get_route_listing(self) -> List[Dict[str, Any]]:
        """Get listing of all routes for introspection."""
        return [
            {
                "domain": domain_name,
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "tags": route.tags,
                "description": route.description
            }
            for domain_name, domain_routes in self.domains.items()
            for route in domain_routes.routes
        ]
    
    def get_domain_routes(self, domain: str) -> Optional[DomainRoutes]:
        """Get routes for a specific domain."""
        return self.domains.get(domain)


# Global registry instance
_registry: Optional[RouteRegistry] = None


def get_registry(app: Optional[FastAPI] = None) -> RouteRegistry:
    """Get the global route registry."""
    global _registry
    if _registry is None:
        _registry = RouteRegistry(app)
    elif app is not None and _registry.app is None:
        _registry.app = app
    return _registry
