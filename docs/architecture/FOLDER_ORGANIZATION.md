# Folder Organization

## 📁 Current Structure

```
fairmind-ethical-sandbox/
├── apps/                    # 🎯 MONOREPO APPLICATIONS
│   ├── web/                # Next.js frontend application
│   │   ├── src/
│   │   │   ├── app/        # Next.js app router pages
│   │   │   │   ├── page.tsx    # Main dashboard
│   │   │   │   ├── ai-bill/    # AI/ML Bill compliance page
│   │   │   │   └── simulation/ # Simulation pages
│   │   │   ├── components/     # React components
│   │   │   │   ├── charts/     # Chart components (Chart.js)
│   │   │   │   ├── ui/         # UI components (Radix UI)
│   │   │   │   └── ...
│   │   │   ├── lib/           # Utilities and API clients
│   │   │   │   ├── api-client.ts    # Backend API client
│   │   │   │   ├── form-validation.ts # Form validation utilities
│   │   │   │   └── responsive-utils.ts # Responsive design utilities
│   │   │   ├── types/         # TypeScript type definitions
│   │   │   └── contexts/      # React contexts
│   │   ├── public/            # Static assets
│   │   └── package.json       # Frontend dependencies
│   └── api/                   # Python FastAPI backend services
│       ├── api/              # API endpoints
│       ├── app/              # Application logic
│       ├── tests/            # Backend tests
│       ├── main.py           # FastAPI application entry point
│       └── requirements.txt  # Python dependencies
├── packages/             # 📦 Shared packages (UI components, etc.)
├── shared/               # 🔧 Shared utilities and configurations
├── docs/                 # 📚 Documentation
├── scripts/              # 🔨 Build and deployment scripts
├── tools/                # 🛠️ Development tools
├── archive/              # 📦 Archived/old code
│   └── old-frontends/    # Previous frontend versions
│       ├── frontend/     # Old frontend folder
│       ├── unified-frontend/ # Old unified frontend
│       └── orginal-ui-reference/ # Original UI reference
└── supabase/             # 🗄️ Database and authentication
```

## 🔄 What Was Organized

### ✅ Moved to Archive
- `frontend/` → `archive/old-frontends/frontend/`
- `unified-frontend/` → `archive/old-frontends/unified-frontend/`
- `apps/orginal-ui-reference/` → `archive/old-frontends/orginal-ui-reference/`

### ✅ Proper Monorepo Structure
- **`apps/web/`** - Main active frontend (Next.js)
- **`apps/api/`** - Main active backend (FastAPI)
- **`packages/`** - Shared packages and UI components
- **`shared/`** - Shared utilities and configurations

### ✅ Cleaned Up
- Removed duplicate and nested directories
- Removed duplicate `.DS_Store` files
- Fixed TypeScript errors in moved components
- Updated build configuration for monorepo

## 🎯 Active Development Folders

### `apps/web/` - Main Frontend Application
This is your **active Next.js application** with all the latest features:
- ✅ AI/ML Bill compliance page (`/ai-bill`)
- ✅ Working Chart.js charts (no more runtime errors)
- ✅ TypeScript types and API client
- ✅ Responsive design utilities
- ✅ Form validation system
- ✅ Builds successfully ✅

### `apps/api/` - Main Backend Services
Consolidated Python FastAPI backend with:
- ✅ API endpoints for AI governance
- ✅ ML service integration
- ✅ Database models and utilities

## 📦 Archived Folders

### `archive/old-frontends/`
Contains all previous frontend versions that are no longer active:
- **`frontend/`** - Old frontend implementation
- **`unified-frontend/`** - Previous unified frontend attempt
- **`orginal-ui-reference/`** - Original UI design reference

## 🚀 Development Workflow

### Monorepo Development
```bash
# Start all services
bun run dev

# Start specific services
bun run dev:web    # Frontend only
bun run dev:api    # Backend only
```

### Individual App Development
```bash
# Frontend Development
cd apps/web
bun install
bun run dev

# Backend Development
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📝 Notes

1. **`apps/web/`** is the main active frontend - all new frontend development should happen here
2. **`apps/api/`** is the main active backend - all new backend development should happen here
3. **`packages/`** contains shared packages that can be used across apps
4. **`archive/`** contains old code for reference - not for active development
5. The structure now follows proper monorepo conventions with Turborepo

## 🔍 Finding Code

- **Active Frontend**: `apps/web/src/`
- **Active Backend**: `apps/api/`
- **Shared Packages**: `packages/`
- **Old Frontends**: `archive/old-frontends/`
- **Documentation**: `docs/`
- **Shared Utilities**: `shared/`

## 🏗️ Monorepo Benefits

1. **Unified Development**: All apps in one repository
2. **Shared Dependencies**: Common packages and utilities
3. **Consistent Tooling**: Same build tools and processes
4. **Easy Refactoring**: Cross-app changes in one place
5. **Better Testing**: End-to-end testing across apps
6. **Simplified CI/CD**: Single pipeline for all apps 