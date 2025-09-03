# 🚀 Railway Phase 2 Deployment Guide

## **Update Existing Railway Deployment to Phase 2**

### **Current Status**
- ✅ **Frontend**: Live at `https://app-demo.fairmind.xyz`
- ✅ **Backend**: Live at `https://api.fairmind.xyz` (Phase 1)
- 🎯 **Goal**: Update backend to Phase 2 with ML simulation engine

---

## **Step 1: Update Railway Backend**

### **1.1 Update Requirements**
```bash
# Add ML dependencies to requirements.txt
echo "scikit-learn>=1.3.0" >> requirements.txt
echo "pandas>=2.0.0" >> requirements.txt
echo "numpy>=1.24.0" >> requirements.txt
echo "joblib>=1.3.0" >> requirements.txt
```

### **1.2 Update Railway Configuration**
```bash
# Set environment variables for Phase 2
railway variables set PHASE=2
railway variables set ML_SIMULATION_ENABLED=true
railway variables set MAX_FILE_SIZE_MB=100
railway variables set ALLOWED_FILE_TYPES=csv,parquet
```

### **1.3 Deploy Phase 2 Backend**
```bash
# Deploy the updated backend
railway up

# Verify deployment
railway status
```

---

## **Step 2: Test Phase 2 Endpoints**

### **2.1 Health Check**
```bash
curl https://api.fairmind.xyz/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "services": {
    "bias_detection": "active",
    "dataset_management": "active",
    "ml_simulation_engine": "active",
    "testing_library": "active"
  }
}
```

### **2.2 System Status**
```bash
curl https://api.fairmind.xyz/api/system/status
```

**Expected Response:**
```json
{
  "success": true,
  "phase": "Phase 2 - Simulation Engine & Real ML Execution",
  "ml_simulation_engine": {
    "status": "active",
    "algorithms_available": {
      "classification": ["random_forest", "logistic_regression"],
      "regression": ["random_forest", "linear_regression"]
    }
  }
}
```

### **2.3 Available Algorithms**
```bash
curl https://api.fairmind.xyz/api/v1/simulations/algorithms/available
```

---

## **Step 3: Update Frontend Configuration**

### **3.1 Update Environment Variables**
Your frontend is already configured to connect to `https://api.fairmind.xyz`, so it will automatically get the new Phase 2 capabilities.

### **3.2 Test Frontend Integration**
- Navigate to `https://app-demo.fairmind.xyz`
- The existing bias detection features should work
- New ML simulation capabilities will be available via API

---

## **Step 4: Verify Complete Integration**

### **4.1 Test ML Simulation**
```bash
# Run a sample simulation
curl -X POST https://api.fairmind.xyz/api/v1/simulations/run \
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

### **4.2 Test Dataset Management**
```bash
# List available algorithms
curl https://api.fairmind.xyz/api/v1/simulations/algorithms/available

# Get system demo info
curl https://api.fairmind.xyz/api/system/demo
```

---

## **Step 5: Production Verification**

### **5.1 Check All Services**
```bash
# Verify all Phase 2 services are active
curl https://api.fairmind.xyz/api/system/status | jq '.services'
```

### **5.2 Monitor Logs**
```bash
# Check Railway logs for any errors
railway logs
```

---

## **🎯 Expected Results After Deployment**

### **✅ Phase 2 Features Available:**
- **ML Simulation Engine**: Train real models on datasets
- **Performance Metrics**: Accuracy, precision, recall, F1, MSE, R²
- **Fairness Analysis**: Protected group performance analysis
- **Dataset Management**: Upload, analyze, and validate datasets
- **Model Persistence**: Save and reload trained models

### **✅ API Endpoints Available:**
- `POST /api/v1/simulations/run` - Run ML simulations
- `GET /api/v1/simulations/algorithms/available` - List algorithms
- `POST /api/v1/datasets/upload` - Upload datasets
- `GET /api/v1/datasets` - List datasets
- `GET /api/system/demo` - Phase 2 demo information

---

## **🔧 Troubleshooting**

### **Common Issues:**

#### **1. ML Dependencies Not Found**
```bash
# Ensure requirements.txt includes:
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
```

#### **2. Memory Issues**
```bash
# Set Railway memory limits
railway variables set RAILWAY_MEMORY_LIMIT=512MB
```

#### **3. File Upload Issues**
```bash
# Verify file size limits
railway variables set MAX_FILE_SIZE_MB=100
```

---

## **🎉 Success Criteria**

Phase 2 deployment is complete when:
- ✅ Health check shows all services active
- ✅ System status shows Phase 2
- ✅ ML simulation endpoints respond correctly
- ✅ Algorithm listing works
- ✅ Sample simulation runs successfully
- ✅ Frontend can connect to new endpoints

---

## **🚀 Next Steps After Deployment**

### **Phase 3: Frontend Integration**
- Build simulation configuration UI
- Create results visualization dashboard
- Add real-time simulation monitoring

### **Phase 4: Advanced Features**
- Hyperparameter optimization
- Model comparison tools
- Bias mitigation techniques

---

## **📞 Support**

If you encounter issues:
1. Check Railway logs: `railway logs`
2. Verify environment variables: `railway variables`
3. Test endpoints individually
4. Check the implementation guide: `docs/implementation/PHASE2_IMPLEMENTATION_GUIDE.md`

**Your Phase 2 deployment will be live at: https://api.fairmind.xyz** 🚀
