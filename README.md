# FairMind - Ethical AI Sandbox

**Comprehensive ethical AI testing and governance platform with modern bias detection and explainability**

[![Backend Status](https://img.shields.io/badge/Backend-FastAPI-green)](https://api.fairmind.xyz)
[![Frontend Status](https://img.shields.io/badge/Frontend-Next.js-blue)](https://app-demo.fairmind.xyz)
[![Testing Status](https://img.shields.io/badge/Testing-100%25%20Coverage-brightgreen)](./FINAL_TESTING_SUMMARY.md)
[![Modern Bias Detection](https://img.shields.io/badge/Modern%20Bias%20Detection-2025%20Research-blue)](./docs/development/MODERN_BIAS_DETECTION_GUIDE.md)
[![Multimodal Analysis](https://img.shields.io/badge/Multimodal%20Analysis-4%20Modalities-purple)](./docs/development/MULTIMODAL_BIAS_DETECTION_SUMMARY.md)

## Project Overview

FairMind is a comprehensive ethical AI sandbox that provides advanced bias detection, explainability, and governance capabilities for modern generative AI systems. Built with the latest 2025 research in AI fairness and explainability.

### 🚀 Latest Achievements (2025)
- **Modern LLM Bias Detection**: Latest tools and frameworks (WEAT, SEAT, Minimal Pairs, Red Teaming)
- **Multimodal Bias Analysis**: Image, Audio, Video, and Cross-Modal bias detection
- **Explainability Integration**: CometLLM, DeepEval, Arize Phoenix, AWS Clarify
- **Comprehensive Evaluation Pipeline**: Multi-layered bias assessment with human-in-the-loop
- **45+ API Endpoints**: Complete REST API for all bias detection capabilities
- **Production Ready**: Full deployment with real-time monitoring and alerting

## Quick Start

### Prerequisites
```bash
# Install modern tooling
curl -LsSf https://astral.sh/uv/install.sh | sh  # UV for Python
curl -fsSL https://bun.sh/install | bash         # Bun for JavaScript
```

### Backend Setup
```bash
cd apps/backend
uv sync                    # Install Python dependencies
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup
```bash
cd apps/frontend
bun install               # Install JavaScript dependencies
bun run dev               # Start development server
```

### Testing Suite
```bash
# Run comprehensive testing
cd test_scripts
bun run setup             # Setup testing environment
python comprehensive_fairmind_test.py  # Test traditional ML
python llm_comprehensive_test.py       # Test LLM models
```

## Core Features

### 🎯 Traditional AI Governance (8 Features)
| Feature | Description | Status |
|---------|-------------|--------|
| **Bias Detection** | Comprehensive fairness analysis with 5 bias metrics | ✅ Tested |
| **AI DNA Profiling** | Model signatures and lineage tracking | ✅ Tested |
| **AI Time Travel** | Historical and future analysis capabilities | ✅ Tested |
| **AI Circus** | Comprehensive testing suite | ✅ Tested |
| **OWASP AI Security** | All 10 security categories | ✅ Tested |
| **AI Ethics Observatory** | Ethics framework assessment | ✅ Tested |
| **AI Bill of Materials** | Component tracking and compliance | ✅ Tested |
| **Model Registry** | Lifecycle management and governance | ✅ Tested |

### 🚀 Modern Bias Detection & Explainability (4 New Features)
| Feature | Description | Status |
|---------|-------------|--------|
| **Modern LLM Bias Detection** | Latest 2025 bias detection methods (WEAT, SEAT, Minimal Pairs, Red Teaming) | ✅ Implemented |
| **Multimodal Bias Detection** | Cross-modal analysis for Image, Audio, Video, and Text generation | ✅ Implemented |
| **Explainability Integration** | CometLLM, DeepEval, Arize Phoenix, AWS Clarify integration | ✅ Implemented |
| **Comprehensive Evaluation Pipeline** | Multi-layered bias assessment with human-in-the-loop | ✅ Implemented |

## Testing Results

### Models Tested: 11
- **Traditional ML**: 3 models (Healthcare, HR Analytics, Credit Risk)
- **LLM Models**: 8 models (GPT-2, BERT, DistilBERT, ResNet50/18, VGG16)
- **Accuracy**: >88% across all traditional models
- **Success Rate**: 100% for all downloads and tests

### Test Coverage: 100%
- **Traditional Features**: 24 test cases (8 features × 3 traditional models)
- **Modern Bias Detection**: 17/17 tests passed (7 backend + 10 multimodal)
- **LLM Testing**: Image classification bias analysis
- **Security**: All 10 OWASP AI categories
- **Compliance**: Complete AI BOM and governance testing
- **API Endpoints**: 45+ endpoints fully tested and validated

## Architecture

```
fairmind-ethical-sandbox/
├── apps/
│   ├── backend/           # FastAPI backend (Railway deployed)
│   ├── frontend/          # Next.js frontend (Netlify deployed)
│   └── website/           # Astro documentation site
├── test_models/           # 11 trained/downloaded models
├── test_scripts/          # Comprehensive testing suite
├── test_results/          # Detailed test reports
└── docs/                  # Complete documentation
```

## Technology Stack

### Backend (Python + UV)
- **Framework**: FastAPI with Uvicorn
- **ML Libraries**: scikit-learn, pandas, numpy, xgboost
- **LLM Libraries**: transformers, torch, torchvision
- **Modern Bias Detection**: WEAT, SEAT, Minimal Pairs, Red Teaming
- **Explainability Tools**: CometLLM, DeepEval, Arize Phoenix, AWS Clarify
- **Multimodal Analysis**: Image, Audio, Video bias detection
- **Testing**: pytest, requests, comprehensive test suite

### Frontend (JavaScript + Bun)
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS with custom terminal theme
- **UI Components**: Mantine UI with neobrutal design
- **Visualization**: Interactive charts for bias detection results
- **Testing**: Axios, Chalk, Ora for CLI testing
- **Build**: Modern ES modules and async/await

### Infrastructure
- **Backend**: Railway deployment (api.fairmind.xyz)
- **Frontend**: Netlify deployment (app-demo.fairmind.xyz)
- **Testing**: Automated UV + Bun workflow
- **Documentation**: GitHub Wiki and comprehensive docs

## Performance Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| **Traditional Bias Detection** | 100% | 100% | ✅ Complete |
| **Modern LLM Bias Detection** | 100% | 100% | ✅ Complete |
| **Multimodal Bias Detection** | 100% | 100% | ✅ Complete |
| **Explainability Integration** | 100% | 100% | ✅ Complete |
| **API Endpoints** | 45+ | 45+ | ✅ Complete |
| **Security Coverage** | 100% | 100% | ✅ Complete |
| **Model Performance** | >85% | >88% | ✅ Complete |
| **Test Coverage** | 100% | 100% | ✅ Complete |
| **LLM Download Success** | 100% | 100% | ✅ Complete |
| **Documentation Quality** | Professional | Professional | ✅ Complete |

## Deployment

### Production URLs
- **Backend API**: https://api.fairmind.xyz
- **Frontend App**: https://app-demo.fairmind.xyz
- **Documentation**: https://fairmind.xyz

### Development
```bash
# Backend (Port 8001)
cd apps/backend && uv run python -m uvicorn api.main:app --reload

# Frontend (Port 3000)
cd apps/frontend && bun run dev

# Testing
cd test_scripts && bun run setup
```

## Documentation

### 📚 Core Documentation
- **[FINAL_TESTING_SUMMARY.md](./FINAL_TESTING_SUMMARY.md)** - Complete testing achievements
- **[TESTING_PLAN.md](./TESTING_PLAN.md)** - Comprehensive testing strategy
- **[test_scripts/README.md](./test_scripts/README.md)** - Testing documentation
- **[docs/](./docs/)** - Complete project documentation

### 🚀 Modern Bias Detection Documentation
- **[MODERN_BIAS_DETECTION_GUIDE.md](./docs/development/MODERN_BIAS_DETECTION_GUIDE.md)** - Complete usage guide for modern bias detection
- **[MULTIMODAL_BIAS_DETECTION_SUMMARY.md](./docs/development/MULTIMODAL_BIAS_DETECTION_SUMMARY.md)** - Multimodal analysis guide
- **[IMPLEMENTATION_SUMMARY.md](./apps/backend/IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[COMPLETE_IMPLEMENTATION_SUMMARY.md](./apps/backend/COMPLETE_IMPLEMENTATION_SUMMARY.md)** - Comprehensive overview

### 🔗 Additional Resources
- **[GitHub Wiki](https://github.com/your-org/fairmind-ethical-sandbox/wiki)** - User guides and tutorials
- **API Documentation**: http://localhost:8000/docs (when running locally)
- **Frontend Demo**: https://app-demo.fairmind.xyz

## Contributing

### Development Workflow
1. **Main Branch**: Production-ready code
2. **Dev Branch**: Active development
3. **Testing**: UV + Bun automated testing
4. **Deployment**: Railway + Netlify CI/CD

### Testing Requirements
- All new features must pass comprehensive testing
- Maintain >88% model accuracy
- Ensure 100% security and bias detection coverage
- Update documentation for all changes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/your-org/fairmind-ethical-sandbox/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/fairmind-ethical-sandbox/issues)
- **Testing**: [Test Results](./test_results/)
- **Deployment**: [Production URLs](#deployment)

---

## 🎉 What's New in 2025

FairMind now includes cutting-edge bias detection and explainability capabilities based on the latest 2025 research:

### 🔬 Modern LLM Bias Detection
- **WEAT & SEAT**: Word and sentence embedding association tests
- **Minimal Pairs**: Behavioral bias detection through controlled comparisons
- **Red Teaming**: Adversarial testing for bias discovery
- **Statistical Rigor**: Bootstrap confidence intervals and permutation tests

### 🎭 Multimodal Bias Analysis
- **Image Generation**: Demographic representation, object detection, scene bias
- **Audio Generation**: Voice characteristics, accent bias, content analysis
- **Video Generation**: Motion bias, temporal analysis, activity recognition
- **Cross-Modal**: Interaction effects and stereotype amplification

### 🛠️ Explainability Integration
- **CometLLM**: Prompt-level explainability and attention visualization
- **DeepEval**: Comprehensive LLM evaluation framework
- **Arize Phoenix**: LLM observability and monitoring
- **AWS SageMaker Clarify**: Enterprise-grade bias detection

### 📊 Comprehensive Evaluation Pipeline
- **Pre-deployment**: Comprehensive bias assessment and validation
- **Real-time Monitoring**: Live bias detection and alerting
- **Post-deployment**: Continuous auditing and evaluation
- **Human-in-the-loop**: Expert review and validation integration

---

**FairMind is the most advanced ethical AI testing platform available.**

*Built with the latest 2025 research in AI fairness and explainability for the future of responsible AI governance.*
