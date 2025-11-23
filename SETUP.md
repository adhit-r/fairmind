# 🚀 FairMind Setup Guide

**Complete setup guide for FairMind - Get up and running in 5 minutes!**

## 📋 Prerequisites Checklist

Before you begin, ensure you have:

- [ ] **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- [ ] **Node.js 18+** installed ([Download](https://nodejs.org/))
- [ ] **Git** installed ([Download](https://git-scm.com/downloads))
- [ ] **Terminal/Command Line** access

### Optional (Recommended)

- [ ] **UV** - Modern Python package manager ([Install](https://github.com/astral-sh/uv))
- [ ] **Bun** - Fast JavaScript runtime ([Install](https://bun.sh/))

## 🎯 Quick Installation (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/adhit-r/fairmind.git
cd fairmind
```

### Step 2: Backend Setup

**Option A: Using UV (Recommended - Faster)**
```bash
cd apps/backend

# Install UV if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Start the server
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

**Option B: Using pip (Traditional)**
```bash
cd apps/backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

✅ Backend should now be running at `http://localhost:8001`  
✅ API docs available at `http://localhost:8001/docs`

### Step 3: Frontend Setup

Open a **new terminal window** and run:

**Option A: Using Bun (Recommended - Faster)**
```bash
cd apps/frontend

# Install Bun if you haven't
curl -fsSL https://bun.sh/install | bash

# Install dependencies
bun install

# Start the development server
bun run dev
```

**Option B: Using npm (Traditional)**
```bash
cd apps/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

✅ Frontend should now be running at `http://localhost:3000`

### Step 4: Verify Installation

1. **Check Backend**: Visit `http://localhost:8001/docs` - You should see the API documentation
2. **Check Frontend**: Visit `http://localhost:3000` - You should see the FairMind dashboard
3. **Test API**: Try accessing `http://localhost:8001/api/v1/health` - Should return `{"status": "healthy"}`

## 🔧 Troubleshooting

### Common Issues

#### Backend Issues

**Problem**: `uv: command not found`
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal or run: source ~/.bashrc
```

**Problem**: `Port 8001 already in use`
```bash
# Use a different port
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload
```

**Problem**: `ModuleNotFoundError`
```bash
# Make sure you're in the right directory
cd apps/backend
# Reinstall dependencies
uv sync  # or: pip install -r requirements.txt
```

#### Frontend Issues

**Problem**: `bun: command not found`
```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash
# Restart terminal or run: source ~/.bashrc
```

**Problem**: `Port 3000 already in use`
```bash
# Use a different port
PORT=3001 bun run dev  # or: PORT=3001 npm run dev
```

**Problem**: `Cannot find module`
```bash
# Delete node_modules and reinstall
rm -rf node_modules
bun install  # or: npm install
```

#### Python Version Issues

**Problem**: `Python version must be 3.9+`
```bash
# Check Python version
python --version  # Should be 3.9 or higher

# If using Python 2, try:
python3 --version

# Install Python 3.9+ if needed
# macOS: brew install python@3.11
# Linux: sudo apt-get install python3.11
# Windows: Download from python.org
```

#### Node.js Version Issues

**Problem**: `Node version must be 18+`
```bash
# Check Node.js version
node --version  # Should be v18 or higher

# Install Node.js 18+ if needed
# macOS: brew install node@18
# Linux: Use nvm - nvm install 18
# Windows: Download from nodejs.org
```

## 📚 Next Steps

### Running Tests

```bash
# Backend tests
cd apps/backend
pytest
pytest --cov  # with coverage

# Frontend tests
cd apps/frontend
bun test  # or: npm test

# Full test suite
cd test_scripts
bun run setup
python comprehensive_fairmind_test.py
```

### Development Workflow

1. **Make Changes**: Edit files in `apps/backend/` or `apps/frontend/`
2. **Auto-reload**: Both servers auto-reload on file changes
3. **Check Logs**: Watch terminal output for errors
4. **Test Changes**: Visit `http://localhost:3000` to see changes

### Environment Variables

**Backend**: Create `.env` file in `apps/backend/`
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/fairmind

# API Keys (optional)
COMETLLM_API_KEY=your_key_here
DEEPEVAL_API_KEY=your_key_here
```

**Frontend**: Create `.env.local` file in `apps/frontend/`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 🎓 Learning Resources

- **Getting Started**: [README.md](README.md)
- **Contributing**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **API Documentation**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Modern Bias Detection**: [docs/development/MODERN_BIAS_DETECTION_GUIDE.md](docs/development/MODERN_BIAS_DETECTION_GUIDE.md)

## 🆘 Still Having Issues?

1. **Check Documentation**: Review [README.md](README.md) and [docs/](./docs/)
2. **Search Issues**: Check [GitHub Issues](https://github.com/adhit-r/fairmind/issues)
3. **Ask for Help**: [Open a Discussion](https://github.com/adhit-r/fairmind/discussions/new)
4. **Report Bug**: [Create an Issue](https://github.com/adhit-r/fairmind/issues/new)

---

**Need help?** Join our [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions) or [open an issue](https://github.com/adhit-r/fairmind/issues/new)!

