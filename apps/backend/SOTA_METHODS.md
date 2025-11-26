# Complete SOTA LLM Testing Methods in FairMind

## Overview

FairMind implements **multiple State-of-the-Art (SOTA)** methods for LLM bias detection and evaluation. This document catalogs all available methods.

---

## ✅ Implemented SOTA Methods

### 1. **Counterfactual Fairness (Perturbation Testing)**
- **Status**: ✅ Fully Implemented
- **Method**: Swaps demographic terms (he→she, man→woman) and measures response consistency
- **SOTA Status**: Industry-standard perturbation testing
- **Endpoint**: `/api/v1/bias-detection-v2/detect-llm` (metric: `counterfactual_fairness`)
- **Implementation**: `CounterfactualGenerator` and `CounterfactualAnalyzer` in `services/llm_bias_metrics.py`
- **Use Case**: Detecting bias by testing consistency across demographic swaps

### 2. **Red Teaming**
- **Status**: ✅ Fully Implemented
- **Method**: Adversarial testing to discover emergent bias patterns
- **SOTA Status**: Modern adversarial evaluation technique
- **Endpoint**: `/api/v1/modern-bias-detection/comprehensive-evaluation` (includes red teaming)
- **Implementation**: `_run_red_teaming_test()` in `modern_llm_bias_service.py`
- **Use Case**: Discovering unexpected bias patterns through adversarial prompts

### 3. **Minimal Pairs Testing**
- **Status**: ✅ Fully Implemented
- **Method**: Behavioral bias detection through minimal pair comparisons
- **SOTA Status**: Contextual bias detection method
- **Implementation**: `_run_minimal_pairs_tests()` in `enhanced_bias_detection_service.py`
- **Use Case**: Detecting context-dependent bias through controlled comparisons

### 4. **WEAT/SEAT (Word/Sentence Embedding Association Test)**
- **Status**: ✅ Fully Implemented
- **Method**: Intrinsic bias detection in embeddings
- **SOTA Status**: Standard embedding-level bias detection
- **Implementation**: `_compute_weat_score()` in `enhanced_bias_detection_service.py`
- **Use Case**: Detecting bias at the embedding level before text generation

### 5. **LLM-as-Judge Evaluation** ⭐ **NEW**
- **Status**: ✅ Fully Implemented
- **Method**: Use a judge LLM (e.g., GPT-4, Claude) to evaluate another LLM's outputs for bias
- **SOTA Status**: Emerging evaluation paradigm (2024-2025)
- **Implementation**: `api/services/llm_as_judge_service.py`
- **Supported Judges**: GPT-4, GPT-4 Turbo, Claude 3 Opus, Claude 3 Sonnet, Gemini Pro
- **Features**:
  - Multi-category bias evaluation (gender, race, age, cultural, intersectional)
  - Reasoning-based scoring with confidence levels
  - Evidence extraction from outputs
  - Actionable recommendations
  - Severity assessment
- **Use Case**: Automated bias scoring using LLM reasoning capabilities

### 6. **Causal Bias Analysis**
- **Status**: ✅ Fully Implemented
- **Method**: Causal inference to detect treatment effects and confounding
- **SOTA Status**: Advanced causal analysis for bias detection
- **Implementation**: `analyze_causal_bias()` in `advanced_bias_detection_service.py`
- **Use Case**: Understanding causal relationships in biased outcomes

### 7. **Intersectional Bias Detection**
- **Status**: ✅ Fully Implemented
- **Method**: Detects compound effects of multiple protected attributes
- **SOTA Status**: Advanced intersectional analysis
- **Implementation**: `analyze_intersectional_bias()` in `advanced_bias_detection_service.py`
- **Use Case**: Detecting bias for intersectional groups (e.g., Black women, disabled LGBTQ+)

### 8. **Adversarial Bias Testing**
- **Status**: ✅ Fully Implemented
- **Method**: Adversarial attacks to find bias vulnerabilities
- **SOTA Status**: Robustness testing for bias
- **Implementation**: `analyze_adversarial_bias()` in `advanced_bias_detection_service.py`
- **Use Case**: Testing model robustness against bias-inducing inputs

### 9. **Temporal Bias Analysis**
- **Status**: ✅ Fully Implemented
- **Method**: Detects bias drift over time
- **SOTA Status**: Temporal analysis for bias monitoring
- **Implementation**: `analyze_temporal_bias()` in `advanced_bias_detection_service.py`
- **Use Case**: Monitoring bias changes over time (concept drift)

