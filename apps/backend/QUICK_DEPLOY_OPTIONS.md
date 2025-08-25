# 🚀 Quick Deployment Options (Avoid Build Timeouts)

## **Problem**: Build timeout due to large ML dependencies (PyTorch, CUDA)

## **Solution Options**:

### **Option 1: Lightweight Railway Deployment (Recommended)**
```bash
# Use lightweight requirements (no PyTorch)
cp requirements-light.txt requirements.txt

# Deploy with lightweight config
cp railway-light.json railway.json

# Deploy
railway up
```

### **Option 2: Render.com (Alternative Platform)**
```bash
# Create render.yaml
cat > render.yaml << 'EOF'
services:
  - type: web
    name: fairmind-api
    env: python
    buildCommand: pip install -r requirements-light.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.7
EOF

# Deploy to Render
# 1. Go to render.com
# 2. Connect your GitHub repo
# 3. Deploy automatically
```

### **Option 3: Fly.io (Fast Deployment)**
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
fly launch

# Deploy
fly deploy
```

### **Option 4: DigitalOcean App Platform**
```bash
# Use the existing Dockerfile
# Deploy via DigitalOcean web interface
# 1. Go to DigitalOcean App Platform
# 2. Connect your GitHub repo
# 3. Use Dockerfile deployment
```

### **Option 5: Heroku (Traditional)**
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create fairmind-api

# Deploy
git push heroku main
```

## **🎯 Recommended: Lightweight Railway**

### **Step 1: Switch to Lightweight Requirements**
```bash
cp requirements-light.txt requirements.txt
```

### **Step 2: Update Railway Config**
```bash
cp railway-light.json railway.json
```

### **Step 3: Deploy**
```bash
railway up
```

### **Step 4: Set Environment Variables**
```bash
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_KEY=your-service-role-key
railway variables set ENVIRONMENT=production
```

### **Step 5: Set Custom Domain**
```bash
railway domain
# Enter: api.fairmind.xyz
```

## **🔧 What's Removed in Lightweight Version:**
- ❌ PyTorch (2.8GB)
- ❌ CUDA libraries (1.5GB)
- ❌ scikit-learn (heavy ML)
- ❌ SDV (synthetic data)
- ❌ CTGAN (generative models)

## **✅ What's Still Available:**
- ✅ FastAPI application
- ✅ All API endpoints
- ✅ Bias detection (basic)
- ✅ BOM scanning
- ✅ OWASP security
- ✅ Model registry
- ✅ Database operations

## **🚀 Alternative: Use External ML Services**
For heavy ML operations, you can:
1. Use Google Colab for model training
2. Use Hugging Face for model hosting
3. Use AWS SageMaker for ML workloads
4. Use local development for ML features

## **📊 Expected Build Time:**
- **Lightweight**: 2-3 minutes
- **Full ML**: 15-20 minutes (timeout risk)

**Choose Option 1 for fastest deployment!** 🚀
