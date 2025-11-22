# MLOps Integration Setup Checklist

Use this checklist to verify your MLOps integration is properly configured.

## ✅ Pre-Setup

- [ ] Decided on platform: W&B, MLflow, or both
- [ ] Have account/access to chosen platform(s)
- [ ] Backend server is running

## ✅ Installation

### For Weights & Biases
- [ ] Installed wandb: `pip install wandb`
- [ ] Verified installation: `wandb --version`

### For MLflow
- [ ] Installed mlflow: `pip install mlflow`
- [ ] Verified installation: `mlflow --version`
- [ ] Started MLflow server (if self-hosted): `mlflow server --host 0.0.0.0 --port 5000`

## ✅ Configuration

### Environment Variables
- [ ] Added `MLOPS_PROVIDER` to `.env` file
- [ ] Set to correct value: `wandb`, `mlflow`, or `both`

### Weights & Biases (if using)
- [ ] Added `WANDB_API_KEY` to `.env`
- [ ] Added `WANDB_PROJECT` to `.env`
- [ ] Added `WANDB_ENTITY` to `.env` (optional but recommended)
- [ ] API key is valid (check at wandb.ai/authorize)

### MLflow (if using)
- [ ] Added `MLFLOW_TRACKING_URI` to `.env`
- [ ] Added `MLFLOW_EXPERIMENT_NAME` to `.env`
- [ ] Tracking server is accessible (test with curl)

## ✅ Testing

### Run Test Script
```bash
cd apps/backend
python3 test_mlops_integration.py
```

- [ ] Script runs without errors
- [ ] Status shows integration enabled
- [ ] Logging test succeeds
- [ ] Run IDs are generated
- [ ] URLs are displayed

### Verify in Platform

#### Weights & Biases
- [ ] Visit wandb.ai
- [ ] Navigate to your project
- [ ] See test run: `ml_bias_test_mlops_integration_001`
- [ ] Metrics are logged correctly
- [ ] Parameters are visible
- [ ] Tags are applied

#### MLflow
- [ ] Visit MLflow UI (e.g., http://localhost:5000)
- [ ] Navigate to experiment: `fairmind_bias_detection`
- [ ] See test run: `ml_bias_test_mlops_integration_001`
- [ ] Metrics are logged correctly
- [ ] Parameters are visible
- [ ] Tags are applied

## ✅ Integration Test

### Run Actual Bias Test
```bash
# Use your existing bias test workflow
# Or use the API to run a test
```

- [ ] Test completes successfully
- [ ] Check backend logs for MLOps logging status
- [ ] Verify run appears in W&B/MLflow
- [ ] All expected metrics are logged

## ✅ API Endpoints

### Status Endpoint
```bash
curl http://localhost:8000/api/v1/mlops/status
```

- [ ] Returns 200 OK
- [ ] Shows correct provider
- [ ] Shows enabled: true
- [ ] Configuration details are correct

### Manual Logging Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/mlops/log-test \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "manual_test_001",
    "model_id": "test_model",
    "test_type": "ml_bias",
    "results": {"accuracy": 0.85},
    "metadata": {}
  }'
```

- [ ] Returns 200 OK
- [ ] Shows success: true
- [ ] Run IDs are returned
- [ ] Verify in W&B/MLflow dashboard

### Run URL Endpoint
```bash
# Replace with actual run_id from previous test
curl http://localhost:8000/api/v1/mlops/run-url/wandb/YOUR_RUN_ID
```

- [ ] Returns 200 OK
- [ ] URL is valid
- [ ] URL opens in browser

## ✅ Production Readiness

### Security
- [ ] API keys are in `.env`, not committed to git
- [ ] `.env` is in `.gitignore`
- [ ] Production environment uses separate W&B project
- [ ] MLflow tracking server is secured (if applicable)

### Monitoring
- [ ] Backend logs show MLOps integration status on startup
- [ ] Errors are logged but don't break core functionality
- [ ] Can monitor experiment runs in dashboards

### Documentation
- [ ] Team knows how to access W&B/MLflow dashboards
- [ ] Team knows how to interpret logged metrics
- [ ] Troubleshooting guide is accessible

## ✅ Troubleshooting

If any checks fail, refer to:
- `MLOPS_INTEGRATION.md` - Comprehensive guide
- `MLOPS_QUICK_START.md` - Quick setup
- Backend logs - Check for error messages

### Common Issues

#### "MLOps integration not available"
- [ ] Installed required packages
- [ ] Restarted backend server
- [ ] Set `MLOPS_PROVIDER` correctly

#### W&B Authentication Failed
- [ ] API key is correct
- [ ] Ran `wandb login`
- [ ] No firewall blocking wandb.ai

#### MLflow Connection Failed
- [ ] MLflow server is running
- [ ] Tracking URI is correct
- [ ] Server is accessible from backend

#### Metrics Not Logging
- [ ] Results contain numeric values
- [ ] Check backend logs for extraction errors
- [ ] Verify metric names are valid

## 🎉 Success!

If all checks pass:
- ✅ MLOps integration is fully configured
- ✅ Bias tests are automatically tracked
- ✅ Experiments are visible in dashboards
- ✅ Team can monitor model fairness over time

**Next Steps:**
1. Run regular bias tests
2. Monitor trends in W&B/MLflow
3. Compare model versions
4. Track fairness improvements
5. Share results with stakeholders

---

**Need Help?**
- Check documentation in `services/` directory
- Review backend logs for errors
- Test with `test_mlops_integration.py`
- Verify configuration in `.env` file
