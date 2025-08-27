# FairMind Testing Suite

Comprehensive testing suite for FairMind ethical sandbox using **UV** for Python and **Bun** for JavaScript.

## 🚀 Quick Start

### Prerequisites

1. **UV** (Python package manager): [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
2. **Bun** (JavaScript runtime): [Install Bun](https://bun.sh/docs/installation)
3. **Kaggle API** credentials (for dataset downloads)

### Setup

```bash
# Run the automated setup script
bun run test_scripts/setup.js

# Or manually install dependencies
cd test_scripts
uv pip install -r requirements.txt
bun install
```

## 📁 Directory Structure

```
test_scripts/
├── setup.js                          # Automated setup script
├── requirements.txt                   # Python dependencies (UV)
├── package.json                      # JavaScript dependencies (Bun)
├── setup_kaggle.py                   # Kaggle dataset downloader
├── train_traditional_models.py       # ML model trainer
├── comprehensive_fairmind_test.py    # Full FairMind testing
├── frontend_test.js                  # Frontend testing (Bun)
└── README.md                         # This file

test_models/
├── traditional_ml/                   # Traditional ML models
│   ├── credit_risk/
│   ├── healthcare/
│   └── hiring/
├── llm_models/                       # LLM models
│   ├── text_generation/
│   ├── image_classification/
│   └── audio_speech/
└── datasets/                         # Raw and processed datasets
    ├── raw/
    └── processed/

test_results/                         # Test results and reports
├── bias_analysis/
├── security_reports/
├── ethics_evaluations/
└── ai_bom_reports/
```

## 🧪 Testing Workflow

### 1. Environment Setup

```bash
# Automated setup (recommended)
bun run test_scripts/setup.js

# Manual setup
cd test_scripts
uv pip install -r requirements.txt
bun install
```

### 2. Dataset Acquisition

```bash
# Download test datasets from Kaggle
python test_scripts/setup_kaggle.py
```

**Available Datasets:**
- **Credit Card Fraud Detection** - Financial bias testing
- **Diabetes Prediction** - Healthcare bias testing  
- **HR Analytics** - Hiring bias testing
- **News Articles** - Text generation bias testing
- **CelebA** - Image classification bias testing
- **FairFace** - Demographic bias testing

### 3. Model Training

```bash
# Train traditional ML models
python test_scripts/train_traditional_models.py
```

**Models Trained:**
- **Credit Risk Model** (Random Forest, Logistic Regression, XGBoost)
- **Healthcare Model** (Logistic Regression)
- **HR Analytics Model** (Random Forest)

### 4. Frontend Testing

```bash
# Test frontend application
bun run test_scripts/frontend_test.js

# Or use npm script
bun run test:frontend
```

**Frontend Tests:**
- Page load testing
- API endpoint validation
- UI component testing
- Responsive design testing
- Accessibility testing
- Performance testing

### 5. Comprehensive FairMind Testing

```bash
# Test all FairMind features
python test_scripts/comprehensive_fairmind_test.py
```

**FairMind Features Tested:**
- **Bias Detection & Fairness Analysis**
- **AI DNA Profiling**
- **AI Time Travel**
- **AI Circus (Comprehensive Testing)**
- **OWASP AI Security**
- **AI Ethics Observatory**
- **AI Bill of Materials (AI BOM)**
- **Model Registry & Governance**

## 📊 Test Results

All test results are saved in the `test_results/` directory:

- `frontend_test_report.json` - Frontend testing results
- `comprehensive_report.json` - Full FairMind testing results
- `bias_analysis/` - Bias detection results
- `security_reports/` - Security testing results
- `ethics_evaluations/` - Ethics assessment results
- `ai_bom_reports/` - AI BOM generation results

## 🔧 Configuration

### Environment Variables

Create `.env.test` file:

```env
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8001
NODE_ENV=test
PYTHONPATH=/path/to/fairmind-ethical-sandbox
TEST_TIMEOUT=30000
TEST_RETRIES=3
LOG_LEVEL=info
```

### Kaggle API Setup

1. Go to [Kaggle Settings](https://www.kaggle.com/settings/account)
2. Scroll to "API" section
3. Click "Create New API Token"
4. Download `kaggle.json`
5. Place in `~/.kaggle/kaggle.json`

## 📈 Success Metrics

### Quantitative Metrics
- **Bias Detection Accuracy**: >95% detection rate
- **Security Coverage**: 100% OWASP AI categories
- **Performance Impact**: <5% overhead
- **Compliance Score**: >90% regulatory compliance

### Qualitative Metrics
- **User Experience**: Intuitive interface
- **Report Quality**: Actionable insights
- **Documentation**: Comprehensive coverage
- **Integration**: Seamless workflow

## 🛠️ Available Scripts

### Python Scripts (UV)

```bash
# Install Python dependencies
uv pip install -r requirements.txt

# Download datasets
python setup_kaggle.py

# Train models
python train_traditional_models.py

# Run comprehensive tests
python comprehensive_fairmind_test.py
```

### JavaScript Scripts (Bun)

```bash
# Install JavaScript dependencies
bun install

# Run frontend tests
bun run test:frontend

# Run API tests
bun run test:api

# Run integration tests
bun run test:integration

# Generate reports
bun run report
```

## 🔍 Troubleshooting

### Common Issues

1. **UV not found**
   ```bash
   # Install UV
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Bun not found**
   ```bash
   # Install Bun
   curl -fsSL https://bun.sh/install | bash
   ```

3. **Kaggle API errors**
   ```bash
   # Check credentials
   ls ~/.kaggle/kaggle.json
   
   # Set permissions
   chmod 600 ~/.kaggle/kaggle.json
   ```

4. **Python dependency conflicts**
   ```bash
   # Use UV for isolated environment
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=debug

# Run with verbose output
python -v comprehensive_fairmind_test.py
bun run test:frontend --verbose
```

## 📚 Additional Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [Bun Documentation](https://bun.sh/docs)
- [Kaggle API Documentation](https://github.com/Kaggle/kaggle-api)
- [FairMind Documentation](./README.md)

## 🤝 Contributing

1. Follow the testing workflow
2. Add new test cases to appropriate scripts
3. Update requirements.txt for new Python dependencies
4. Update package.json for new JavaScript dependencies
5. Document new test procedures

## 📄 License

This testing suite is part of the FairMind ethical sandbox project.