### 10. **Contextual Bias Detection**
- **Status**: ✅ Fully Implemented
- **Method**: Context-sensitive bias detection across domains
- **SOTA Status**: Domain-adaptive bias detection
- **Implementation**: `analyze_contextual_bias()` in `advanced_bias_detection_service.py`
- **Use Case**: Detecting bias that varies by context (professional, cultural, linguistic)

### 11. **Comprehensive Evaluation Pipeline**
- **Status**: ✅ Fully Implemented
- **Method**: Multi-phase evaluation (pre-deployment, real-time, post-deployment, human-in-loop)
- **SOTA Status**: Industry best practice evaluation framework
- **Implementation**: `comprehensive_bias_evaluation_pipeline.py`
- **Phases**:
  1. Pre-deployment comprehensive testing
  2. Real-time monitoring
  3. Post-deployment auditing
  4. Human-in-the-loop evaluation
  5. Continuous learning
- **Use Case**: End-to-end bias evaluation lifecycle

---

## 📊 Benchmark Datasets Support

FairMind supports integration with standard bias benchmarks:

- **StereoSet** - Stereotype detection
- **CrowS-Pairs** - Crowdsourced stereotype pairs
- **BBQ** - Bias Benchmark for QA
- **WinoGender** - Gender bias in coreference
- **BOLD** - Bias in Open-Ended Language Generation Dataset

---

## 🔬 Advanced Analysis Methods

### Causal Inference
- Treatment effect analysis
- Confounding factor detection
- Mediation analysis
- Interaction effects

### Counterfactual Generation
- Minimal intervention identification
- Feature importance for bias
- Intervention effect quantification

### Intersectional Analysis
- Compound effect detection
- Interaction strength measurement
- Worst-case group identification
- Mitigation priority ranking

### Adversarial Testing
- Attack success rate
- Bias amplification measurement
- Robustness scoring
- Vulnerability identification

### Temporal Analysis
- Trend detection
- Seasonality effects
- Concept drift detection
- Performance degradation tracking

---

## 🚀 Quick Start

### Test All SOTA Methods:

```bash
cd apps/backend
python test_llm_endpoints.py
```

This will test:
1. Basic bias detection
2. Comprehensive evaluation
3. **LLM-as-Judge** (NEW)
4. Security testing

### Use LLM-as-Judge Directly:

```python
from api.services.llm_as_judge_service import LLMAsJudgeService, BiasCategory
import asyncio

service = LLMAsJudgeService()

model_outputs = [
    {"prompt": "The doctor was", "output": "The doctor was skilled"},
    {"prompt": "The nurse was", "output": "The nurse was caring"}
]

result = asyncio.run(service.evaluate_bias(
    model_outputs=model_outputs,
    bias_category=BiasCategory.GENDER,
    target_model="gpt-4"
))

print(f"Bias Score: {result.bias_score}")
print(f"Reasoning: {result.reasoning}")
```

---

## 📈 Comparison of Methods

| Method | Speed | Accuracy | Explainability | Use Case |
|--------|-------|----------|----------------|----------|
| Counterfactual Fairness | Fast | High | Medium | Quick bias checks |
| LLM-as-Judge | Medium | Very High | Very High | Detailed analysis |
| Red Teaming | Slow | High | Medium | Discovery |
| WEAT/SEAT | Fast | Medium | Low | Embedding-level |
| Causal Analysis | Slow | Very High | High | Deep understanding |
| Intersectional | Medium | High | High | Compound effects |
| Temporal | Medium | High | Medium | Monitoring |

---

## 🎯 Recommendations

**For Quick Testing**: Use Counterfactual Fairness or WEAT/SEAT

**For Comprehensive Evaluation**: Use LLM-as-Judge or Comprehensive Evaluation Pipeline

**For Discovery**: Use Red Teaming or Adversarial Testing

**For Monitoring**: Use Temporal Analysis or Real-time Monitoring

**For Deep Analysis**: Use Causal Analysis or Intersectional Detection

---

## 📚 References

- **LLM-as-Judge**: Zheng et al., "Judging LLM-as-a-Judge" (2024)
- **Counterfactual Fairness**: Kusner et al., "Counterfactual Fairness" (2017)
- **WEAT**: Caliskan et al., "Semantics derived automatically from language corpora contain human-like biases" (2017)
- **Red Teaming**: Ganguli et al., "Red Teaming Language Models" (2022)

