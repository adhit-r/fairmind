# FairMind - Ethical AI Governance Platform

> Open-source platform for AI fairness, bias detection, and responsible AI development. Detect bias in LLMs, multimodal AI, and machine learning models with cutting-edge 2025 research methods.

[![Backend Status](https://img.shields.io/badge/Backend-FastAPI-green)](https://api.fairmind.xyz)
[![Frontend Status](https://img.shields.io/badge/Frontend-Next.js-blue)](https://app-demo.fairmind.xyz)
[![Testing Status](https://img.shields.io/badge/Testing-100%25%20Coverage-brightgreen)](./FINAL_TESTING_SUMMARY.md)
[![Contributors](https://img.shields.io/github/contributors/adhit-r/fairmind)](https://github.com/adhit-r/fairmind/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/adhit-r/fairmind/good%20first%20issue)](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Stars](https://img.shields.io/github/stars/adhit-r/fairmind?style=social)](https://github.com/adhit-r/fairmind/stargazers)

**Live Demo:** [app-demo.fairmind.xyz](https://app-demo.fairmind.xyz) | **Documentation:** [docs/](./docs/) | **Issues:** [GitHub Issues](https://github.com/adhit-r/fairmind/issues) | **Discussions:** [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions)

---

## Table of Contents

```
┌─────────────────────────────────────────────────────────────┐
│                    TABLE OF CONTENTS                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Quick Start Guide                                        │
│ 2. Platform Overview                                        │
│ 3. Architecture Diagram                                      │
│ 4. Feature Matrix                                           │
│ 5. API Endpoints Reference                                  │
│ 6. Frontend Pages Overview                                  │
│ 7. Technology Stack                                         │
│ 8. Project Statistics                                        │
│ 9. Contributors                                             │
│ 10. Development Guide                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start Guide

### Installation Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    INSTALLATION FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Prerequisites                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Python     │  │   Node.js    │  │     UV       │    │
│  │   3.9+       │  │    18+       │  │   (Latest)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                              │
│  Step 2: Clone Repository                                   │
│  ┌────────────────────────────────────────────────────┐   │
│  │ git clone https://github.com/adhit-r/fairmind.git │   │
│  │ cd fairmind                                        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  Step 3: Backend Setup (Terminal 1)                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ cd apps/backend                                    │   │
│  │ uv sync                                            │   │
│  │ uv run python -m uvicorn api.main:app --reload    │   │
│  └────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    ▼                                         │
│         http://localhost:8000                              │
│                                                              │
│  Step 4: Frontend Setup (Terminal 2)                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │ cd apps/frontend                                   │   │
│  │ bun install                                        │   │
│  │ bun run dev                                        │   │
│  └────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    ▼                                         │
│         http://localhost:3000                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Prerequisites Table

| Requirement | Version | Installation Link | Purpose |
|-------------|---------|------------------|---------|
| **Python** | 3.9+ | [python.org](https://www.python.org/downloads/) | Backend runtime |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) | Frontend runtime |
| **UV** | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | Python package manager |
| **Bun** | Latest | `curl -fsSL https://bun.sh/install \| bash` | JavaScript runtime & package manager |

### Installation Commands

```bash
# 1. Clone Repository
git clone https://github.com/adhit-r/fairmind.git
cd fairmind

# 2. Backend Setup (Terminal 1)
cd apps/backend
uv sync  # or: pip install -r requirements.txt
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Frontend Setup (Terminal 2)
cd apps/frontend
bun install  # or: npm install
bun run dev  # or: npm run dev

# 4. Verify Installation
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Port Configuration

| Service | Default Port | Configuration |
|---------|--------------|---------------|
| **Backend API** | 8000 | `--port` flag in uvicorn command |
| **Frontend** | 3000 | Next.js default (configurable in package.json) |
| **API Docs** | 8000/docs | Auto-generated Swagger UI |

**Note:** If backend runs on a different port, configure frontend:
```bash
# Create apps/frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## Platform Overview

### What is FairMind?

FairMind is a comprehensive **AI fairness testing platform** that helps developers, researchers, and organizations build **responsible AI systems**. Our platform provides advanced bias detection, explainability tools, and compliance tracking for modern AI applications.

### Platform Capabilities Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLATFORM CAPABILITIES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   BIAS       │  │ EXPLAINABLE  │  │  COMPLIANCE  │         │
│  │  DETECTION   │  │      AI      │  │   TRACKING   │         │
│  │              │  │              │  │              │         │
│  │ • LLM Bias   │  │ • CometLLM   │  │ • OWASP AI   │         │
│  │ • Multimodal │  │ • DeepEval   │  │ • AI BOM     │         │
│  │ • Classic ML │  │ • Arize      │  │ • GDPR       │         │
│  │ • WEAT/SEAT  │  │ • AWS Clarify│  │ • EU AI Act  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   REAL-TIME  │  │   MODEL      │  │   SECURITY   │         │
│  │  MONITORING  │  │  REGISTRY    │  │   TESTING    │         │
│  │              │  │              │  │              │         │
│  │ • Live Alerts│  │ • Lifecycle  │  │ • SAST/DAST  │         │
│  │ • Drift Det. │  │ • Versioning │  │ • Dependency │         │
│  │ • Metrics    │  │ • Lineage    │  │ • Container  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Target Users

| User Type | Use Cases | Key Features |
|-----------|-----------|--------------|
| **AI Researchers** | Bias research, model evaluation | WEAT, SEAT, Multimodal analysis |
| **ML Engineers** | Production model monitoring | Real-time monitoring, drift detection |
| **Compliance Officers** | Regulatory compliance | GDPR, EU AI Act, OWASP AI mapping |
| **Data Scientists** | Model fairness assessment | Statistical parity, equal opportunity |
| **DevOps Teams** | Security scanning | SAST, DAST, dependency scanning |

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FAIRMIND PLATFORM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                                    ┌──────────────┐                         │
│                                    │   USERS      │                         │
│                                    │  (Browser)   │                         │
│                                    └──────┬───────┘                         │
│                                           │                                  │
│                                           │ HTTP/REST                        │
│                                           │                                  │
│                    ┌──────────────────────▼──────────────────────┐          │
│                    │         FRONTEND LAYER                     │          │
│                    │  ┌────────────────────────────────────┐   │          │
│                    │  │  Next.js 14 (React 18 + TypeScript) │   │          │
│                    │  │  • 36 Pages                         │   │          │
│                    │  │  • Mantine UI Components            │   │          │
│                    │  │  • Neobrutal Design System         │   │          │
│                    │  └────────────────────────────────────┘   │          │
│                    └──────────────────────┬──────────────────────┘          │
│                                           │                                  │
│                                           │ REST API                         │
│                                           │                                  │
│                    ┌──────────────────────▼──────────────────────┐          │
│                    │         BACKEND LAYER                      │          │
│                    │  ┌────────────────────────────────────┐   │          │
│                    │  │  FastAPI (Python 3.9+)             │   │          │
│                    │  │  • 24 Route Modules                │   │          │
│                    │  │  • 35 Service Modules              │   │          │
│                    │  │  • 45+ API Endpoints               │   │          │
│                    │  └────────────────────────────────────┘   │          │
│                    │  ┌────────────────────────────────────┐   │          │
│                    │  │  ML/AI Libraries                   │   │          │
│                    │  │  • scikit-learn                     │   │          │
│                    │  │  • transformers                     │   │          │
│                    │  │  • torch                            │   │          │
│                    │  │  • pandas, numpy                    │   │          │
│                    │  └────────────────────────────────────┘   │          │
│                    └──────────────────────┬──────────────────────┘          │
│                                           │                                  │
│                    ┌──────────────────────▼──────────────────────┐          │
│                    │      INFRASTRUCTURE LAYER                  │          │
│                    │  ┌──────────────┐  ┌──────────────┐       │          │
│                    │  │   Railway    │  │   Netlify    │       │          │
│                    │  │  (Backend)   │  │  (Frontend)  │       │          │
│                    │  └──────────────┘  └──────────────┘       │          │
│                    └────────────────────────────────────────────┘          │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
fairmind/
├── apps/
│   ├── backend/                    # FastAPI Backend
│   │   ├── api/
│   │   │   ├── routes/             # 24 route modules
│   │   │   │   ├── bias_detection.py
│   │   │   │   ├── modern_bias_detection.py
│   │   │   │   ├── fairness_governance.py
│   │   │   │   ├── ai_governance.py
│   │   │   │   ├── security.py
│   │   │   │   ├── ai_bom.py
│   │   │   │   ├── lifecycle.py
│   │   │   │   └── ... (17 more)
│   │   │   ├── services/           # 35 service modules
│   │   │   │   ├── bias_detection_service.py
│   │   │   │   ├── explainability_service.py
│   │   │   │   ├── compliance_service.py
│   │   │   │   └── ... (32 more)
│   │   │   └── main.py            # FastAPI app entry
│   │   ├── config/                 # Configuration
│   │   ├── middleware/             # Security, logging
│   │   └── tests/                  # Test suite (100% coverage)
│   │
│   ├── frontend/                    # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/                # 36 pages
│   │   │   │   ├── dashboard/
│   │   │   │   ├── bias/
│   │   │   │   ├── advanced-bias/
│   │   │   │   ├── security/
│   │   │   │   ├── ai-bom/
│   │   │   │   └── ... (31 more)
│   │   │   ├── components/         # React components
│   │   │   │   ├── brutal/         # Neobrutal components
│   │   │   │   ├── charts/         # Data visualization
│   │   │   │   └── dashboard/      # Dashboard components
│   │   │   ├── hooks/              # Custom React hooks
│   │   │   └── styles/             # Design system CSS
│   │   └── tests/                  # Frontend tests
│   │
│   └── website/                     # Documentation site
│
├── docs/                            # Comprehensive documentation
│   ├── api/                         # API documentation
│   ├── architecture/                # Architecture guides
│   ├── development/                 # Development guides
│   └── deployment/                  # Deployment guides
│
├── test_scripts/                    # Integration test suite
└── test_models/                     # Sample ML models
```

---

## Features

### Feature Categories Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE CATEGORIES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  TRADITIONAL AI GOVERNANCE (8 Features)                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • Bias Detection (5+ metrics)                          │   │
│  │  • AI DNA Profiling                                     │   │
│  │  • AI Time Travel                                       │   │
│  │  • AI Circus (Testing Suite)                            │   │
│  │  • OWASP AI Security                                    │   │
│  │  • AI Ethics Observatory                                │   │
│  │  • AI Bill of Materials                                 │   │
│  │  • Model Registry                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  MODERN BIAS DETECTION (2025 Research)                  │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • LLM Bias Detection (WEAT, SEAT, Minimal Pairs)       │   │
│  │  • Multimodal Analysis (Image, Audio, Video)            │   │
│  │  • Explainability (4 tools integrated)                  │   │
│  │  • Evaluation Pipeline (Multi-layered)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PRODUCTION FEATURES                                     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • 45+ API Endpoints                                    │   │
│  │  • Real-time Monitoring                                 │   │
│  │  • 100% Test Coverage                                   │   │
│  │  • Production Deployment                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Traditional AI Governance Features

| Feature | Description | Status | Endpoints |
|---------|-------------|--------|-----------|
| **Bias Detection** | 5+ fairness metrics (statistical parity, equal opportunity, calibration) | Production Ready | `/api/v1/bias/*` |
| **AI DNA Profiling** | Model signatures and lineage tracking | Production Ready | `/api/v1/models/*` |
| **AI Time Travel** | Historical and future analysis capabilities | Production Ready | `/api/v1/analytics/*` |
| **AI Circus** | Comprehensive testing suite | Production Ready | `/api/v1/testing/*` |
| **OWASP AI Security** | All 10 OWASP AI security categories | Production Ready | `/api/v1/security/*` |
| **AI Ethics Observatory** | Ethics framework assessment | Production Ready | `/api/v1/ethics/*` |
| **AI Bill of Materials** | Component tracking and compliance | Production Ready | `/api/v1/ai-bom/*` |
| **Model Registry** | Lifecycle management and governance | Production Ready | `/api/v1/models/*` |

### Modern Bias Detection Features (2025 Research)

| Feature | Description | Status | Methods |
|---------|-------------|--------|---------|
| **LLM Bias Detection** | Detect bias in Large Language Models | Production Ready | WEAT, SEAT, Minimal Pairs, Red Teaming |
| **Multimodal Analysis** | Analyze bias across multiple modalities | Production Ready | Image, Audio, Video, Cross-Modal |
| **Explainability** | Integrate with major explainability tools | Production Ready | CometLLM, DeepEval, Arize Phoenix, AWS Clarify |
| **Evaluation Pipeline** | Multi-layered assessment with human-in-the-loop | Production Ready | Comprehensive evaluation framework |

### Production Features

| Feature | Count | Status |
|---------|-------|--------|
| **API Endpoints** | 45+ | Production Ready |
| **Frontend Pages** | 36 | Production Ready |
| **Backend Routes** | 24 | Production Ready |
| **Backend Services** | 35 | Production Ready |
| **Test Coverage** | 100% | Complete |

---

## API Endpoints Reference

### API Endpoint Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    API ENDPOINT CATEGORIES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Category              │  Endpoints  │  Route Files             │
│  ──────────────────────┼─────────────┼─────────────────────────│
│  Bias Detection       │     12+     │  bias_detection.py       │
│  Modern Bias          │     8+      │  modern_bias_detection.py│
│  Fairness Governance  │     10+     │  fairness_governance.py  │
│  AI Governance        │     15+     │  ai_governance.py        │
│  Security             │     10+     │  security.py             │
│  AI BOM               │     6+      │  ai_bom.py               │
│  Lifecycle            │     8+      │  lifecycle.py            │
│  Core (Models/Data)   │     10+     │  core.py                 │
│  Database             │     8+      │  database.py             │
│  Benchmark Suite      │     6+      │  benchmark_suite.py      │
│                                                                   │
│  TOTAL                │     45+     │  24 route modules        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key API Endpoints

| Endpoint | Method | Description | Category |
|----------|--------|-------------|----------|
| `/api/v1/bias/detect` | POST | Detect bias in ML models | Bias Detection |
| `/api/v1/bias/llm/weat` | POST | WEAT test for LLMs | Modern Bias |
| `/api/v1/fairness/metrics` | POST | Compute fairness metrics | Fairness Governance |
| `/api/v1/ai-governance/policies` | GET/POST | Policy management | AI Governance |
| `/api/v1/security/scan` | POST | Security scanning | Security |
| `/api/v1/ai-bom/create` | POST | Create AI BOM | AI BOM |
| `/api/v1/lifecycle/projects` | GET | List projects | Lifecycle |
| `/api/v1/models` | GET | List models | Core |
| `/health` | GET | Health check | System |

**Full API Documentation:** [api.fairmind.xyz/docs](https://api.fairmind.xyz/docs)

---

## Frontend Pages Overview

### Frontend Page Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND PAGES (36 Total)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Core Pages:                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /dashboard          Main dashboard                      │   │
│  │  /bias               Traditional bias detection         │   │
│  │  /advanced-bias       Modern LLM bias detection          │   │
│  │  /security           Security overview                   │   │
│  │  /security/scans      Security scanning                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Governance Pages:                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /ai-governance       Governance dashboard               │   │
│  │  /compliance          Compliance tracking                │   │
│  │  /policies            Policy management                  │   │
│  │  /risks               Risk assessment                    │   │
│  │  /evidence            Evidence tracking                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Model Management:                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /models               Model registry                    │   │
│  │  /models/upload        Upload models                    │   │
│  │  /datasets             Dataset management                │   │
│  │  /lifecycle            Lifecycle management              │   │
│  │  /ai-bom               AI Bill of Materials              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Analytics & Monitoring:                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /analytics            Analytics dashboard               │   │
│  │  /monitoring           Real-time monitoring              │   │
│  │  /reports              Generated reports                 │   │
│  │  /benchmarks           Performance benchmarks            │   │
│  │  /fairness             Fairness analysis                 │   │
│  │  /provenance           Data provenance                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  System Pages:                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /settings             Application settings              │   │
│  │  /status               System status                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Pages Table

| Page | Route | Description | Status |
|------|-------|-------------|--------|
| Dashboard | `/dashboard` | Main dashboard with metrics | Production |
| Bias Detection | `/bias` | Traditional bias detection | Production |
| Advanced Bias | `/advanced-bias` | Modern LLM bias detection | Production |
| Security | `/security` | Security overview | Production |
| Security Scans | `/security/scans` | Security scanning interface | Production |
| AI Governance | `/ai-governance` | Governance dashboard | Production |
| Compliance | `/compliance` | Regulatory compliance | Production |
| Policies | `/policies` | Policy management | Production |
| Risks | `/risks` | Risk assessment | Production |
| Evidence | `/evidence` | Compliance evidence tracking | Production |
| Models | `/models` | Model registry | Production |
| Model Upload | `/models/upload` | Upload new models | Production |
| Datasets | `/datasets` | Dataset management | Production |
| Lifecycle | `/lifecycle` | Model lifecycle management | Production |
| AI BOM | `/ai-bom` | AI Bill of Materials | Production |
| Analytics | `/analytics` | Analytics dashboard | Production |
| Monitoring | `/monitoring` | Real-time monitoring | Production |
| Reports | `/reports` | Generated reports | Production |
| Benchmarks | `/benchmarks` | Performance benchmarks | Production |
| Fairness | `/fairness` | Fairness analysis | Production |
| Provenance | `/provenance` | Data provenance | Production |
| Settings | `/settings` | Application settings | Production |
| Status | `/status` | System status | Production |

---

## Technology Stack

### Technology Stack Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    TECHNOLOGY STACK                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  BACKEND STACK:                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Language:     Python 3.9+                              │   │
│  │  Framework:    FastAPI                                  │   │
│  │  Package Mgr:  UV (recommended)                         │   │
│  │  ML Libraries: scikit-learn, transformers, torch        │   │
│  │  Data:         pandas, numpy                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  FRONTEND STACK:                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Framework:    Next.js 14                                │   │
│  │  Library:      React 18                                  │   │
│  │  Language:     TypeScript                                │   │
│  │  UI Library:   Mantine v7                                │   │
│  │  Runtime:      Bun (recommended)                         │   │
│  │  Design:       Neobrutal Design System                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  INFRASTRUCTURE:                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Backend Hosting:  Railway                               │   │
│  │  Frontend Hosting: Netlify                               │   │
│  │  Version Control: GitHub                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  TESTING:                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Backend:  pytest (100% coverage)                       │   │
│  │  Frontend: Jest, Playwright                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack Table

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Backend Language** | Python | 3.9+ | Core language |
| **Backend Framework** | FastAPI | Latest | Web framework |
| **Package Manager** | UV | Latest | Python package management |
| **ML Framework** | scikit-learn | Latest | Traditional ML algorithms |
| **LLM Framework** | transformers | Latest | LLM support |
| **Deep Learning** | torch | Latest | Deep learning models |
| **Data Processing** | pandas | Latest | Data manipulation |
| **Numerical Computing** | numpy | Latest | Numerical operations |
| **Frontend Framework** | Next.js | 14 | React framework |
| **UI Library** | React | 18 | Component library |
| **Type System** | TypeScript | Latest | Type safety |
| **UI Components** | Mantine | v7 | UI component library |
| **Frontend Runtime** | Bun | Latest | JavaScript runtime |
| **Backend Hosting** | Railway | - | Production hosting |
| **Frontend Hosting** | Netlify | - | Production hosting |
| **Backend Testing** | pytest | Latest | Unit & integration tests |
| **Frontend Testing** | Jest | Latest | Unit tests |
| **E2E Testing** | Playwright | Latest | End-to-end tests |

---

## Project Statistics

### Codebase Statistics

```
┌─────────────────────────────────────────────────────────────────┐
│                    CODEBASE STATISTICS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Backend:                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Route Modules:        24                               │   │
│  │  Service Modules:      35                               │   │
│  │  API Endpoints:        45+                              │   │
│  │  Test Coverage:        100%                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Frontend:                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Pages:                 36                               │   │
│  │  Components:           50+                              │   │
│  │  Design System:        Neobrutal                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Project:                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Contributors:          4                              │   │
│  │  Total Commits:         84+                             │   │
│  │  Open Issues:           65+                              │   │
│  │  Good First Issues:     15+                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Project Metrics Table

| Metric | Value | Status |
|--------|-------|--------|
| **Test Coverage** | 100% | Complete |
| **API Endpoints** | 45+ | Production Ready |
| **Frontend Pages** | 36 | Production Ready |
| **Backend Routes** | 24 | Production Ready |
| **Backend Services** | 35 | Production Ready |
| **Contributors** | 3 | Active |
| **Total Commits** | 84+ | Growing |
| **Open Issues** | 65+ | Active |
| **Good First Issues** | 15+ | Available |
| **Models Tested** | 11+ | Verified |
| **Features** | 12+ | Production Ready |

---

## Contributors

### Contributors Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTRIBUTORS                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Core Contributors:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  adhit-r                   81 contributions            │   │
│  │  • Platform architecture                                 │   │
│  │  • Core features                                         │   │
│  │  • Documentation                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Code Contributors:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  solidcode79                3 contributions             │   │
│  │  • E2E test improvements (PR #108)                       │   │
│  │  • Test stability                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Code Reviewers:                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  resmasrirajendran-ui      Code reviews                  │   │
│  │  • Frontend code review                                  │   │
│  │  • UI/UX feedback                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Contributors Table

| Contributor | Contributions | Role | Focus Areas |
|-------------|---------------|------|-------------|
| **[adhit-r](https://github.com/adhit-r)** | 81 commits | Core Developer | Platform architecture, core features, documentation |
| **[solidcode79](https://github.com/solidcode79)** | 3 commits | Contributor | E2E testing, test stability (PR #108) |
| **[resmasrirajendran-ui](https://github.com/resmasrirajendran-ui)** | Code Reviews | Code Reviewer | Frontend code review, UI/UX feedback |
| **[kishore8220](https://github.com/kishore8220)** | Code Reviews | Code Reviewer/Repo Maintainer/Developer | Overall repo maintainer |

kishore8220

**Thank you** to all contributors who help make FairMind better. See [CONTRIBUTORS.md](./CONTRIBUTORS.md) for complete contributor details.

---

## Development Guide

### Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Setup Development Environment                                │
│     ┌─────────────────────────────────────────────────────┐    │
│     │  Backend:  uv sync                                  │    │
│     │  Frontend: bun install                              │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                   │
│  2. Run Development Servers                                      │
│     ┌─────────────────────────────────────────────────────┐    │
│     │  Backend:  uv run python -m uvicorn api.main:app   │    │
│     │  Frontend: bun run dev                              │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                   │
│  3. Run Tests                                                    │
│     ┌─────────────────────────────────────────────────────┐    │
│     │  Backend:  pytest --cov                            │    │
│     │  Frontend: bun test                                │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                   │
│  4. Build for Production                                         │
│     ┌─────────────────────────────────────────────────────┐    │
│     │  Backend:  uv run python -m uvicorn api.main:app   │    │
│     │  Frontend: bun run build && bun run start          │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Development Commands

| Task | Backend | Frontend |
|------|---------|----------|
| **Install Dependencies** | `uv sync` | `bun install` |
| **Run Development Server** | `uv run python -m uvicorn api.main:app --reload` | `bun run dev` |
| **Run Tests** | `pytest` | `bun test` |
| **Run Tests with Coverage** | `pytest --cov` | `bun run test:coverage` |
| **Lint Code** | `ruff check .` | `bun run lint` |
| **Format Code** | `ruff format .` | `bun run format` |
| **Build for Production** | `uv run python -m uvicorn api.main:app` | `bun run build` |
| **Start Production** | Same as build | `bun run start` |

### Testing Strategy

| Test Type | Tool | Coverage | Status |
|-----------|------|----------|--------|
| **Backend Unit Tests** | pytest | 100% | Complete |
| **Backend Integration Tests** | pytest | High | Complete |
| **Frontend Unit Tests** | Jest | Active | In Progress |
| **E2E Tests** | Playwright | Active | In Progress |
| **API Tests** | pytest | Complete | Complete |

---

## Documentation

### Documentation Structure

| Document | Description | Link |
|----------|-------------|------|
| **Setup Guide** | Complete installation instructions | [SETUP.md](./SETUP.md) |
| **Contributing Guide** | How to contribute | [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md) |
| **Contributors** | List of contributors | [CONTRIBUTORS.md](./CONTRIBUTORS.md) |
| **Roadmap** | Project roadmap and milestones | [ROADMAP.md](./ROADMAP.md) |
| **API Documentation** | Interactive API docs | [api.fairmind.xyz/docs](https://api.fairmind.xyz/docs) |
| **Modern Bias Guide** | LLM bias detection guide | [docs/development/MODERN_BIAS_DETECTION_GUIDE.md](./docs/development/MODERN_BIAS_DETECTION_GUIDE.md) |
| **Multimodal Guide** | Multimodal bias detection | [docs/development/MULTIMODAL_BIAS_DETECTION_SUMMARY.md](./docs/development/MULTIMODAL_BIAS_DETECTION_SUMMARY.md) |

---

## Live Demo

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Application** | [app-demo.fairmind.xyz](https://app-demo.fairmind.xyz) | Main application interface |
| **Backend API** | [api.fairmind.xyz](https://api.fairmind.xyz) | REST API endpoint |
| **API Documentation** | [api.fairmind.xyz/docs](https://api.fairmind.xyz/docs) | Interactive Swagger UI |

---

## Contributing

We welcome contributions! FairMind is open source and community-driven.

### Quick Start for Contributors

1. **Pick an Issue**: Browse [good first issues](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
2. **Fork & Clone**: Fork the repo and clone your fork
3. **Create Branch**: `git checkout -b feature/your-feature-name`
4. **Make Changes**: Follow our [contributing guidelines](docs/CONTRIBUTING.md)
5. **Submit PR**: Open a pull request with your changes

### Why Contribute?

- **Make AI Better**: Help build tools that make AI systems more fair and transparent
- **Learn & Grow**: Work with cutting-edge AI/ML technologies
- **Build Portfolio**: Contribute to a meaningful open-source project
- **Join Community**: Connect with developers and researchers worldwide

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

| Resource | Link |
|----------|------|
| **Documentation** | [docs/](./docs/) |
| **Issues** | [GitHub Issues](https://github.com/adhit-r/fairmind/issues) |
| **Discussions** | [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions) |
| **Community** | [COMMUNITY.md](.github/COMMUNITY.md) |

---

**FairMind - Making AI fair, transparent, and accountable for everyone.**

*Built for the AI ethics community*
