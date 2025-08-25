# 🧪 Local Testing Guide - FairMind Platform

## 🚀 **Quick Start**

### **1. Start the Backend Server**
```bash
cd backend
uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Start the Frontend Server**
```bash
cd frontend
bun run dev
```

### **3. Run the Test Script**
```bash
./test-local.sh
```

---

## 📋 **Access URLs**

### **Frontend Pages**
- **Main Page**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **Model Upload**: http://localhost:3000/model-upload
- **Model Testing**: http://localhost:3000/model-testing
- **Analytics**: http://localhost:3000/analytics

### **Backend API**
- **Health Check**: http://localhost:8000/health
- **API Base**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🎯 **Demo Scenarios to Test**

### **Scenario 1: Dashboard Overview**
1. Navigate to http://localhost:3000/dashboard
2. Verify SQ1-specific demo data is displayed
3. Check team performance metrics
4. Test quick action buttons
5. Review recent activity feed

### **Scenario 2: Model Upload**
1. Navigate to http://localhost:3000/model-upload
2. Test drag-and-drop file upload
3. Fill in model metadata
4. Verify success confirmation
5. Test navigation back to dashboard

### **Scenario 3: Model Testing**
1. Navigate to http://localhost:3000/model-testing
2. Select a model from the list
3. Choose test type (bias, security, compliance)
4. Watch real-time progress tracking
5. Review detailed test results

### **Scenario 4: Analytics & Reporting**
1. Navigate to http://localhost:3000/analytics
2. Review overview metrics
3. Check trend analysis
4. Test team performance views
5. Verify report generation

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Frontend Not Loading**
```bash
# Kill existing processes
pkill -f "bun run dev"

# Clear Next.js cache
cd frontend
rm -rf .next
bun run dev
```

#### **Backend Not Responding**
```bash
# Kill existing processes
pkill -f "uvicorn"

# Restart backend
cd backend
uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Port Already in Use**
```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### **Client Component Errors**
- Ensure all components using React hooks have `"use client"` directive
- Check for missing imports or dependencies
- Clear browser cache and reload

---

## 📊 **Demo Data Overview**

### **Models Available**
1. **Credit Risk Assessment Model v2.1** (Risk Management)
2. **Customer Churn Predictor** (Customer Success)
3. **Revenue Forecasting Model** (Finance)
4. **Fraud Detection System** (Security)
5. **Market Sentiment Analyzer** (Trading - Archived)

### **Test Results**
- Bias detection tests with detailed metrics
- Security analysis with vulnerability assessment
- Performance testing with latency and throughput
- Compliance checks for GDPR, CCPA, SOX

### **Analytics Data**
- 12 months of trend data
- Team performance comparisons
- Issue distribution and severity
- Real-time notifications

---

## 🎯 **SQ1 Demo Checklist**

### **Pre-Demo Setup**
- [ ] Both servers running (frontend + backend)
- [ ] All pages accessible
- [ ] Demo data loaded
- [ ] Browser tabs prepared
- [ ] Screen sharing tested

### **Demo Flow**
- [ ] Welcome and introduction (5 minutes)
- [ ] Dashboard walkthrough (10 minutes)
- [ ] Model upload demo (10 minutes)
- [ ] Testing & analysis demo (10 minutes)
- [ ] Analytics & reporting (5 minutes)
- [ ] Q&A session (5-10 minutes)

### **Key Features to Highlight**
- [ ] Comprehensive model management
- [ ] Real-time bias detection
- [ ] Security vulnerability assessment
- [ ] Compliance monitoring
- [ ] Team performance tracking
- [ ] Automated reporting

---

## 📞 **Support**

### **If You Encounter Issues**
1. Check the troubleshooting section above
2. Verify both servers are running
3. Clear browser cache and reload
4. Check terminal logs for error messages
5. Restart servers if necessary

### **Demo Environment Status**
- **Frontend**: ✅ Running on http://localhost:3000
- **Backend**: ✅ Running on http://localhost:8000
- **Demo Data**: ✅ Loaded and ready
- **All Pages**: ✅ Accessible and functional

---

## 🎉 **Ready for SQ1 Demo!**

The platform is fully functional and ready for presentation to the SQ1 team. All features are working, demo data is comprehensive, and the interface is professional and intuitive.

**Happy Demo-ing! 🚀**
