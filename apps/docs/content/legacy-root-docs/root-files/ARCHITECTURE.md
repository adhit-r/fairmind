# FairMind Architecture

FairMind is built on a modern, scalable architecture designed for real-time AI governance.

## High-Level Overview

```mermaid
graph TD
    User[User] --> Frontend[Frontend (Next.js)]
    Frontend --> API[Backend API (FastAPI)]
    
    subgraph Backend
        API --> Auth[Auth Service]
        API --> Bias[Bias Detection Engine]
        API --> Compliance[Compliance Engine]
        API --> Remediation[Remediation Wizard]
        API --> Marketplace[Model Marketplace]
        
        Bias --> ML[Classic ML Libs]
        Bias --> LLM[LLM Evaluators]
        
        Remediation --> AIF360[AIF360 / sklearn]
    end
    
    subgraph Data
        API --> DB[(PostgreSQL)]
        API --> Cache[(Redis)]
        API --> VectorDB[(Vector Store)]
    end
    
    subgraph MLOps
        API --> WandB[Weights & Biases]
        API --> MLflow[MLflow]
    end
```

## Core Components

### 1. Backend (`apps/backend`)
*   **Framework**: FastAPI
*   **Language**: Python 3.11+
*   **Key Services**:
    *   `BiasDetectionService`: Core logic for fairness metrics.
    *   `RemediationWizardService`: Automated bias mitigation.
    *   `ReportGeneratorService`: PDF report generation.
    *   `MarketplaceService`: Model registry and discovery.

### 2. Frontend (`apps/frontend`)
*   **Framework**: Next.js 14 (App Router)
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS, Shadcn UI
*   **State Management**: React Hooks, Context

### 3. Data Layer
*   **PostgreSQL**: Primary transactional database (Users, Models, Reports).
*   **Redis**: Caching for real-time metrics and session data.
*   **Vector Store**: RAG system for regulatory compliance documents.

## Design Principles
*   **Domain-Driven Design (DDD)**: Code is organized by business domains (e.g., `domain/bias`, `domain/compliance`).
*   **Dependency Injection**: Services are injected to promote testability and modularity.
*   **Async First**: Heavy computations (bias analysis) are handled asynchronously.
