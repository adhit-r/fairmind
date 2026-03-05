# ML Engineering Guide - Fairmind

## Overview
This guide covers the ML engineering workflows, best practices, and tools used in Fairmind for AI bias detection and fairness analysis.

## Directory Structure

```
apps/ml/
├── models/                    # ML model definitions
│   ├── bias_detection/       # Bias detection models
│   ├── fairness_metrics/     # Fairness calculation models
│   ├── explainability/       # SHAP, LIME, DALEX models
│   └── monitoring/           # Model monitoring models
├── pipelines/                # ML training pipelines
│   ├── data_processing.py    # Data preprocessing pipeline
│   ├── feature_engineering.py # Feature creation pipeline
│   ├── model_training.py     # Model training pipeline
│   └── model_evaluation.py   # Model evaluation pipeline
├── experiments/              # Experiment tracking
│   ├── experiment_tracker.py # MLflow experiment management
│   ├── hyperparameter_tuning.py # Hyperparameter optimization
│   └── model_comparison.py   # Model performance comparison
├── data/                     # Data processing and validation
│   ├── raw/                  # Raw datasets
│   ├── processed/            # Processed datasets
│   └── features/             # Feature datasets
├── evaluation/               # Model evaluation and metrics
│   ├── metrics.py            # Evaluation metrics
│   ├── fairness_metrics.py   # Fairness evaluation
│   └── explainability.py     # Model explainability
├── deployment/               # Model deployment and serving
│   ├── model_serving.py      # Model serving endpoints
│   ├── model_monitoring.py   # Production monitoring
│   └── deployment_pipeline.py # Deployment automation
└── mlflow/                   # MLflow configuration
    └── mlflow_config.py      # MLflow setup and configuration
```

## ML Workflow

### 1. Data Processing Pipeline
```bash
# Run data processing
dvc repro data_processing

# Or run directly
python apps/ml/pipelines/data_processing.py
```

**Features:**
- Data validation and quality assessment
- Missing value handling
- Categorical encoding
- Data type conversion
- Quality metrics logging

### 2. Model Training Pipeline
```bash
# Run model training
dvc repro model_training

# Or run directly
python apps/ml/pipelines/model_training.py
```

**Features:**
- Multiple algorithm support (Random Forest, Logistic Regression, etc.)
- Automatic model type detection (classification vs regression)
- Cross-validation and hyperparameter tuning
- Model performance metrics
- MLflow experiment tracking

### 3. Model Evaluation Pipeline
```bash
# Run model evaluation
dvc repro model_evaluation

# Or run directly
python apps/ml/pipelines/model_evaluation.py
```

**Features:**
- Comprehensive model evaluation
- Fairness metrics calculation
- Bias detection analysis
- Model explainability (SHAP, LIME, DALEX)
- Performance comparison

## MLflow Integration

### Experiment Tracking
```python
import mlflow
from apps.ml.mlflow_config import get_experiment

# Set up experiment
experiment = get_experiment()
mlflow.set_experiment(experiment.name)

# Start run
with mlflow.start_run(run_name="bias_detection_experiment"):
    # Log parameters
    mlflow.log_params({
        "model_type": "random_forest",
        "n_estimators": 100,
        "max_depth": 10
    })
    
    # Train model
    model = train_model(X, y)
    
    # Log metrics
    mlflow.log_metrics({
        "accuracy": accuracy_score(y_test, y_pred),
        "fairness_score": calculate_fairness_score(model, X_test, y_test)
    })
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
```

### Model Registry
```python
# Register model
model_version = mlflow.register_model(
    model_uri="runs:/{run_id}/model",
    name="bias_detection_model"
)

# Transition to staging
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="bias_detection_model",
    version=model_version.version,
    stage="Staging"
)
```

## DVC Integration

### Data Versioning
```bash
# Add data to DVC
dvc add apps/ml/data/raw/dataset.csv

# Commit changes
git add apps/ml/data/raw/dataset.csv.dvc
git commit -m "Add new dataset"
```

### Pipeline Execution
```bash
# Run entire pipeline
dvc repro

# Run specific stage
dvc repro model_training

# Show pipeline status
dvc status
```

## Bias Detection Models

### Fairness Metrics
- **Demographic Parity**: Equal positive prediction rates across groups
- **Equalized Odds**: Equal true positive and false positive rates
- **Equal Opportunity**: Equal true positive rates
- **Disparate Impact**: Ratio of positive prediction rates

### Bias Detection Algorithms
1. **Statistical Parity Analysis**
2. **Group-wise Performance Analysis**
3. **Fairness Constraint Optimization**
4. **Bias Mitigation Techniques**

## Model Explainability

### SHAP Integration
```python
import shap
from apps.ml.evaluation.explainability import SHAPExplainer

explainer = SHAPExplainer(model, X_train)
shap_values = explainer.explain(X_test)
```

### LIME Integration
```python
from lime import lime_tabular
from apps.ml.evaluation.explainability import LIMEExplainer

explainer = LIMEExplainer(model, X_train)
explanations = explainer.explain(X_test)
```

### DALEX Integration
```python
import dalex
from apps.ml.evaluation.explainability import DALEXExplainer

explainer = DALEXExplainer(model, X_train, y_train)
explanations = explainer.explain(X_test)
```

## Model Monitoring

### Performance Monitoring
- Model accuracy tracking
- Prediction drift detection
- Data quality monitoring
- Fairness metrics monitoring

### Alert System
- Performance degradation alerts
- Bias increase alerts
- Data quality alerts
- System health alerts

## Best Practices

### 1. Experiment Management
- Use descriptive run names
- Log all hyperparameters
- Track data versions
- Document model decisions

### 2. Model Development
- Start with simple models
- Use cross-validation
- Test for bias early
- Document model limitations

### 3. Deployment
- Use model registry
- Implement A/B testing
- Monitor model performance
- Plan for model updates

### 4. Fairness
- Test multiple fairness metrics
- Consider intersectional bias
- Document fairness trade-offs
- Regular bias audits

## Getting Started

### 1. Setup Environment
```bash
# Install ML dependencies
pip install -r apps/ml/requirements.txt

# Initialize DVC
dvc init

# Start MLflow server
mlflow server --host 0.0.0.0 --port 5000
```

### 2. Run Sample Pipeline
```bash
# Process sample data
python apps/ml/pipelines/data_processing.py

# Train sample model
python apps/ml/pipelines/model_training.py

# Evaluate model
python apps/ml/pipelines/model_evaluation.py
```

### 3. View Results
- MLflow UI: http://localhost:5000
- Model artifacts: `apps/ml/models/`
- Evaluation results: `apps/ml/evaluation/`

## Troubleshooting

### Common Issues
1. **MLflow connection errors**: Check MLFLOW_TRACKING_URI
2. **DVC pipeline failures**: Check data dependencies
3. **Model training errors**: Verify data format and quality
4. **Memory issues**: Use data sampling for large datasets

### Performance Optimization
1. **Data sampling**: Use stratified sampling for large datasets
2. **Feature selection**: Remove irrelevant features
3. **Model optimization**: Use hyperparameter tuning
4. **Caching**: Enable DVC caching for repeated runs

## Next Steps
1. **Add more ML algorithms**
2. **Implement advanced bias detection**
3. **Add model serving endpoints**
4. **Integrate with production monitoring**
