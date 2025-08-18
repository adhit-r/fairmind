# 🚀 Quick Railway Deployment Guide

## **Deploy to Railway in 5 Minutes**

### **Step 1: Install Railway CLI**
```bash
npm install -g @railway/cli
```

### **Step 2: Login to Railway**
```bash
railway login
```

### **Step 3: Initialize Project**
```bash
railway init
```

### **Step 4: Deploy**
```bash
railway up
```

### **Step 5: Set Custom Domain**
```bash
railway domain
# Enter: api.fairmind.xyz
```

### **Step 6: Set Environment Variables**
```bash
# Set Supabase configuration
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_KEY=your-service-role-key

# Set other required variables
railway variables set ENVIRONMENT=production
railway variables set JWT_SECRET=your-secret-key
```

### **Step 7: Verify Deployment**
```bash
# Check deployment status
railway status

# View logs
railway logs

# Test health endpoint
curl https://api.fairmind.xyz/health
```

## **🎯 Your API will be live at: https://api.fairmind.xyz**

### **✅ What's Included:**
- ✅ FastAPI application with all endpoints
- ✅ AI Governance features (Bias Detection, BOM, OWASP Security)
- ✅ CORS configured for frontend
- ✅ Health check endpoint
- ✅ Automatic HTTPS
- ✅ Environment variable management

### **🔗 Integration with Frontend:**
Your frontend at `https://app-demo.fairmind.xyz` is already configured to connect to `https://api.fairmind.xyz`.

### **📊 API Endpoints Available:**
- `GET /health` - Health check
- `GET /models` - List AI models
- `POST /models/upload` - Upload model
- `POST /bias/analyze` - Bias analysis
- `GET /bom/scan` - AI Bill of Materials
- `POST /owasp/analyze` - OWASP security testing
- `GET /docs` - API documentation

**Ready to deploy! Run the commands above to get your API live.** 🚀
