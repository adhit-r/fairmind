# 🚀 FairMind MLOps Integration

**Lightweight experiment tracking for bias detection tests**

Track your bias detection experiments in [Weights & Biases](https://wandb.ai) and/or [MLflow](https://mlflow.org) with zero code changes.

---

## 📋 Quick Links

- **[5-Minute Setup](./MLOPS_QUICK_START.md)** - Get started fast
- **[Complete Guide](./MLOPS_INTEGRATION.md)** - Detailed documentation
- **[Setup Checklist](./MLOPS_SETUP_CHECKLIST.md)** - Verify your configuration
- **[Implementation Summary](./MLOPS_IMPLEMENTATION_SUMMARY.md)** - Technical details

---

## ✨ Features

- ✅ **Automatic Logging** - Every bias test is tracked automatically
- ✅ **Dual Platform Support** - Works with W&B, MLflow, or both
- ✅ **Zero Code Changes** - Just configure and go
- ✅ **Smart Metric Extraction** - Automatically logs all numeric metrics
- ✅ **Fail-Safe** - MLOps errors don't break your tests
- ✅ **REST API** - Check status and log tests via HTTP
- ✅ **Lightweight** - Minimal dependencies and overhead

---

## 🎯 What You Get

### Automatic Tracking
Every bias test automatically logs:
- **Metrics**: accuracy, bias_score, demographic_parity, etc.
- **Parameters**: model_id, test_type, configuration
- **Tags**: Organized by test type and model
- **Metadata**: Full test context and results

### Dashboards
View your experiments in:
- **W&B**: Rich visualizations, comparisons, reports
- **MLflow**: Model registry, experiment tracking, deployment

### Insights
- Compare model versions
- Track fairness over time
- Identify bias trends
- Share results with stakeholders

---

## 🚀 Quick Start

### 1. Choose Your Platform

**Weights & Biases** (Recommended for beginners)
- ☁️ Cloud-based, no setup required
- 📊 Beautiful visualizations
- 🆓 Free tier available

**MLflow** (Recommended for self-hosting)
- 🏠 Self-hosted, full control
- 🔧 Open source
- 🔒 Keep data private

### 2. Install Dependencies

```bash
# For W&B
pip install wandb

# For MLflow
pip install mlflow

# For both
pip install wandb mlflow
```

### 3. Configure

Add to `.env`:

```bash
# Choose: none, wandb, mlflow, or both
MLOPS_PROVIDER=wandb

# W&B (if using)
WANDB_API_KEY=your-api-key
WANDB_PROJECT=fairmind-bias-detection
WANDB_ENTITY=your-username

# MLflow (if using)
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=fairmind_bias_detection
```

### 4. Test

```bash
cd apps/backend
python3 test_mlops_integration.py
```

### 5. Run Tests

```python
# Your existing code - no changes needed!
await bias_test_results.save_test_result(
    test_id="test_001",
    model_id="my_model",
    test_type="ml_bias",
    results={"accuracy": 0.85, "bias_score": 0.12}
)
# ✅ Automatically logged to W&B/MLflow!
```

### 6. View Results

- **W&B**: Visit [wandb.ai](https://wandb.ai)
- **MLflow**: Visit your tracking server (e.g., http://localhost:5000)

---

## 📊 Example: What Gets Logged

### Input (Your Test Results)
```python
{
    "accuracy": 0.85,
    "precision": 0.82,
    "recall": 0.88,
    "f1_score": 0.85,
    "bias_score": 0.12,
    "demographic_parity": 0.95,
    "equalized_odds": 0.93,
    "disparate_impact": 0.98,
    "summary": {
        "total_metrics": 8,
        "passed_metrics": 7,
        "failed_metrics": 1
    }
}
```

### Output (What's Logged)

**Metrics:**
- accuracy: 0.85
- precision: 0.82
- recall: 0.88
- f1_score: 0.85
- bias_score: 0.12
- demographic_parity: 0.95
- equalized_odds: 0.93
- disparate_impact: 0.98
- summary_total_metrics: 8
- summary_passed_metrics: 7
- summary_failed_metrics: 1

**Parameters:**
- test_id: test_001
- model_id: my_model
- test_type: ml_bias

**Tags:**
- ml_bias
- my_model
- fairmind

---

## 🔌 API Endpoints

### Check Status
```bash
GET /api/v1/mlops/status
```

Returns:
```json
{
  "success": true,
  "enabled": true,
  "status": {
    "provider": "wandb",
    "wandb": {"enabled": true, "project": "fairmind-bias-detection"},
    "mlflow": {"enabled": false}
  }
}
```

### Manual Logging
```bash
POST /api/v1/mlops/log-test
```

Body:
```json
{
  "test_id": "test_001",
  "model_id": "my_model",
  "test_type": "ml_bias",
  "results": {"accuracy": 0.85},
  "metadata": {}
}
```

### Get Run URL
```bash
GET /api/v1/mlops/run-url/{provider}/{run_id}
```

Returns:
```json
{
  "success": true,
  "url": "https://wandb.ai/team/project/runs/abc123"
}
```

---

## 🏗️ Architecture

```
Bias Test
    ↓
BiasTestResultService
    ├─→ Supabase/Local (Primary Storage)
    └─→ MLOpsIntegrationService
         ├─→ Weights & Biases ☁️
         ├─→ MLflow 🖥️
         └─→ None (Disabled)
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [MLOPS_QUICK_START.md](./MLOPS_QUICK_START.md) | 5-minute setup guide |
| [MLOPS_INTEGRATION.md](./MLOPS_INTEGRATION.md) | Complete documentation |
| [MLOPS_SETUP_CHECKLIST.md](./MLOPS_SETUP_CHECKLIST.md) | Verify your setup |
| [MLOPS_IMPLEMENTATION_SUMMARY.md](./MLOPS_IMPLEMENTATION_SUMMARY.md) | Technical details |

---

## 🧪 Testing

Run the test script:

```bash
cd apps/backend
python3 test_mlops_integration.py
```

Expected output:
```
🚀 FairMind MLOps Integration Test Suite

============================================================
MLOps Integration Status Test
============================================================

Provider: wandb
Integration Enabled: True

--- Weights & Biases ---
Enabled: True
Project: fairmind-bias-detection
Entity: my-team

============================================================
MLOps Logging Test
============================================================

Logging test data...
Test ID: test_mlops_integration_001
Model ID: test_model_v1
Test Type: ml_bias

--- Logging Results ---

Weights & Biases:
  ✅ Success!
  Run ID: abc123xyz
  URL: https://wandb.ai/my-team/fairmind-bias-detection/runs/abc123xyz

============================================================
Test Summary
============================================================

✅ All tests passed!
```

---

## 🔧 Configuration Options

### Provider Options

| Value | Description |
|-------|-------------|
| `none` | Disabled (default) |
| `wandb` | Weights & Biases only |
| `mlflow` | MLflow only |
| `both` | Both platforms |

### Environment Variables

**Required:**
- `MLOPS_PROVIDER` - Choose platform(s)

**W&B (if using):**
- `WANDB_API_KEY` - Your API key (required)
- `WANDB_PROJECT` - Project name (optional)
- `WANDB_ENTITY` - Username/team (optional)

**MLflow (if using):**
- `MLFLOW_TRACKING_URI` - Server URL (optional)
- `MLFLOW_EXPERIMENT_NAME` - Experiment name (optional)

---

## 🐛 Troubleshooting

### Integration Not Working

1. **Check configuration:**
   ```bash
   curl http://localhost:8000/api/v1/mlops/status
   ```

2. **Run test script:**
   ```bash
   python3 test_mlops_integration.py
   ```

3. **Check backend logs:**
   ```bash
   tail -f backend.log | grep -i mlops
   ```

### W&B Issues

- **Authentication:** Run `wandb login`
- **API Key:** Check at [wandb.ai/authorize](https://wandb.ai/authorize)
- **Network:** Ensure wandb.ai is accessible

### MLflow Issues

- **Server:** Check `curl http://localhost:5000/health`
- **URI:** Verify `MLFLOW_TRACKING_URI` is correct
- **Firewall:** Ensure port 5000 is open

---

## 💡 Best Practices

1. **Start Simple** - Begin with one platform
2. **Use Meaningful IDs** - Makes tracking easier
3. **Add Metadata** - Include context about tests
4. **Monitor Regularly** - Check dashboards weekly
5. **Compare Versions** - Track improvements over time

---

## 🎓 Learn More

### Weights & Biases
- [Documentation](https://docs.wandb.ai)
- [Tutorials](https://wandb.ai/site/tutorials)
- [Examples](https://github.com/wandb/examples)

### MLflow
- [Documentation](https://mlflow.org/docs/latest/index.html)
- [Tutorials](https://mlflow.org/docs/latest/tutorials-and-examples/index.html)
- [GitHub](https://github.com/mlflow/mlflow)

---

## 🤝 Support

Need help?
1. Check the [documentation](./MLOPS_INTEGRATION.md)
2. Run the [test script](../test_mlops_integration.py)
3. Review the [checklist](./MLOPS_SETUP_CHECKLIST.md)
4. Check backend logs for errors

---

## 📝 License

Part of the FairMind project. See main repository for license details.

---

## 🎉 Success!

Once configured, every bias test you run will be automatically tracked in your chosen MLOps platform. No code changes needed - just configure and go!

**Happy tracking! 🚀**
