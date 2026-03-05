# Phase 2 Implementation Guide

## 🎯 **Overview**
This guide walks you through implementing and testing Phase 2: Simulation Engine & Real ML Execution in FairMind.

## 🚀 **What We've Built in Phase 2**

### **1. ML Simulation Engine**
- **File**: `apps/backend/api/services/simulation_service.py`
- **Purpose**: Executes real ML models on datasets and calculates fairness metrics
- **Features**: Model training, performance metrics, fairness analysis, model persistence

### **2. Simulation API Routes**
- **File**: `apps/backend/api/routes/simulations.py`
- **Purpose**: REST API endpoints for running simulations and managing results
- **Endpoints**: Run, list, get, delete, rerun, status, algorithms, validate

### **3. Phase 2 Enhanced Backend**
- **File**: `apps/backend/start_phase2_backend.py`
- **Purpose**: Complete backend with bias detection + dataset management + ML simulation
- **Features**: All services integrated, comprehensive system status, demo endpoints

### **4. ML Algorithms Supported**
- **Classification**: Random Forest, Logistic Regression
- **Regression**: Random Forest, Linear Regression
- **Features**: Hyperparameter customization, feature scaling, model persistence

### **5. Fairness Metrics**
- **Performance Ratios**: Compare metrics across protected groups
- **Group Analysis**: Individual performance for each protected attribute
- **Statistical Parity**: Equal prediction rates across groups

---

## 🔧 **Implementation Steps**

### **Step 1: Install ML Dependencies**

Ensure these Python packages are installed:
```bash
pip install scikit-learn pandas numpy joblib
```

**Required packages:**
- `scikit-learn` - ML algorithms and metrics
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `joblib` - Model persistence

### **Step 2: Start Phase 2 Backend**

```bash
cd apps/backend
source .venv/bin/activate
python start_phase2_backend.py
```

The backend will start on port 8000 with:
- Bias detection system (existing)
- Dataset management system (Phase 1)
- ML simulation engine (Phase 2 - NEW!)
- Combined API endpoints
- Interactive documentation at `/docs`

---

## 🧪 **Testing the ML Simulation Engine**

### **Test 1: System Status**

```bash
curl http://localhost:8000/api/system/status
```

**Expected Response:**
```json
{
  "success": true,
  "phase": "Phase 2 - Simulation Engine & Real ML Execution",
  "ml_simulation_engine": {
    "status": "active",
    "simulations_run": 0,
    "models_trained": 0,
    "algorithms_available": {
      "classification": ["random_forest", "logistic_regression"],
      "regression": ["random_forest", "linear_regression"]
    }
  }
}
```

### **Test 2: Available Algorithms**

```bash
curl http://localhost:8000/api/v1/simulations/algorithms/available
```

**Expected Response:**
```json
{
  "success": true,
  "algorithms": {
    "classification": {
      "random_forest": {
        "description": "Random Forest Classifier",
        "hyperparameters": {
          "n_estimators": {"type": "int", "default": 100, "min": 10, "max": 1000}
        }
      }
    },
    "regression": {
      "random_forest": {
        "description": "Random Forest Regressor",
        "hyperparameters": {
          "n_estimators": {"type": "int", "default": 100, "min": 10, "max": 1000}
        }
      }
    }
  }
}
```

### **Test 3: Validate Simulation Configuration**

```bash
curl -X POST http://localhost:8000/api/v1/simulations/validate-config \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "sample",
    "model_type": "regression",
    "algorithm": "random_forest",
    "target_column": "income",
    "feature_columns": ["age", "education", "experience"],
    "protected_attributes": ["gender", "race"]
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Configuration validation passed",
  "validation": {
    "dataset_shape": [20, 7],
    "available_columns": ["age", "income", "education", "experience", "gender", "race", "region"],
    "target_column": "income",
    "feature_columns": ["age", "education", "experience"],
    "protected_attributes": ["gender", "race"],
    "model_type": "regression",
    "algorithm": "random_forest"
  }
}
```

### **Test 4: Run ML Simulation**

