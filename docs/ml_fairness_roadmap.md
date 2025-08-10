# ML Fairness Platform Development Roadmap

## Project Overview

A comprehensive machine learning fairness auditing platform with real-time simulation capabilities, explainability features, and robust monitoring systems. The platform enables users to upload models and datasets, run fairness assessments, and visualize bias detection results.

---

## Development Phases

### Phase 0: Foundation Stabilization
**Duration:** 1-2 days

#### Frontend Tasks
- Configure environment variables (`NEXT_PUBLIC_API_URL` and Supabase authentication keys)
- Remove hardcoded demo data from pages and components
- Establish proper API communication patterns

#### Backend Tasks
- Validate upload and simulation endpoint functionality
- Implement comprehensive logging and error handling
- Standardize HTTP response shapes (2xx/4xx/5xx)

#### Database Tasks
- Execute database seeding procedures
- Verify user profiles and Row Level Security (RLS) implementation
- Create tables for simulation persistence and artifact storage

---

### Phase 1: Real Simulation Data Pipeline (Dataset Ingestion)
**Duration:** 3-5 days

#### Backend Development

##### Dataset Management
- **POST /datasets/upload** endpoint supporting CSV/Parquet formats
- Column validation and schema inference
- Persistent storage in `datasets/` directory
- Database persistence: `datasets` table with fields:
  - `id`, `path`, `schema_json`, `created_by`, `created_at`

##### Simulation Engine
- **POST /simulation/run** endpoint accepting:
  - Model path, dataset ID/path, target variable
  - Feature selection, protected attributes
- scikit-learn pickle model support with predict/predict_proba
- Performance metrics computation:
  - Accuracy, Precision, Recall, F1-Score, AUC

##### Fairness Assessment
- Demographic parity analysis
- Disparate impact measurement
- Equal opportunity evaluation
- Equalized odds calculation
- Subgroup-specific metrics across protected attributes

##### Data Persistence
- `simulation_runs` table structure:
  - `id`, `model_path`, `dataset_id`, `config_json`
  - `metrics_json`, `status`, `created_by`, `created_at`

#### Frontend Development

##### Enhanced Upload Interface
- Extended ModelUpload component with dataset upload capabilities
- Form validation for target variables, features, and protected attributes
- Interactive parameter selection interface

##### Simulation Management
- "Run Simulation" modal with dataset and parameter selection
- Real-time job status monitoring
- Results presentation with metric cards and download options

##### Data Visualization
- Subgroup breakdown tables
- Integration with existing chart components:
  - `fairness-chart`, `risk-heatmap`, `performance-matrix`
- Live data binding to simulation results

**Acceptance Criteria:** Complete model and dataset upload → simulation execution → real metrics visualization → database persistence

---

### Phase 2: Synthetic Data Generation
**Duration:** 2-4 days

#### Backend Implementation
- **POST /datasets/synthetic** endpoint for tabular data generation
- Schema template support with configurable distributions
- Normal and categorical distribution priors
- Protected attribute distribution control
- Consistent persistence with real dataset workflow

#### Frontend Development
- Synthetic dataset generation wizard
- Feature type and size configuration interface
- Correlation and distribution parameter controls
- Protected attribute distribution settings
- Clear data source labeling (synthetic vs. real)

**Acceptance Criteria:** Synthetic dataset generation → simulation execution → results visualization with proper source identification

---

### Phase 3: Explainability and Robustness Analysis
**Duration:** 3-5 days

#### Explainability Features
- SHAP integration for feature importance analysis
- Local and global explanation generation
- Model-type compatibility validation
- Top feature identification and ranking

#### Robustness Testing
- Feature perturbation analysis (noise injection, feature dropout)
- Robustness metric estimation
- Performance degradation assessment under adversarial conditions

#### Frontend Enhancements
- SHAP summary chart implementation
- Local explanation interface
- Robustness score panel
- Integration with `explainability-treemap` and `robustness-chart` components

---

### Phase 4: Monitoring and Drift Detection
**Duration:** 3-5 days

#### Backend Monitoring
- **POST /monitor/drift/run** endpoint for drift analysis
- Population Stability Index (PSI) and Kolmogorov-Smirnov test implementation
- Sliding window analysis for temporal patterns
- Persistent `drift_runs` table for historical tracking

#### Real-time Communication
- WebSocket or Server-Sent Events for job status updates
- Alternative polling mechanism for job progress monitoring

#### Frontend Dashboard
- Monitoring dashboard with trend visualization
- Alert system for significant drift detection
- Integration with `model-drift-chart` and `time-series-chart` components

---

### Phase 5: Storage and Governance
**Duration:** 2-4 days

#### Storage Migration
- Supabase Storage integration for artifact management
- Signed URL implementation for secure file access
- Migration from local `uploads/` directory

#### Metadata Management
- Comprehensive lineage tracking
- Artifact relationship mapping
- User association via profiles table

#### Access Control
- Role-Based Access Control (RBAC) implementation
- Enhanced Row Level Security policies:
  - Owner: read/write permissions
  - Organization: read access
  - Public: conditional read access with flagging

---

## Technical Implementation Details

### Backend Architecture (FastAPI)

#### Core Endpoints

