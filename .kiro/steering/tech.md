# FairMind Technology Stack

## Architecture
FairMind follows a modern monorepo architecture with separate frontend and backend applications, plus supporting services.

## Backend Technology Stack

### Core Framework
- **FastAPI**: Modern Python web framework with automatic API documentation
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and serialization
- **Python 3.11+**: Modern Python with type hints and async support

### AI/ML Libraries
- **scikit-learn**: Traditional ML algorithms and bias detection
- **pandas & numpy**: Data processing and numerical computations
- **transformers**: Hugging Face transformers for LLM bias detection
- **torch & torchvision**: PyTorch for deep learning models

### Database & Storage
- **Supabase**: PostgreSQL-based backend-as-a-service
- **SQLAlchemy**: ORM for database operations
- **psycopg2**: PostgreSQL adapter
- **Redis**: Caching and rate limiting

### Security & Authentication
- **python-jose**: JWT token handling
- **passlib**: Password hashing with bcrypt
- **python-dotenv**: Environment variable management

### Development Tools
- **pytest**: Testing framework with async support
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking
- **pre-commit**: Git hooks for code quality

## Frontend Technology Stack

### Core Framework
- **Next.js 14**: React framework with App Router
- **React 18**: Modern React with concurrent features
- **TypeScript**: Static type checking

### UI & Styling
- **Mantine v7**: Modern React components library
- **Tailwind CSS**: Utility-first CSS framework
- **Tabler Icons**: Icon system
- **Framer Motion**: Animation library

### State Management
- **Zustand**: Lightweight state management
- **React Context**: Built-in state management for themes

### Development Tools
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **Jest**: Testing framework

## Build Systems & Package Management

### Backend
- **UV**: Modern Python package manager (recommended)
- **pip**: Traditional Python package manager (fallback)
- **pyproject.toml**: Modern Python project configuration

### Frontend
- **Bun**: Fast JavaScript runtime and package manager (recommended)
- **npm**: Traditional Node.js package manager (fallback)

## Common Development Commands

### Backend Setup
```bash
cd apps/backend

# Using UV (recommended)
uv sync                    # Install dependencies
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# Using pip (fallback)
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup
```bash
cd apps/frontend

# Using Bun (recommended)
bun install               # Install dependencies
bun run dev               # Start development server

# Using npm (fallback)
npm install
npm run dev
```

### Testing Commands
```bash
# Backend testing
cd apps/backend
pytest                    # Run all tests
pytest --cov             # Run with coverage
python test_phase2.py     # Run integration tests

# Frontend testing
cd apps/frontend
bun test                  # Run Jest tests
bun run lint              # Run ESLint
bun run type-check        # Run TypeScript checks
```

### Production Build
```bash
# Backend
cd apps/backend
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd apps/frontend
bun run build
bun run start
```

## Development Environment

### Required Tools
- **Python 3.11+**: Backend runtime
- **Node.js 18+**: Frontend runtime
- **UV**: Python package manager (install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Bun**: JavaScript runtime (install via: `curl -fsSL https://bun.sh/install | bash`)

### Environment Variables
- Backend: `.env`, `.env.example`, `.env.production` in `apps/backend/`
- Frontend: `.env.local`, `.env.example`, `.env.production` in `apps/frontend/`

### Code Quality Standards
- **Python**: Black formatting, isort imports, mypy type checking, 100-character line length
- **TypeScript**: ESLint + Prettier, strict TypeScript configuration
- **Testing**: Minimum 80% code coverage for backend, comprehensive test suites
- **Security**: Pre-commit hooks, dependency scanning, security headers

## Deployment

### Production URLs
- **Backend API**: https://api.fairmind.xyz (Railway)
- **Frontend App**: https://app-demo.fairmind.xyz (Netlify)
- **Documentation**: https://fairmind.xyz (Astro/Netlify)

### Infrastructure
- **Backend**: Railway deployment with PostgreSQL
- **Frontend**: Netlify with automatic deployments
- **Database**: Supabase PostgreSQL with real-time features
- **Monitoring**: Built-in health checks and logging