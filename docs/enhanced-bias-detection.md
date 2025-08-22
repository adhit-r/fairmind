# Enhanced Bias Detection System

## Overview

The Enhanced Bias Detection System is a comprehensive solution for identifying, analyzing, and mitigating bias in AI models. It provides multi-layered analysis capabilities with statistical methods, custom rules, LLM-powered insights, and dynamic simulation.

## Key Features

### 1. Statistical Bias Analysis

#### Statistical Parity
- **Definition**: Ensures equal positive prediction rates across protected groups
- **Formula**: `|P(Y=1|A=a) - P(Y=1|A=b)| ≤ threshold`
- **Implementation**: Automatically calculated for all sensitive attributes
- **Threshold**: Configurable (default: 0.1)

#### Demographic Parity
- **Definition**: Equal selection rates across demographic groups
- **Formula**: `|P(Y=1|A=a) - P(Y=1|A=b)| ≤ threshold`
- **Use Case**: Hiring, lending, admissions decisions
- **Threshold**: Configurable (default: 0.05)

#### Equal Opportunity
- **Definition**: Equal true positive rates across groups
- **Formula**: `|P(Y=1|Y_true=1,A=a) - P(Y=1|Y_true=1,A=b)| ≤ threshold`
- **Use Case**: Medical diagnosis, criminal justice
- **Threshold**: Configurable (default: 0.1)

#### Predictive Rate Parity
- **Definition**: Equal precision across groups
- **Formula**: `|P(Y_true=1|Y=1,A=a) - P(Y_true=1|Y=1,A=b)| ≤ threshold`
- **Use Case**: Risk assessment, quality control
- **Threshold**: Configurable (default: 0.1)

### 2. Custom Bias Rules Engine

#### Rule Categories

##### Statistical Rules
```python
{
  "id": "statistical_parity_rule",
  "name": "Statistical Parity Check",
  "category": "statistical",
  "enabled": true,
  "parameters": {
    "threshold": 0.1,
    "sensitive_columns": ["gender", "race"]
  }
}
```

##### Demographic Rules
```python
{
  "id": "demographic_parity_rule",
  "name": "Demographic Parity Check",
  "category": "demographic",
  "enabled": true,
  "parameters": {
    "threshold": 0.05,
    "protected_groups": ["minority", "female"]
  }
}
```

##### Behavioral Rules
```python
{
  "id": "individual_fairness_rule",
  "name": "Individual Fairness Check",
  "category": "behavioral",
  "enabled": true,
  "parameters": {
    "similarity_threshold": 0.8,
    "feature_weights": {"age": 0.3, "income": 0.7}
  }
}
```

##### Temporal Rules
```python
{
  "id": "temporal_fairness_rule",
  "name": "Temporal Fairness Check",
  "category": "temporal",
  "enabled": true,
  "parameters": {
    "time_window": "30d",
    "drift_threshold": 0.1
  }
}
```

##### Geographic Rules
```python
{
  "id": "geographic_fairness_rule",
  "name": "Geographic Fairness Check",
  "category": "geographic",
  "enabled": true,
  "parameters": {
    "regions": ["north", "south", "east", "west"],
    "max_variation": 0.15
  }
}
```

#### Rule Configuration

```python
# Example rule configuration
custom_rules = [
    {
        "id": "income_bias_check",
        "name": "Income-based Bias Detection",
        "category": "statistical",
        "enabled": True,
        "parameters": {
            "threshold": 0.08,
            "sensitive_columns": ["income_level"],
            "severity": "high"
        }
    },
    {
        "id": "age_fairness_check",
        "name": "Age Fairness Validation",
        "category": "demographic",
        "enabled": True,
        "parameters": {
            "threshold": 0.06,
            "protected_groups": ["young", "elderly"],
            "severity": "medium"
        }
    }
]
```

### 3. LLM-Powered Analysis

#### Features
- **Natural Language Processing**: Advanced bias pattern recognition
- **Contextual Understanding**: Domain-specific bias identification
- **Explainable AI**: Human-readable bias explanations
- **Custom Prompts**: Tailored analysis for specific use cases

#### Implementation

```python
# LLM Analysis Configuration
llm_config = {
    "enabled": True,
    "model": "gpt-4",
    "temperature": 0.1,
    "max_tokens": 1000,
    "custom_prompt": """
    Analyze the following dataset for potential bias:
    - Dataset: {dataset_name}
    - Target: {target_column}
    - Sensitive attributes: {sensitive_columns}
    
    Focus on:
    1. Statistical disparities
    2. Potential discrimination patterns
    3. Recommendations for mitigation
    """
}
```

