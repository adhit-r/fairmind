# LLM Bias Detection Implementation Guide

## Overview
FairMind's headline feature for 2026: Comprehensive LLM bias detection with WEAT, SEAT, StereoSet, CrowS-Pairs, Minimal Pairs, and BBQ tests. Includes explainability analysis, compliance assessment, and actionable recommendations.

## Architecture

### Backend (Ready ✅)
- **Service**: `src/application/services/modern_llm_bias_service.py`
- **Routes**: `api/routes/modern_bias_detection.py` (prefix: `/api/v1/modern-bias`)

#### Key Endpoints
- `POST /api/v1/modern-bias/comprehensive-evaluation` - Main evaluation endpoint
- `POST /api/v1/modern-bias/multimodal-detection` - Multimodal bias detection
- `POST /api/v1/modern-bias/explainability-analysis` - Explainability-specific analysis
- `GET /api/v1/modern-bias/bias-tests` - List available tests
- `GET /api/v1/modern-bias/bias-categories` - List bias categories
- `GET /api/v1/modern-bias/detection-results` - Fetch stored results from DB

#### Request Schema
```typescript
{
  model_outputs: Array<{
    text?: string
    image_url?: string
    audio_url?: string
    video_url?: string
    metadata?: Record<string, any>
    protected_attributes?: Record<string, any>
  }>
  model_type: 'llm' | 'image_gen' | 'audio_gen' | 'video_gen'
  evaluation_config?: {
    test_types?: string[]
    evaluation_datasets?: string[]
  }
  include_explainability?: boolean
  include_multimodal?: boolean
}
```

#### Response Schema
```typescript
{
  timestamp: string (ISO)
  model_type: string
  evaluation_summary: {
    total_tests: number
    tests_passed: number
    tests_failed: number
    overall_bias_rate: number
    evaluation_time?: string
  }
  bias_tests: {
    pre_deployment?: Record<string, any>  // Test results
    real_time_monitoring?: Record<string, any>
    post_deployment?: Record<string, any>
  }
  explainability_analysis: {
    methods_used?: string[]
    insights?: string[]
    visualizations?: string[]
    confidence?: number
  }
  overall_risk: 'low' | 'medium' | 'high' | 'critical'
  risk_factors?: string[]
  recommendations: string[]
  compliance_status: {
    gdpr_compliant?: boolean
    ai_act_compliant?: boolean
    fairness_score?: number
  }
}
```

### Frontend (Phase 1 Complete ✅)

#### Location
`apps/frontend/src/app/(dashboard)/modern-bias/page.tsx`

#### Components
1. **Test Configuration Tab** (`form` state)
   - LLM description textarea
   - Model type selector (radio buttons)
   - Bias test checkboxes
   - Protected attributes pills
   - Run evaluation button

2. **Results Tab** (`results` state)
   - Overall risk banner (colored)
   - Risk factors card
   - Evaluation summary grid
   - Compliance status card
   - Explainability analysis card
   - Recommendations card
   - Export buttons (PDF/JSON)

#### Styling
- Neobrutal design: 4px borders, hard shadows, sharp corners
- Color scheme:
  - Risk levels: green/yellow/orange/red
  - Primary: black borders, white background
  - Accents: matches FairMind brand (teal/orange)

#### State Management
```typescript
// Form state
{
  model_description: string
  model_type: 'llm' | 'image_gen' | 'audio_gen' | 'video_gen'
  selected_tests: string[]
  protected_attributes: string[]
}

// Results state
{
  timestamp: string
  model_type: string
  evaluation_summary: {...}
  bias_tests: {...}
  explainability_analysis: {...}
  overall_risk: string
  risk_factors: string[]
  recommendations: string[]
  compliance_status: {...}
}
```

## Implementation Phases

### Phase 1: Core UI & API Integration ✅ COMPLETE
- [x] Form design with all inputs
- [x] Results rendering with proper data display
- [x] API endpoint integration
- [x] Hook enhancements
- [x] Neobrutal styling

### Phase 2: Export Functionality 🔄 IN PROGRESS
**Estimated: 6-8 hours**

#### PDF Export
- Use `@react-pdf/renderer` or `pdfkit` for generation
- Template structure:
  ```
  1. Header with FairMind branding
  2. Executive Summary (overall risk, bias rate, pass/fail counts)
  3. Test Configuration Details
  4. Risk Assessment Section
     - Overall risk level
     - Risk factors list
  5. Compliance Status
     - Framework compliance table
     - Fairness score visualization
  6. Explainability Analysis
     - Methods used
     - Key insights
     - Visualization references
  7. Recommendations
     - Numbered action items
     - Priority indicators
  8. Footer with timestamp, digital signature
  ```

Implementation:
1. Create PDF generation utility `src/lib/export/pdf-generator.ts`
2. Add PDF export button handler in page.tsx
3. Implement template rendering
4. Add timestamp and digital signature
5. Test PDF generation with sample data

#### JSON Export
- Simple JSON stringify with indentation
- Include metadata (exported date, FairMind version)
- Machine-readable format for downstream systems

Implementation:
1. Add JSON export button handler
2. Create JSON formatter utility
3. Trigger download via blob URL
4. Support for scheduled exports

### Phase 3: Dashboard Integration 🔄 NEXT
**Estimated: 4-6 hours**

- Add bias detection widget to compliance dashboard
- Show latest evaluation summary
- Link to detailed results page
- Display bias trends over time
- Integration with risk scoring algorithm

Files to modify:
- `apps/frontend/src/app/(dashboard)/compliance-dashboard/page.tsx`
- Create `components/dashboard/BiasDetectionWidget.tsx`
- Create `components/charts/BiasScoreTrendChart.tsx`

