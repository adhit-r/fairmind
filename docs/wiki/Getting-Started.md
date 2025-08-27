# 🚀 Getting Started with FairMind

Welcome to FairMind! This guide will help you get up and running with the ethical AI governance platform quickly.

## 🎯 **What You'll Learn**

By the end of this guide, you'll have:
- ✅ FairMind installed and running locally
- ✅ Understanding of the core features
- ✅ Ability to upload and test your first model
- ✅ Knowledge of the testing infrastructure

## 📋 **Prerequisites**

### **System Requirements**
- **Operating System**: macOS, Linux, or Windows
- **Python**: 3.9 or higher
- **Node.js**: 18 or higher (for frontend)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB free space

### **Modern Tooling Installation**

#### **1. Install UV (Python Package Manager)**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

#### **2. Install Bun (JavaScript Runtime)**
```bash
# macOS/Linux
curl -fsSL https://bun.sh/install | bash

# Windows
powershell -c "irm bun.sh/install.ps1 | iex"

# Verify installation
bun --version
```

## 🏗️ **Installation**

### **1. Clone the Repository**
```bash
git clone https://github.com/your-org/fairmind-ethical-sandbox.git
cd fairmind-ethical-sandbox
```

### **2. Backend Setup**
```bash
# Navigate to backend directory
cd apps/backend

# Install Python dependencies with UV
uv sync

# Start the development server
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

The backend will be available at: http://localhost:8001

### **3. Frontend Setup**
```bash
# Open a new terminal and navigate to frontend directory
cd apps/frontend

# Install JavaScript dependencies with Bun
bun install

# Start the development server
bun run dev
```

The frontend will be available at: http://localhost:3000

### **4. Verify Installation**
```bash
# Test backend health
curl http://localhost:8001/health

# Test frontend
open http://localhost:3000
```

## 🎪 **Core Features Overview**

### **1. Dashboard**
The main dashboard provides an overview of:
- **Model Registry**: All registered models
- **Recent Activity**: Latest actions and tests
- **Governance Metrics**: Key performance indicators
- **Security Status**: Current security assessments

### **2. Bias Detection**
Test your models for fairness across:
- **Demographic Parity**: Equal prediction rates across groups
- **Equalized Odds**: Equal true/false positive rates
- **Equal Opportunity**: Equal true positive rates
- **Individual Fairness**: Similar predictions for similar individuals
- **Counterfactual Fairness**: Fairness under interventions

### **3. Security Testing**
Comprehensive OWASP AI security assessment:
- **AI01:2023 - Prompt Injection**
- **AI02:2023 - Training Data Poisoning**
- **AI03:2023 - Model Inversion**
- **AI04:2023 - Model Theft**
- **AI05:2023 - Supply Chain Attacks**
- **AI06:2023 - Sensitive Information Disclosure**
- **AI07:2023 - Unsafe Model Serialization**
- **AI08:2023 - Model Skewing**
- **AI09:2023 - Model Repo Poisoning**
- **AI10:2023 - Inference Endpoint Denial of Service**

### **4. Model Registry**
Manage your AI models with:
- **Model Upload**: Register new models
- **Version Control**: Track model versions
- **Metadata Management**: Store model information
- **Lifecycle Tracking**: Monitor model stages

## 🧪 **Testing Your First Model**

### **1. Run the Testing Suite**
```bash
# Navigate to test scripts directory
cd test_scripts

# Setup testing environment
bun run setup

# Run comprehensive testing
python comprehensive_fairmind_test.py
```

### **2. Test LLM Models**
```bash
# Test LLM models (requires downloaded models)
python llm_comprehensive_test.py
```

### **3. View Test Results**
```bash
# Check test results
ls test_results/

# View comprehensive report
cat test_results/comprehensive_report.json
```

## 📊 **Understanding the Interface**

### **Navigation Structure**
```
DISCOVER
├── Dashboard          # Main overview
└── Model Registry     # Model management

UPLOAD
├── Model Upload       # Upload new models
└── Dataset Management # Manage datasets

TEST
├── Bias Detection     # Fairness analysis
├── Security Testing   # Security assessment
└── AI Circus          # Comprehensive testing

MONITOR
├── AI DNA Profiling   # Model signatures
├── AI Time Travel     # Historical analysis
└── Performance Metrics # Model performance

GOVERN
├── Ethics Observatory # Ethics assessment
├── Compliance Monitoring # Regulatory compliance
└── Policy Management  # Governance policies

ANALYZE
├── Reports            # Generated reports
├── Analytics          # Data analytics
└── Insights           # AI insights
```

### **Key UI Elements**
- **Sidebar Navigation**: Categorized feature access
- **Terminal Theme**: Black/white with gold accents
- **High Contrast**: Excellent accessibility
- **Responsive Design**: Works on all screen sizes

## 🔧 **Configuration**

### **Environment Variables**
Create a `.env.local` file in the frontend directory:
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8001

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_REAL_TIME=true
```

### **Backend Configuration**
Create a `.env` file in the backend directory:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/fairmind

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]

# External Services
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

## 🚀 **Next Steps**

### **1. Explore Features**
- [Bias Detection Guide](./Bias-Detection.md)
- [Security Testing Guide](./Security-Testing.md)
- [Model Registry Guide](./Model-Registry.md)

### **2. Upload Your Models**
- [Model Upload Tutorial](./Model-Upload.md)
- [Dataset Management](./Dataset-Management.md)
- [Model Validation](./Model-Validation.md)

### **3. Run Comprehensive Tests**
- [Testing Guide](./Testing-Guide.md)
- [Performance Testing](./Performance-Testing.md)
- [Security Assessment](./Security-Assessment.md)

### **4. Deploy to Production**
- [Deployment Guide](./Deployment-Guide.md)
- [Configuration Guide](./Configuration.md)
- [Monitoring Setup](./Monitoring.md)

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Backend Won't Start**
```bash
# Check if port is in use
lsof -i :8001

# Kill process if needed
kill -9 <PID>

# Restart backend
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

#### **Frontend Build Errors**
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
bun install

# Restart development server
bun run dev
```

#### **Testing Issues**
```bash
# Check Python environment
uv run python --version

# Reinstall test dependencies
uv sync --reinstall

# Run tests with verbose output
python -v comprehensive_fairmind_test.py
```

### **Getting Help**
- **Documentation**: Check the [Wiki Home](./Home.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/fairmind-ethical-sandbox/issues)
- **Community**: [Discussions](https://github.com/your-org/fairmind-ethical-sandbox/discussions)

## 🎉 **Congratulations!**

You've successfully set up FairMind and are ready to start testing your AI models for ethical compliance, bias detection, and security vulnerabilities.

**Next up**: [Upload your first model](./Model-Upload.md) or explore the [API Reference](./API-Reference.md) for advanced usage.

---

**🎯 Ready to make AI more ethical? Let's get started!**
