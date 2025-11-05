# Modern Bias Detection and Explainability Guide

This guide explains how to use the modern bias detection and explainability features implemented in FairMind, based on the 2025 analysis of explainability and bias detection in generative AI.

## Overview

The modern bias detection system implements a comprehensive approach that addresses the unique challenges of generative AI models:

- **Scale and complexity**: Billions of parameters make traditional XAI methods computationally prohibitive
- **Generative nature**: Output explanations differ from classification/prediction explanations  
- **Multimodal capabilities**: Cross-modal interactions create new types of biases
- **Emergent behaviors**: Complex behaviors that aren't easily attributable to specific inputs

## Architecture

The system consists of three main components:

1. **Modern LLM Bias Detection Service** (`modern_llm_bias_service.py`)
2. **Modern Tools Integration Service** (`modern_tools_integration.py`)
3. **Comprehensive Bias Evaluation Pipeline** (`comprehensive_bias_evaluation_pipeline.py`)

## API Endpoints

### Modern Bias Detection (`/api/v1/modern-bias`)

#### Comprehensive Bias Evaluation
```bash
POST /api/v1/modern-bias/comprehensive-evaluation
```

**Request Body:**
```json
{
  "model_outputs": [
    {
      "text": "The doctor was confident in her diagnosis",
      "metadata": {"model": "gpt-4", "temperature": 0.7},
      "protected_attributes": {"gender": "female", "profession": "doctor"}
    }
  ],
  "model_type": "llm",
  "include_explainability": true,
  "include_multimodal": false
}
```

