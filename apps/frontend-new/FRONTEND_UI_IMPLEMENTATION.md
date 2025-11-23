# 🎯 FairMind Frontend UI - MLOps Integration

## ✅ What We Built

This implementation adds comprehensive **dataset management** and **bias test history** features to the FairMind frontend, creating a complete MLOps workflow for bias detection.

---

## 📦 New Features

### 1. **Test History Page** (`/dashboard/tests`)
- **View all bias detection tests** in a searchable, filterable table
- **Filter by test type**: ML Bias vs LLM Bias
- **Search** by model ID, test ID, or summary
- **Quick statistics**: Total tests, passed, warnings, critical
- **Risk level badges**: Visual indicators for low/medium/high/critical
- **Direct navigation** to detailed test results

### 2. **Test Detail Page** (`/dashboard/tests/[testId]`)
- **Comprehensive test results** with full metrics breakdown
- **Visual representations**: Progress bars for each metric
- **Pass/Fail distribution** with percentage breakdowns
- **Group scores** for each protected attribute
- **Detailed interpretations** for each fairness metric
- **Actionable recommendations** for bias mitigation
- **Export functionality**: Download results as JSON

### 3. **Enhanced Dataset Management** (`/dashboard/datasets/[datasetId]`)
- **Dataset detail view** with complete metadata
- **Schema visualization**: All columns with data types
- **Data preview**: First N rows of the dataset
- **File statistics**: Row count, column count, file size
- **Quick actions**: Run bias test directly from dataset
- **Delete functionality**: Remove datasets with confirmation

### 4. **Updated Datasets Page** (`/dashboard/datasets`)
- **Clickable rows** for easy navigation
- **View button** to access dataset details
- **Upload dialog** for new datasets
- **Status indicators** for active datasets

---

## 🔧 Technical Implementation

### New API Endpoints (`/lib/api/endpoints.ts`)
```typescript
biasV2: {
  uploadDataset: '/api/v1/bias-v2/upload-dataset',
  detect: '/api/v1/bias-v2/detect',
  detectLLM: '/api/v1/bias-v2/detect-llm',
  getTest: (testId) => `/api/v1/bias-v2/test/${testId}`,
  datasets: '/api/v1/bias-v2/datasets',
  getDataset: (datasetId) => `/api/v1/bias-v2/datasets/${datasetId}`,
  deleteDataset: (datasetId) => `/api/v1/bias-v2/datasets/${datasetId}`,
  history: '/api/v1/bias-v2/history',
  statistics: '/api/v1/bias-v2/statistics',
}
```

### Custom React Hooks (`/lib/api/hooks/useTestHistory.ts`)
- `useTestHistory()` - Fetch and filter test history
- `useTestStatistics()` - Get aggregated statistics
- `useTestDetail()` - Fetch detailed test results

### Key Components
- **Test History Table**: Sortable, filterable, paginated
- **Test Detail Cards**: Modular metric displays
- **Dataset Schema Grid**: Visual column type indicators
- **Progress Visualizations**: Custom progress bars for metrics

---

## 🎨 UI/UX Features

