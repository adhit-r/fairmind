# FairMind API Documentation

## Overview

FairMind provides a comprehensive REST API for modern bias detection, explainability, and AI governance. The API includes 45+ endpoints across 4 main modules, implementing the latest 2025 research in AI fairness and explainability.

## Base URL

- **Production**: `https://api.fairmind.xyz`
- **Development**: `http://localhost:8000`

## Authentication

Currently, the API is open for development and testing. Production authentication will be implemented in future releases.

## API Modules

### 1. Modern LLM Bias Detection (`/api/v1/modern-bias`)

**12 endpoints** for advanced LLM bias detection using latest 2025 research methods.

#### Core Endpoints

**Detect LLM Bias**
```http
POST /api/v1/modern-bias/detect
Content-Type: application/json

{
  "model_outputs": [
    {
      "text": "The CEO is a successful businessman",
      "metadata": {"model": "gpt-3.5-turbo"},
      "protected_attributes": {"gender": "male"}
    }
  ],
  "category": "representational",
  "evaluation_config": {
    "confidence_level": 0.95,
    "bootstrap_samples": 1000
  }
}
```

**Run Evaluation Pipeline**
```http
POST /api/v1/modern-bias/evaluation-pipeline
Content-Type: application/json

{
  "model_outputs": [...],
  "pipeline_config": {
    "phases": ["pre_deployment", "real_time_monitoring"],
    "compliance_frameworks": ["eu_ai_act", "ftc_guidelines"]
  }
}
```

**Get Bias Categories**
```http
GET /api/v1/modern-bias/categories
```

**Real-time Monitoring**
```http
GET /api/v1/modern-bias/monitoring
```

**Compliance Reporting**
```http
GET /api/v1/modern-bias/compliance
```

### 2. Multimodal Bias Detection (`/api/v1/multimodal-bias`)

**9 endpoints** for cross-modal bias analysis across Image, Audio, Video, and Text generation.

#### Core Endpoints

**Image Generation Bias Detection**
```http
POST /api/v1/multimodal-bias/image-detection
Content-Type: application/json

{
  "model_outputs": [
    {
      "text": "A professional in an office",
      "image_url": "https://example.com/image1.jpg",
      "metadata": {"generated_by": "dall-e-3"},
      "protected_attributes": {"gender": "male", "race": "white"}
    }
  ],
  "analysis_config": {
    "demographic_analysis": true,
    "object_detection_bias": true,
    "scene_bias": true
  }
}
```

**Audio Generation Bias Detection**
```http
POST /api/v1/multimodal-bias/audio-detection
Content-Type: application/json

{
  "model_outputs": [
    {
      "text": "Hello, how can I help you today?",
      "audio_url": "https://example.com/audio1.wav",
      "metadata": {"generated_by": "elevenlabs"},
      "protected_attributes": {"gender": "male", "accent": "american"}
    }
  ]
}
```

**Video Generation Bias Detection**
```http
POST /api/v1/multimodal-bias/video-detection
Content-Type: application/json

{
  "model_outputs": [
    {
      "text": "A person working at a computer",
      "video_url": "https://example.com/video1.mp4",
      "metadata": {"generated_by": "runway-ml"},
      "protected_attributes": {"gender": "male", "age": "middle"}
    }
  ]
}
```

**Cross-Modal Bias Detection**
```http
POST /api/v1/multimodal-bias/cross-modal-detection
Content-Type: application/json

{
  "model_outputs": [...],
  "modalities": ["text", "image", "audio"],
  "analysis_config": {
    "interaction_analysis": true,
    "stereotype_amplification": true
  }
}
```

**Comprehensive Multimodal Analysis**
```http
POST /api/v1/multimodal-bias/comprehensive-analysis
Content-Type: application/json

{
  "model_outputs": [...],
  "modalities": ["text", "image", "audio", "video"],
  "analysis_config": {
    "individual_modality_analysis": true,
    "cross_modal_analysis": true,
    "overall_assessment": true
  }
}
```