### Phase 4: Advanced Features 🔄 FUTURE
**Estimated: 12-15 hours**

#### Model Comparison
- Side-by-side evaluation of multiple LLMs
- Comparative risk assessment
- Performance benchmarking
- Create `modern-bias/compare` route

#### Bias Visualization Enhancements
- Heatmaps for test categories
- Attention visualizations
- Activation patching results display
- Counterfactual examples

#### Evaluation History
- Timeline view of evaluations
- Trend analysis
- Historical comparison
- Store in database with audit trail

## Current Status

### What Works
✅ Form accepts LLM description and test configuration
✅ Results display with all data types
✅ Risk assessment and compliance display
✅ Explainability insights rendered
✅ API endpoints properly formatted
✅ Neobrutal design consistently applied

### What's Missing
- Export functionality (buttons are UI-only)
- Database storage of results
- Historical data retrieval
- Model comparison
- Advanced visualizations
- E2E integration tests

## Testing Strategy

### Unit Tests
```bash
npm run test -- modern-bias/page.test.tsx
```

### E2E Tests
```bash
npm run test:e2e -- modern-bias.spec.ts
```

Test scenarios:
1. Form submission with valid data
2. Form validation (required fields)
3. Results display with mock data
4. Export button functionality
5. Navigation between tabs
6. Risk level color coding

### Manual Testing Checklist
- [ ] Form accepts LLM description
- [ ] All 6 bias tests selectable
- [ ] Protected attributes configurable
- [ ] Results tab shows all data
- [ ] Risk banner color matches level
- [ ] Export buttons functional
- [ ] Responsive design on mobile
- [ ] Dark mode compatibility

## Database Schema (For Phase 3)

```sql
CREATE TABLE bias_evaluations (
  id UUID PRIMARY KEY,
  model_description TEXT,
  model_type VARCHAR(50),
  model_id VARCHAR(255),
  dataset_id VARCHAR(255),
  test_configuration JSONB,
  evaluation_summary JSONB,
  bias_tests JSONB,
  explainability_analysis JSONB,
  overall_risk VARCHAR(20),
  risk_factors TEXT[],
  recommendations TEXT[],
  compliance_status JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  user_id UUID REFERENCES users(id)
);

CREATE INDEX idx_model_id ON bias_evaluations(model_id);
CREATE INDEX idx_user_created ON bias_evaluations(user_id, created_at DESC);
```

## API Client Configuration

### Endpoints (Fixed)
`src/lib/api/endpoints.ts`
```typescript
modernBiasDetection: {
  comprehensiveEvaluation: '/api/v1/modern-bias/comprehensive-evaluation',
  multimodalDetection: '/api/v1/modern-bias/multimodal-detection',
  explainabilityAnalysis: '/api/v1/modern-bias/explainability-analysis',
  biasTests: '/api/v1/modern-bias/bias-tests',
  biasCategories: '/api/v1/modern-bias/bias-categories',
  evaluationDatasets: '/api/v1/modern-bias/evaluation-datasets',
  detectionResults: '/api/v1/modern-bias/detection-results',
  evaluationHistory: '/api/v1/modern-bias/evaluation-history',
  health: '/api/v1/modern-bias/health',
}
```

### Hooks
`src/lib/api/hooks/useModernBias.ts`
- `runComprehensiveEvaluation()` ✅
- `runWEATTest()` ✅
- `getBiasTests()` ✅
- `getBiasCategories()` ✅
- `getDetectionResults()` ✅ (Added Phase 1)
- `runExplainabilityAnalysis()` ✅ (Added Phase 1)

## Compliance & Audit

### Evidence Collection
- Evaluation results are audit-ready
- Timestamps on all results
- Risk factors support regulatory requirements
- Recommendations linked to NITI Aayog/RBI guidelines

### Compliance Frameworks
- GDPR: Fairness assessment in Article 13 compliance
- EU AI Act: High-risk classification in bias testing
- NITI Aayog: Bias mitigation recommendations align with guidelines
- RBI AI Framework: Fairness metrics included

## References

### Backend Service
- File: `src/application/services/modern_llm_bias_service.py`
- Methods:
  - `comprehensive_bias_evaluation()`
  - `detect_multimodal_bias()`
  - `_run_explainability_analysis()`

### Related Features
- **Explainability Studio**: Detailed explanation visualization
- **Multimodal Bias Detection**: Image, audio, video bias
- **PDF/DOCX Report Export**: Centralized export engine
- **Compliance Dashboard**: Risk scoring integration

## Known Limitations & Future Work

1. **Real-time Monitoring**: Currently simulation-only, needs production data feeds
2. **Visualizations**: Placeholder for attention heatmaps and activation maps
3. **Model Comparison**: Single model only, MVP limitation
4. **Scheduled Evaluations**: Not yet implemented (scheduler ready in backend)
5. **API Performance**: Large evaluation datasets may timeout (current: 60s)

## Next Session Priorities

1. **PDF Export** (6-8 hours)
   - Implement PDF generation
   - Create template system
   - Add digital signatures

2. **JSON Export** (2 hours)
   - Simple JSON formatter
   - Download mechanism

3. **Dashboard Widget** (4-6 hours)
   - Create bias score widget
   - Add trend visualization
   - Integrate with main dashboard

## Helpful Commands

```bash
# Start development server
npm run dev

# Run tests
npm run test
npm run test:e2e

# Build
npm run build

# Check types
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

## Contact & Questions

This is the headline feature for FairMind 2026. Regular updates to this document will track progress and integration with other features.

---
Last Updated: 2026-03-20
Status: Phase 1 Complete, Phase 2 In Progress
