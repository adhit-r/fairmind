# FairMind Ethical Sandbox

A comprehensive AI governance and bias detection platform for responsible AI development.

## Overview

FairMind Ethical Sandbox provides enterprise-grade tools for AI model governance, bias detection, security testing, and compliance monitoring. Built with modern technologies and a focus on accessibility and user experience.

## Project Structure

```
fairmind-ethical-sandbox/
├── apps/
│   ├── backend/          # FastAPI backend with AI governance APIs
│   ├── frontend/         # Next.js frontend with terminal-inspired UI
│   └── website/          # Documentation site (Astro)
├── docs/                 # Project documentation
├── infrastructure/       # Deployment and infrastructure configs
├── scripts/             # Utility scripts
├── supabase/            # Database configuration
└── tests/               # Test suites
```

## Quick Start

### Backend (FastAPI)
```bash
cd apps/backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8001
```

### Frontend (Next.js)
```bash
cd apps/frontend
bun install
bun dev
```

### Documentation
```bash
cd apps/website
bun install
bun dev
```

## Features

- **AI Model Governance** - Comprehensive model lifecycle management
- **Bias Detection** - Advanced fairness testing with multiple algorithms
- **Security Testing** - OWASP AI/LLM security assessment
- **Compliance Monitoring** - NIST, GDPR, and regulatory adherence
- **Modern UI/UX** - Terminal-inspired design with high accessibility

## Technology Stack

- **Backend**: FastAPI, Python, Supabase
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Documentation**: Astro, Fumadocs
- **Deployment**: Railway, Netlify

## Development

See individual app directories for specific development instructions:
- [Backend Development](apps/backend/README.md)
- [Frontend Development](apps/frontend/README.md)
- [Documentation](apps/website/README.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
