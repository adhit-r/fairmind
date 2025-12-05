# Frontend API Client and State Management - Design Document

## Overview

This design document outlines the technical approach to implement a centralized API client layer and state management system for the FairMind frontend. The implementation will provide a single source of truth for application state, consistent API communication patterns, and improved user experience through proper loading and error states.

The refactored frontend will eliminate prop drilling, reduce code duplication, and make the application easier to test and maintain.

## Architecture

### Current State (Problems)
```
React Components
├── Direct fetch() calls scattered throughout
├── Prop drilling (passing data through multiple levels)
├── Inconsistent error handling
├── No loading states
├── No caching
├── Hardcoded API URLs
└── No state management
```

### Target State (Solution)
```
React Application
├── API Client Layer
│   ├── api/client.ts (centralized HTTP client)
│   ├── api/endpoints.ts (endpoint definitions)
│   ├── api/cache.ts (response caching)
│   └── api/interceptors.ts (request/response processing)
├── State Management
│   ├── store/
│   │   ├── auth.store.ts
│   │   ├── bias-detection.store.ts
│   │   ├── compliance.store.ts
│   │   └── root.store.ts
│   └── hooks/
│       ├── useApi.ts (data fetching)
│       ├── useMutation.ts (data mutation)
│       ├── useForm.ts (form handling)
│       └── useStore.ts (state access)
├── Components (simplified)
│   ├── Use hooks instead of direct API calls
│   ├── Receive data from store
│   └── Dispatch actions for mutations
└── Types
    ├── api.types.ts
    ├── store.types.ts
    └── domain.types.ts
```

## Components and Interfaces

### 1. API Client Layer

**Purpose**: Centralized HTTP communication with the backend

**Components**:
- `APIClient` class - Main HTTP client
- `RequestInterceptor` - Processes requests
- `ResponseInterceptor` - Processes responses
- `ErrorHandler` - Handles API errors

**Interface**:
```typescript
class APIClient {
  constructor(baseURL: string, config?: ClientConfig)
  
  async get<T>(path: string, options?: RequestOptions): Promise<T>
  async post<T>(path: string, data: any, options?: RequestOptions): Promise<T>
  async put<T>(path: string, data: any, options?: RequestOptions): Promise<T>
  async delete<T>(path: string, options?: RequestOptions): Promise<T>
  
  setAuthToken(token: string): void
  clearAuthToken(): void
  setBaseURL(url: string): void
}

interface RequestOptions {
  headers?: Record<string, string>
  params?: Record<string, any>
  timeout?: number
  cache?: boolean
  cacheTTL?: number
}
```

**Key Features**:
- Automatic authentication header injection
- Request/response interceptors
- Error handling and formatting
- Request deduplication
- Response caching
- Timeout handling
- Retry logic with exponential backoff

### 2. State Management Store

**Purpose**: Centralized application state with predictable updates

**Components**:
- `Store` class - Root store
- Domain stores (AuthStore, BiasDetectionStore, etc.)
- Actions - State mutations
- Selectors - State queries

**Interface**:
```typescript
interface Store {
  auth: AuthStore
  biasDetection: BiasDetectionStore
  compliance: ComplianceStore
  monitoring: MonitoringStore
  
  subscribe(listener: () => void): () => void
  getState(): RootState
  dispatch(action: Action): void
}

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: Error | null
  
  login(username: string, password: string): Promise<void>
  logout(): void
  refreshToken(): Promise<void>
}
```

**Key Features**:
- Centralized state container
- Predictable state updates
- Time-travel debugging
- Middleware support
- Persistence support

### 3. Custom Hooks

**Purpose**: Encapsulate common patterns for data fetching and mutations

**Components**:
- `useApi` hook - Data fetching
- `useMutation` hook - Data mutation
- `useForm` hook - Form handling
- `useStore` hook - State access