**Dataset Management**
```
POST /datasets/upload
- Multipart form support
- CSV/Parquet detection
- Schema inference and validation
- Database persistence with owner tracking
```

**Simulation Engine**
```
POST /simulation/run
- Model loading (joblib/pickle)
- Dataset integration (pandas)
- Comprehensive metrics computation
- Persistent result storage
```

**Synthetic Data**
```
POST /datasets/synthetic
- Schema-driven generation
- Distribution parameter support
- Protected attribute handling
```

#### Advanced Features

**Explainability Pipeline**
- SHAP compatibility validation
- Feature importance extraction
- Local explanation generation

**Robustness Assessment**
- Systematic perturbation testing
- Performance delta computation
- Stability metric calculation

**Monitoring Infrastructure**
- Drift detection algorithms
- Time-window analysis
- Historical comparison capabilities

### Database Schema (Supabase)

#### Core Tables

**Datasets Table**
```sql
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES profiles(id),
    path TEXT NOT NULL,
    schema_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Simulation Runs Table**
```sql
CREATE TABLE simulation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES profiles(id),
    model_path TEXT NOT NULL,
    dataset_id UUID REFERENCES datasets(id),
    config_json JSONB,
    metrics_json JSONB,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Security Policies

**Row Level Security Implementation**
- Dataset access: owner read/write, organizational read, conditional public read
- Simulation runs: owner read/write, organizational read, conditional public read
- Performance indexing on owner_id, created_at, and dataset_id

### Frontend Architecture (Next.js)

#### User Interface Components

**Dataset Management**
- Upload interface with drag-and-drop support
- Target variable and feature selection
- Protected attribute configuration
- Real-time validation feedback

**Simulation Interface**
- Model and dataset pairing
- Parameter configuration modal
- Job status monitoring
- Results presentation and export

**Visualization Suite**
- Real-time chart updates
- Interactive filtering and drilling
- Export capabilities for metrics and visualizations

---

## API Contracts

### Dataset Upload
```json
POST /datasets/upload
Content-Type: multipart/form-data

Response:
{
    "success": true,
    "dataset_id": "uuid",
    "path": "/path/to/dataset",
    "schema": {
        "columns": [{"name": "string", "type": "string"}],
        "rows": 1000
    }
}
```

### Synthetic Data Generation
```json
POST /datasets/synthetic
{
    "rows": 1000,
    "columns": [
        {
            "name": "age",
            "type": "numeric",
            "distribution": "normal",
            "params": {"mean": 35, "std": 10}
        }
    ],
    "protected_attributes": ["gender", "race"]
}
```

### Simulation Execution
```json
POST /simulation/run
{
    "model_path": "/path/to/model.pkl",
    "dataset_id": "uuid",
    "target": "outcome",
    "features": ["age", "income", "education"],
    "protected_attributes": ["gender", "race"]
}

Response:
{
    "success": true,
    "run_id": "uuid",
    "metrics": {
        "performance": {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1": 0.85
        },
        "fairness": {
            "demographic_parity": 0.03,
            "equalized_odds": 0.05,
            "subgroups": [...]
        }
    }
}
```

---

## Security and Compliance

### Data Protection
- Service-role key isolation from frontend
- File type and size validation
- Filename sanitization and security scanning
- CSV header validation and sanitization

### Rate Limiting
- Upload endpoint throttling
- Simulation execution limits
- User-based quotas

### Access Control
- Authentication requirement for all operations
- Resource ownership validation
- Organizational boundary enforcement

---

## Quality Assurance

### End-to-End Testing
- Complete workflow validation: upload → simulation → visualization → persistence
- Cross-browser compatibility testing
- Mobile responsiveness verification

### Unit Testing Coverage
- Metrics calculation accuracy
- Schema validation robustness
- Fairness function correctness

### Performance Testing
- Large dataset handling (chunked processing)
- Concurrent user simulation
- Timeout and resource management

---

## Deployment Timeline

### Week 1: Core Implementation
- Phase 1 completion with real data pipeline
- Visualization integration and testing
- Basic UI functionality verification

### Week 2: Advanced Features
- Explainability and robustness implementation
- User interface polish and optimization
- Drift detection foundation

### Week 3: Monitoring and Production
- Complete monitoring dashboard
- Storage migration to Supabase
- Background job implementation

---

## Success Metrics

### Technical Acceptance
- Zero hardcoded metrics in production interface
- Real-time simulation result computation and persistence
- Interactive visualizations with comprehensive tooltips and legends
- Secure multi-tenant data isolation

### User Experience
- Intuitive upload and configuration workflow
- Clear result presentation and export capabilities
- Historical simulation run access
- Responsive interface across devices

### Current Implementation Status

**Backend Progress:**
- POST /datasets/upload endpoint operational (CSV/Parquet support)
- Enhanced POST /simulation/run with real data processing
- scikit-learn model compatibility verified
- Performance and basic fairness metrics implemented

**Configuration:**
- Backend: `PORT=8001 python backend/main.py`
- Frontend: `http://localhost:3000`
- Environment: `NEXT_PUBLIC_API_URL=http://localhost:8001`

**Next Steps:**
- Dataset upload UI integration
- Real-time result visualization
- Database persistence validation