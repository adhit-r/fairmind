# Backend Architecture Refactoring - Design Document

## Overview

This design document outlines the technical approach to refactor the FairMind backend architecture. The refactoring will establish clear separation of concerns, implement proper dependency injection, organize routes systematically, and ensure robust error handling and configuration management.

The refactored architecture will provide a solid foundation for scalability, testability, and maintainability while maintaining backward compatibility with existing API clients.

## Architecture

### Current State (Problems)
```
FastAPI Application
├── 30+ Route Modules (scattered, no organization)
│   ├── auth.py (authentication)
│   ├── bias_detection.py (bias detection)
│   ├── compliance_reporting.py (compliance)
│   ├── ... (many more)
│   └── Silent failures on import errors
├── Services (tightly coupled to routes)
├── Database (direct connections, no pooling)
├── Configuration (scattered across files)
└── Middleware (inconsistent ordering)
```

### Target State (Solution)
```
FastAPI Application
├── Route Registry (centralized, validated)
│   ├── routes/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── bias_detection/
│   │   ├── compliance/
│   │   ├── monitoring/
│   │   └── registry.py (validates all routes)
├── Services (dependency injected)
│   ├── service_container.py (DI container)
│   ├── auth_service.py
│   ├── bias_detection_service.py
│   └── ...
├── Database (connection pooling)
│   ├── connection_pool.py
│   ├── models.py
│   └── migrations/
├── Configuration (centralized)
│   ├── settings.py (validated)
│   ├── environments/
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
└── Middleware (ordered pipeline)
    ├── cors.py
    ├── security_headers.py
    ├── authentication.py
    ├── logging.py
    └── error_handling.py
```

## Components and Interfaces

### 1. Route Registry System

**Purpose**: Centralized registration and validation of all API routes

**Components**:
- `RouteRegistry` class - Manages route registration
- `RouteValidator` class - Validates route configuration
- `RouteLoader` class - Dynamically loads route modules

**Interface**:
```python
class RouteRegistry:
    def register_route(self, domain: str, router: APIRouter) -> None
    def validate_all_routes(self) -> List[ValidationError]
    def get_registered_routes(self) -> List[RouteInfo]
    def get_route_by_path(self, path: str) -> Optional[RouteInfo]
```

**Key Features**:
- Automatic discovery of route modules
- Validation of route documentation
- Error handling with detailed messages
- Route listing endpoint for debugging

### 2. Dependency Injection Container

**Purpose**: Manage service instantiation and dependency resolution

**Components**:
- `ServiceContainer` class - DI container
- `ServiceProvider` class - Provides services to routes
- `Dependency` decorator - Marks injectable dependencies

**Interface**:
```python
class ServiceContainer:
    def register(self, service_type: Type, factory: Callable) -> None
    def resolve(self, service_type: Type) -> Any
    def get_provider(self) -> ServiceProvider
    def validate_dependencies(self) -> List[str]
```

**Key Features**:
- Type-based dependency resolution
- Singleton and transient lifetimes
- Circular dependency detection
- Mock injection for testing

### 3. Configuration Management

**Purpose**: Centralized, validated configuration with environment support

**Components**:
- `Settings` class - Base configuration
- `EnvironmentSettings` - Environment-specific settings
- `ConfigValidator` - Validates configuration

**Interface**:
```python
class Settings:
    database_url: str
    redis_url: str
    jwt_secret: str
    environment: str
    debug: bool
    
    @classmethod
    def from_env(cls) -> Settings
    def validate(self) -> List[str]
```

**Key Features**:
- Environment variable loading
- Type validation with Pydantic
- Default values with overrides
- Sensitive data masking in logs

### 4. Error Handling System

**Purpose**: Consistent error handling and logging across all endpoints

**Components**:
- `AppException` - Base exception class
- `ErrorHandler` - Middleware for error handling
- `ErrorFormatter` - Formats errors for API responses
- `ErrorLogger` - Logs errors with context

