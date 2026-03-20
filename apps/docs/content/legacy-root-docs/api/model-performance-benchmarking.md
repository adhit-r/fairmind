# Model Performance Benchmarking API

This document provides comprehensive documentation for the Model Performance Benchmarking API, which allows you to compare multiple models across various performance metrics.

## Overview

The Model Performance Benchmarking API enables you to:
- Run performance benchmarks on multiple models
- Compare models across various metrics (accuracy, latency, fairness, etc.)
- Track historical performance metrics
- Generate comprehensive performance reports
- Identify the best performing models

## Endpoints

### Run Benchmark

**POST** `/api/v1/model-performance/run-benchmark`

Run a performance benchmark on multiple models using the same dataset.

**Request Body:**
```json
{
  "benchmark_name": "Credit Risk Model Comparison",
  "dataset_id": "credit-risk-dataset-1",
  "task_type": "classification",
  "model_predictions": {
    "model-1": [0, 1, 0, 1, 0],
    "model-2": [0, 1, 1, 1, 0]
  },
  "ground_truth": [0, 1, 0, 1, 0],
  "model_metadata": {
    "model-1": {
      "name": "Random Forest",
      "latency_ms": 50.5,
      "memory_usage_mb": 256.0
    },
    "model-2": {
      "name": "Neural Network",
      "latency_ms": 120.3,
      "memory_usage_mb": 512.0
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "run_id": "benchmark-run-123",
  "benchmark_name": "Credit Risk Model Comparison",
  "metrics": {
    "model-1": {
      "accuracy": 0.85,
      "f1_score": 0.82,
      "latency_ms": 50.5
    },
    "model-2": {
      "accuracy": 0.88,
      "f1_score": 0.85,
      "latency_ms": 120.3
    }
  },
  "comparison_results": {
    "rankings": {
      "accuracy": [
        {"model_id": "model-2", "value": 0.88, "rank": 1},
        {"model_id": "model-1", "value": 0.85, "rank": 2}
      ]
    },
    "best_models": {
      "accuracy": "model-2",
      "latency_ms": "model-1"
    }
  }
}
```

### Compare Models

**POST** `/api/v1/model-performance/compare-models`

Compare multiple models based on their historical performance metrics.

**Request Body:**
```json
{
  "model_ids": ["model-1", "model-2", "model-3"],
  "metrics_to_compare": ["accuracy", "f1_score", "latency_ms"]
}
```

**Response:**
```json
{
  "success": true,
  "benchmark_id": "comparison-123",
  "models": ["model-1", "model-2", "model-3"],
  "comparison_metrics": {
    "accuracy": {
      "model-1": 0.85,
      "model-2": 0.88,
      "model-3": 0.82
    }
  },
  "rankings": {
    "accuracy": [
      {"model_id": "model-2", "value": 0.88, "rank": 1},
      {"model_id": "model-1", "value": 0.85, "rank": 2},
      {"model_id": "model-3", "value": 0.82, "rank": 3}
    ]
  },
  "best_model": {
    "accuracy": "model-2"
  }
}
```

### List Benchmark Runs

**GET** `/api/v1/model-performance/benchmark-runs?limit=10&offset=0`

List recent benchmark runs.

