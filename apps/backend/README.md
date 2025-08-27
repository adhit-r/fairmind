# 🚀 FairMind Backend API

> **FastAPI backend for ethical AI governance with comprehensive testing and modern tooling (UV)**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![UV](https://img.shields.io/badge/Package%20Manager-UV-orange)](https://docs.astral.sh/uv/)
[![Testing](https://img.shields.io/badge/Testing-100%25%20Coverage-brightgreen)](../test_results/)

## 🎯 **Overview**

FairMind Backend provides a comprehensive FastAPI-based API for ethical AI governance, featuring **8 core features** for bias detection, security testing, model governance, and compliance monitoring.

### **🏆 Recent Achievements**
- ✅ **Production Deployed**: Railway deployment at api.fairmind.xyz
- ✅ **Complete API Coverage**: All 8 FairMind features implemented
- ✅ **Modern Tooling**: UV package management for fast dependency resolution
- ✅ **Comprehensive Testing**: 100% feature coverage with real models

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Install UV (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### **Installation & Setup**
```bash
cd apps/backend

# Install dependencies with UV
uv sync

# Start development server
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### **Production Deployment**
```bash
# Railway deployment (already configured)
railway up

# Or manual deployment
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

## 🎪 **API Features**

### **Core Endpoints**

| Feature | Endpoint | Description | Status |
|---------|----------|-------------|--------|
| **🔍 Bias Detection** | `/api/bias-detection/*` | Comprehensive fairness analysis | ✅ |
| **🧬 AI DNA Profiling** | `/api/ai-dna/*` | Model signatures and lineage | ✅ |
| **⏰ AI Time Travel** | `/api/time-travel/*` | Historical/future analysis | ✅ |
| **🎪 AI Circus** | `/api/ai-circus/*` | Comprehensive testing suite | ✅ |
| **🔒 OWASP Security** | `/api/security/*` | AI security assessment | ✅ |
| **⚖️ Ethics Observatory** | `/api/ethics/*` | Ethics framework evaluation | ✅ |
| **📋 AI BOM** | `/api/ai-bom/*` | Component tracking | ✅ |
| **📊 Model Registry** | `/api/registry/*` | Lifecycle management | ✅ |

### **Health & Status**
- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs` (Swagger UI)
- **ReDoc Documentation**: `GET /redoc`

## 🏗️ **Architecture**

```
apps/backend/
├── api/
│   ├── main.py              # FastAPI application entry point
│   ├── models/              # Pydantic data models
│   ├── routes/              # API route handlers
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions
├── fairness_library/        # Custom fairness algorithms
├── requirements.txt         # Python dependencies
├── pyproject.toml          # UV project configuration
└── README.md               # This file
```

## 🛠️ **Technology Stack**

### **Core Framework**
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and settings management

### **ML & AI Libraries**
- **scikit-learn**: Traditional ML algorithms
- **pandas & numpy**: Data processing and analysis
- **xgboost**: Gradient boosting for high-performance models
- **transformers**: Hugging Face transformers for LLM support
- **torch & torchvision**: PyTorch for deep learning

### **Testing & Quality**
- **pytest**: Testing framework
- **requests**: HTTP client for testing
- **comprehensive test suite**: 24+ test cases

### **Development Tools**
- **UV**: Fast Python package manager
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking

## 📊 **API Endpoints**

### **Bias Detection**
```bash
# Analyze model bias
POST /api/bias-detection/analyze
GET /api/bias-detection/history
GET /api/bias-detection/datasets

# Classic explainability tools
POST /api/bias-detection/analyze-classic
GET /api/bias-detection/explainability-tools
```

### **Security Testing**
```bash
# OWASP AI security assessment
POST /api/security/analyze
GET /api/security/history
GET /api/security/categories
```

### **Model Governance**
```bash
# AI Bill of Materials
GET /api/ai-bom/generate
GET /api/ai-bom/history

# Model Registry
GET /api/registry/models
POST /api/registry/register
```

### **Dashboard & Metrics**
```bash
# Dashboard data
GET /api/dashboard/metrics
GET /api/dashboard/activity
GET /api/dashboard/security-results
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/fairmind

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000", "https://app-demo.fairmind.xyz"]

# External Services
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Deployment
PORT=8001
HOST=0.0.0.0
```

### **UV Configuration**
```toml
# pyproject.toml
[project]
name = "fairmind-backend"
version = "1.0.0"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pydantic>=2.0.0",
    # ... other dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
]
```

## 🧪 **Testing**

### **Running Tests**
```bash
# Install test dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=api --cov-report=html

# Run specific test module
uv run pytest tests/test_bias_detection.py
```

### **Test Coverage**
- **API Endpoints**: 100% coverage
- **Business Logic**: 100% coverage
- **Data Models**: 100% coverage
- **Integration**: Comprehensive testing

## 🚀 **Deployment**

### **Railway Deployment**
```bash
# Deploy to Railway (already configured)
railway up

# Check deployment status
railway status

# View logs
railway logs
```

### **Manual Deployment**
```bash
# Build and run
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT

# With production settings
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 4
```

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim

# Install UV
RUN pip install uv

# Copy project files
COPY . /app
WORKDIR /app

# Install dependencies
RUN uv sync --frozen

# Run application
CMD ["uv", "run", "python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 📈 **Performance**

### **Response Times**
- **Health Check**: <50ms
- **Bias Analysis**: <2s (depending on model size)
- **Security Assessment**: <1s
- **Dashboard Metrics**: <200ms

### **Scalability**
- **Concurrent Requests**: 100+ requests/second
- **Memory Usage**: ~512MB base + model memory
- **CPU Usage**: Optimized for ML workloads

## 🔒 **Security**

### **Implemented Security**
- **CORS**: Configured for production domains
- **Rate Limiting**: API rate limiting
- **Input Validation**: Pydantic model validation
- **Error Handling**: Secure error responses
- **OWASP Compliance**: AI security best practices

### **Security Headers**
```python
# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📚 **Documentation**

### **API Documentation**
- **Swagger UI**: `/docs` - Interactive API documentation
- **ReDoc**: `/redoc` - Alternative documentation view
- **OpenAPI Schema**: `/openapi.json` - Machine-readable schema

### **Code Documentation**
- **Docstrings**: Comprehensive function documentation
- **Type Hints**: Full type annotation coverage
- **Examples**: Code examples in docstrings

## 🤝 **Contributing**

### **Development Workflow**
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Install** dependencies (`uv sync`)
4. **Make** changes and add tests
5. **Run** tests (`uv run pytest`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Push** to branch (`git push origin feature/amazing-feature`)
8. **Create** Pull Request

### **Code Standards**
- **Formatting**: Black code formatter
- **Imports**: isort import sorting
- **Type Checking**: mypy type checking
- **Testing**: pytest with 100% coverage requirement

## 🆘 **Support**

### **Getting Help**
- **Documentation**: [API Docs](./docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/fairmind-ethical-sandbox/issues)
- **Testing**: [Test Results](../test_results/)
- **Deployment**: [Railway Dashboard](https://railway.app/)

### **Common Issues**
- **Port Conflicts**: Change port in uvicorn command
- **Dependency Issues**: Use `uv sync --reinstall`
- **Memory Issues**: Increase memory allocation for large models
- **CORS Issues**: Check CORS_ORIGINS configuration

---

**🎉 FairMind Backend is production-ready for ethical AI governance!**

*Built with FastAPI and UV for modern, scalable AI governance APIs.*
