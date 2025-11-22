# MLOps Integration Quick Setup

This guide will help you set up W&B or MLflow integration in under 5 minutes.

## Option 1: Weights & Biases (Recommended for Quick Start)

### Step 1: Install W&B
```bash
pip install wandb
```

### Step 2: Get API Key
1. Sign up at [wandb.ai](https://wandb.ai) (free account available)
2. Go to [wandb.ai/authorize](https://wandb.ai/authorize)
3. Copy your API key

### Step 3: Configure Environment
Add to your `.env` file:
```bash
MLOPS_PROVIDER=wandb
WANDB_API_KEY=your-api-key-here
WANDB_PROJECT=fairmind-bias-detection
WANDB_ENTITY=your-username
```

### Step 4: Test
```bash
cd apps/backend
python3 test_mlops_integration.py
```

### Step 5: View Results
Visit [wandb.ai](https://wandb.ai) to see your logged experiments!

---

## Option 2: MLflow (Self-Hosted)

### Step 1: Install MLflow
```bash
pip install mlflow
```

### Step 2: Start MLflow Server
```bash
mlflow server --host 0.0.0.0 --port 5000
```

### Step 3: Configure Environment
Add to your `.env` file:
```bash
MLOPS_PROVIDER=mlflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=fairmind_bias_detection
```

### Step 4: Test
```bash
cd apps/backend
python3 test_mlops_integration.py
```

### Step 5: View Results
Visit [http://localhost:5000](http://localhost:5000) to see your MLflow UI!

---

## Option 3: Both W&B and MLflow

Simply set:
```bash
MLOPS_PROVIDER=both
```

And configure both sets of credentials as shown above.

---

## Verify Integration

Once configured, every bias test will automatically log to your chosen platform(s):

```python
# This will automatically log to W&B/MLflow
await bias_test_results.save_test_result(
    test_id="test_001",
    user_id="user_123",
    model_id="my_model",
    dataset_id="dataset_456",
    test_type="ml_bias",
    results={
        "accuracy": 0.85,
        "bias_score": 0.12,
        # ... other metrics
    }
)
```

Check your W&B dashboard or MLflow UI to see the logged experiment!

---

## Troubleshooting

### "MLOps integration not available"
- Install required packages: `pip install wandb mlflow`
- Restart the backend server

### W&B login issues
```bash
wandb login
# Paste your API key when prompted
```

### MLflow connection issues
- Ensure MLflow server is running: `curl http://localhost:5000/health`
- Check `MLFLOW_TRACKING_URI` is correct

---

## Next Steps

See [MLOPS_INTEGRATION.md](./MLOPS_INTEGRATION.md) for:
- Detailed configuration options
- API endpoints
- Advanced usage
- Best practices