**Interface**:
```typescript
function useApi<T>(
  endpoint: string,
  options?: UseApiOptions
): UseApiResult<T>

interface UseApiResult<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

function useMutation<T, R>(
  mutationFn: (data: T) => Promise<R>,
  options?: UseMutationOptions
): UseMutationResult<T, R>

interface UseMutationResult<T, R> {
  mutate: (data: T) => Promise<R>
  isLoading: boolean
  error: Error | null
  data: R | null
}

function useForm<T>(
  initialValues: T,
  onSubmit: (values: T) => Promise<void>,
  options?: UseFormOptions
): UseFormResult<T>

interface UseFormResult<T> {
  values: T
  errors: Record<string, string>
  touched: Record<string, boolean>
  isSubmitting: boolean
  handleChange: (e: ChangeEvent) => void
  handleBlur: (e: FocusEvent) => void
  handleSubmit: (e: FormEvent) => Promise<void>
  setFieldValue: (field: string, value: any) => void
}
```

**Key Features**:
- Automatic loading/error state management
- Caching support
- Retry logic
- Optimistic updates
- Form validation
- Error handling

### 4. Caching System

**Purpose**: Reduce network requests and improve performance

**Components**:
- `CacheManager` - Manages cache entries
- `CacheStrategy` - Cache invalidation strategies
- `CacheStorage` - In-memory cache storage

**Interface**:
```typescript
class CacheManager {
  set<T>(key: string, value: T, ttl?: number): void
  get<T>(key: string): T | null
  has(key: string): boolean
  delete(key: string): void
  clear(): void
  invalidate(pattern: string): void
  
  getStats(): CacheStats
}

interface CacheStats {
  size: number
  hits: number
  misses: number
  hitRate: number
}
```

**Key Features**:
- TTL-based expiration
- Pattern-based invalidation
- Cache statistics
- Memory management
- Stale-while-revalidate support

### 5. Error Handling

**Purpose**: Consistent error handling and user feedback

**Components**:
- `APIError` class - API error wrapper
- `ErrorFormatter` - Formats errors for display
- `ErrorBoundary` - React error boundary

**Interface**:
```typescript
class APIError extends Error {
  status: number
  code: string
  details?: Record<string, any>
  
  isClientError(): boolean
  isServerError(): boolean
  isNetworkError(): boolean
}

function formatError(error: APIError): FormattedError {
  return {
    title: string
    message: string
    actions: ErrorAction[]
  }
}

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error) => void
}
```

**Key Features**:
- Structured error objects
- User-friendly error messages
- Error recovery actions
- Error logging
- Error boundaries

### 6. Type Safety

**Purpose**: Ensure type safety across API calls and state

**Components**:
- Type definitions for API endpoints
- Type definitions for state
- Type definitions for components

**Interface**:
```typescript
// API Types
interface BiasDetectionRequest {
  modelId: string
  datasetId: string
  testTypes: string[]
  parameters?: Record<string, any>
}

interface BiasDetectionResponse {
  testId: string
  status: "pending" | "running" | "completed" | "failed"
  results: BiasTestResult[]
  timestamp: string
}

// State Types
interface BiasDetectionState {
  tests: BiasTest[]
  currentTest: BiasTest | null
  isLoading: boolean
  error: Error | null
}

// Component Props
interface BiasDetectionComponentProps {
  onTestComplete?: (result: BiasTestResult) => void
  showAdvancedOptions?: boolean
}
```

**Key Features**:
- Full TypeScript support
- Auto-generated types from OpenAPI
- Type-safe API calls
- Type-safe state access
- Type-safe component props

### 7. Request Deduplication

**Purpose**: Prevent duplicate requests for the same data

**Components**:
- `RequestDeduplicator` - Deduplicates requests
- `RequestCache` - Caches in-flight requests

**Interface**:
```typescript
class RequestDeduplicator {
  async execute<T>(
    key: string,
    fn: () => Promise<T>
  ): Promise<T>
  
  clear(pattern?: string): void
}
```

**Key Features**:
- Automatic deduplication
- In-flight request caching
- Pattern-based clearing
- Configurable timeout

### 8. Offline Support

**Purpose**: Allow offline usage with sync when connection restored

**Components**:
- `OfflineManager` - Manages offline state
- `SyncQueue` - Queues actions for sync
- `ConflictResolver` - Resolves sync conflicts

**Interface**:
```typescript
class OfflineManager {
  isOnline(): boolean
  onOnline(callback: () => void): () => void
  onOffline(callback: () => void): () => void
}

class SyncQueue {
  enqueue(action: Action): void
  dequeue(): Action | null
  sync(): Promise<void>
  clear(): void
}

interface ConflictResolution {
  strategy: "local" | "remote" | "merge"
  resolve(local: any, remote: any): any
}
```