```bash
curl -X POST http://localhost:8000/api/v1/simulations/run \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "sample",
    "model_type": "regression",
    "algorithm": "random_forest",
    "target_column": "income",
    "feature_columns": ["age", "education", "experience"],
    "protected_attributes": ["gender", "race"],
    "test_size": 0.2,
    "random_state": 42
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "simulation_id": "uuid",
  "results": {
    "simulation_id": "uuid",
    "dataset_id": "sample_income_data",
    "config": {
      "model_type": "regression",
      "algorithm": "random_forest",
      "target_column": "income",
      "feature_columns": ["age", "education", "experience"],
      "protected_attributes": ["gender", "race"]
    },
    "performance_metrics": {
      "mse": 1234567.89,
      "rmse": 1111.11,
      "r2_score": 0.85
    },
    "fairness_metrics": {
      "gender": {
        "group_0": {
          "mse": 987654.32,
          "rmse": 993.81,
          "r2_score": 0.87,
          "sample_size": 8
        },
        "group_1": {
          "mse": 1481481.48,
          "rmse": 1217.16,
          "r2_score": 0.83,
          "sample_size": 12
        },
        "fairness_ratios": {
          "r2_score_ratio": 0.95
        }
      }
    },
    "execution_time_ms": 1250,
    "status": "completed"
  },
  "message": "Simulation completed successfully"
}
```

### **Test 5: Get Simulation Results**

```bash
curl http://localhost:8000/api/v1/simulations/{simulation_id}
```

**Expected Response:**
```json
{
  "success": true,
  "simulation_id": "uuid",
  "results": {
    "simulation_id": "uuid",
    "performance_metrics": {
      "mse": 1234567.89,
      "rmse": 1111.11,
      "r2_score": 0.85
    },
    "fairness_metrics": {
      "gender": {
        "group_0": {"r2_score": 0.87, "sample_size": 8},
        "group_1": {"r2_score": 0.83, "sample_size": 12},
        "fairness_ratios": {"r2_score_ratio": 0.95}
      }
    },
    "status": "completed",
    "execution_time_ms": 1250
  }
}
```

### **Test 6: List Simulations**

```bash
curl http://localhost:8000/api/v1/simulations
```

**Expected Response:**
```json
{
  "success": true,
  "simulations": [
    {
      "simulation_id": "uuid",
      "dataset_id": "sample_income_data",
      "config": {
        "model_type": "regression",
        "algorithm": "random_forest"
      },
      "performance_metrics": {
        "r2_score": 0.85
      },
      "status": "completed",
      "execution_time_ms": 1250,
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

---

## 📊 **API Documentation**

### **Simulation Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/simulations/run` | Run ML simulation |
| `GET` | `/api/v1/simulations` | List simulations |
| `GET` | `/api/v1/simulations/{id}` | Get simulation results |
| `GET` | `/api/v1/simulations/{id}/status` | Get simulation status |
| `POST` | `/api/v1/simulations/{id}/rerun` | Rerun simulation |
| `DELETE` | `/api/v1/simulations/{id}` | Delete simulation |
| `GET` | `/api/v1/simulations/algorithms/available` | Get available algorithms |
| `POST` | `/api/v1/simulations/validate-config` | Validate configuration |

### **System Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | System overview |
| `GET` | `/health` | Health check |
| `GET` | `/api/system/status` | Detailed system status |
| `GET` | `/api/system/info` | System capabilities |
| `GET` | `/api/system/demo` | Demo information |

---

## 🔍 **Understanding the Results**

### **Performance Metrics**

#### **Classification Models:**
- **Accuracy**: Overall correct predictions
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1 Score**: Harmonic mean of precision and recall

#### **Regression Models:**
- **MSE**: Mean Squared Error
- **RMSE**: Root Mean Squared Error
- **R² Score**: Coefficient of determination (0-1, higher is better)

### **Fairness Metrics**

#### **Performance Ratios:**
- **R² Ratio**: Compare R² scores across protected groups
- **Accuracy Ratio**: Compare accuracy across groups (classification)
- **Precision Ratio**: Compare precision across groups (classification)

