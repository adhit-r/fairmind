# MLOps Integration for FairMind

This lightweight integration connects FairMind's bias detection system with popular MLOps platforms for experiment tracking and model monitoring.

## Supported Platforms

- **Weights & Biases (W&B)**: Cloud-based experiment tracking with rich visualizations
- **MLflow**: Open-source platform for the complete machine learning lifecycle

## Features

✅ **Automatic Logging**: Bias test results are automatically logged to configured platforms  
✅ **Flexible Configuration**: Support for W&B, MLflow, both, or none  
✅ **Metric Extraction**: Automatically extracts and logs numeric metrics from test results  
✅ **Run Tracking**: Track experiment runs with unique IDs and URLs  
✅ **Non-Blocking**: MLOps logging failures don't affect core functionality  
✅ **Lightweight**: Minimal dependencies and overhead  

## Quick Start

### 1. Install Dependencies

Choose the platform(s) you want to use:

```bash
# For Weights & Biases
pip install wandb

# For MLflow
pip install mlflow

# For both
pip install wandb mlflow
```

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Choose provider: none, wandb, mlflow, or both
MLOPS_PROVIDER=wandb

# Weights & Biases Configuration
WANDB_API_KEY=your-wandb-api-key
WANDB_PROJECT=fairmind-bias-detection
WANDB_ENTITY=your-wandb-username-or-team

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=fairmind_bias_detection
```

### 3. Get Your API Keys

#### Weights & Biases

1. Sign up at [wandb.ai](https://wandb.ai)
2. Go to [wandb.ai/authorize](https://wandb.ai/authorize)
3. Copy your API key
4. Set `WANDB_API_KEY` in your `.env` file

#### MLflow

1. Start MLflow tracking server:
   ```bash
   mlflow server --host 0.0.0.0 --port 5000
   ```
2. Set `MLFLOW_TRACKING_URI=http://localhost:5000` in your `.env` file

For cloud MLflow, use your hosted tracking URI.

## Usage

### Automatic Logging

Once configured, all bias tests are automatically logged:

```python
from services.bias_test_results import bias_test_results

# Run a bias test
await bias_test_results.save_test_result(
    test_id="test_123",
    user_id="user_456",
    model_id="my_model",
    dataset_id="dataset_789",
    test_type="ml_bias",
    results={
        "accuracy": 0.85,
        "bias_score": 0.12,
        "demographic_parity": 0.95,
        # ... other metrics
    },
    metadata={
        "model_type": "classification",
        "protected_attributes": ["gender", "race"]
    }
)

# Results are automatically logged to W&B and/or MLflow!
```

### Manual Logging via API

You can also manually log tests using the REST API:

```bash
# Check MLOps status
curl http://localhost:8000/api/v1/mlops/status

# Manually log a test
curl -X POST http://localhost:8000/api/v1/mlops/log-test \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test_123",
    "model_id": "my_model",
    "test_type": "ml_bias",
    "results": {
      "accuracy": 0.85,
      "bias_score": 0.12
    },
    "metadata": {
      "model_type": "classification"
    }
  }'

# Get run URL
curl http://localhost:8000/api/v1/mlops/run-url/wandb/run_id_here
```

### Programmatic Access

```python
from services.mlops_integration import mlops_integration

# Check if MLOps is enabled
if mlops_integration.is_enabled():
    print("MLOps integration is active!")

# Get status
status = mlops_integration.get_status()
print(f"Provider: {status['provider']}")
print(f"W&B enabled: {status['wandb']['enabled']}")
print(f"MLflow enabled: {status['mlflow']['enabled']}")

# Manual logging
logging_status = mlops_integration.log_bias_test(
    test_id="test_123",
    model_id="my_model",
    test_type="ml_bias",
    results={"accuracy": 0.85},
    metadata={"model_type": "classification"}
)

print(f"W&B run ID: {logging_status['wandb']['run_id']}")
print(f"MLflow run ID: {logging_status['mlflow']['run_id']}")
```

## What Gets Logged

### Metrics

The integration automatically extracts and logs:

- **Fairness Metrics**: demographic_parity, equalized_odds, equal_opportunity, etc.
- **Performance Metrics**: accuracy, precision, recall, f1_score
- **Bias Scores**: bias_score, disparate_impact, statistical_parity_difference
- **Custom Metrics**: Any numeric values in your results

### Parameters