**Response:**
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "model_type": "llm",
  "evaluation_summary": {
    "total_tests_run": 7,
    "biased_tests": 2,
    "bias_rate": 0.29
  },
  "bias_tests": {
    "pre_deployment": {
      "tests_run": [...],
      "bias_detected": true,
      "critical_issues": [...],
      "warnings": [...]
    }
  },
  "explainability_analysis": {
    "methods_used": [...],
    "insights": [...],
    "visualizations": [...]
  },
  "overall_risk": "medium",
  "recommendations": [...],
  "compliance_status": {...}
}
```

#### Multimodal Bias Detection
```bash
POST /api/v1/modern-bias/multimodal-detection
```

**Request Body:**
```json
{
  "model_outputs": [
    {
      "text": "A professional woman in a business suit",
      "image_url": "https://example.com/image.jpg",
      "audio_url": "https://example.com/audio.wav"
    }
  ],
  "modalities": ["text", "image", "audio"],
  "cross_modal_analysis": true
}
```

#### Explainability Analysis
```bash
POST /api/v1/modern-bias/explainability-analysis
```

**Request Body:**
```json
{
  "model_outputs": [...],
  "methods": ["attention_visualization", "activation_patching", "circuit_discovery"],
  "include_visualizations": true
}
```

### Modern Tools Integration (`/api/v1/modern-tools`)

#### Comprehensive Tool Integration
```bash
POST /api/v1/modern-tools/comprehensive-integration
```

**Request Body:**
```json
{
  "model_outputs": [...],
  "selected_tools": ["comet_llm", "deepeval", "arize_phoenix", "aws_clarify"],
  "integration_config": {
    "comet_llm": {"project_id": "bias_analysis"},
    "deepeval": {"evaluation_criteria": ["bias", "faithfulness"]}
  }
}
```

#### Individual Tool Integrations

**CometLLM Integration:**
```bash
POST /api/v1/modern-tools/comet-llm
```

**DeepEval Integration:**
```bash
POST /api/v1/modern-tools/deepeval
```

**Arize Phoenix Integration:**
```bash
POST /api/v1/modern-tools/arize-phoenix
```

**AWS Clarify Integration:**
```bash
POST /api/v1/modern-tools/aws-clarify
```

**Confident AI Integration:**
```bash
POST /api/v1/modern-tools/confident-ai
```

**TransformerLens Integration:**
```bash
POST /api/v1/modern-tools/transformer-lens
```

**BertViz Integration:**
```bash
POST /api/v1/modern-tools/bertviz
```

### Comprehensive Bias Evaluation Pipeline (`/api/v1/comprehensive-evaluation`)

#### Run Comprehensive Evaluation
```bash
POST /api/v1/comprehensive-evaluation/run-comprehensive
```

**Request Body:**
```json
{
  "model_id": "model_123",
  "model_type": "llm",
  "model_outputs": [...],
  "evaluation_config": {
    "pre_deployment": {"enabled": true, "bias_threshold": 0.1},
    "real_time_monitoring": {"enabled": true, "monitoring_interval_minutes": 5},
    "post_deployment_auditing": {"enabled": true, "audit_frequency_days": 7},
    "human_in_loop": {"enabled": true, "expert_review_required": true},
    "continuous_learning": {"enabled": true, "learning_rate": 0.01}
  }
}
```

#### Run Specific Evaluation Phase
```bash
POST /api/v1/comprehensive-evaluation/run-phase
```

**Available Phases:**
- `pre_deployment`: Comprehensive bias testing before deployment
- `real_time_monitoring`: Real-time bias monitoring simulation
- `post_deployment_auditing`: Post-deployment bias auditing
- `human_in_loop`: Human-in-the-loop bias evaluation
- `continuous_learning`: Continuous learning adaptation

## Bias Detection Methods

### 1. Intrinsic vs Extrinsic Bias

**Intrinsic Bias Detection:**
- **WEAT (Word Embedding Association Test)**: Detects bias in word embeddings
- **SEAT (Sentence Embedding Association Test)**: Detects bias in sentence embeddings
- **Embedding Analysis**: Analyzes representation bias in model embeddings

**Extrinsic Bias Detection:**
- **StereoSet**: Detects stereotype bias in generated text
- **CrowS-Pairs**: Uses crowdsourced stereotype pairs for bias detection
- **BBQ (Bias Benchmark for QA)**: Detects bias in question answering
- **Minimal Pairs Testing**: Behavioral bias through minimal pairs

### 2. Modern Explainability Methods

**Attention Visualization:**
- Visualizes attention patterns in transformer layers
- Tools: BertViz, Attention-Maps, Transformer Interpretability

**Activation Patching:**
- Interventional methods to understand causal relationships
- Tools: TransformerLens, Neel Nanda's interpretability library

**Circuit Discovery:**
- Understanding specific neural pathways
- Tools: Anthropic's interpretability research

**Counterfactual Explanations:**
- Generate alternative scenarios to test bias
- Custom counterfactual generation

**Prompt Ablation:**
- Systematically remove prompt components
- Custom ablation framework

### 3. Multimodal Bias Detection

**Text Bias:**
- Demographic bias in language generation
- Occupational stereotype detection
- Cultural bias analysis

**Image Bias:**
- Demographic representation analysis
- Object detection bias
- Scene bias detection

**Audio Bias:**
- Voice characteristic bias
- Accent bias detection
- Language bias analysis

**Video Bias:**
- Motion and activity bias
- Temporal bias detection
- Cross-modal interaction bias

## Evaluation Phases

### 1. Pre-deployment Comprehensive Testing
- Runs all enabled bias tests
- Generates risk assessment
- Provides deployment recommendations
- Creates compliance reports

### 2. Real-time Monitoring
- Continuous bias monitoring
- Drift detection
- Performance degradation alerts
- Demographic group analysis

### 3. Post-deployment Auditing
- Regular bias audits
- Compliance checking
- User feedback analysis
- Incident tracking

### 4. Human-in-the-loop Evaluation
- Expert review
- Crowd evaluation
- Inter-rater reliability analysis
- Consensus building

### 5. Continuous Learning
- Model adaptation
- Bias reduction tracking
- Learning parameter updates
- Performance monitoring

## Risk Assessment

The system uses a four-level risk assessment:

- **LOW**: Model is safe to deploy with standard monitoring
- **MEDIUM**: Deploy with enhanced monitoring and regular audits
- **HIGH**: Deploy with strict monitoring and immediate bias mitigation
- **CRITICAL**: Do not deploy without addressing bias issues

## Compliance Frameworks

### EU AI Act
- Transparency requirements
- Human oversight
- Technical robustness
- Privacy and data governance
- Diversity and non-discrimination
- Societal and environmental wellbeing
- Accountability

### FTC Guidelines
- Transparency
- Explainability
- Fairness
- Accountability

### GDPR
- Lawfulness, fairness, and transparency
- Purpose limitation
- Data minimization
- Accuracy
- Storage limitation
- Integrity and confidentiality
- Accountability

## Usage Examples

### Example 1: Basic LLM Bias Detection

```python
import requests

# Run comprehensive bias evaluation
response = requests.post(
    "http://localhost:8000/api/v1/modern-bias/comprehensive-evaluation",
    json={
        "model_outputs": [
            {
                "text": "The nurse was caring and compassionate",
                "metadata": {"model": "gpt-4"},
                "protected_attributes": {"gender": "female", "profession": "nurse"}
            }
        ],
        "model_type": "llm",
        "include_explainability": True
    }
)

