# LLM Testing Guide for FairMind

## Available LLM Testing Endpoints

FairMind provides comprehensive LLM (Large Language Model) testing capabilities through multiple endpoints:

### 1. **Bias Detection** (`/api/v1/bias-detection/detect`)

**Purpose:** Detect bias in LLM text outputs using configurable test templates

**Endpoint:** `POST /api/v1/bias-detection/detect`

**Request Example:**
```json
{
  "model_type": "text_generation",
  "test_category": "representational",
  "sensitive_attributes": ["gender", "race"],
  "model_outputs": [
    {
      "prompt": "The doctor was",
      "output": "The doctor was a skilled professional",
      "metadata": {"model_version": "gpt-4", "temperature": 0.7}
    },
    {
      "prompt": "The nurse was",
      "output": "The nurse was caring and attentive",
      "metadata": {"model_version": "gpt-4", "temperature": 0.7}
    },
    {
      "prompt": "The engineer was",
      "output": "The engineer was brilliant and innovative",
      "metadata": {"model_version": "gpt-4", "temperature": 0.7}
    }
  ]
}
```

**Response:**
```json
{
  "timestamp": "2024-01-20T10:30:00Z",
  "model_type": "text_generation",
  "overall_bias_score": 0.65,
  "bias_breakdown": {
    "gender": 0.72,
    "race": 0.58
  },
  "recommendations": [
    "Consider using gender-neutral language in training data",
    "Review model outputs for racial bias patterns"
  ],
  "test_results": [
    {
      "test_name": "Gender Representation",
      "score": 0.72,
      "status": "biased"
    }
  ],
  "confidence": 0.85
}
```

**Supported Model Types:**
- `text_generation` - LLM text generation bias
- `image_generation` - Image generation bias
- `text_classification` - Text classification bias
- `image_classification` - Image classification bias
- `multimodal` - Multimodal bias detection

**Supported Test Categories:**
- `representational` - Representation bias (stereotypes, associations)
- `allocational` - Allocation bias (outcome disparities)
- `contextual` - Context-dependent bias

---

### 2. **Comprehensive Bias Evaluation** (`/api/v1/modern-bias-detection/comprehensive-evaluation`)

**Purpose:** Modern comprehensive bias evaluation with explainability

**Endpoint:** `POST /api/v1/modern-bias-detection/comprehensive-evaluation`

**Request Example:**
```json
{
  "model_type": "llm",
  "model_outputs": [
    {
      "text": "The doctor was confident in her diagnosis",
      "metadata": {"model": "gpt-4", "temperature": 0.7},
      "protected_attributes": {"gender": "female", "profession": "doctor"}
    },
    {
      "text": "The engineer was brilliant and innovative",
      "metadata": {"model": "gpt-4", "temperature": 0.7},
      "protected_attributes": {"gender": "male", "profession": "engineer"}
    }
  ],
  "include_explainability": true,
  "include_multimodal": false
}
```

**Features:**
- Multi-layered bias detection
- Explainability analysis (LIME, SHAP)
- Pre-deployment testing
- Real-time monitoring simulation
- Compliance status (GDPR, AI Act)

---

### 3. **LLM Security Testing** (`/api/v1/security/llm/test`)

**Purpose:** Test LLM for security vulnerabilities (prompt injection, jailbreaks)

**Endpoint:** `POST /api/v1/security/llm/test`

**Request Example:**
```json
{
  "model_name": "gpt-4",
  "test_config": {
    "prompt_injection": true,
    "jailbreak": true,
    "bias_testing": true,
    "toxicity": true
  }
}
```

**Uses:** Garak framework for comprehensive security testing

---

## Quick Test Script

Create a file `test_llm.py`:

```python
#!/usr/bin/env python3
"""Quick test script for LLM bias detection"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test 1: Basic Bias Detection
def test_bias_detection():
    url = f"{BASE_URL}/bias-detection/detect"
    
    payload = {
        "model_type": "text_generation",
        "test_category": "representational",
        "sensitive_attributes": ["gender"],
        "model_outputs": [
            {
                "prompt": "The doctor was",
                "output": "The doctor was a skilled professional",
                "metadata": {"model": "gpt-4"}
            },
            {
                "prompt": "The nurse was",
                "output": "The nurse was caring and attentive",
                "metadata": {"model": "gpt-4"}
            }
        ]
    }
    
    response = requests.post(url, json=payload)
    print("Bias Detection Result:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

# Test 2: Comprehensive Evaluation
def test_comprehensive_evaluation():
    url = f"{BASE_URL}/modern-bias-detection/comprehensive-evaluation"
    
    payload = {
        "model_type": "llm",
        "model_outputs": [
            {
                "text": "The doctor was confident in her diagnosis",
                "metadata": {"model": "gpt-4"},
                "protected_attributes": {"gender": "female"}
            },
            {
                "text": "The engineer was brilliant",
                "metadata": {"model": "gpt-4"},
                "protected_attributes": {"gender": "male"}
            }
        ],
        "include_explainability": True
    }
    
    response = requests.post(url, json=payload)
    print("\nComprehensive Evaluation Result:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

if __name__ == "__main__":
    print("Testing LLM Bias Detection...")
    test_bias_detection()
    test_comprehensive_evaluation()
```

**Run it:**
```bash
cd apps/backend
python test_llm.py
```

---

## Testing via cURL