- `test_id`: Unique test identifier
- `model_id`: Model being tested
- `test_type`: Type of bias test (ml_bias, llm_bias, etc.)
- All metadata fields (if they're strings, numbers, or booleans)

### Tags

- Test type
- Model ID
- Project name

### Summary Statistics

- Overall bias detection status
- Risk level
- High-level summary information

## Configuration Options

### Provider Options

| Value | Description |
|-------|-------------|
| `none` | No MLOps integration (default) |
| `wandb` | Only Weights & Biases |
| `mlflow` | Only MLflow |
| `both` | Both W&B and MLflow |

### Environment Variables

#### Weights & Biases

| Variable | Required | Description |
|----------|----------|-------------|
| `WANDB_API_KEY` | Yes | Your W&B API key |
| `WANDB_PROJECT` | No | Project name (default: fairmind-bias-detection) |
| `WANDB_ENTITY` | No | Username or team name |

#### MLflow

| Variable | Required | Description |
|----------|----------|-------------|
| `MLFLOW_TRACKING_URI` | No | Tracking server URI (default: http://localhost:5000) |
| `MLFLOW_EXPERIMENT_NAME` | No | Experiment name (default: fairmind_bias_detection) |

## API Endpoints

### GET `/api/v1/mlops/status`

Get current MLOps integration status.

**Response:**
```json
{
  "success": true,
  "status": {
    "provider": "wandb",
    "wandb": {
      "enabled": true,
      "project": "fairmind-bias-detection",
      "entity": "my-team"
    },
    "mlflow": {
      "enabled": false,
      "tracking_uri": null,
      "experiment_name": null
    }
  },
  "enabled": true
}
```

### POST `/api/v1/mlops/log-test`

Manually log a bias test to MLOps platforms.

**Request:**
```json
{
  "test_id": "test_123",
  "model_id": "my_model",
  "test_type": "ml_bias",
  "results": {
    "accuracy": 0.85,
    "bias_score": 0.12
  },
  "metadata": {
    "model_type": "classification"
  }
}
```

**Response:**
```json
{
  "success": true,
  "logging_status": {
    "wandb": {
      "enabled": true,
      "success": true,
      "run_id": "abc123",
      "url": "https://wandb.ai/team/project/runs/abc123"
    },
    "mlflow": {
      "enabled": false,
      "success": false
    }
  }
}
```

### GET `/api/v1/mlops/run-url/{provider}/{run_id}`

Get URL for a specific MLOps run.

**Response:**
```json
{
  "success": true,
  "provider": "wandb",
  "run_id": "abc123",
  "url": "https://wandb.ai/team/project/runs/abc123"
}
```

## Troubleshooting

### W&B Not Logging

1. Check API key: `echo $WANDB_API_KEY`
2. Verify you're logged in: `wandb login`
3. Check logs for errors: Look for "W&B logging error" in backend logs
4. Ensure `wandb` package is installed: `pip install wandb`

### MLflow Not Logging

1. Check tracking server is running: `curl http://localhost:5000/health`
2. Verify tracking URI: `echo $MLFLOW_TRACKING_URI`
3. Check logs for errors: Look for "MLflow logging error" in backend logs
4. Ensure `mlflow` package is installed: `pip install mlflow`

### Integration Disabled

If you see "MLOps integration not available":

1. Check `MLOPS_PROVIDER` is set to `wandb`, `mlflow`, or `both`
2. Verify required packages are installed
3. Check backend logs for initialization errors
4. Restart the backend server after configuration changes

## Architecture

```
┌─────────────────────────────────────────┐
│  Bias Test Results Service              │
│  (services/bias_test_results.py)        │
└─────────────┬───────────────────────────┘
              │
              │ Calls on save
              ▼
┌─────────────────────────────────────────┐
│  MLOps Integration Service              │
│  (services/mlops_integration.py)        │
└─────────────┬───────────────────────────┘
              │
              ├──────────────┬─────────────┐
              ▼              ▼             ▼
         ┌────────┐    ┌─────────┐   ┌────────┐
         │  W&B   │    │ MLflow  │   │  None  │
         └────────┘    └─────────┘   └────────┘
```

## Performance Impact

- **Minimal**: Logging happens asynchronously and doesn't block test execution
- **Fail-Safe**: Errors in MLOps logging are caught and logged but don't affect core functionality
- **Lightweight**: Only active when explicitly enabled via configuration

## Best Practices

1. **Start with one platform**: Begin with W&B or MLflow, not both
2. **Use meaningful model IDs**: Makes it easier to track experiments
3. **Include metadata**: Add context like model type, dataset info, etc.
4. **Monitor logs**: Check backend logs for MLOps integration status
5. **Test locally first**: Verify integration works before deploying to production

## Next Steps

- View your experiments in [W&B Dashboard](https://wandb.ai)
- Access MLflow UI at your tracking server URL
- Explore logged metrics and visualizations
- Compare different model versions
- Track bias trends over time

## Support

For issues or questions:
- Check the [FairMind Documentation](https://github.com/yourusername/fairmind)
- W&B Docs: [docs.wandb.ai](https://docs.wandb.ai)
- MLflow Docs: [mlflow.org/docs](https://mlflow.org/docs/latest/index.html)