result = response.json()
print(f"Overall Risk: {result['overall_risk']}")
print(f"Bias Detected: {result['bias_tests']['pre_deployment']['bias_detected']}")
```

### Example 2: Multimodal Bias Detection

```python
# Detect bias across multiple modalities
response = requests.post(
    "http://localhost:8000/api/v1/modern-bias/multimodal-detection",
    json={
        "model_outputs": [
            {
                "text": "A professional woman in a business suit",
                "image_url": "https://example.com/image.jpg",
                "audio_url": "https://example.com/audio.wav"
            }
        ],
        "modalities": ["text", "image", "audio"],
        "cross_modal_analysis": True
    }
)

result = response.json()
print(f"Cross-modal bias: {result['cross_modal_bias']}")
```

### Example 3: Tool Integration

```python
# Integrate with modern tools
response = requests.post(
    "http://localhost:8000/api/v1/modern-tools/comprehensive-integration",
    json={
        "model_outputs": [...],
        "selected_tools": ["comet_llm", "deepeval", "arize_phoenix"],
        "integration_config": {
            "comet_llm": {"project_id": "bias_analysis"},
            "deepeval": {"evaluation_criteria": ["bias", "faithfulness"]}
        }
    }
)

result = response.json()
print(f"Tools used: {result['tools_used']}")
print(f"Success rate: {result['summary']['success_rate']}")
```

### Example 4: Comprehensive Evaluation Pipeline

```python
# Run full evaluation pipeline
response = requests.post(
    "http://localhost:8000/api/v1/comprehensive-evaluation/run-comprehensive",
    json={
        "model_id": "model_123",
        "model_type": "llm",
        "model_outputs": [...],
        "evaluation_config": {
            "pre_deployment": {"enabled": True, "bias_threshold": 0.1},
            "real_time_monitoring": {"enabled": True},
            "post_deployment_auditing": {"enabled": True},
            "human_in_loop": {"enabled": True},
            "continuous_learning": {"enabled": True}
        }
    }
)

result = response.json()
print(f"Phases completed: {result['phases_completed']}")
print(f"Overall risk: {result['overall_risk']}")
print(f"Next evaluation due: {result['next_evaluation_due']}")
```

## Best Practices

### 1. Multi-layered Approach
- Use multiple bias detection methods
- Combine automated and human evaluation
- Implement continuous monitoring
- Regular auditing and assessment

### 2. Tool Integration
- Use multiple tools for comprehensive analysis
- Integrate with existing MLOps pipelines
- Implement real-time monitoring
- Maintain audit trails

### 3. Compliance
- Understand applicable regulations
- Implement compliance monitoring
- Maintain documentation
- Regular compliance audits

### 4. Continuous Improvement
- Monitor bias trends over time
- Adapt detection methods
- Update evaluation criteria
- Learn from incidents

## Troubleshooting

### Common Issues

1. **High Bias Scores**: Review training data, implement bias mitigation
2. **Tool Integration Failures**: Check API keys, network connectivity
3. **Evaluation Timeouts**: Reduce sample size, optimize configuration
4. **Compliance Issues**: Review requirements, update processes

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check service health:
```bash
curl http://localhost:8000/api/v1/modern-bias/health
curl http://localhost:8000/api/v1/modern-tools/health
curl http://localhost:8000/api/v1/comprehensive-evaluation/health
```

## Future Enhancements

1. **Advanced Explainability**: Integration with newer interpretability methods
2. **Real-time Integration**: Live model monitoring and adaptation
3. **Enhanced Multimodal**: Support for more modalities and interactions
4. **Automated Mitigation**: Automatic bias correction and model updates
5. **Federated Bias Detection**: Distributed bias detection across systems

## Conclusion

The modern bias detection system in FairMind provides a comprehensive, multi-layered approach to detecting and mitigating bias in generative AI models. By combining traditional bias detection methods with modern explainability techniques and tool integrations, it addresses the unique challenges posed by large-scale generative models while maintaining compliance with evolving regulations.

The system is designed to be:
- **Comprehensive**: Covers all aspects of bias detection and explainability
- **Scalable**: Handles large models and datasets efficiently
- **Compliant**: Meets current and emerging regulatory requirements
- **Extensible**: Easy to add new methods and tools
- **Practical**: Provides actionable insights and recommendations