#### **Interpretation:**
- **Ratio = 1.0**: Perfect fairness (equal performance)
- **Ratio > 1.0**: Group 1 performs better than Group 0
- **Ratio < 1.0**: Group 0 performs better than Group 1
- **Target**: Ratios close to 1.0 indicate fair models

---

## 🎯 **Sample Use Cases**

### **Use Case 1: Income Prediction Fairness**

**Dataset**: Income prediction with gender and race as protected attributes
**Goal**: Ensure model performs equally well across demographic groups

**Configuration:**
```json
{
  "model_type": "regression",
  "algorithm": "random_forest",
  "target_column": "income",
  "feature_columns": ["age", "education", "experience"],
  "protected_attributes": ["gender", "race"]
}
```

**Expected Output:**
- Performance metrics (MSE, RMSE, R²)
- Fairness analysis across gender and race groups
- Performance ratios to identify bias

### **Use Case 2: Loan Approval Classification**

**Dataset**: Loan approval with age and region as protected attributes
**Goal**: Ensure equal opportunity across age groups and regions

**Configuration:**
```json
{
  "model_type": "classification",
  "algorithm": "logistic_regression",
  "target_column": "loan_approved",
  "feature_columns": ["income", "credit_score", "employment_years"],
  "protected_attributes": ["age", "region"]
}
```

**Expected Output:**
- Classification metrics (accuracy, precision, recall, F1)
- Fairness analysis across age and region groups
- Equal opportunity ratios

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```
ModuleNotFoundError: No module named 'sklearn'
```
**Solution**: Install scikit-learn: `pip install scikit-learn`

#### **2. Memory Errors**
```
MemoryError during model training
```
**Solution**: Reduce dataset size or use smaller models

#### **3. Configuration Validation Failures**
```
Target column not found in dataset
```
**Solution**: Check column names and ensure they exist in the dataset

#### **4. Model Training Failures**
```
ValueError: Input contains NaN
```
**Solution**: Ensure dataset has no missing values or handle them in preprocessing

### **Debug Mode**

Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### **Performance Tuning**

For large datasets:
- Use `test_size=0.1` for faster execution
- Reduce `n_estimators` for Random Forest
- Use simpler algorithms for quick testing

---

## 🎯 **Next Steps After Phase 2**

### **Phase 2 Complete ✅**
- [x] ML simulation engine working
- [x] Real model training and evaluation
- [x] Fairness metrics calculation
- [x] Performance analysis
- [x] Model persistence

### **Phase 3: Frontend Integration**
- [ ] Build simulation configuration UI
- [ ] Create results visualization dashboard
- [ ] Implement real-time status updates
- [ ] Add interactive fairness analysis

### **Phase 4: Advanced Features**
- [ ] Hyperparameter optimization
- [ ] Model comparison tools
- [ ] Bias mitigation techniques
- [ ] Automated fairness reports

---

## 📚 **Additional Resources**

### **Documentation**
- **Phase 1 Guide**: `docs/implementation/PHASE1_IMPLEMENTATION_GUIDE.md`
- **API Design**: `docs/api/SIMULATION_API_DESIGN.md`
- **Current Roadmap**: `docs/CURRENT_ROADMAP.md`

### **Code Files**
- **Simulation Service**: `apps/backend/api/services/simulation_service.py`
- **Simulation Routes**: `apps/backend/api/routes/simulations.py`
- **Phase 2 Backend**: `apps/backend/start_phase2_backend.py`

### **Sample Data**
- **Test Dataset**: `apps/backend/sample_datasets/sample_income_data.csv`

---

## 🎉 **Success Criteria**

Phase 2 is complete when:
- [x] ML simulation engine starts without errors
- [x] All simulation API endpoints respond correctly
- [x] Models train successfully on sample dataset
- [x] Performance metrics are calculated accurately
- [x] Fairness metrics are computed across protected groups
- [x] Models are saved and can be reloaded
- [x] System status shows all services active
- [x] Demo endpoint provides clear usage examples

**Congratulations! You've successfully implemented Phase 2 of FairMind's ML simulation capabilities!** 🚀

**What would you like to focus on next?**