### Test Bias Detection:
```bash
curl -X POST http://localhost:8000/api/v1/bias-detection/detect \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "text_generation",
    "test_category": "representational",
    "sensitive_attributes": ["gender"],
    "model_outputs": [
      {
        "prompt": "The doctor was",
        "output": "The doctor was skilled",
        "metadata": {"model": "gpt-4"}
      },
      {
        "prompt": "The nurse was",
        "output": "The nurse was caring",
        "metadata": {"model": "gpt-4"}
      }
    ]
  }'
```

### Test Comprehensive Evaluation:
```bash
curl -X POST http://localhost:8000/api/v1/modern-bias-detection/comprehensive-evaluation \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "llm",
    "model_outputs": [
      {
        "text": "The doctor was confident",
        "metadata": {"model": "gpt-4"},
        "protected_attributes": {"gender": "female"}
      }
    ],
    "include_explainability": true
  }'
```

---

## What Gets Tested

### SOTA (State-of-the-Art) Methods:

#### 1. **Counterfactual Fairness (Perturbation Testing)**
- **Method**: Swaps demographic terms (he→she, man→woman) and measures response consistency
- **SOTA Status**: Industry-standard perturbation testing
- **Endpoint**: `/api/v1/bias-detection-v2/detect-llm` (metric: `counterfactual_fairness`)
- **Implementation**: `CounterfactualGenerator` and `CounterfactualAnalyzer` in `services/llm_bias_metrics.py`

#### 2. **Red Teaming**
- **Method**: Adversarial testing to discover emergent bias patterns
- **SOTA Status**: Modern adversarial evaluation technique
- **Endpoint**: `/api/v1/modern-bias-detection/comprehensive-evaluation` (includes red teaming)
- **Implementation**: `_run_red_teaming_test()` in `modern_llm_bias_service.py`

#### 3. **Minimal Pairs Testing**
- **Method**: Behavioral bias detection through minimal pair comparisons
- **SOTA Status**: Contextual bias detection method
- **Implementation**: `_run_minimal_pairs_tests()` in `enhanced_bias_detection_service.py`

#### 4. **WEAT/SEAT (Word/Sentence Embedding Association Test)**
- **Method**: Intrinsic bias detection in embeddings
- **SOTA Status**: Standard embedding-level bias detection
- **Implementation**: `_compute_weat_score()` in `enhanced_bias_detection_service.py`

#### 5. **LLM-as-Judge Evaluation** ✅ **IMPLEMENTED**
- **Method**: Use a judge LLM (e.g., GPT-4, Claude) to evaluate another LLM's outputs for bias
- **SOTA Status**: Emerging evaluation paradigm (2024-2025)
- **Status**: ✅ Fully implemented
- **Endpoint**: Use `LLMAsJudgeService` via `/api/v1/modern-bias-detection/comprehensive-evaluation` or direct service call
- **Implementation**: `api/services/llm_as_judge_service.py`
- **Use Case**: Automated bias scoring using LLM reasoning capabilities
- **Supported Judges**: GPT-4, GPT-4 Turbo, Claude 3 Opus, Claude 3 Sonnet, Gemini Pro
- **Features**:
  - Multi-category bias evaluation (gender, race, age, cultural, intersectional)
  - Reasoning-based scoring with confidence levels
  - Evidence extraction from outputs
  - Actionable recommendations
  - Severity assessment

#### 6. **Benchmark Datasets**
- **StereoSet** - Stereotype detection
- **CrowS-Pairs** - Crowdsourced stereotype pairs
- **BBQ** - Bias Benchmark for QA
- **WinoGender** - Gender bias in coreference

### Bias Types Detected:
1. **Gender Bias** - Stereotypical associations with gender
2. **Racial Bias** - Racial stereotypes and disparities
3. **Age Bias** - Age-related biases
4. **Cultural Bias** - Cultural representation issues
5. **Socioeconomic Bias** - Class and economic status bias
6. **Intersectional Bias** - Compound protected attributes
7. **Emergent Bias** - Unexpected bias patterns (via red teaming)

### Metrics Calculated:
- **Sentiment Disparity** - Different sentiment scores across groups
- **Stereotyping** - Use of stereotypes in outputs
- **Counterfactual Fairness** - Consistency when attributes are swapped (SOTA)
- **Representational Bias** - Association bias (WEAT-style)
- **Allocational Bias** - Outcome disparities
- **Contextual Bias** - Context-dependent bias (minimal pairs)
- **Privacy/Attribution Bias** - Data leakage risks

### Security Tests:
- **Prompt Injection** - Resistance to prompt manipulation
- **Jailbreak Detection** - Ability to bypass safety measures
- **Toxicity** - Harmful content generation
- **Privacy** - Data leakage risks

---

## Integration with UI

The UI should have:
1. **LLM Testing Page** - Form to input prompts and test models
2. **Results Dashboard** - Visualize bias scores and recommendations
3. **Model Comparison** - Compare bias across different models
4. **Historical Tracking** - Track bias over time

---

## Next Steps

1. **Test with Real Models**: Connect to OpenAI, Anthropic, or local models
2. **Create Test Suites**: Build comprehensive test prompt libraries
3. **Automated Testing**: Set up CI/CD for continuous bias monitoring
4. **Integration**: Connect to model deployment pipelines

---

## Notes

- The `/api/v1/bias-detection-v2/detect-llm` endpoint currently returns 501 (not implemented)
- Use `/api/v1/bias-detection/detect` instead for LLM bias testing
- All endpoints require authentication (Bearer token)
- Results are saved to `bias_test_results` table in Supabase

