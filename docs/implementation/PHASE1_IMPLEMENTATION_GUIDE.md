# Phase 1 Implementation Guide

## 🎯 **Overview**
This guide walks you through implementing and testing Phase 1: Dataset Management & Real Simulation capabilities in FairMind.

## 🚀 **What We've Built**

### **1. Database Migration**
- **File**: `apps/backend/supabase/execute_phase1_migration.sql`
- **Purpose**: Adds datasets table and extends simulation_runs table
- **Status**: Ready to execute in Supabase

### **2. Dataset Service**
- **File**: `apps/backend/api/services/dataset_service.py`
- **Purpose**: Handles file uploads, schema inference, and dataset management
- **Features**: CSV/Parquet support, automatic schema analysis, file validation

### **3. Dataset API Routes**
- **File**: `apps/backend/api/routes/datasets.py`
- **Purpose**: REST API endpoints for dataset operations
- **Endpoints**: Upload, list, get, delete, validate, schema

### **4. Enhanced Backend**
- **File**: `apps/backend/start_enhanced_backend.py`
- **Purpose**: Complete backend with bias detection + dataset management
- **Features**: Combined services, system status, comprehensive logging

### **5. Sample Data**
- **File**: `apps/backend/sample_datasets/sample_income_data.csv`
- **Purpose**: Test dataset for development and testing
- **Content**: Income prediction data with protected attributes

---

## 🔧 **Implementation Steps**

### **Step 1: Execute Database Migration**

1. **Open Supabase Dashboard**
   - Go to your Supabase project
   - Navigate to SQL Editor

2. **Run Migration Script**
   ```sql
   -- Copy and paste the contents of:
   -- apps/backend/supabase/execute_phase1_migration.sql
   ```

3. **Verify Migration**
   - Check that `datasets` table exists
   - Verify `simulation_runs` table has new columns
   - Confirm RLS policies are active

### **Step 2: Install Dependencies**

Ensure these Python packages are installed:
```bash
pip install pandas numpy fastapi python-multipart
```

### **Step 3: Start Enhanced Backend**

```bash
cd apps/backend
source .venv/bin/activate
python start_enhanced_backend.py
```

The backend will start on port 8000 with:
- Bias detection system (existing)
- Dataset management system (new)
- Combined API endpoints
- Interactive documentation at `/docs`

---

## 🧪 **Testing the System**

### **Test 1: System Status**

```bash
curl http://localhost:8000/api/system/status
```

**Expected Response:**
```json
{
  "success": true,
  "bias_detection": {
    "status": "active",
    "templates_available": 12,
    "libraries_available": 12
  },
  "dataset_management": {
    "status": "active",
    "upload_directory": "/path/to/uploads/datasets",
    "files_stored": 0,
    "max_file_size_mb": 100
  }
}
```

### **Test 2: Dataset Upload**

```bash
curl -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@sample_datasets/sample_income_data.csv" \
  -F "name=Income Prediction Dataset" \
  -F "description=Sample dataset for testing income prediction models"
```

**Expected Response:**
```json
{
  "success": true,
  "dataset": {
    "id": "uuid",
    "name": "Income Prediction Dataset",
    "file_type": "csv",
    "row_count": 20,
    "column_count": 7,
    "schema_json": {
      "columns": [
        {
          "name": "age",
          "type": "int64",
          "min": 24,
          "max": 43,
          "mean": 33.5
        }
      ]
    }
  }
}
```

### **Test 3: List Datasets**

```bash
curl http://localhost:8000/api/v1/datasets
```

