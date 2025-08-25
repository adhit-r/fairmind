# FairMind API - Python FastAPI Backend

> **ML/AI Services for AI Governance Platform**

A high-performance Python FastAPI backend providing ML/AI services for bias analysis, fairness metrics, compliance monitoring, and real-time data processing.

## 🏗️ **Architecture**

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Next.js       │◄──────────────►│   Python        │
│   Frontend      │                 │   FastAPI       │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │ WebSocket/Real-time              │ HTTP/REST
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│   Supabase      │◄────────────────│   Supabase      │
│   (Real-time)   │                 │   (Database)    │
└─────────────────┘                 └─────────────────┘
```

## 🚀 **Quick Start**

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 **API Endpoints**

### **Health Check**
```bash
curl http://localhost:8000/health
```

### **Governance Metrics**
```bash
curl http://localhost:8000/governance/metrics
```

### **Models**
```bash
curl http://localhost:8000/models
```

### **Simulations**
```bash
curl http://localhost:8000/simulations
```

### **AI Bill Requirements**
```bash
curl http://localhost:8000/ai-bill/requirements
```

### **WebSocket (Real-time)**
```bash
# Connect to WebSocket for real-time updates
ws://localhost:8000/ws
```

## 🛠️ **Features**

### **ML/AI Services**
- **Bias Analysis**: Comprehensive bias detection across demographics
- **Fairness Metrics**: Demographic parity, equalized odds, equal opportunity
- **Explainability**: SHAP/LIME integration for model interpretability
- **Compliance Scoring**: NIST AI RMF compliance assessment
- **Drift Detection**: Data and concept drift monitoring

### **Real-time Processing**
- **WebSocket Server**: Real-time data broadcasting
- **Async Processing**: Non-blocking ML operations
- **Live Updates**: Instant metric updates to frontend

### **Data Management**
- **Mock Data Generation**: Dynamic test data for development
- **API Responses**: Standardized response formats
- **Error Handling**: Comprehensive error management

## 📁 **Project Structure**

```
apps/api/
├── main.py              # FastAPI application entry point
├── websocket.py         # WebSocket server for real-time updates
├── requirements.txt     # Python dependencies
├── supabase/           # Database migrations and seeds
│   └── seed.sql        # Database seed data
└── README.md           # This file
```

## 🔧 **Development**

### **Dependencies**
- **FastAPI**: High-performance web framework
- **Uvicorn**: ASGI server
- **Pandas/NumPy**: Data processing and analysis
- **WebSockets**: Real-time communication

### **Environment Variables**
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database (Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## 📈 **Performance**

- **Async Processing**: Non-blocking ML operations
- **Real-time Updates**: WebSocket broadcasting
- **Scalable**: Horizontal scaling ready
- **Type Safe**: Pydantic model validation

## 🔒 **Security**

- **Input Validation**: Pydantic model validation
- **Error Handling**: Comprehensive error management
- **CORS**: Cross-origin resource sharing configured
- **Rate Limiting**: Built-in rate limiting (configurable)

## 🚀 **Deployment**

### **Docker**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Cloud Deployment**
- **Vercel**: Serverless deployment
- **Railway**: Container deployment
- **Heroku**: Container deployment
- **AWS/GCP**: Container orchestration

## 📊 **Monitoring**

- **Health Checks**: `/health` endpoint
- **Metrics**: Built-in FastAPI metrics
- **Logging**: Structured logging
- **Error Tracking**: Comprehensive error handling

---

**FairMind API** - Powering responsible AI governance with Python and FastAPI.
