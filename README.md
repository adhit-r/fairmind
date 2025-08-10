# FairMind Ethical Sandbox

**Building responsible AI systems for a better future**

A comprehensive AI governance platform for testing, monitoring, and ensuring ethical AI deployment through real-time analytics, bias detection, and compliance management.

# Core Philosophy
Purpose-Built Governance Workflow – More than just analytics; clear paths from insight to action.

Org-Scoped Registry & Runs – Persisted summaries for dashboards, auditability, and organizational compliance.

Actionable Next Steps – One-click synthetic counterfactual generation to validate and iterate immediately.

Lightweight Default Path – Works with just a model file and a minimal dataset; advanced integrations optional.

Opinionated UX – Objective-driven dashboard sections: Analyze, Monitor, Explain, Govern, Simulate.

Enterprise-Ready – Easy integration with Row-Level Security (RLS), approvals, audit trails, and alerts.
## Live Demo
ß
**Try the platform:** [https://app-demo.fairmind.xyz](https://app-demo.fairmind.xyz)

The demo starts with an empty dashboard. Click "Load Demo Data" to explore all features with synthetic data.



## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   Python        │    │   Supabase      │
│   Frontend      │◄──►│   FastAPI       │◄──►│   Database      │
│   (UI/UX)       │    │   (ML/AI)       │    │   (Auth/Data)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14 + TypeScript | Modern React UI with real-time updates |
| **Backend** | Python FastAPI | ML/AI services, bias analysis, compliance |
| **Database** | Supabase (PostgreSQL) | Data storage, auth, real-time subscriptions |
| **Knowledge Graph** | Neo4j AuraDB | Advanced relationship analysis |
| **Deployment** | Netlify | Static hosting for demo |

## Key Features

### Advanced Bias Detection
- **SHAP Analysis**: Model interpretability and feature importance
- **LIME Analysis**: Local interpretable model explanations
- **Knowledge Graph**: Neo4j-powered relationship analysis
- **Geographic Bias**: Cross-country cultural factor analysis
- **Model DNA**: Genetic lineage and inheritance tracking

### Real-time Monitoring
- Live dashboard with 22 specialized dashboards
- Real-time alerts and drift detection
- Performance monitoring and risk assessment
- Compliance tracking and audit trails

### AI Bill of Materials (AIBOM)
- Comprehensive model inventory
- Dependency tracking and vulnerability assessment
- Security attestation and compliance mapping
- Risk profiling and mitigation strategies

### Geographic & Cultural Analysis
- Cross-country bias detection
- Cultural factor analysis
- Regional compliance requirements
- Demographic fairness assessment

## Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd fairmind-ethical-sandbox

# Install dependencies
npm install
cd frontend && npm install --legacy-peer-deps

# Start development server
cd frontend && npm run dev

# Access the application
open http://localhost:3000
```

### Demo Deployment

```bash
# Deploy to demo subdomain
./deploy-demo.sh

# Demo will be available at:
# https://app-demo.fairmind.xyz
```

## Project Structure

```
fairmind-ethical-sandbox/
├── frontend/              # Next.js frontend application
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities and services
│   │   └── types/         # TypeScript definitions
│   ├── package.json       # Frontend dependencies
│   └── next.config.js     # Next.js configuration
├── backend/               # Python FastAPI backend
│   ├── main.py            # FastAPI application
│   ├── websocket.py       # Real-time WebSocket server
│   ├── requirements.txt   # Python dependencies
│   └── supabase/          # Database migrations
├── fairmind-website/      # Marketing website (Astro)
│   ├── src/               # Astro source files
│   ├── public/            # Static assets
│   ├── package.json       # Website dependencies
│   └── netlify.toml       # Deployment configuration
├── docs/                  # Comprehensive documentation
├── supabase/              # Database configuration
├── package.json           # Root project configuration
└── README.md              # This file
```

## Dashboard Features

### Main Dashboard
- Overview of all AI governance metrics
- Real-time alerts and notifications
- Quick access to all specialized dashboards

### Specialized Dashboards
1. **Advanced Bias Detection** - SHAP, LIME, Knowledge Graph analysis
2. **Geographic Bias Analysis** - Cross-country cultural factors
3. **Model DNA Signatures** - Genetic lineage and inheritance
4. **Real-time Monitoring** - Live alerts and drift detection
5. **Compliance Tracking** - AI Bill compliance and audit trails
6. **Analytics Dashboard** - Charts, visualizations, and metrics
7. **Knowledge Graph** - Neo4j-powered relationship analysis
8. **AIBOM Management** - AI Bill of Materials tracking

## Development

### Marketing Website
```bash
cd fairmind-website
npm install
npm run dev          # Start Astro development server
npm run build        # Build for production
```

### Frontend Development
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint
```

### Backend Development
```bash
cd backend
python main.py       # Start FastAPI server
# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management
```bash
# Start Supabase locally
npm run dev:supabase

# Reset database
npm run supabase:reset

# Push migrations
npm run supabase:db:push
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Governance Metrics
```bash
curl http://localhost:8000/governance/metrics
```

### Models
```bash
curl http://localhost:8000/models
```

### Simulations
```bash
curl http://localhost:8000/simulations
```

### AI Bill Requirements
```bash
curl http://localhost:8000/ai-bill/requirements
```

## Security & Compliance

- **Authentication**: Supabase Auth with role-based access
- **Data Privacy**: GDPR and CCPA compliance features
- **Audit Logging**: Comprehensive activity tracking
- **Encryption**: Data encryption at rest and in transit

## Real-time Features

The platform uses Supabase's real-time capabilities for:
- Live dashboard updates
- Real-time compliance monitoring
- Instant alert notifications
- Live model performance tracking

## Documentation

- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **[Feature Checklist](docs/features/FEATURE_CHECKLIST.md)** - Development progress tracking
- **[Architecture Guide](docs/architecture/)** - System architecture and design
- **[Setup Guides](docs/setup/)** - Installation and configuration
- **[API Documentation](docs/api/)** - API endpoints and usage
- **[Neo4j Setup](docs/guides/QUICK_NEO4J_SETUP.md)** - Knowledge graph setup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Fairmind Ethical Sandbox** - Building responsible AI systems for a better future.