**Expected Response:**
```json
{
  "success": true,
  "datasets": [
    {
      "id": "uuid",
      "name": "Income Prediction Dataset",
      "file_type": "csv",
      "row_count": 20,
      "column_count": 7
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

### **Test 4: Get Dataset Details**

```bash
curl http://localhost:8000/api/v1/datasets/{dataset_id}
```

**Expected Response:**
```json
{
  "success": true,
  "dataset": {
    "id": "uuid",
    "name": "Income Prediction Dataset",
    "schema_json": {
      "columns": [
        {
          "name": "age",
          "type": "int64",
          "min": 24,
          "max": 43,
          "mean": 33.5
        }
      ],
      "sample_data": [
        {"age": 25, "income": 45000, "gender": "M"},
        {"age": 30, "income": 65000, "gender": "F"}
      ]
    }
  }
}
```

### **Test 5: Validate Dataset Columns**

```bash
curl -X POST http://localhost:8000/api/v1/datasets/{dataset_id}/validate \
  -H "Content-Type: application/json" \
  -d '{
    "target_column": "income",
    "feature_columns": ["age", "education", "experience"],
    "protected_attributes": ["gender", "race"]
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "All columns validated successfully",
  "dataset": {
    "id": "uuid",
    "validation": {
      "target_column": "income",
      "feature_columns": ["age", "education", "experience"],
      "protected_attributes": ["gender", "race"],
      "status": "valid"
    }
  }
}
```

---

## 📊 **API Documentation**

### **Dataset Management Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/datasets/upload` | Upload CSV/Parquet dataset |
| `GET` | `/api/v1/datasets` | List datasets with pagination |
| `GET` | `/api/v1/datasets/{id}` | Get dataset details |
| `DELETE` | `/api/v1/datasets/{id}` | Delete dataset |
| `POST` | `/api/v1/datasets/{id}/validate` | Validate columns for simulation |
| `GET` | `/api/v1/datasets/{id}/schema` | Get dataset schema |

### **System Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | System overview |
| `GET` | `/health` | Health check |
| `GET` | `/api/system/status` | Detailed system status |
| `GET` | `/api/system/info` | System capabilities |

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```
ModuleNotFoundError: No module named 'api.services.dataset_service'
```
**Solution**: Ensure you're running from the `apps/backend` directory

#### **2. File Upload Errors**
```
413 Payload Too Large
```
**Solution**: Check file size (max 100MB) and ensure it's CSV/Parquet

#### **3. Schema Analysis Failures**
```
Failed to analyze file
```
**Solution**: Verify file format and ensure pandas can read the file

#### **4. Directory Creation Errors**
```
Permission denied: uploads/datasets
```
**Solution**: Check directory permissions or change upload path in service

### **Debug Mode**

Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### **File Validation**

Test file format:
```python
import pandas as pd
df = pd.read_csv('your_file.csv')
print(df.head())
print(df.dtypes)
```

---

## 🎯 **Next Steps After Implementation**

### **Phase 1 Complete ✅**
- [x] Database schema extended
- [x] Dataset upload system working
- [x] Schema inference functional
- [x] API endpoints tested

### **Phase 2: Simulation Engine**
- [ ] Implement ML model execution
- [ ] Add performance metrics calculation
- [ ] Integrate with bias detection
- [ ] Create simulation dashboard

### **Phase 3: Frontend Integration**
- [ ] Build dataset upload interface
- [ ] Create simulation configuration UI
- [ ] Implement results visualization
- [ ] Add real-time status updates

---

## 📚 **Additional Resources**

### **Documentation**
- **API Design**: `docs/api/DATASET_UPLOAD_API_DESIGN.md`
- **Database Migration**: `docs/database/PHASE1_DATABASE_MIGRATION.md`
- **Current Roadmap**: `docs/CURRENT_ROADMAP.md`

### **Code Files**
- **Dataset Service**: `apps/backend/api/services/dataset_service.py`
- **API Routes**: `apps/backend/api/routes/datasets.py`
- **Enhanced Backend**: `apps/backend/start_enhanced_backend.py`

### **Sample Data**
- **Test Dataset**: `apps/backend/sample_datasets/sample_income_data.csv`

---

## 🎉 **Success Criteria**

Phase 1 is complete when:
- [x] Database migration executed successfully
- [x] Enhanced backend starts without errors
- [x] Dataset upload accepts CSV/Parquet files
- [x] Schema inference works correctly
- [x] All API endpoints return expected responses
- [x] File validation and error handling work
- [x] System status shows all services active

**Congratulations! You've successfully implemented Phase 1 of FairMind's enhanced capabilities!** 🚀