### 3. Modern Tools Integration (`/api/v1/modern-tools`)

**12 endpoints** for integrating with external explainability and bias detection tools.

#### Core Endpoints

**Integrate External Tools**
```http
POST /api/v1/modern-tools/integrate
Content-Type: application/json

{
  "tool_config": {
    "cometllm": {
      "enabled": true,
      "api_key": "your-api-key",
      "project_name": "fairmind-bias-detection"
    },
    "deepeval": {
      "enabled": true,
      "config": {
        "evaluation_metrics": ["bias", "fairness", "toxicity"]
      }
    }
  }
}
```

**CometLLM Integration**
```http
POST /api/v1/modern-tools/cometllm
Content-Type: application/json

{
  "prompt": "Generate a professional headshot",
  "model_output": "A successful businessman in a suit",
  "analysis_type": "attention_visualization"
}
```

**DeepEval Integration**
```http
POST /api/v1/modern-tools/deepeval
Content-Type: application/json

{
  "model_outputs": [...],
  "evaluation_config": {
    "metrics": ["bias", "fairness", "toxicity"],
    "thresholds": {"bias": 0.1, "fairness": 0.05}
  }
}
```

**Tool Status**
```http
GET /api/v1/modern-tools/status
```

**Performance Metrics**
```http
GET /api/v1/modern-tools/performance
```

### 4. Comprehensive Evaluation Pipeline (`/api/v1/comprehensive-evaluation`)

**12 endpoints** for running complete bias evaluation pipelines with human-in-the-loop validation.

#### Core Endpoints

**Run Full Evaluation**
```http
POST /api/v1/comprehensive-evaluation/run
Content-Type: application/json

{
  "model_outputs": [...],
  "pipeline_config": {
    "phases": ["pre_deployment", "real_time_monitoring", "post_deployment"],
    "human_in_the_loop": true,
    "compliance_frameworks": ["eu_ai_act", "ftc_guidelines", "gdpr"]
  }
}
```

**Get Pipeline Status**
```http
GET /api/v1/comprehensive-evaluation/status/{pipeline_id}
```

**Get Results**
```http
GET /api/v1/comprehensive-evaluation/results/{pipeline_id}
```

**Real-time Monitoring**
```http
POST /api/v1/comprehensive-evaluation/monitoring
Content-Type: application/json

{
  "pipeline_id": "pipeline_123",
  "monitoring_config": {
    "alert_thresholds": {"bias_score": 0.15, "fairness_score": 0.1},
    "notification_channels": ["email", "webhook"]
  }
}
```

## Response Formats

### Standard Response Structure

```json
{
  "success": true,
  "data": {
    "results": [...],
    "metadata": {
      "timestamp": "2025-01-01T12:00:00Z",
      "processing_time": 1.23,
      "confidence": 0.95
    }
  },
  "error": null
}
```

### Bias Detection Response

```json
{
  "success": true,
  "data": {
    "bias_results": [
      {
        "bias_type": "representational",
        "bias_score": 0.18,
        "confidence": 0.85,
        "is_biased": true,
        "details": {
          "demographic_breakdown": {
            "gender": {"male": 0.6, "female": 0.4}
          }
        },
        "recommendations": [
          "Increase diversity in training data",
          "Implement demographic balancing"
        ],
        "timestamp": "2025-01-01T12:00:00Z"
      }
    ],
    "overall_assessment": {
      "overall_bias_score": 0.16,
      "risk_level": "medium",
      "biased_categories": ["representational", "allocational"]
    }
  }
}
```

### Multimodal Analysis Response