#### Example LLM Response
```json
{
  "bias_patterns": [
    {
      "type": "statistical_disparity",
      "attribute": "gender",
      "severity": "high",
      "description": "Female applicants have 15% lower approval rates",
      "confidence": 0.92
    }
  ],
  "recommendations": [
    "Implement demographic parity constraints",
    "Review feature engineering for gender-related bias",
    "Consider data augmentation for underrepresented groups"
  ],
  "risk_assessment": {
    "overall_risk": "medium",
    "legal_risk": "high",
    "reputational_risk": "medium"
  }
}
```

### 4. Dynamic Simulation

#### Simulation Scenarios

##### Demographic Shift
```python
simulation_config = {
    "scenario": "demographic_shift",
    "parameters": {
        "time_horizon": "2_years",
        "population_change": {
            "minority_groups": "+15%",
            "age_distribution": "aging_population"
        },
        "confidence_level": 0.95
    }
}
```

##### Data Drift
```python
simulation_config = {
    "scenario": "data_drift",
    "parameters": {
        "drift_type": "concept_drift",
        "drift_magnitude": 0.2,
        "detection_window": "30_days",
        "mitigation_strategy": "retraining"
    }
}
```

##### Deployment Impact
```python
simulation_config = {
    "scenario": "deployment_impact",
    "parameters": {
        "deployment_scale": "production",
        "user_population": "diverse",
        "monitoring_period": "6_months",
        "alert_thresholds": {
            "bias_increase": 0.1,
            "performance_degradation": 0.05
        }
    }
}
```

#### Simulation Results
```json
{
  "scenario": "demographic_shift",
  "results": {
    "bias_amplification": 0.12,
    "confidence_interval": [0.08, 0.16],
    "recommendations": [
      "Implement adaptive fairness constraints",
      "Monitor bias drift continuously",
      "Plan for model retraining"
    ]
  }
}
```

## API Usage

### Basic Bias Analysis

```python
import requests

# Basic bias analysis
response = requests.post(
    "http://localhost:8000/bias/analyze-real",
    data={
        "dataset_name": "adult",
        "target_column": "income",
        "sensitive_columns": ["sex", "race"],
        "custom_rules": [],
        "llm_enabled": False,
        "simulation_enabled": False
    }
)

print(response.json())
```

### Advanced Analysis with Custom Rules

```python
# Advanced analysis with custom rules and LLM
custom_rules = [
    {
        "id": "income_bias_check",
        "name": "Income-based Bias Detection",
        "category": "statistical",
        "enabled": True,
        "parameters": {
            "threshold": 0.08,
            "sensitive_columns": ["income_level"]
        }
    }
]

response = requests.post(
    "http://localhost:8000/bias/analyze-real",
    data={
        "dataset_name": "adult",
        "target_column": "income",
        "sensitive_columns": ["sex", "race"],
        "custom_rules": custom_rules,
        "llm_enabled": True,
        "llm_prompt": "Analyze for gender and racial bias in income prediction",
        "simulation_enabled": True
    }
)

print(response.json())
```

### Python SDK Usage

```python
from fairmind import BiasDetector

# Initialize detector
detector = BiasDetector()

# Configure analysis
config = {
    "dataset": "adult",
    "target": "income",
    "sensitive_columns": ["sex", "race"],
    "custom_rules": custom_rules,
    "llm_enabled": True,
    "simulation_enabled": True
}

# Run analysis
results = detector.analyze(config)

# Access results
print(f"Overall bias score: {results.bias_score}")
print(f"Issues found: {len(results.issues)}")
print(f"Recommendations: {results.recommendations}")
```

## Supported Datasets

### Built-in Datasets

1. **Adult Census Income**
   - **Description**: Income prediction based on demographic features
   - **Size**: 48,842 samples
   - **Features**: 14 attributes
   - **Target**: Income > $50K
   - **Sensitive**: sex, race

2. **COMPAS**
   - **Description**: Criminal recidivism prediction
   - **Size**: 6,172 samples
   - **Features**: 7 attributes
   - **Target**: Recidivism within 2 years
   - **Sensitive**: race, sex

3. **German Credit**
   - **Description**: Credit risk assessment
   - **Size**: 1,000 samples
   - **Features**: 20 attributes
   - **Target**: Good credit risk
   - **Sensitive**: age, sex

4. **Diabetes**
   - **Description**: Medical diagnosis prediction
   - **Size**: 768 samples
   - **Features**: 8 attributes
   - **Target**: Diabetes diagnosis
   - **Sensitive**: age, sex

5. **Titanic**
   - **Description**: Survival prediction
   - **Size**: 891 samples
   - **Features**: 12 attributes
   - **Target**: Survival
   - **Sensitive**: sex, class

