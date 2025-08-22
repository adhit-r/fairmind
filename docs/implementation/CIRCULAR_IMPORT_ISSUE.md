# GitHub Issue: Fix circular import in AI BOM models

## Bug Description

There's a circular import issue in the AI BOM models where `DataLayer` and other layer models are trying to reference `AIBOMComponent` before it's defined.

## Error Details
```
NameError: name 'AIBOMComponent' is not defined
```

## Location
- File: `backend/api/models/ai_bom.py`
- Line: 38 in `DataLayer` class

## Expected Behavior
Layer models should be able to reference `AIBOMComponent` without circular import issues.

## Proposed Solution
1. Reorder the class definitions to define `AIBOMComponent` before the layer models
2. Or use forward references with `List['AIBOMComponent']` syntax
3. Or create separate model files to avoid circular dependencies

## Priority
High - This blocks testing and deployment of the AI BOM service

## Labels
- bug
- ai-bom
- models
- high-priority

## Steps to Reproduce
1. Navigate to backend directory
2. Run: `python -c "from api.services.ai_bom_db_service import create_ai_bom_service"`
3. Observe the NameError

## Status
- [x] Issue created
- [x] Code fix implemented
- [x] Tests passing
- [x] Issue resolved

## Resolution
Fixed by using forward references with `List['AIBOMComponent']` syntax and adding `TYPE_CHECKING` import to avoid circular dependencies.