**Interface**:
```python
class AppException(Exception):
    status_code: int
    error_code: str
    message: str
    details: Optional[Dict]

class ErrorHandler:
    async def __call__(self, request: Request, exc: Exception) -> JSONResponse
```

**Key Features**:
- Structured error responses
- Request context in logs
- Sensitive data sanitization
- Error tracking integration

### 5. Health Check System

**Purpose**: Monitor application and dependency health

**Components**:
- `HealthChecker` - Checks application health
- `DependencyChecker` - Checks external dependencies
- `HealthEndpoint` - Exposes health status

**Interface**:
```python
class HealthChecker:
    async def check_health(self) -> HealthStatus
    async def check_readiness(self) -> ReadinessStatus
    async def check_liveness(self) -> LivenessStatus

class HealthStatus:
    status: str  # "healthy" or "unhealthy"
    checks: Dict[str, CheckResult]
    timestamp: datetime
```

**Key Features**:
- Database connectivity check
- Cache connectivity check
- External service checks
- Kubernetes probe support

### 6. Middleware Pipeline

**Purpose**: Process requests/responses in defined order

**Components**:
- `MiddlewarePipeline` - Manages middleware ordering
- Individual middleware classes

**Execution Order**:
1. CORS Middleware
2. Security Headers Middleware
3. Request Logging Middleware
4. Authentication Middleware
5. Rate Limiting Middleware
6. Error Handling Middleware

**Interface**:
```python
class Middleware:
    async def __call__(self, request: Request, call_next) -> Response
    def get_priority(self) -> int
```

### 7. Service Layer

**Purpose**: Encapsulate business logic independent of HTTP

**Components**:
- Base `Service` class
- Domain-specific services (AuthService, BiasDetectionService, etc.)
- Service interfaces

**Interface**:
```python
class Service:
    def __init__(self, dependencies: ServiceContainer)
    async def execute(self, *args, **kwargs) -> Result

class AuthService(Service):
    async def authenticate(self, username: str, password: str) -> User
    async def create_token(self, user: User) -> Token
    async def verify_token(self, token: str) -> User
```

**Key Features**:
- Dependency injection
- Domain-specific exceptions
- Testable without HTTP context
- Reusable across endpoints

### 8. Database Connection Management

**Purpose**: Manage database connections with pooling and health checks

**Components**:
- `ConnectionPool` - Manages connection pooling
- `DatabaseManager` - Handles connections
- `Migration` - Database schema management

**Interface**:
```python
class ConnectionPool:
    async def get_connection(self) -> Connection
    async def release_connection(self, conn: Connection) -> None
    async def health_check(self) -> bool
    async def close_all(self) -> None

class DatabaseManager:
    async def execute(self, query: str, params: Dict) -> Result
    async def transaction(self) -> Transaction
```

**Key Features**:
- Connection pooling
- Automatic retry with backoff
- Health checks
- Transaction support

### 9. API Versioning

**Purpose**: Support multiple API versions with clear migration paths

**Components**:
- `APIVersion` - Version identifier
- `VersionedRouter` - Routes for specific versions
- `VersionMigration` - Migration helpers

**Interface**:
```python
class APIVersion:
    major: int
    minor: int
    status: str  # "stable", "beta", "deprecated"
    deprecation_date: Optional[datetime]

class VersionedRouter:
    def add_route(self, path: str, handler: Callable, version: APIVersion)
    def get_routes_for_version(self, version: APIVersion) -> List[Route]
```

**Key Features**:
- Multiple version support
- Deprecation warnings
- Migration helpers
- Version-specific error handling

## Data Models

### Configuration Model
```python
@dataclass
class Settings:
    # Database
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Cache
    redis_url: Optional[str] = None
    cache_ttl: int = 3600
    
    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    
    # Environment
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # API
    api_title: str = "FairMind API"
    api_version: str = "1.0.0"
    rate_limit_requests: int = 100
```