6. **Credit Card Fraud**
   - **Description**: Fraud detection
   - **Size**: 284,807 samples
   - **Features**: 30 attributes
   - **Target**: Fraudulent transaction
   - **Sensitive**: amount, location

### Custom Dataset Upload

```python
# Upload custom dataset
detector.upload_dataset(
    file_path="path/to/dataset.csv",
    name="my_custom_dataset",
    description="Custom dataset for bias analysis",
    target_column="target",
    sensitive_columns=["gender", "age"]
)
```

## Integration with Responsible AI Tools

### Fairlearn Integration

```python
# Fairlearn bias metrics
fairlearn_results = detector.fairlearn_analysis(
    dataset=dataset,
    target=target,
    sensitive_columns=sensitive_columns
)

print(f"Demographic Parity Difference: {fairlearn_results.demographic_parity_difference}")
print(f"Equalized Odds Difference: {fairlearn_results.equalized_odds_difference}")
```

### AI Fairness 360 Integration

```python
# AIF360 bias metrics
aif360_results = detector.aif360_analysis(
    dataset=dataset,
    target=target,
    sensitive_columns=sensitive_columns
)

print(f"Statistical Parity Difference: {aif360_results.statistical_parity_difference}")
print(f"Equal Opportunity Difference: {aif360_results.equal_opportunity_difference}")
print(f"Disparate Impact: {aif360_results.disparate_impact}")
```

### SHAP Integration

```python
# SHAP explainability
shap_results = detector.shap_analysis(
    dataset=dataset,
    model=model,
    target=target
)

print(f"Feature importance: {shap_results.feature_importance}")
print(f"Bias contribution: {shap_results.bias_contribution}")
```

### DALEX Integration

```python
# DALEX explainability
dalex_results = detector.dalex_analysis(
    dataset=dataset,
    model=model,
    target=target
)

print(f"Model performance: {dalex_results.model_performance}")
print(f"Feature importance: {dalex_results.feature_importance}")
```

## Real-time Monitoring

### Dashboard Configuration

```python
# Configure monitoring dashboard
monitoring_config = {
    "metrics": ["bias_score", "fairness_metrics", "performance_metrics"],
    "alerts": {
        "bias_threshold": 0.1,
        "performance_threshold": 0.05,
        "notification_channels": ["email", "slack"]
    },
    "update_frequency": "5_minutes"
}

detector.setup_monitoring(monitoring_config)
```

### Alert Configuration

```python
# Configure alerts
alerts = {
    "bias_increase": {
        "threshold": 0.1,
        "severity": "high",
        "action": "immediate_notification"
    },
    "performance_degradation": {
        "threshold": 0.05,
        "severity": "medium",
        "action": "scheduled_review"
    }
}

detector.configure_alerts(alerts)
```

## Best Practices

### 1. Data Preparation
- Ensure data quality and completeness
- Identify and document sensitive attributes
- Handle missing values appropriately
- Validate data distributions

### 2. Model Development
- Use diverse training data
- Implement fairness constraints
- Regular bias testing during development
- Document model decisions and assumptions

### 3. Deployment
- Continuous monitoring setup
- Automated bias detection
- Regular model retraining
- Stakeholder communication

### 4. Maintenance
- Regular bias audits
- Performance monitoring
- Model versioning
- Compliance documentation

## Troubleshooting

### Common Issues

1. **High Bias Scores**
   - Review data preprocessing
   - Check for data leakage
   - Consider fairness constraints
   - Analyze feature importance

2. **LLM Analysis Failures**
   - Check API key configuration
   - Verify prompt formatting
   - Monitor rate limits
   - Use fallback analysis

3. **Simulation Errors**
   - Validate simulation parameters
   - Check data compatibility
   - Monitor resource usage
   - Review error logs

### Performance Optimization

1. **Large Datasets**
   - Use sampling for initial analysis
   - Implement parallel processing
   - Optimize memory usage
   - Consider distributed computing

2. **Real-time Analysis**
   - Cache intermediate results
   - Use streaming processing
   - Optimize API responses
   - Implement rate limiting

## Support and Resources

### Documentation
- [API Reference](./api-reference.md)
- [Tutorials](./tutorials.md)
- [Examples](./examples.md)
- [Best Practices](./best-practices.md)

### Community
- [GitHub Discussions](https://github.com/fairmind/discussions)
- [Community Forum](https://community.fairmind.xyz)
- [Slack Channel](https://fairmind.slack.com)

### Support
- [Email Support](mailto:support@fairmind.xyz)
- [Documentation](https://docs.fairmind.xyz)
- [Video Tutorials](https://fairmind.xyz/tutorials)

---

*This documentation is continuously updated. For the latest version, visit [docs.fairmind.xyz](https://docs.fairmind.xyz).*
