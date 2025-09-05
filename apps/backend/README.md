# 🚀 FairMind Phase 2 Backend

**Complete ML Simulation Engine with Bias Detection and Dataset Management**

## 🎯 **What This Is**
- **Phase 2 Backend** with full ML simulation capabilities
- **Bias Detection** across protected groups
- **Dataset Management** for CSV/Parquet files
- **Real ML Execution** with scikit-learn models
- **Fairness Analysis** with performance metrics

## 🚀 **Quick Start**

### **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend
python start_phase2_backend.py
```

### **Production Deployment**
```bash
# Deploy to Railway
railway up

# Your API will be live at: https://api.fairmind.xyz
```

## 📁 **Clean File Structure**
```
backend/
├── start_phase2_backend.py    # 🎯 Main Phase 2 backend
├── requirements.txt            # 📦 All dependencies
├── test_phase2.py             # 🧪 Phase 2 testing
├── RAILWAY_PHASE2_DEPLOYMENT.md  # 🚀 Deployment guide
├── api/                       # 🔌 API package
│   ├── routes/                # 🛣️ API endpoints
│   ├── services/              # ⚙️ Business logic
│   └── models/                # 📊 Data models
├── sample_datasets/           # 📊 Sample data for testing
├── models/                    # 🤖 Trained ML models
├── simulation_results/        # 📈 Simulation results
└── uploads/                   # 📁 Dataset uploads
```

## 🌐 **API Endpoints**

### **Core System**
- `GET /` - System overview
- `GET /health` - Health check
- `GET /api/system/status` - Detailed status
- `GET /api/system/demo` - Phase 2 demo info

### **ML Simulations**
- `POST /api/v1/simulations/run` - Run ML simulation
- `GET /api/v1/simulations/algorithms/available` - List algorithms
- `GET /api/v1/simulations/{id}` - Get simulation results

### **Datasets**
- `POST /api/v1/datasets/upload` - Upload dataset
- `GET /api/v1/datasets` - List datasets
- `GET /api/v1/datasets/{id}/schema` - Get schema

### **Bias Detection**
- `POST /api/v1/bias/detect` - Detect bias
- `GET /api/v1/bias/templates` - Available templates

## 🧪 **Testing**
```bash
# Test all Phase 2 components
python test_phase2.py

# Test specific simulation
python -c "
import asyncio
from test_phase2 import test_sample_simulation
asyncio.run(test_sample_simulation())
"
```

## 🚀 **Deployment Status**
- ✅ **Frontend**: Live at https://app-demo.fairmind.xyz
- 🔄 **Backend**: Phase 2 deploying to Railway
- 🌐 **API**: Will be live at https://api.fairmind.xyz

## 📚 **Documentation**
- **Deployment**: `RAILWAY_PHASE2_DEPLOYMENT.md`
- **API Docs**: http://localhost:8000/docs (when running locally)
- **Implementation**: `docs/implementation/PHASE2_IMPLEMENTATION_GUIDE.md`

---

**🎉 Your FairMind Phase 2 backend is clean, organized, and ready for production!**