### Design System
- **Brutal Design**: Consistent 2px black borders, shadow effects
- **Color-coded Risk Levels**:
  - 🟢 Low: Green (#22c55e)
  - 🟡 Medium: Yellow (#eab308)
  - 🟠 High: Orange (#f97316)
  - 🔴 Critical: Red (#ef4444)

### Interactive Elements
- **Hover effects** on table rows
- **Loading skeletons** for better UX
- **Toast notifications** for actions
- **Confirmation dialogs** for destructive actions

---

## 📊 Data Flow

```
User Action → Frontend Hook → API Client → Backend (bias-v2) → Supabase
                                                                    ↓
                                                            bias_test_results
                                                            datasets
```

### Test History Flow
1. User navigates to `/dashboard/tests`
2. `useTestHistory()` hook fetches from `/api/v1/bias-v2/history`
3. Backend queries Supabase `bias_test_results` table
4. Results displayed in table with filters
5. Click test → Navigate to `/dashboard/tests/[testId]`
6. `useTestDetail()` fetches full results
7. Display metrics, visualizations, recommendations

### Dataset Management Flow
1. User uploads dataset via `/dashboard/datasets`
2. File sent to `/api/v1/bias-v2/upload-dataset`
3. Backend stores in Supabase Storage + metadata in DB
4. Dataset appears in list with ID
5. Click dataset → Navigate to `/dashboard/datasets/[datasetId]`
6. Display schema, preview, metadata
7. "Run Bias Test" button → Pre-fill bias detection form

---

## 🚀 Usage Examples

### Running a Bias Test
```typescript
// 1. Upload dataset
POST /api/v1/bias-v2/upload-dataset
Body: FormData with CSV file

// 2. Run bias detection
POST /api/v1/bias-v2/detect
Body: {
  model_id: "credit-model-v1",
  dataset_id: "ds_20251123_abc123",
  protected_attribute: "gender",
  prediction_column: "approved",
  fairness_threshold: 0.8
}

// 3. View results
GET /api/v1/bias-v2/test/ml-test-20251123010000
```

### Viewing Test History
```typescript
// Get all tests
GET /api/v1/bias-v2/history?limit=50&offset=0

// Filter by model
GET /api/v1/bias-v2/history?model_id=credit-model-v1

// Filter by type
GET /api/v1/bias-v2/history?test_type=ml_bias
```

### Getting Statistics
```typescript
// Overall statistics
GET /api/v1/bias-v2/statistics

// Model-specific statistics
GET /api/v1/bias-v2/statistics?model_id=credit-model-v1

// Returns:
{
  total_tests: 42,
  ml_tests: 30,
  llm_tests: 12,
  risk_distribution: {
    low: 20,
    medium: 15,
    high: 5,
    critical: 2
  },
  pass_rate: 0.71
}
```

---

## 🔗 Integration with Backend

### Backend Requirements
The backend (`/apps/backend`) already has:
- ✅ Supabase integration (`services/bias_test_results.py`)
- ✅ Dataset storage (`services/dataset_storage.py`)
- ✅ Bias detection v2 API (`api/routes/bias_detection_v2.py`)
- ✅ Database schema (`supabase/bias_test_results_setup.sql`)

### Supabase Schema
```sql
-- Test Results Table
bias_test_results (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  model_id TEXT NOT NULL,
  dataset_id TEXT,
  test_type TEXT CHECK (test_type IN ('ml_bias', 'llm_bias')),
  timestamp TIMESTAMP WITH TIME ZONE,
  overall_risk TEXT CHECK (overall_risk IN ('low', 'medium', 'high', 'critical')),
  metrics_passed INTEGER,
  metrics_failed INTEGER,
  results JSONB,
  summary TEXT,
  recommendations TEXT[],
  metadata JSONB
)
```

---

## 🎯 Next Steps: MLOps Integrations

Now that the UI foundation is complete, you can add:

### Option 1: Weights & Biases (W&B) Integration
- Log test results to W&B
- Track metrics over time
- Compare model versions
- Team collaboration

### Option 2: MLflow Integration
- Open-source experiment tracking
- Self-hosted option
- Model registry
- Artifact storage

### Option 3: DVC Integration
- Data version control
- Dataset lineage tracking
- Reproducible pipelines

---

## 📝 Files Created/Modified

### New Files
- `/apps/frontend-new/src/lib/api/hooks/useTestHistory.ts`
- `/apps/frontend-new/src/app/(dashboard)/tests/page.tsx`
- `/apps/frontend-new/src/app/(dashboard)/tests/[testId]/page.tsx`
- `/apps/frontend-new/src/app/(dashboard)/datasets/[datasetId]/page.tsx`

### Modified Files
- `/apps/frontend-new/src/lib/api/endpoints.ts` - Added biasV2 endpoints
- `/apps/frontend-new/src/app/(dashboard)/datasets/page.tsx` - Added navigation

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] Upload a dataset via `/dashboard/datasets`
- [ ] Run a bias test using the dataset
- [ ] View test in history at `/dashboard/tests`
- [ ] Click test to see detailed results
- [ ] Check all metrics display correctly
- [ ] Verify recommendations appear
- [ ] Export test results as JSON
- [ ] Navigate to dataset detail page
- [ ] Verify schema and preview display
- [ ] Delete a dataset (with confirmation)

### API Testing
```bash
# Test history endpoint
curl http://localhost:8000/api/v1/bias-v2/history

# Test statistics endpoint
curl http://localhost:8000/api/v1/bias-v2/statistics

# Test detail endpoint
curl http://localhost:8000/api/v1/bias-v2/test/ml-test-20251123010000
```

---

## 🎨 Screenshots

### Test History Page
- Filterable table with search
- Risk level badges
- Quick statistics cards
- Responsive design

### Test Detail Page
- Comprehensive metrics breakdown
- Visual progress indicators
- Group score comparisons
- Actionable recommendations

### Dataset Detail Page
- Schema visualization
- Data preview table
- Metadata display
- Quick action buttons

---

## 🔒 Security Considerations

- ✅ **Row Level Security (RLS)**: Users can only see their own tests/datasets
- ✅ **JWT Authentication**: All API calls require valid token
- ✅ **Permission checks**: `require_permission()` decorators on endpoints
- ✅ **Input validation**: Pydantic models validate all inputs
- ✅ **Confirmation dialogs**: Destructive actions require confirmation

---

## 📚 Documentation

### For Users
- Navigate to `/dashboard/tests` to view all bias tests
- Click any test to see detailed metrics and recommendations
- Use filters to find specific tests
- Export results for reporting

### For Developers
- All API endpoints are in `endpoints.ts`
- Custom hooks are in `lib/api/hooks/`
- Page components are in `app/(dashboard)/`
- Backend integration is via `api-client.ts`

---

## ✨ Summary

We've successfully built:
1. ✅ **Test History UI** - Complete with filtering and search
2. ✅ **Test Detail View** - Comprehensive metrics visualization
3. ✅ **Dataset Management** - Upload, view, delete datasets
4. ✅ **Dataset Detail View** - Schema, preview, metadata
5. ✅ **API Integration** - Full backend connectivity
6. ✅ **Type Safety** - TypeScript interfaces for all data
7. ✅ **Error Handling** - Proper loading states and error messages
8. ✅ **Responsive Design** - Works on all screen sizes

**The foundation is now ready for MLOps integrations like W&B, MLflow, or DVC!** 🚀
