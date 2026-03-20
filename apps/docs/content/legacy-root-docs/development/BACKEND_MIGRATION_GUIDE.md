# Backend Architecture Migration Guide

## Overview

This guide details the migration from the legacy backend architecture to the new domain-driven design. The new architecture emphasizes modularity, dependency injection, and centralized route management.

## Architecture Changes

### 1. Directory Structure

**Old Structure:**
```
apps/backend/
├── api/
│   ├── routes/       # All routes mixed together
│   └── services/     # All services mixed together
```

**New Structure:**
```
apps/backend/
├── core/             # Core infrastructure (DI, Exceptions, Logging)
├── domain/           # Domain-driven modules
│   ├── bias_detection/
│   ├── compliance/
│   ├── monitoring/
│   └── mlops/
├── infrastructure/   # Database, Cache, External services
└── api/              # API layer (Registry, Versioning)
```

### 2. Key Components

- **Service Container**: Dependency injection container for managing service lifecycles.
- **Route Registry**: Centralized route discovery and registration.
- **Base Service**: Common base class for all domain services.
- **API Versioning**: Robust versioning system with deprecation support.

## Migration Steps for New Domains

To migrate a new domain (e.g., `auth`), follow these steps:

### Step 1: Create Domain Structure

Create the directory structure in `apps/backend/domain/<domain_name>/`:
```
domain/<domain_name>/
├── __init__.py
├── routes/
│   ├── __init__.py
│   └── <domain>_routes.py
└── services/
    ├── __init__.py
    └── <domain>_service.py
```

### Step 2: Implement Service

Inherit from `AsyncBaseService` and use dependency injection:

```python
from core.base_service import AsyncBaseService
from core.container import service, ServiceLifetime

@service(lifetime=ServiceLifetime.SINGLETON)
class MyService(AsyncBaseService):
    async def do_something(self):
        self._log_operation("doing_something")
        # ... logic ...
```

### Step 3: Implement Routes

Create routes using `APIRouter` and inject services:

```python
from fastapi import APIRouter, Depends
from core.container import inject
from .services.my_service import MyService

router = APIRouter()

@router.get("/")
async def get_item(
    service: MyService = Depends(inject(MyService))
):
    return await service.do_something()
```

### Step 4: Export Router

Ensure the router is exported in `domain/<domain_name>/routes/__init__.py`:

```python
from .<domain>_routes import router

__all__ = ["router"]
```

The `RouteRegistry` will automatically discover and register these routes on startup.

## Legacy Code

Legacy code has been moved to `apps/backend/_legacy_backup/`. Do not modify files in this directory; they are for reference only.

## Testing

- New tests should be placed in `apps/backend/tests/`.
- Use `conftest.py` fixtures for `ServiceContainer` and `RouteRegistry`.
