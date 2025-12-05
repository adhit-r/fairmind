# Migration Plan: Moving Away from Supabase

## 1. Executive Summary
This document outlines the strategy for migrating the FairMind platform away from Supabase to a self-hosted, cloud-agnostic architecture. This move is driven by the need for:
- **Data Sovereignty**: Full control over sensitive AI model and dataset data.
- **Cost Control**: Eliminating third-party quotas and pricing tiers.
- **Enterprise Readiness**: Supporting on-premise and air-gapped deployments.
- **Reliability**: Removing dependencies on external managed services.

## 2. Target Architecture (The "FairMind Stack")

We will replace the monolithic Supabase backend with a modular, containerized stack orchestrated via Docker Compose / Kubernetes.

| Component | Current (Supabase) | Target (Self-Hosted) | Rationale |
|-----------|--------------------|----------------------|-----------|
| **Database** | Supabase Postgres | **PostgreSQL 16** (Docker) | Industry standard, open-source, no quotas. |
| **Auth** | Supabase Auth (GoTrue) | **Keycloak** or **Auth.js** | Keycloak for enterprise SSO/SAML; Auth.js for simpler needs. |
| **Storage** | Supabase Storage | **MinIO** (S3 Compatible) | Self-hosted S3 API, high performance, scalable. |
| **Realtime** | Supabase Realtime | **Redis Pub/Sub** + **Socket.io** | Standard pattern for realtime events (logs, progress). |
| **Vector DB** | pgvector (Supabase) | **pgvector** (Self-hosted) | Same technology, just self-managed. |

## 3. Migration Strategy

### Phase 1: Database & Storage (Immediate)
The most critical dependencies are data persistence and file storage.

1.  **Database**:
    -   Switch `DATABASE_URL` to point to a local Dockerized PostgreSQL instance.
    -   Use `Alembic` for all schema management (already in place).
    -   **Action**: Create `docker-compose.yml` with `postgres` service.

2.  **Object Storage**:
    -   Replace `SupabaseService` storage calls with a generic `StorageService` interface.
    -   Implement `MinIOStorageProvider` using `boto3` (standard AWS SDK).
    -   **Action**: Add `minio` service to `docker-compose.yml`.

### Phase 2: Authentication (High Effort)
Supabase Auth provides "magic" (email handling, session management) that we must replicate.

**Option A: Keycloak (Recommended for Enterprise)**
-   **Pros**: Full IAM, SSO, OIDC, SAML, User Federation (LDAP/AD).
-   **Cons**: Heavyweight, complex setup.
-   **Integration**: Backend validates JWTs issued by Keycloak. Frontend redirects to Keycloak login page.

**Option B: Auth.js / NextAuth (Recommended for Speed)**
-   **Pros**: Integrated with Next.js, supports many providers, lightweight.
-   **Cons**: Less "enterprise" features out of the box compared to Keycloak.
-   **Integration**: Frontend handles login, Backend validates JWT/Session.

**Decision**: We will start with **Option B (Auth.js)** for the immediate term as it integrates tightly with our Next.js frontend, while designing the backend to accept standard OIDC tokens (allowing future Keycloak switch).

### Phase 3: Realtime (Medium Effort)
Replace Supabase Realtime subscriptions (used for log streaming, progress updates).

1.  **Architecture**: Use Redis as a message broker.
2.  **Backend**: Publish events to Redis channels (e.g., `simulation_updates:{id}`).
3.  **Frontend**: Connect to a dedicated WebSocket server (or Next.js API route) that subscribes to Redis and forwards messages.

## 4. Implementation Steps

### Step 1: Create Docker Compose Stack
Create a `docker-compose.yml` in the root directory:

```yaml
version: '3.8'
services:
  # Core Database
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: fairmind
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: fairmind
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Object Storage
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio_admin
      MINIO_ROOT_PASSWORD: minio_password
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  # Cache & Realtime Broker
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  minio_data:
```

### Step 2: Refactor Backend Services

1.  **Abstract Storage**:
    Create `apps/backend/core/storage/storage_provider.py`:
    ```python
    class StorageProvider(ABC):
        async def upload(self, file: BinaryIO, path: str) -> str: ...
        async def download(self, path: str) -> BinaryIO: ...
        async def delete(self, path: str) -> bool: ...
    ```
    Implement `S3StorageProvider` (for MinIO/AWS) and `LocalStorageProvider` (for dev).

2.  **Abstract Auth**:
    Update `SupabaseAuthMiddleware` to be a generic `JWTAuthMiddleware`.
    -   Accept standard JWKS URL for token verification.
    -   Decouple from Supabase-specific claims if possible.

### Step 3: Frontend Updates

1.  **Remove Supabase Client**:
    -   Replace `createClientComponentClient` with standard API calls to our backend.
    -   For Auth, switch to `next-auth` hooks (`useSession`, `signIn`, `signOut`).

2.  **File Uploads**:
    -   Instead of `supabase.storage.upload`, POST files to `/api/v1/upload` (Backend handles MinIO upload).

## 5. Migration Checklist

- [ ] Create `docker-compose.yml` with Postgres, MinIO, Redis.
- [ ] Update Backend `.env` to point to local services.
- [ ] Run Alembic migrations on new Postgres instance.
- [ ] Implement `S3StorageProvider` in Backend.
- [ ] Create `/api/v1/auth/*` endpoints (or setup NextAuth).
- [ ] Update Frontend to use new Auth and Upload endpoints.
- [ ] Verify all "Real Data" workflows (Upload -> Process -> Test).

## 6. Conclusion
This migration will make FairMind a truly independent, enterprise-grade platform. While it requires initial engineering effort, it eliminates external risks and aligns with the product's long-term goals of privacy and compliance.
