# FairMind - Ethical AI Governance Platform

> **Open-source platform for AI fairness, bias detection, and responsible AI development. Detect bias in LLMs, multimodal AI, and machine learning models with cutting-edge 2025 research methods.**

[![Backend Status](https://img.shields.io/badge/Backend-FastAPI-green)](https://api.fairmind.xyz)
[![Frontend Status](https://img.shields.io/badge/Frontend-Next.js-blue)](https://app-demo.fairmind.xyz)
[![Testing Status](https://img.shields.io/badge/Testing-100%25%20Coverage-brightgreen)](./FINAL_TESTING_SUMMARY.md)
[![Contributors](https://img.shields.io/github/contributors/adhit-r/fairmind)](https://github.com/adhit-r/fairmind/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/adhit-r/fairmind/good%20first%20issue)](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Stars](https://img.shields.io/github/stars/adhit-r/fairmind?style=social)](https://github.com/adhit-r/fairmind)

**🌐 Live Demo:** [app-demo.fairmind.xyz](https://app-demo.fairmind.xyz) | **📚 Documentation:** [docs/](./docs/) | **🐛 Issues:** [GitHub Issues](https://github.com/adhit-r/fairmind/issues) | **💬 Discussions:** [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions)

---

## 🎯 What is FairMind?

FairMind is a comprehensive **AI fairness testing platform** that helps developers, researchers, and organizations build **responsible AI systems**. Our platform provides:

- **🔍 Advanced Bias Detection**: Detect bias in LLMs, multimodal AI, and traditional ML models
- **📊 Explainability Tools**: Integrate with CometLLM, DeepEval, Arize Phoenix, and AWS Clarify
- **⚖️ Fairness Metrics**: 5+ bias metrics including statistical parity, equal opportunity, and calibration
- **🎭 Multimodal Analysis**: Analyze bias across text, image, audio, and video modalities
- **🛡️ Security & Compliance**: OWASP AI security, AI Bill of Materials, and compliance tracking
- **📈 Real-time Monitoring**: Live bias detection and alerting for production systems

**Perfect for:** AI researchers, ML engineers, compliance officers, and organizations building ethical AI systems.

---

## 🚀 Quick Start (5 Minutes)

> **📖 Detailed Setup Guide**: See [SETUP.md](./SETUP.md) for complete installation instructions and troubleshooting.

### Prerequisites

| Requirement | Version | Install |
|------------|---------|---------|
| **Python** | 3.9+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **UV** (recommended) | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Bun** (recommended) | Latest | `curl -fsSL https://bun.sh/install \| bash` |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/adhit-r/fairmind.git
cd fairmind

# 2. Backend Setup (Terminal 1)
cd apps/backend
uv sync  # or: pip install -r requirements.txt
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# 3. Frontend Setup (Terminal 2)
cd apps/frontend
bun install  # or: npm install
bun run dev  # or: npm run dev
```

**✅ That's it!** Visit `http://localhost:3000` to see the dashboard.

### First-Time Setup

```bash
# Optional: Run tests to verify installation
cd test_scripts
bun run setup
python comprehensive_fairmind_test.py
```

**📖 Need help?** Check our [Getting Started Guide](docs/CONTRIBUTING.md#-quick-start) or [open an issue](https://github.com/adhit-r/fairmind/issues/new).

---

## ✨ Key Features

### 🎯 Traditional AI Governance

| Feature | Description | Status |
|---------|-------------|--------|
| **Bias Detection** | 5+ fairness metrics (statistical parity, equal opportunity, calibration) | ✅ |
| **AI DNA Profiling** | Model signatures and lineage tracking | ✅ |
| **AI Time Travel** | Historical and future analysis capabilities | ✅ |
| **AI Circus** | Comprehensive testing suite | ✅ |
| **OWASP AI Security** | All 10 OWASP AI security categories | ✅ |
| **AI Ethics Observatory** | Ethics framework assessment | ✅ |
| **AI Bill of Materials** | Component tracking and compliance | ✅ |
| **Model Registry** | Lifecycle management and governance | ✅ |

### 🚀 Modern Bias Detection (2025 Research)

| Feature | Description | Status |
|---------|-------------|--------|
| **LLM Bias Detection** | WEAT, SEAT, Minimal Pairs, Red Teaming methods | ✅ |
| **Multimodal Analysis** | Image, Audio, Video, Cross-Modal bias detection | ✅ |
| **Explainability** | CometLLM, DeepEval, Arize Phoenix, AWS Clarify | ✅ |
| **Evaluation Pipeline** | Multi-layered assessment with human-in-the-loop | ✅ |

### 📊 Production Features

- **45+ API Endpoints**: Complete REST API for bias detection
- **Real-time Monitoring**: Live bias detection and alerting
- **100% Test Coverage**: Comprehensive testing suite
- **Production Ready**: Deployed on Railway & Netlify

---

## 🏗️ Architecture

```
fairmind/
├── apps/
│   ├── backend/          # FastAPI backend (Python)
│   ├── frontend/         # Next.js frontend (React/TypeScript)
│   └── website/          # Documentation site
├── test_models/          # Sample ML models
├── test_scripts/         # Testing suite
└── docs/                # Documentation
```

### Technology Stack

- **Backend**: FastAPI, Python 3.9+, UV package manager
- **Frontend**: Next.js 14, React 18, TypeScript, Mantine UI
- **ML Libraries**: scikit-learn, transformers, torch, pandas, numpy
- **Deployment**: Railway (backend), Netlify (frontend)
- **Testing**: pytest, Jest, Playwright

---

## 📖 Documentation

### Quick Links

- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute
- **[Roadmap](ROADMAP.md)** - Project roadmap and milestones
- **[Changelog](CHANGELOG.md)** - Version history
- **[API Documentation](https://api.fairmind.xyz/docs)** - Interactive API docs
- **[Modern Bias Detection Guide](./docs/development/MODERN_BIAS_DETECTION_GUIDE.md)** - LLM bias detection
- **[Multimodal Analysis Guide](./docs/development/MULTIMODAL_BIAS_DETECTION_SUMMARY.md)** - Multimodal bias

### Complete Documentation

- **Getting Started**: Setup and installation guides
- **API Reference**: Complete API documentation
- **Development Guides**: Contributing and development workflows
- **Deployment**: Production deployment instructions
- **Testing**: Testing strategies and examples

---

## 🤝 Contributing

We welcome contributions! FairMind is open source and community-driven.

### Quick Start for Contributors

1. **Pick an Issue**: Browse [good first issues](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
2. **Fork & Clone**: Fork the repo and clone your fork
3. **Create Branch**: `git checkout -b feature/your-feature-name`
4. **Make Changes**: Follow our [contributing guidelines](docs/CONTRIBUTING.md)
5. **Submit PR**: Open a pull request with your changes

### 🎯 Good First Issues

Perfect for newcomers:
- [#97](https://github.com/adhit-r/fairmind/issues/97) - 📝 Create Interactive API Documentation
- [#98](https://github.com/adhit-r/fairmind/issues/98) - 🧪 Add E2E Tests with Playwright
- [#99](https://github.com/adhit-r/fairmind/issues/99) - ✨ Add Loading States & Skeleton Screens
- [#103](https://github.com/adhit-r/fairmind/issues/103) - 🎨 Improve Accessibility & Keyboard Navigation
- [#106](https://github.com/adhit-r/fairmind/issues/106) - 📱 Improve Mobile Responsiveness

**📊 See all issues:** [Issue Navigator](docs/CONTRIBUTING.md#-visual-issue-navigator--progress-tracker)

### Why Contribute?

- **Make AI Better**: Help build tools that make AI systems more fair and transparent
- **Learn & Grow**: Work with cutting-edge AI/ML technologies
- **Build Portfolio**: Contribute to a meaningful open-source project
- **Join Community**: Connect with developers and researchers worldwide

---

## 🌐 Live Demo

- **Frontend**: [app-demo.fairmind.xyz](https://app-demo.fairmind.xyz)
- **Backend API**: [api.fairmind.xyz](https://api.fairmind.xyz)
- **API Docs**: [api.fairmind.xyz/docs](https://api.fairmind.xyz/docs)

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| **Test Coverage** | 100% |
| **API Endpoints** | 45+ |
| **Models Tested** | 11 |
| **Features** | 12+ |
| **Contributors** | Growing |
| **Open Issues** | 65+ |
| **Good First Issues** | 15+ |

---

## 🛠️ Development

### Running Locally

```bash
# Backend (http://localhost:8001)
cd apps/backend
uv sync
uv run python -m uvicorn api.main:app --reload

# Frontend (http://localhost:3000)
cd apps/frontend
bun install
bun run dev
```

### Testing

```bash
# Backend tests
cd apps/backend
pytest
pytest --cov

# Frontend tests
cd apps/frontend
bun test
bun run lint

# Full test suite
cd test_scripts
bun run setup
python comprehensive_fairmind_test.py
```

### Building for Production

```bash
# Backend
cd apps/backend
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd apps/frontend
bun run build
bun run start
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/adhit-r/fairmind/issues)
- **Discussions**: [GitHub Discussions](https://github.com/adhit-r/fairmind/discussions)
- **Community**: [COMMUNITY.md](.github/COMMUNITY.md)

---

## 🌟 Star History

If you find FairMind useful, please consider giving us a ⭐ star on GitHub!

---

## 🔗 Related Projects

- **[OWASP AI Security](https://owasp.org/www-project-vulnerable-ai-applications/)** - AI security guidelines
- **[AI Fairness 360](https://github.com/Trusted-AI/AIF360)** - IBM's AI fairness toolkit
- **[What-If Tool](https://pair-code.github.io/what-if-tool/)** - Google's model analysis tool

---

## 📈 Roadmap

See our [ROADMAP.md](ROADMAP.md) for planned features and milestones.

**Q1 2025**: Foundation & Core Features ✅  
**Q2 2025**: Advanced Features & Community Building 🔄  
**Q3 2025**: Enterprise Features & Scale 📋  
**Q4 2025**: AI Research & Innovation 📋  

---

## 🎉 What's New in 2025

### Latest Achievements

- ✅ **Modern LLM Bias Detection**: WEAT, SEAT, Minimal Pairs, Red Teaming
- ✅ **Multimodal Bias Analysis**: Image, Audio, Video, Cross-Modal detection
- ✅ **Explainability Integration**: 4 major explainability tools integrated
- ✅ **Comprehensive Evaluation Pipeline**: Multi-layered bias assessment
- ✅ **Production Deployment**: Fully deployed and monitored
- ✅ **100% Test Coverage**: Comprehensive testing suite

### Research Highlights

- **Word Embedding Association Test (WEAT)**: Detects bias in word embeddings
- **Sentence Embedding Association Test (SEAT)**: Extends WEAT to sentence-level
- **Minimal Pairs**: Behavioral bias detection through controlled comparisons
- **Red Teaming**: Adversarial testing for bias discovery
- **Multimodal Bias**: Cross-modal interaction effects analysis

---

**Built with ❤️ for the AI ethics community**

*FairMind - Making AI fair, transparent, and accountable for everyone.*

---

## 📝 SEO Keywords

AI fairness, bias detection, ethical AI, AI governance, machine learning fairness, algorithmic bias, explainable AI, responsible AI, AI ethics, LLM bias detection, multimodal bias analysis, AI compliance, AI testing platform, fairness testing, model fairness, AI auditing, bias mitigation, fairness metrics, AI transparency, WEAT, SEAT, red teaming, bias mitigation, AI explainability, model monitoring, AI security, OWASP AI, AI compliance, responsible AI development, machine learning bias, AI fairness framework, ethical machine learning, AI bias testing, model fairness evaluation, AI transparency tools, bias detection algorithms, fairness metrics, AI governance platform, responsible AI toolkit, AI ethics framework

---

## 📚 Additional Resources

- **⚡ Quick Start**: [QUICK_START.md](QUICK_START.md) - Get started in 2 minutes
- **🔧 Setup Guide**: [SETUP.md](SETUP.md) - Complete installation guide with troubleshooting
- **🗺️ Roadmap**: [ROADMAP.md](ROADMAP.md) - Project roadmap and milestones
- **📝 Changelog**: [CHANGELOG.md](CHANGELOG.md) - Version history
- **🤝 Contributing**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - How to contribute
- **🌟 Community**: [.github/COMMUNITY.md](.github/COMMUNITY.md) - Community guidelines
- **🔍 SEO Guide**: [.github/SEO.md](.github/SEO.md) - SEO and community building strategies

---

**FairMind - Making AI fair, transparent, and accountable for everyone.** 🌍✨