### Route Information Model
```python
@dataclass
class RouteInfo:
    path: str
    methods: List[str]
    domain: str
    description: str
    tags: List[str]
    requires_auth: bool
    rate_limit: Optional[int]
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None
```

### Health Status Model
```python
@dataclass
class CheckResult:
    name: str
    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    timestamp: datetime

@dataclass
class HealthStatus:
    status: str
    checks: Dict[str, CheckResult]
    timestamp: datetime
    version: str
```

### Error Response Model
```python
@dataclass
class ErrorResponse:
    error_code: str
    message: str
    status_code: int
    timestamp: datetime
    request_id: str
    details: Optional[Dict] = None
    trace_id: Optional[str] = None
```

## Error Handling

### Error Hierarchy
```
AppException (base)
├── ValidationError
├── AuthenticationError
├── AuthorizationError
├── NotFoundError
├── ConflictError
├── RateLimitError
├── ExternalServiceError
└── InternalServerError
```

### Error Handling Flow
1. Exception occurs in route handler or service
2. Exception is caught by error handling middleware
3. Exception is logged with request context
4. Exception is formatted as JSON response
5. Response is returned to client

### Logging Strategy
- **INFO**: Normal operations, route access
- **WARNING**: Recoverable errors, retries
- **ERROR**: Unrecoverable errors, failures
- **DEBUG**: Detailed execution flow, variable values

## Testing Strategy

### Unit Testing
- Test each service independently
- Mock external dependencies
- Test error conditions
- Test configuration validation

### Integration Testing
- Test route handlers with real services
- Test database operations
- Test middleware pipeline
- Test error handling

### Property-Based Testing
- Test route registry validation
- Test configuration loading
- Test dependency resolution
- Test error formatting

### Test Coverage Targets
- Services: 90%+
- Routes: 80%+
- Middleware: 85%+
- Overall: 80%+

## Performance Considerations

### Optimization Strategies
1. **Connection Pooling** - Reuse database connections
2. **Caching** - Cache frequently accessed data
3. **Async/Await** - Non-blocking I/O operations
4. **Lazy Loading** - Load modules on demand
5. **Compression** - Compress API responses

### Monitoring Metrics
- Request latency (p50, p95, p99)
- Error rate
- Database query time
- Cache hit rate
- Connection pool utilization

## Security Considerations

### Authentication & Authorization
- JWT token validation on protected routes
- Role-based access control (RBAC)
- Token refresh mechanism
- Secure token storage

### Input Validation
- Validate all request data
- Sanitize user inputs
- Prevent SQL injection
- Prevent XSS attacks

### Error Handling
- Don't expose sensitive information in errors
- Log errors securely
- Track security events
- Alert on suspicious activity

## Deployment Considerations

### Environment Configuration
- Development: Debug enabled, mock services
- Staging: Production-like, real services
- Production: Debug disabled, security hardened

### Health Checks
- Kubernetes readiness probe: `/health/ready`
- Kubernetes liveness probe: `/health/live`
- Simple health check: `/health`

### Graceful Shutdown
- Stop accepting new requests
- Wait for in-flight requests to complete
- Close database connections
- Flush logs

## Migration Path

### Phase 1: Preparation
1. Create new architecture modules
2. Implement route registry
3. Implement DI container
4. Write tests for new components

### Phase 2: Gradual Migration
1. Migrate routes one domain at a time
2. Migrate services to use DI
3. Update configuration management
4. Update error handling

### Phase 3: Cleanup
1. Remove old route loading code
2. Remove old configuration code
3. Remove old error handling code
4. Update documentation

### Phase 4: Validation
1. Run full test suite
2. Performance testing
3. Security review
4. Production deployment

## Backward Compatibility

### API Compatibility
- Maintain existing endpoint paths
- Support old API versions
- Provide migration helpers
- Deprecation warnings in headers

### Configuration Compatibility
- Support old environment variables
- Provide migration guide
- Gradual deprecation period
- Clear error messages