**Response:**
```json
{
  "success": true,
  "runs": [
    {
      "run_id": "benchmark-run-123",
      "benchmark_name": "Credit Risk Model Comparison",
      "task_type": "classification",
      "models": ["model-1", "model-2"],
      "created_at": "2024-01-20T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Get Benchmark Run

**GET** `/api/v1/model-performance/benchmark-runs/{run_id}`

Get detailed information about a specific benchmark run.

### Get Model Performance History

**GET** `/api/v1/model-performance/models/{model_id}/performance-history?limit=10`

Get historical performance metrics for a specific model.

### Generate Performance Report

**GET** `/api/v1/model-performance/benchmark-runs/{run_id}/report`

Generate a comprehensive performance report for a benchmark run.

### Get Task Types

**GET** `/api/v1/model-performance/task-types`

Get list of available task types for benchmarking.

### Get Performance Metrics

**GET** `/api/v1/model-performance/performance-metrics`

Get list of available performance metrics.

## Performance Metrics

### Classification Metrics
- `accuracy`: Overall accuracy
- `precision`: Precision score
- `recall`: Recall score
- `f1_score`: F1 score
- `roc_auc`: ROC AUC score (binary classification)
- `log_loss`: Log loss

### Regression Metrics
- `mse`: Mean Squared Error
- `rmse`: Root Mean Squared Error
- `mae`: Mean Absolute Error
- `r2_score`: R² score

### System Metrics
- `latency_ms`: Prediction latency in milliseconds
- `throughput_rps`: Throughput in requests per second
- `memory_usage_mb`: Memory usage in megabytes
- `cpu_usage_percent`: CPU usage percentage

### Fairness Metrics
- `demographic_parity`: Demographic parity score
- `equalized_odds`: Equalized odds score
- `equal_opportunity`: Equal opportunity score

## Task Types

- `classification`: Classification tasks
- `regression`: Regression tasks
- `text_generation`: Text generation tasks
- `image_classification`: Image classification tasks
- `multimodal`: Multimodal tasks

## Code Examples

### Python

```python
import requests

# Run benchmark
response = requests.post(
    "http://localhost:8000/api/v1/model-performance/run-benchmark",
    json={
        "benchmark_name": "Credit Risk Model Comparison",
        "dataset_id": "credit-risk-dataset-1",
        "task_type": "classification",
        "model_predictions": {
            "model-1": [0, 1, 0, 1, 0],
            "model-2": [0, 1, 1, 1, 0]
        },
        "ground_truth": [0, 1, 0, 1, 0],
        "model_metadata": {
            "model-1": {
                "name": "Random Forest",
                "latency_ms": 50.5,
                "memory_usage_mb": 256.0
            }
        }
    }
)

result = response.json()
print(f"Best accuracy: {result['comparison_results']['best_models']['accuracy']}")
```

### JavaScript

```javascript
// Run benchmark
const response = await fetch('http://localhost:8000/api/v1/model-performance/run-benchmark', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    benchmark_name: 'Credit Risk Model Comparison',
    dataset_id: 'credit-risk-dataset-1',
    task_type: 'classification',
    model_predictions: {
      'model-1': [0, 1, 0, 1, 0],
      'model-2': [0, 1, 1, 1, 0]
    },
    ground_truth: [0, 1, 0, 1, 0]
  })
});

const result = await response.json();
console.log(`Best accuracy: ${result.comparison_results.best_models.accuracy}`);
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/model-performance/run-benchmark" \
  -H "Content-Type: application/json" \
  -d '{
    "benchmark_name": "Credit Risk Model Comparison",
    "dataset_id": "credit-risk-dataset-1",
    "task_type": "classification",
    "model_predictions": {
      "model-1": [0, 1, 0, 1, 0],
      "model-2": [0, 1, 1, 1, 0]
    },
    "ground_truth": [0, 1, 0, 1, 0]
  }'
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request data (mismatched prediction/ground truth lengths)
- `404 Not Found`: Benchmark run not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error during benchmarking

## Best Practices

1. **Consistent Data**: Ensure all model predictions are on the same dataset
2. **Metadata**: Include system metrics (latency, memory) for comprehensive comparison
3. **Historical Tracking**: Use model IDs consistently to track performance over time
4. **Fairness Metrics**: Include fairness metrics when comparing models for production use
5. **Regular Benchmarking**: Run benchmarks regularly to track model performance degradation

## Next Steps

- Explore the interactive API documentation at `/docs` (development mode)
- Check the benchmark runs endpoint to see historical comparisons
- Use the performance report endpoint to generate detailed analysis

