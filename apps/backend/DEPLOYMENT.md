# 🚀 FairMind Deployment Guide

## **Current Deployment Status**
- ✅ **Frontend**: Live at https://app-demo.fairmind.xyz
- ✅ **Backend**: Live at https://api.fairmind.xyz
- 🎯 **Phase**: Phase 2 - Simulation Engine & Real ML Execution

---

## **🌐 Railway Backend Configuration**

### **Project Details**
- **Project ID**: `5fc6533c-b90e-491d-ab27-0038534d9062`
- **Service ID**: `369ef2c0-382c-4276-84e6-5ce2fb9ad350`
- **Environment**: `production`
- **Public Domain**: `api.fairmind.xyz`

### **Environment Variables**
```bash
PHASE=2
ML_SIMULATION_ENABLED=true
MAX_FILE_SIZE_MB=100
ALLOWED_FILE_TYPES=csv,parquet
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### **Deployment Commands**
```bash
# Deploy to Railway
railway up

# Check status
railway status

# View logs
railway logs

# Set environment variables
railway variables set PHASE=2
railway variables set ML_SIMULATION_ENABLED=true
```

---

## **📱 Netlify Frontend Configuration**

### **Site Details**
- **Site ID**: `9a9e1fcc-0cf6-4a7e-81e7-60c5a137047c`
- **Domain**: `app-demo.fairmind.xyz`
- **Build Command**: `bun run build`
- **Publish Directory**: `out`

### **Environment Variables**
```bash
NEXT_PUBLIC_API_URL=https://api.fairmind.xyz
NEXT_PUBLIC_APP_URL=https://app-demo.fairmind.xyz
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### **Deployment Commands**
```bash
# Deploy to Netlify
netlify deploy --prod

# Check status
netlify status
```

---

## **🔗 API Endpoints**

### **Health & Status**
- `GET /health` - Health check
- `GET /api/system/status` - System status
- `GET /api/system/demo` - Demo information

### **ML Simulation Engine**
- `POST /api/v1/simulations/run` - Run ML simulations
- `GET /api/v1/simulations/algorithms/available` - List algorithms
- `GET /api/v1/simulations` - List simulation runs

### **Dataset Management**
- `POST /api/v1/datasets/upload` - Upload datasets
- `GET /api/v1/datasets` - List datasets
- `GET /api/v1/datasets/{id}` - Get dataset details

### **Bias Detection**
- `GET /api/v1/bias/templates` - List bias test templates
- `POST /api/v1/bias/analyze` - Run bias analysis
- `GET /api/v1/bias/results` - Get bias analysis results

### **AI/ML BOM**
- `GET /api/v1/ai-bom/models` - List models
- `POST /api/v1/ai-bom/scan` - Scan model for vulnerabilities
- `GET /api/v1/ai-bom/reports` - Get BOM reports

---

## **📊 Phase 2 Features**

### **ML Simulation Engine**
- **Algorithms**: Random Forest, Logistic/Linear Regression
- **Model Types**: Classification & Regression
- **Fairness Metrics**: Performance ratios across protected groups
- **Model Persistence**: Save/load trained models

### **Dataset Management**
- **File Types**: CSV, Parquet
- **Max Size**: 100MB
- **Schema Inference**: Automatic column analysis
- **Validation**: Column type and format checking

### **Bias Detection**
- **Templates**: 6 pre-built bias test templates
- **Libraries**: 12 testing libraries available
- **Categories**: Text, Image, Multimodal bias detection

---

## **🚀 Quick Deploy Commands**

### **Backend (Railway)**
```bash
cd apps/backend
railway up
```

### **Frontend (Netlify)**
```bash
cd apps/frontend
netlify deploy --prod
```

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

#### **4. Database Connection Issues**
```bash
# Verify Supabase credentials
railway variables set SUPABASE_URL=your_url
railway variables set SUPABASE_SERVICE_ROLE_KEY=your_key
```

---

## **🎯 Testing Deployment**

### **Health Check**
```bash
curl https://api.fairmind.xyz/health
```

### **System Status**
```bash
curl https://api.fairmind.xyz/api/system/status
```

### **Available Algorithms**
```bash
curl https://api.fairmind.xyz/api/v1/simulations/algorithms/available
```

---

**🎉 Your FairMind platform is ready for production!**

- **Frontend**: https://app-demo.fairmind.xyz
- **Backend API**: https://api.fairmind.xyz
- **Documentation**: See `docs/` directory for detailed guides
