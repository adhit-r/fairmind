# Service Migration Guide

## Overview

This guide shows how to migrate existing services to use the new `BaseService` class.

**Benefits**:
- Consistent logging across all services
- Standardized error handling
- Built-in validation helpers
- Dependency injection support
- Lifecycle management

---

## Step-by-Step Migration

### 1. Add Imports

```python
from core.base_service import BaseService
from core.container import service, ServiceLifetime
from core.exceptions import ValidationError, InvalidDataError
from core.interfaces import ILogger
```

### 2. Update Class Declaration

**Before**:
```python
class MyService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
```

**After**:
```python
@service(lifetime=ServiceLifetime.SINGLETON)  # or TRANSIENT
class MyService(BaseService):
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        # Your initialization
```

### 3. Replace Logging

**Before**:
```python
logger.info(f"Processing request")
logger.error(f"Error occurred: {str(e)}")
```

**After**:
```python
self._log_operation("process_request", user_id=123)
self._log_error("process_request", e, user_id=123)
```

### 4. Add Validation

**Before**:
```python
if not param1:
    raise Exception("param1 is required")
if not isinstance(param2, str):
    raise Exception("param2 must be string")
```

**After**:
```python
self._validate_required(param1=param1)
self._validate_type('param2', param2, str)
```

### 5. Update Error Handling

**Before**:
```python
try:
    # operation
except Exception as e:
    logger.error(f"Failed: {e}")
    raise
```

**After**:
```python
try:
    # operation
except Exception as e:
    self._handle_error(
        "operation_name",
        e,
        raise_as=InvalidDataError,  # Re-raise as domain exception
        context_key="value"
    )
```

### 6. Create Domain Models

**Before** (returning dicts):
```python
def get_data(self) -> dict:
    return {
        "id": "123",
        "name": "Test",
        "value": 42
    }
```

**After** (returning domain objects):
```python
@dataclass
class DataResult:
    id: str
    name: str
    value: int

def get_data(self) -> DataResult:
    return DataResult(
        id="123",
        name="Test",
        value=42
    )
```

### 7. Remove HTTP Logic

Services should only contain business logic. Move HTTP concerns to routes.

**Before** (service returns HTTP response):
```python
def create_item(self, data: dict):
    # ... logic ...
    return JSONResponse(
        status_code=201,
        content={"id": item_id}
    )
```

**After** (service returns domain object, route handles HTTP):
```python
# In service:
def create_item(self, data: dict) -> Item:
    # ... logic ...
    return Item(id=item_id, ...)

# In route:
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_item(request: ItemRequest, service=Depends(get_service)):
    item = service.create_item(request.dict())
    return ItemResponse.from_domain(item)
```

---

## Example: Complete Migration

### Old Service

```python
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.users = {}
    
    def create_user(self, name: str, email: str) -> dict:
        if not name:
            raise ValueError("Name required")
        if not email:
            raise ValueError("Email required")
        
        user_id = len(self.users) + 1
        self.users[user_id] = {"name": name, "email": email}
        
        logger.info(f"User created: {user_id}")
        
        return {"id": user_id, "name": name, "email": email}
```

### New Service

```python
from dataclasses import dataclass
from typing import Optional

from core.base_service import BaseService
from core.container import service, ServiceLifetime
from core.exceptions import ValidationError
from core.interfaces import ILogger


@dataclass
class User:
    """Domain model for User."""
    id: int
    name: str
    email: str


@service(lifetime=ServiceLifetime.SINGLETON)
class UserService(BaseService):
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)
        self.users = {}
    
    def create_user(self, name: str, email: str) -> User:
        # Use built-in validation
        self._validate_required(name=name, email=email)
        
        user_id = len(self.users) + 1
        user = User(id=user_id, name=name, email=email)
        self.users[user_id] = user
        
        # Use structured logging
        self._log_operation(
            "create_user",
            user_id=user_id,
            name=name
        )
        
        return user  # Return domain object
```

---

## Migration Checklist

For each service, complete these steps:

- [ ] Add `BaseService` imports
- [ ] Add `@service` decorator
- [ ] Update `__init__` to accept `ILogger`
- [ ] Call `super().__init__(logger)`
- [ ] Replace `logger.*` with `self._log_*`
- [ ] Create domain models (dataclasses)
- [ ] Update return types to domain objects
- [ ] Replace generic exceptions with `ValidationError`/`InvalidDataError`
- [ ] Use `_validate_required()` and `_validate_type()`
- [ ] Use `_handle_error()` for error handling
- [ ] Remove HTTP response logic
- [ ] Move service to `domain/*/services/`
- [ ] Update route imports
- [ ] Test service in isolation

---

## Common Patterns

### Pattern 1: Database Operations

```python
def get_item(self, item_id: str) -> Item:
    self._validate_required(item_id=item_id)
    
    try:
        # Database query
        result = self.db.query(Item).get(item_id)
        
        if not result:
            raise NotFoundError("Item", item_id)
        
        self._log_operation("get_item", item_id=item_id)
        return result
    
    except Exception as e:
        self._handle_error("get_item", e, item_id=item_id)
```

### Pattern 2: External API Calls

```python
def fetch_data(self, api_key: str) -> DataResult:
    self._validate_required(api_key=api_key)
    
    try:
        response = requests.get(url, headers={"Authorization": api_key})
        response.raise_for_status()
        
        self._log_operation("fetch_data", status=response.status_code)
        return DataResult.from_api(response.json())
    
    except requests.RequestException as e:
        self._handle_error(
            "fetch_data",
            e,
            raise_as=ExternalServiceError
        )
```

### Pattern 3: Async Operations

```python
from core.base_service import AsyncBaseService

@service(lifetime=ServiceLifetime.SINGLETON)
class AsyncDataService(AsyncBaseService):
    async def process_data(self, data: dict) -> ProcessResult:
        self._validate_required(data=data)
        
        try:
            result = await self._process_async(data)
            self._log_operation("process_data", size=len(data))
            return result
        
        except Exception as e:
            self._handle_error("process_data", e)
```

---

## Testing Services

Services are now easy to test because of DI:

```python
import pytest
from core.base_service import BaseService

def test_user_service():
    # Create service without DI for testing
    service = UserService()
    
    # Test
    user = service.create_user("Alice", "alice@example.com")
    
    assert user.id is not None
    assert user.name == "Alice"
    assert user.email == "alice@example.com"

def test_validation():
    service = UserService()
    
    with pytest.raises(ValidationError):
        service.create_user("", "alice@example.com")
```

---

## Next Steps

1. Start with simple services (fewer dependencies)
2. Migrate one domain at a time
3. Test each migrated service
4. Update routes to use migrated services
5. Remove old service files after migration

**Recommended Order**:
1. Auth services (foundational)
2. Dataset services (simple)
3. Bias detection services
4. Compliance services
5. MLOps services
