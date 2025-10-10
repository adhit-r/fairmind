# FairMind Project Structure

## Repository Organization
FairMind follows a monorepo structure with clear separation of concerns and organized by application domains.

## Top-Level Structure
```
fairmind-ethical-sandbox/
├── apps/                  # Main applications
├── docs/                  # Documentation
├── archive/               # Archived code and documentation
├── scripts/               # Utility scripts
├── k8s/                   # Kubernetes configurations
├── mlops/                 # MLOps configurations
└── supabase/              # Database configurations
```

## Applications Structure (`apps/`)

### Backend (`apps/backend/`)
```
backend/
├── api/                   # FastAPI application
│   ├── main.py           # Main application entry point
│   ├── routes/           # API route handlers
│   └── services/         # Business logic services
├── config/               # Configuration modules
│   ├── settings.py       # Application settings
│   ├── database.py       # Database configuration
│   ├── logging.py        # Logging configuration
│   └── auth.py           # Authentication configuration
├── database/             # Database models and connections
├── middleware/           # Custom middleware
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Modern Python project config
└── .env.example          # Environment variables template
```

### Frontend (`apps/frontend/`)
```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Reusable React components
│   ├── lib/              # Utilities and configurations
│   ├── providers/        # React context providers
│   └── styles/           # CSS and styling
├── package.json          # Node.js dependencies
├── next.config.js        # Next.js configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── tsconfig.json         # TypeScript configuration
```

### ML (`apps/ml/`)
```
ml/
├── data/                 # Data management
│   ├── raw/             # Raw datasets
│   ├── processed/       # Processed datasets
│   └── features/        # Feature engineering
├── models/              # ML model implementations
├── pipelines/           # Data and training pipelines
├── evaluation/          # Model evaluation scripts
└── requirements.txt     # ML-specific dependencies
```

### Website (`apps/website/`)
```
website/
├── src/                 # Astro source files
├── public/              # Static assets
├── astro.config.mjs     # Astro configuration
└── package.json         # Dependencies
```

## Key Directories

### Documentation (`docs/`)
- **api/**: API documentation
- **architecture/**: System architecture docs
- **business/**: Business and strategy docs
- **deployment/**: Deployment guides
- **development/**: Development guides
- **implementation/**: Implementation details
- **ml/**: ML engineering documentation
- **research/**: Research papers and findings

### Configuration Files
- **Backend**: `.env`, `.env.example`, `.env.production`
- **Frontend**: `.env.local`, `.env.example`, `.env.production`
- **Database**: `supabase/` directory with SQL migrations
- **Deployment**: `k8s/` for Kubernetes, `mlops/` for ML operations

## File Naming Conventions

### Python Files (Backend)
- **Snake case**: `bias_detection_service.py`
- **Test files**: `test_*.py` or `*_test.py`
- **Configuration**: `settings.py`, `database.py`
- **Services**: `*_service.py`
- **Models**: `models.py` or `*_models.py`

### TypeScript/JavaScript Files (Frontend)
- **PascalCase for components**: `GlassmorphicCard.tsx`
- **camelCase for utilities**: `useApi.ts`
- **kebab-case for pages**: `bias-detection/page.tsx`
- **Configuration**: `next.config.js`, `tailwind.config.js`

### Directory Conventions
- **Lowercase with hyphens**: `bias-detection/`, `ai-bom/`
- **Plural for collections**: `components/`, `services/`, `routes/`
- **Singular for single purpose**: `config/`, `middleware/`

## Import Patterns

### Backend Python Imports
```python
# Standard library
import os
from pathlib import Path

# Third-party
from fastapi import FastAPI
import pandas as pd

# Local imports
from ..config.settings import settings
from ..services.bias_detection_service import BiasDetectionService
```

### Frontend TypeScript Imports
```typescript
// React and Next.js
import React from 'react';
import { NextPage } from 'next';

// Third-party libraries
import { Card, Text } from '@mantine/core';

// Local imports
import { GlassmorphicCard } from '@/components/GlassmorphicCard';
import { useApi } from '@/hooks/useApi';
```

## Environment Configuration

### Backend Environment Files
- **Development**: `.env` (local development)
- **Production**: `.env.production` (production settings)
- **Template**: `.env.example` (example configuration)

### Frontend Environment Files
- **Development**: `.env.local` (local development)
- **Production**: `.env.production` (production settings)
- **Template**: `.env.example` (example configuration)

## Testing Structure

### Backend Tests
```
tests/
├── __init__.py
├── conftest.py           # Pytest configuration
├── test_api.py           # API endpoint tests
├── test_services/        # Service layer tests
└── test_integration/     # Integration tests
```

### Frontend Tests
```
src/
├── components/
│   └── __tests__/        # Component tests
├── hooks/
│   └── __tests__/        # Hook tests
└── utils/
    └── __tests__/        # Utility tests
```

## Asset Organization

### Backend Assets
- **Models**: `models/` - Trained ML models
- **Datasets**: `sample_datasets/` - Sample data files
- **Uploads**: `uploads/` - User uploaded files
- **Results**: `simulation_results/` - Analysis results

### Frontend Assets
- **Images**: `public/images/` - Static images
- **Icons**: Tabler Icons via npm package
- **Styles**: `src/styles/` - CSS modules and global styles

## Archive Structure
The `archive/` directory contains:
- **code/**: Archived code implementations
- **documentation/**: Historical documentation
- **datasets/**: Archived datasets
- Organized by date and feature for easy reference

## Development Workflow Directories
- **scripts/**: Utility scripts for backup, deployment, security scanning
- **k8s/**: Kubernetes deployment configurations
- **mlops/**: MLOps pipeline configurations
- **supabase/**: Database migrations and setup scripts

## Best Practices

### File Organization
- Keep related files together in logical directories
- Use consistent naming conventions across the project
- Separate configuration from implementation code
- Group tests near the code they test

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports last
- Use absolute imports where possible

### Configuration Management
- Use environment variables for configuration
- Provide example files for all environments
- Keep sensitive data out of version control
- Document all configuration options