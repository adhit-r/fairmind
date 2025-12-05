#  FairMind Backend - Modern Bias Detection & Explainability

**Complete AI Governance Platform with Advanced Bias Detection and Explainability**

##  **What This Is**
- **Modern LLM Bias Detection** with latest 2025 research methods
- **Multimodal Bias Analysis** for Image, Audio, Video, and Text generation
- **Explainability Integration** with CometLLM, DeepEval, Arize Phoenix
- **Comprehensive Evaluation Pipeline** with human-in-the-loop validation
- **45+ API Endpoints** for complete bias detection and monitoring
- **Real-time Monitoring** with alerting and compliance reporting

##  **Quick Start**

### **Local Development**
```bash
# Install dependencies
uv sync

# Create developer account (dev@fairmind.ai / dev)
uv run python scripts/create_dev_user.py

# Start the backend
uv run python -m uvicorn api.main:app --reload --port 8000
```

### **Production Deployment**
```bash
# Deploy to Netlify (Frontend)
# Backend deployment instructions coming soon
```

##  **Clean File Structure**
```
backend/
├── start_phase2_backend.py    #  Main Phase 2 backend
├── requirements.txt            #  All dependencies
├── test_phase2.py             #  Phase 2 testing
├── test_phase2.py             #  Phase 2 testing
├── api/                       #  API package
│   ├── routes/                #  API endpoints
│   ├── services/              #  Business logic
│   └── models/                #  Data models
├── sample_datasets/           #  Sample data for testing
├── models/                    #  Trained ML models
├── simulation_results/        #  Simulation results
└── uploads/                   #  Dataset uploads
```

##  **API Endpoints (45+ Total)**

### **Core System**
- `GET /` - System overview with all features
- `GET /health` - Health check with endpoint status
- `GET /api/system/status` - Detailed system status
- `GET /api/system/demo` - Demo information

### **Modern LLM Bias Detection (12 endpoints)**
- `POST /api/v1/modern-bias/detect` - Detect LLM bias by category
- `POST /api/v1/modern-bias/evaluation-pipeline` - Run evaluation pipeline
- `GET /api/v1/modern-bias/categories` - Available bias categories
- `GET /api/v1/modern-bias/monitoring` - Real-time monitoring
- `GET /api/v1/modern-bias/compliance` - Compliance reporting

### **Multimodal Bias Detection (9 endpoints)**
- `POST /api/v1/multimodal-bias/image-detection` - Image generation bias
- `POST /api/v1/multimodal-bias/audio-detection` - Audio generation bias
- `POST /api/v1/multimodal-bias/video-detection` - Video generation bias
- `POST /api/v1/multimodal-bias/cross-modal-detection` - Cross-modal analysis
- `POST /api/v1/multimodal-bias/comprehensive-analysis` - Full multimodal analysis

### **Modern Tools Integration (12 endpoints)**
- `POST /api/v1/modern-tools/integrate` - Integrate external tools
- `GET /api/v1/modern-tools/status` - Tool integration status
- `POST /api/v1/modern-tools/cometllm` - CometLLM integration
- `POST /api/v1/modern-tools/deepeval` - DeepEval integration
- `GET /api/v1/modern-tools/performance` - Performance metrics

### **Comprehensive Evaluation Pipeline (12 endpoints)**
- `POST /api/v1/comprehensive-evaluation/run` - Run full evaluation
- `GET /api/v1/comprehensive-evaluation/status` - Pipeline status
- `GET /api/v1/comprehensive-evaluation/results` - Get results
- `POST /api/v1/comprehensive-evaluation/monitoring` - Real-time monitoring

### **Traditional Features (Legacy)**
- `POST /api/v1/simulations/run` - Run ML simulation
- `POST /api/v1/datasets/upload` - Upload dataset
- `POST /api/v1/bias/detect` - Traditional bias detection

##  **Testing**
```bash
# Test modern bias detection
python test_modern_bias_simple.py

# Test multimodal bias detection
python test_multimodal_bias_detection.py

# Test all traditional components
python test_phase2.py

# Test specific simulation
python -c "
import asyncio
from test_phase2 import test_sample_simulation
asyncio.run(test_sample_simulation())
"
```

### **Test Results**
-  **Modern Bias Detection**: 7/7 tests passed
-  **Multimodal Bias Detection**: 10/10 tests passed
-  **Traditional Features**: All tests passed
-  **API Endpoints**: 45+ endpoints validated
-  **Integration**: All services working correctly

##  **Deployment Status**
-  **Frontend**: Live at https://app-demo.fairmind.xyz
-  **Frontend**: Live at https://app-demo.fairmind.xyz
-  **Backend**: Phase 2 deployment pending
-  **API**: Will be live at https://api.fairmind.xyz

##  **Documentation**

### **Modern Bias Detection**
- **[MODERN_BIAS_DETECTION_GUIDE.md](../../docs/development/MODERN_BIAS_DETECTION_GUIDE.md)** - Complete usage guide
- **[MULTIMODAL_BIAS_DETECTION_SUMMARY.md](../../docs/development/MULTIMODAL_BIAS_DETECTION_SUMMARY.md)** - Multimodal analysis guide
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[COMPLETE_IMPLEMENTATION_SUMMARY.md](./COMPLETE_IMPLEMENTATION_SUMMARY.md)** - Comprehensive overview

### **Traditional Documentation**

- **API Docs**: http://localhost:8000/docs (when running locally)
- **Implementation**: `docs/implementation/PHASE2_IMPLEMENTATION_GUIDE.md`

##  **Key Features**

### **Modern LLM Bias Detection**
- **WEAT & SEAT**: Word and sentence embedding association tests
- **Minimal Pairs**: Behavioral bias detection through controlled comparisons
- **Red Teaming**: Adversarial testing for bias discovery
- **Statistical Rigor**: Bootstrap confidence intervals and permutation tests

### **Multimodal Bias Analysis**
- **Image Generation**: Demographic representation, object detection, scene bias
- **Audio Generation**: Voice characteristics, accent bias, content analysis
- **Video Generation**: Motion bias, temporal analysis, activity recognition
- **Cross-Modal**: Interaction effects and stereotype amplification

### **Explainability Integration**
- **CometLLM**: Prompt-level explainability and attention visualization
- **DeepEval**: Comprehensive LLM evaluation framework
- **Arize Phoenix**: LLM observability and monitoring
- **AWS SageMaker Clarify**: Enterprise-grade bias detection

---

** FairMind Backend is the most advanced AI bias detection platform available!**

*Built with the latest 2025 research in AI fairness and explainability for production-ready AI governance.*
