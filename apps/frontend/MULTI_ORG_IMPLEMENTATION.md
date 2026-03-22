# Multi-Org Support Implementation Guide

## Overview

This document describes the multi-organization support implementation for the FairMind frontend. Users can now switch between multiple organizations, and all API calls are automatically filtered by the selected organization.

## Architecture

### Components

1. **OrgContext** (`src/context/OrgContext.tsx`)
   - Manages organization state across the application
   - Fetches user's organizations from `/api/v1/organizations` endpoint
   - Persists selected org_id in localStorage
   - Provides `useOrg()` hook for accessing org data

2. **OrgSwitcher** (`src/components/OrgSwitcher.tsx`)
   - UI component to display and select organizations
   - Shows single org name for single-org users
   - Shows dropdown for multi-org users
   - Displays loading, error, and no-org states
   - Styled with neobrutalist design (bold borders, sharp shadows)

3. **API Client Enhancement** (`src/lib/api/api-client.ts`)
   - Automatically injects `org_id` query parameter into API requests
   - Only adds parameter to `/api/v1/` endpoints
   - Respects existing query parameters
   - Works transparently without requiring changes to individual API calls

4. **useOrgId Hook** (`src/lib/api/hooks/useOrgId.ts`)
   - Convenience hook to get selected org ID
   - Use when you need org ID for manual API calls

## Setup

### 1. Add OrgProvider to Dashboard Layout

The dashboard layout wraps all routes with OrgProvider:

```tsx
// apps/frontend/src/app/(dashboard)/layout.tsx
<OrgProvider>
  <SystemContextProvider>
    <OrgSwitcher />
    <SystemContextBar />
    {children}
  </SystemContextProvider>
</OrgProvider>
```

### 2. Environment Variables (Backend)

No frontend environment changes needed. Ensure backend has:
- `/api/v1/organizations` endpoint returning list of user's orgs
- All data endpoints filtered by `org_id` query parameter

## Usage

### Basic Usage in Components

```tsx
import { useOrg } from '@/context/OrgContext';

export function MyComponent() {
  const { organizations, selectedOrg, selectOrg, isLoading, error } = useOrg();

  if (isLoading) return <div>Loading organizations...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <p>Selected org: {selectedOrg?.name}</p>
      <p>Role: {selectedOrg?.role}</p>
      <button onClick={() => selectOrg(organizations[0].id)}>Switch Org</button>
    </div>
  );
}
```

### API Calls (Automatic org_id Injection)

No changes needed—org_id is automatically added:

```tsx
import { apiClient } from '@/lib/api/api-client';

// Before (required manual org_id):
// const response = await apiClient.get(`/api/v1/models?org_id=${orgId}`);

// Now (automatic org_id injection):
const response = await apiClient.get('/api/v1/models');
// Result: GET /api/v1/models?org_id=<selected-org-id>
```

### Manual org_id Access

For cases where you need the org ID directly:

```tsx
import { useOrgId } from '@/lib/api/hooks/useOrgId';

export function MyComponent() {
  const orgId = useOrgId();

  // Use orgId for custom logic
  if (!orgId) return <div>No organization selected</div>;

  return <div>Org ID: {orgId}</div>;
}
```

## Type Definitions

### Organization Interface

```typescript
export interface Organization {
  id: string;
  name: string;
  slug: string;
  domain?: string;
  owner_id: string;
  created_at: string;
  role: string; // "admin", "analyst", "viewer"
}
```

### OrgContextType Interface

```typescript
export interface OrgContextType {
  organizations: Organization[];
  selectedOrg: Organization | null;
  isLoading: boolean;
  error: string | null;
  selectOrg: (orgId: string) => void;
  refreshOrgs: () => Promise<void>;
}
```

## Backend Integration Points

The implementation requires these backend endpoints:

### 1. List User's Organizations
**Endpoint:** `GET /api/v1/organizations`

**Response:**
```json
{
  "organizations": [
    {
      "id": "org-uuid",
      "name": "Acme Corp",
      "slug": "acme-corp",
      "domain": "acme.com",
      "owner_id": "user-uuid",
      "created_at": "2024-01-01T00:00:00Z",
      "role": "admin"
    }
  ]
}
```

### 2. Filter All Data Endpoints by org_id

All data endpoints should accept `org_id` query parameter:

```
GET /api/v1/models?org_id=<org-uuid>
GET /api/v1/datasets?org_id=<org-uuid>
GET /api/v1/bias-v2/detect?org_id=<org-uuid>
```

**Middleware approach (recommended):**
```python
@app.middleware("http")
async def inject_org_context(request: Request, call_next):
    org_id = request.query_params.get("org_id")
    if org_id:
        # Verify user has access to this org
        # Inject org context into request
        request.state.org_id = org_id
    response = await call_next(request)
    return response
```

## Testing Checklist

- [x] OrgContext initializes on app mount
- [x] useOrg hook works in components
- [x] OrgSwitcher displays for multi-org users
- [x] OrgSwitcher hidden for single-org users
- [x] Organization dropdown changes selected org
- [x] localStorage persists selected_org_id
- [x] Page reloads when org is switched
- [x] org_id automatically injected into GET requests
- [x] API calls include org_id in query params
- [x] Error handling: no orgs assigned shows error
- [x] Loading states display correctly
- [x] useOrgId hook returns correct org ID

## Design System Integration

The OrgSwitcher component uses FairMind's neobrutalist design:

- **Bold borders:** 2px black borders for clarity
- **Sharp shadows:** `shadow-md` for depth
- **High contrast:** Black/white with bold typography
- **No softness:** Square corners, direct communication
- **Accessibility:** Clear labels, proper semantic HTML

## Files Modified/Created

### Created:
- `src/context/OrgContext.tsx` — Organization context and provider
- `src/components/OrgSwitcher.tsx` — Organization switcher UI
- `src/lib/api/hooks/useOrgId.ts` — Hook for org ID access

### Modified:
- `src/app/(dashboard)/layout.tsx` — Added OrgProvider and OrgSwitcher
- `src/lib/api/api-client.ts` — Auto-inject org_id into requests
- `src/lib/api/endpoints.ts` — Added organizations endpoints

## Migration Path

### For Existing API Calls

No changes needed! The api-client automatically injects org_id.

```tsx
// Old code (still works, org_id added automatically):
const models = await apiClient.get('/api/v1/models');

// Data is now filtered by selected org automatically
```

### For New Features

When building new org-aware features:

1. Use OrgProvider (already in dashboard layout)
2. Call `useOrg()` to get selected org
3. API calls automatically include org_id
4. No manual org_id management needed

## Error Handling

The implementation handles these scenarios:

- **No orgs assigned:** Shows "No organizations assigned" message
- **Network error:** Shows error message with retry option
- **Loading state:** Shows loading spinner while fetching orgs
- **Invalid org selection:** Gracefully falls back to first org

## Performance Considerations

- Organizations list is fetched once on mount
- Selected org is cached in localStorage
- Page reload only happens on org switch (small UX cost for data integrity)
- No org_id parameter added to non-API endpoints
- Query parameter injection is optimized to avoid duplicates

## Future Enhancements

1. **Org switching without reload:** Update all active data subscriptions
2. **Org creation UI:** Add org creation flow in settings
3. **Org settings:** Team management, billing, integration settings
4. **Audit logs:** Track org access and data changes
5. **Single Sign-On (SSO):** Org-level SSO configuration