**Key Features**:
- Offline detection
- Action queuing
- Automatic sync
- Conflict resolution
- Retry logic

## Data Models

### API Response Model
```typescript
interface APIResponse<T> {
  data: T
  status: "success" | "error"
  timestamp: string
  requestId: string
}

interface APIError {
  code: string
  message: string
  details?: Record<string, any>
  status: number
}
```

### State Model
```typescript
interface RootState {
  auth: AuthState
  biasDetection: BiasDetectionState
  compliance: ComplianceState
  monitoring: MonitoringState
  ui: UIState
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: Error | null
}

interface UIState {
  theme: "light" | "dark"
  sidebarOpen: boolean
  notifications: Notification[]
  modals: Record<string, boolean>
}
```

### Hook Result Models
```typescript
interface UseApiResult<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
  isRefetching: boolean
}

interface UseMutationResult<T, R> {
  mutate: (data: T) => Promise<R>
  isLoading: boolean
  error: Error | null
  data: R | null
  reset: () => void
}
```

## Error Handling

### Error Types
```typescript
enum ErrorType {
  NETWORK = "NETWORK",
  VALIDATION = "VALIDATION",
  AUTHENTICATION = "AUTHENTICATION",
  AUTHORIZATION = "AUTHORIZATION",
  NOT_FOUND = "NOT_FOUND",
  CONFLICT = "CONFLICT",
  RATE_LIMIT = "RATE_LIMIT",
  SERVER = "SERVER",
  UNKNOWN = "UNKNOWN"
}
```

### Error Handling Flow
1. API call fails
2. Error is caught by API client
3. Error is formatted and wrapped
4. Error is passed to hook/component
5. Component displays error to user
6. User can retry or take other action

## Testing Strategy

### Unit Testing
- Test API client methods
- Test store actions and selectors
- Test hooks with mock API
- Test error handling
- Test caching logic

### Integration Testing
- Test API client with real backend
- Test store with real services
- Test hooks with real components
- Test offline functionality
- Test sync logic

### Property-Based Testing
- Test cache invalidation patterns
- Test request deduplication
- Test error formatting
- Test state transitions

### Test Coverage Targets
- API Client: 90%+
- Store: 85%+
- Hooks: 80%+
- Overall: 80%+

## Performance Considerations

### Optimization Strategies
1. **Code Splitting** - Lazy load routes and components
2. **Caching** - Cache API responses
3. **Deduplication** - Prevent duplicate requests
4. **Memoization** - Memoize expensive computations
5. **Virtualization** - Virtualize long lists
6. **Image Optimization** - Optimize images
7. **Bundle Size** - Minimize bundle size

### Monitoring Metrics
- API response time
- Cache hit rate
- Error rate
- Component render time
- Bundle size
- Memory usage

## Security Considerations

### Authentication
- Store JWT token securely
- Refresh token before expiration
- Clear token on logout
- Validate token on app load

### Authorization
- Check permissions before rendering
- Disable unauthorized actions
- Handle 403 responses
- Redirect to login on 401

### Data Protection
- Don't store sensitive data in state
- Sanitize user inputs
- Validate API responses
- Use HTTPS only

## Deployment Considerations

### Environment Configuration
- Development: Mock API, debug enabled
- Staging: Real API, debug enabled
- Production: Real API, debug disabled

### Build Optimization
- Code splitting by route
- Tree shaking unused code
- Minification and compression
- Source maps for debugging

### Performance Monitoring
- Track API response times
- Monitor error rates
- Track cache hit rates
- Monitor bundle size

## Migration Path

### Phase 1: Setup
1. Create API client layer
2. Create store structure
3. Create custom hooks
4. Write tests

### Phase 2: Gradual Migration
1. Migrate components one page at a time
2. Replace direct API calls with hooks
3. Replace prop drilling with store
4. Update error handling

### Phase 3: Cleanup
1. Remove old API call patterns
2. Remove old state management
3. Remove prop drilling
4. Update documentation

### Phase 4: Validation
1. Run full test suite
2. Performance testing
3. User acceptance testing
4. Production deployment

## Backward Compatibility

### API Compatibility
- Support old API versions
- Provide migration helpers
- Deprecation warnings
- Clear error messages

### Component Compatibility
- Maintain component props
- Provide wrapper components
- Gradual deprecation
- Migration guide