```json
{
  "success": true,
  "data": {
    "timestamp": "2025-01-01T12:00:00Z",
    "modalities": ["text", "image", "audio"],
    "individual_modality_results": {
      "image": [
        {
          "modality": "image",
          "bias_type": "demographic_representation",
          "bias_score": 0.18,
          "confidence": 0.85,
          "is_biased": true,
          "details": {...},
          "recommendations": [...]
        }
      ]
    },
    "cross_modal_results": [
      {
        "modality": "text",
        "bias_type": "cross_modal_stereotypes",
        "bias_score": 0.16,
        "confidence": 0.77,
        "is_biased": true,
        "details": {...},
        "recommendations": [...]
      }
    ],
    "overall_assessment": {
      "overall_bias_score": 0.16,
      "biased_modalities": ["image", "audio"],
      "cross_modal_bias_detected": true,
      "risk_level": "medium"
    },
    "recommendations": [
      "Implement immediate bias mitigation measures",
      "Focus bias mitigation on: image, audio",
      "Implement cross-modal consistency monitoring"
    ]
  }
}
```

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "model_outputs",
      "issue": "Required field is missing"
    }
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid input data
- `MODEL_NOT_FOUND`: Model not found
- `BIAS_DETECTION_FAILED`: Bias detection process failed
- `TOOL_INTEGRATION_ERROR`: External tool integration failed
- `PIPELINE_ERROR`: Evaluation pipeline failed
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `INTERNAL_SERVER_ERROR`: Internal server error

## Rate Limiting

- **Standard endpoints**: 100 requests per minute
- **Heavy computation endpoints**: 10 requests per minute
- **Batch processing**: 5 requests per minute

## SDKs and Libraries

### Python SDK (Coming Soon)
```python
from fairmind import FairMindClient

client = FairMindClient(api_key="your-api-key")

# Detect LLM bias
results = client.detect_llm_bias(
    model_outputs=outputs,
    category="representational"
)

# Multimodal analysis
results = client.multimodal_analysis(
    model_outputs=outputs,
    modalities=["text", "image", "audio"]
)
```

### JavaScript SDK (Coming Soon)
```javascript
import { FairMindClient } from '@fairmind/sdk';

const client = new FairMindClient({ apiKey: 'your-api-key' });

// Detect LLM bias
const results = await client.detectLLMBias({
  modelOutputs: outputs,
  category: 'representational'
});

// Multimodal analysis
const results = await client.multimodalAnalysis({
  modelOutputs: outputs,
  modalities: ['text', 'image', 'audio']
});
```

## Webhooks

### Webhook Events

- `bias.detected`: Bias detected in model outputs
- `pipeline.completed`: Evaluation pipeline completed
- `monitoring.alert`: Monitoring threshold exceeded
- `compliance.violation`: Compliance violation detected

### Webhook Payload

```json
{
  "event": "bias.detected",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": {
    "pipeline_id": "pipeline_123",
    "bias_score": 0.18,
    "risk_level": "medium",
    "details": {...}
  }
}
```

## Best Practices

### 1. Input Validation
- Always validate model outputs before sending
- Include metadata and protected attributes
- Use appropriate data types and formats

### 2. Error Handling
- Implement proper error handling for all API calls
- Check response status codes
- Handle rate limiting gracefully

### 3. Performance Optimization
- Use batch processing for large datasets
- Implement caching for repeated requests
- Monitor API usage and costs

### 4. Security
- Use HTTPS for all API calls
- Implement proper authentication (when available)
- Sanitize input data before processing

## Support

- **Documentation**: [GitHub Wiki](https://github.com/your-org/fairmind-ethical-sandbox/wiki)
- **API Reference**: http://localhost:8000/docs (when running locally)
- **Issues**: [GitHub Issues](https://github.com/your-org/fairmind-ethical-sandbox/issues)
- **Email**: support@fairmind.xyz

## Changelog

### v2.0.0 (2025-01-01)
- Added Modern LLM Bias Detection API
- Added Multimodal Bias Detection API
- Added Modern Tools Integration API
- Added Comprehensive Evaluation Pipeline API
- 45+ new endpoints
- Complete 2025 research implementation

### v1.0.0 (2024-12-01)
- Initial release with traditional bias detection
- Basic ML simulation capabilities
- Core AI governance features
