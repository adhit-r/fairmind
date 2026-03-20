# FairMind API Endpoints Documentation

Complete mapping of all API endpoints available in the FairMind backend.

**Base URL**: `http://localhost:8000` (development)  
**API Version**: `v1`  
**Prefix**: `/api/v1`

## Table of Contents

1. [Health & Status](#health--status)
2. [Authentication](#authentication)
3. [Core Services](#core-services)
4. [Database](#database)
5. [AI BOM](#ai-bom)
6. [Bias Detection](#bias-detection)
7. [Security](#security)
8. [Monitoring](#monitoring)
9. [Fairness Governance](#fairness-governance)
10. [Provenance](#provenance)
11. [Advanced Fairness](#advanced-fairness)
12. [Modern Bias Detection](#modern-bias-detection)
13. [Modern Tools Integration](#modern-tools-integration)
14. [Comprehensive Bias Evaluation](#comprehensive-bias-evaluation)
15. [Multimodal Bias Detection](#multimodal-bias-detection)
16. [Advanced Bias Detection](#advanced-bias-detection)
17. [Real-time Model Integration](#real-time-model-integration)
18. [Benchmark Suite](#benchmark-suite)
19. [Model Performance Benchmarking](#model-performance-benchmarking)
20. [AI Governance](#ai-governance)

---

## Health & Status

### GET `/health`
Comprehensive health check endpoint.

**Response**: Health status object

### GET `/health/ready`
Kubernetes readiness probe endpoint.

**Response**: Readiness status

### GET `/health/live`
Kubernetes liveness probe endpoint.

**Response**: Liveness status

---

## Authentication

**Base Path**: `/api/v1/auth`

### POST `/api/v1/auth/register`
Register a new user.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response**: `User` object

### POST `/api/v1/auth/token`
Login to get access token (OAuth2 compatible).

**Request Body** (Form Data):
- `username`: Email address
- `password`: Password

**Response**:
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer"
}
```

### GET `/api/v1/auth/me`
Get current user information.

**Headers**:
- `Authorization`: `Bearer <access_token>`

**Response**: `User` object

---

## Core Services

**Base Path**: `/api/v1/core`

### GET `/api/v1/core/`
Root endpoint information.

**Response**: API information

### GET `/api/v1/core/health`
Health check.

**Response**: Health status

### GET `/api/v1/core/models`
List all models.

**Query Parameters**:
- `limit`: int (default: 10)
- `offset`: int (default: 0)

**Response**: Array of models

### GET `/api/v1/core/datasets`
List all datasets.

**Query Parameters**:
- `limit`: int (default: 10)
- `offset`: int (default: 0)

**Response**: Array of datasets

### GET `/api/v1/core/activity/recent`
Get recent activity.

**Response**: Array of activity items

### GET `/api/v1/core/governance/metrics`
Get governance metrics.

**Response**: Governance metrics object

### GET `/api/v1/core/metrics/summary`
Get metrics summary.

**Response**: Metrics summary object

### POST `/api/v1/core/models`
Create new model.

**Request Body**: Model creation data

**Response**: Created model

### POST `/api/v1/core/datasets`
Create new dataset.

**Request Body**: Dataset creation data

**Response**: Created dataset

---

## Database

**Base Path**: `/api/v1/database`

### GET `/api/v1/database/profiles`
Get user profiles from database.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of profiles

### GET `/api/v1/database/bias-analyses`
Get geographic bias analyses.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of bias analyses

### GET `/api/v1/database/audit-logs`
Get audit logs.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of audit logs

### GET `/api/v1/database/country-metrics`
Get country metrics.

**Response**: Country metrics object

### GET `/api/v1/database/dashboard-stats`
Get dashboard statistics.

**Response**: Dashboard stats object

### GET `/api/v1/database/models`
Get models from database.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of models

### GET `/api/v1/database/reports`
Get reports.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of reports

### GET `/api/v1/database/monitoring-metrics`
Get monitoring metrics.

**Response**: Monitoring metrics object

### GET `/api/v1/database/health`
Health check.

**Response**: Health status

### GET `/api/v1/database/test-script`
Test script endpoint.

**Response**: Test result

---

## AI BOM

**Base Path**: `/api/v1/ai-bom`

Endpoints for AI Bill of Materials management.

---

## Bias Detection

**Base Path**: `/api/v1/bias-detection`

### POST `/api/v1/bias-detection/detect`
Detect bias in data or model.

**Request Body**: Bias detection parameters

**Response**: `BiasTestResponse` with detection results

### POST `/api/v1/bias-detection/test/weat`
Run WEAT (Word Embedding Association Test).

**Request Body**: WEAT test parameters

**Response**: Test results

### POST `/api/v1/bias-detection/test/fairness`
Test fairness metrics.

**Request Body**: Fairness test parameters

**Response**: Fairness test results

### POST `/api/v1/bias-detection/test/image`
Test image bias.

**Request Body**: Image test parameters

**Response**: Image bias results

### POST `/api/v1/bias-detection/test/text`
Test text bias.

**Request Body**: Text test parameters

**Response**: Text bias results

### POST `/api/v1/bias-detection/templates`
Create bias test template.

**Request Body**: Template data

**Response**: `TemplateResponse`

### GET `/api/v1/bias-detection/templates`
List all templates.

**Response**: `TemplateResponse` with templates array

### GET `/api/v1/bias-detection/libraries`
List available bias detection libraries.

**Response**: Array of libraries

### POST `/api/v1/bias-detection/libraries/{library_name}/install`
Install bias detection library.

**Response**: Installation status

### GET `/api/v1/bias-detection/history`
Get bias detection history.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of history items

### GET `/api/v1/bias-detection/export`
Export bias detection results.

**Query Parameters**:
- `format`: string (csv, json, pdf)

**Response**: Export file

### GET `/api/v1/bias-detection/health`
Health check.

**Response**: Health status

---

## Security

**Base Path**: `/api/v1/security`

### POST `/api/v1/security/container/scan`
Scan container for security issues.

**Request Body**: Container scan parameters

**Response**: `SecurityScanResponse`

### POST `/api/v1/security/llm/test`
Test LLM for security vulnerabilities.

**Request Body**: LLM test parameters

**Response**: `SecurityScanResponse`

### POST `/api/v1/security/model/analyze`
Analyze model for security issues.

**Request Body**: Model analysis parameters

**Response**: `SecurityScanResponse`

### POST `/api/v1/security/report/generate`
Generate security report.

**Request Body**: Report generation parameters

**Response**: `SecurityReportResponse`

### GET `/api/v1/security/status`
Get security service status.

**Response**: Status object

### GET `/api/v1/security/scans/history`
Get scan history.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of scan history items

### GET `/api/v1/security/scans/{scan_id}`
Get specific scan details.

**Path Parameters**:
- `scan_id`: string

**Response**: Scan details object

### GET `/api/v1/security/compliance/frameworks`
Get compliance frameworks.

**Response**: Array of compliance frameworks

---

## Monitoring

**Base Path**: `/api/v1/monitoring`

Endpoints for system monitoring and metrics.

---

## Fairness Governance

**Base Path**: `/api/v1/fairness-governance`

### POST `/api/v1/fairness-governance/compute-classic-ml-fairness`
Compute classic ML fairness metrics.

**Request Body**:
```json
{
  "y_true": [0, 1, 0],
  "y_pred": [0, 1, 1],
  "sensitive_attributes": {},
  "metrics": ["demographic_parity", "equalized_odds"],
  "confidence_level": 0.95,
  "threshold": 0.05
}
```

**Response**: Fairness metrics

---

## Provenance

**Base Path**: `/api/v1/provenance`

Endpoints for model and data provenance tracking.

---

## Advanced Fairness

**Base Path**: `/api/v1/advanced-fairness`

Endpoints for advanced fairness analysis.

---

## Modern Bias Detection

**Base Path**: `/api/v1/modern-bias-detection`

### POST `/api/v1/modern-bias-detection/comprehensive-evaluation`
Run comprehensive bias evaluation.

**Request Body**: Evaluation parameters

**Response**: `BiasEvaluationResponse`

### POST `/api/v1/modern-bias-detection/multimodal-detection`
Detect bias in multimodal data.

**Request Body**: Multimodal detection parameters

**Response**: `MultimodalBiasResponse`

### POST `/api/v1/modern-bias-detection/explainability-analysis`
Analyze model explainability.

**Request Body**: Explainability parameters

**Response**: `ExplainabilityResponse`

### GET `/api/v1/modern-bias-detection/bias-tests`
List available bias tests.

**Response**: Array of bias tests

### PUT `/api/v1/modern-bias-detection/bias-tests/configure`
Configure bias test.

**Request Body**: Configuration data

**Response**: Configuration result

### GET `/api/v1/modern-bias-detection/bias-categories`
Get bias categories.

**Response**: Array of bias categories

### GET `/api/v1/modern-bias-detection/evaluation-datasets`
Get evaluation datasets.

**Response**: Array of datasets

### GET `/api/v1/modern-bias-detection/health`
Health check.

**Response**: Health status

### POST `/api/v1/modern-bias-detection/batch-evaluation`
Run batch evaluation.

**Request Body**: Batch evaluation parameters

**Response**: Batch evaluation results

### GET `/api/v1/modern-bias-detection/detection-results`
Get detection results.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of results

### GET `/api/v1/modern-bias-detection/evaluation-history`
Get evaluation history.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of history items

---

## Modern Tools Integration

**Base Path**: `/api/v1/modern-tools-integration`

### POST `/api/v1/modern-tools-integration/comprehensive-integration`
Run comprehensive tool integration.

**Request Body**: Integration parameters

**Response**: `ComprehensiveIntegrationResponse`

### POST `/api/v1/modern-tools-integration/comet-llm`
Integrate with Comet LLM.

**Request Body**: Comet LLM parameters

**Response**: `ToolIntegrationResponse`

### POST `/api/v1/modern-tools-integration/deepeval`
Integrate with DeepEval.

**Request Body**: DeepEval parameters

**Response**: `ToolIntegrationResponse`

### POST `/api/v1/modern-tools-integration/arize-phoenix`
Integrate with Arize Phoenix.

**Request Body**: Arize Phoenix parameters

**Response**: `ToolIntegrationResponse`

### POST `/api/v1/modern-tools-integration/aws-clarify`
Integrate with AWS Clarify.

**Request Body**: AWS Clarify parameters

**Response**: `ToolIntegrationResponse`

### POST `/api/v1/modern-tools-integration/confident-ai`
Integrate with Confident AI.

**Request Body**: Confident AI parameters

**Response**: `ToolIntegrationResponse`

### POST `/api/v1/modern-tools-integration/transformer-lens`
Integrate with Transformer Lens.

**Request Body**: Transformer Lens parameters

**Response**: `ToolIntegrationResponse`

### POST `/api/v1/modern-tools-integration/bertviz`
Integrate with BERTviz.

**Request Body**: BERTviz parameters

**Response**: `ToolIntegrationResponse`

### GET `/api/v1/modern-tools-integration/available-tools`
List available tools.

**Response**: Array of available tools

### PUT `/api/v1/modern-tools-integration/configure-tool/{tool_id}`
Configure tool.

**Path Parameters**:
- `tool_id`: string

**Request Body**: Configuration data

**Response**: Configuration result

### GET `/api/v1/modern-tools-integration/tool-status`
Get tool status.

**Response**: Tool status object

### GET `/api/v1/modern-tools-integration/health`
Health check.

**Response**: Health status

### POST `/api/v1/modern-tools-integration/batch-integration`
Run batch integration.

**Request Body**: Batch integration parameters

**Response**: Batch integration results

### GET `/api/v1/modern-tools-integration/integration-history`
Get integration history.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of history items

---

## Comprehensive Bias Evaluation

**Base Path**: `/api/v1/comprehensive-bias-evaluation`

### POST `/api/v1/comprehensive-bias-evaluation/run-comprehensive`
Run comprehensive bias evaluation.

**Request Body**: Evaluation parameters

**Response**: `ComprehensiveEvaluationResponse`

### POST `/api/v1/comprehensive-bias-evaluation/run-phase`
Run specific evaluation phase.

**Request Body**: Phase parameters

**Response**: Phase results

### GET `/api/v1/comprehensive-bias-evaluation/evaluation-history`
Get evaluation history.

**Response**: `EvaluationHistoryResponse`

### GET `/api/v1/comprehensive-bias-evaluation/evaluation/{evaluation_id}`
Get specific evaluation details.

**Path Parameters**:
- `evaluation_id`: string

**Response**: Evaluation details

### GET `/api/v1/comprehensive-bias-evaluation/available-phases`
Get available phases.

**Response**: Array of phases

### GET `/api/v1/comprehensive-bias-evaluation/risk-levels`
Get risk levels.

**Response**: Array of risk levels

### GET `/api/v1/comprehensive-bias-evaluation/compliance-frameworks`
Get compliance frameworks.

**Response**: Array of frameworks

### PUT `/api/v1/comprehensive-bias-evaluation/configure-phase`
Configure evaluation phase.

**Request Body**: Phase configuration

**Response**: Configuration result

### GET `/api/v1/comprehensive-bias-evaluation/pipeline-status`
Get pipeline status.

**Response**: Pipeline status object

### GET `/api/v1/comprehensive-bias-evaluation/health`
Health check.

**Response**: Health status

### POST `/api/v1/comprehensive-bias-evaluation/batch-evaluation`
Run batch evaluation.

**Request Body**: Batch evaluation parameters

**Response**: Batch evaluation results

### GET `/api/v1/comprehensive-bias-evaluation/evaluation-metrics`
Get evaluation metrics.

**Response**: Metrics object

---

## Multimodal Bias Detection

**Base Path**: `/api/v1/multimodal-bias-detection`

### POST `/api/v1/multimodal-bias-detection/image-detection`
Detect bias in images.

**Request Body**: Image detection parameters

**Response**: Array of `MultimodalBiasResult`

### POST `/api/v1/multimodal-bias-detection/audio-detection`
Detect bias in audio.

**Request Body**: Audio detection parameters

**Response**: Array of `MultimodalBiasResult`

### POST `/api/v1/multimodal-bias-detection/video-detection`
Detect bias in video.

**Request Body**: Video detection parameters

**Response**: Array of `MultimodalBiasResult`

### POST `/api/v1/multimodal-bias-detection/cross-modal-detection`
Detect bias across modalities.

**Request Body**: Cross-modal parameters

**Response**: Array of `MultimodalBiasResult`

### POST `/api/v1/multimodal-bias-detection/comprehensive-analysis`
Run comprehensive multimodal analysis.

**Request Body**: Analysis parameters

**Response**: `ComprehensiveMultimodalResponse`

### GET `/api/v1/multimodal-bias-detection/available-modalities`
Get available modalities.

**Response**: Array of modalities

### GET `/api/v1/multimodal-bias-detection/bias-detectors`
Get available bias detectors.

**Response**: Array of detectors

### GET `/api/v1/multimodal-bias-detection/health`
Health check.

**Response**: Health status

### POST `/api/v1/multimodal-bias-detection/batch-analysis`
Run batch analysis.

**Request Body**: Batch analysis parameters

**Response**: Batch analysis results

---

## Advanced Bias Detection

**Base Path**: `/api/v1/advanced-bias-detection`

### GET `/api/v1/advanced-bias-detection/`
Get advanced bias detection capabilities.

**Response**: Capabilities object

### POST `/api/v1/advanced-bias-detection/causal-analysis`
Perform causal bias analysis.

**Request Body**: Causal analysis parameters

**Response**: `AnalysisResponse`

### POST `/api/v1/advanced-bias-detection/counterfactual-analysis`
Perform counterfactual bias analysis.

**Request Body**: Counterfactual parameters

**Response**: `AnalysisResponse`

### POST `/api/v1/advanced-bias-detection/intersectional-analysis`
Perform intersectional bias analysis.

**Request Body**: Intersectional parameters

**Response**: `AnalysisResponse`

### POST `/api/v1/advanced-bias-detection/adversarial-testing`
Perform adversarial bias testing.

**Request Body**: Adversarial test parameters

**Response**: `AnalysisResponse`

### POST `/api/v1/advanced-bias-detection/temporal-analysis`
Perform temporal bias analysis.

**Request Body**: Temporal parameters

**Response**: `AnalysisResponse`

### POST `/api/v1/advanced-bias-detection/contextual-analysis`
Perform contextual bias analysis.

**Request Body**: Contextual parameters

**Response**: `AnalysisResponse`

### GET `/api/v1/advanced-bias-detection/bias-types`
Get available bias types.

**Response**: Array of bias types

### GET `/api/v1/advanced-bias-detection/analysis-methods`
Get available analysis methods.

**Response**: Array of methods

### GET `/api/v1/advanced-bias-detection/health`
Health check.

**Response**: Health status

---

## Real-time Model Integration

**Base Path**: `/api/v1/realtime-model-integration`

### GET `/api/v1/realtime-model-integration/`
Get real-time model integration capabilities.

**Response**: Capabilities object

### POST `/api/v1/realtime-model-integration/configure-model`
Configure model for real-time integration.

**Request Body**: Model configuration

**Response**: Configuration result

### POST `/api/v1/realtime-model-integration/test-connection`
Test connection to model.

**Request Body**: Connection test parameters

**Response**: `ConnectionTestResponse`

### POST `/api/v1/realtime-model-integration/bias-test`
Perform single bias test.

**Request Body**: Bias test parameters

**Response**: `BiasTestResponse`

### POST `/api/v1/realtime-model-integration/comprehensive-analysis`
Perform comprehensive bias analysis.

**Request Body**: Analysis parameters

**Response**: `ComprehensiveAnalysisResponse`

### GET `/api/v1/realtime-model-integration/providers`
Get supported model providers.

**Response**: Array of providers

### GET `/api/v1/realtime-model-integration/bias-test-types`
Get available bias test types.

**Response**: Array of test types

### GET `/api/v1/realtime-model-integration/health`
Health check.

**Response**: Health status

---

## Benchmark Suite

**Base Path**: `/api/v1/benchmark-suite`

### GET `/api/v1/benchmark-suite/`
Get benchmark suite capabilities.

**Response**: Capabilities object

### POST `/api/v1/benchmark-suite/create-dataset`
Create benchmark dataset.

**Request Body**: Dataset creation parameters

**Response**: `BenchmarkDatasetResponse`

### POST `/api/v1/benchmark-suite/evaluate-model`
Evaluate model on benchmark.

**Request Body**: Evaluation parameters

**Response**: `BenchmarkResultResponse`

### POST `/api/v1/benchmark-suite/create-comprehensive-suite`
Create comprehensive benchmark suite.

**Request Body**: Suite creation parameters

**Response**: `BenchmarkSuiteResponse`

### GET `/api/v1/benchmark-suite/benchmark-types`
Get available benchmark types.

**Response**: Array of benchmark types

### GET `/api/v1/benchmark-suite/dataset-types`
Get available dataset types.

**Response**: Array of dataset types

### GET `/api/v1/benchmark-suite/evaluation-metrics`
Get available evaluation metrics.

**Response**: Array of metrics

### GET `/api/v1/benchmark-suite/datasets`
Get available datasets.

**Response**: Array of datasets

### GET `/api/v1/benchmark-suite/dataset/{dataset_id}`
Get specific dataset details.

**Path Parameters**:
- `dataset_id`: string

**Response**: Dataset details

### GET `/api/v1/benchmark-suite/health`
Health check.

**Response**: Health status

---

## Model Performance Benchmarking

**Base Path**: `/api/v1/model-performance-benchmarking`

### POST `/api/v1/model-performance-benchmarking/run-benchmark`
Run a performance benchmark.

**Request Body**: Benchmark parameters

**Response**: `BenchmarkRunResponse`

### POST `/api/v1/model-performance-benchmarking/compare-models`
Compare multiple models.

**Request Body**: Comparison parameters

**Response**: `ModelComparisonResponse`

### GET `/api/v1/model-performance-benchmarking/benchmark-runs`
List benchmark runs.

**Query Parameters**:
- `limit`: int (default: 10)

**Response**: Array of benchmark runs

### GET `/api/v1/model-performance-benchmarking/benchmark-runs/{run_id}`
Get benchmark run details.

**Path Parameters**:
- `run_id`: string

**Response**: Benchmark run details

### GET `/api/v1/model-performance-benchmarking/models/{model_id}/performance-history`
Get model performance history.

**Path Parameters**:
- `model_id`: string

**Response**: Performance history

### GET `/api/v1/model-performance-benchmarking/benchmark-runs/{run_id}/report`
Generate performance report.

**Path Parameters**:
- `run_id`: string

**Response**: Performance report

### GET `/api/v1/model-performance-benchmarking/task-types`
Get available task types.

**Response**: Array of task types

### GET `/api/v1/model-performance-benchmarking/performance-metrics`
Get available performance metrics.

**Response**: Array of metrics

---

## AI Governance

**Base Path**: `/api/v1/ai-governance`

### POST `/api/v1/ai-governance/policies`
Create policy rule.

**Request Body**: Policy rule data

**Response**: Created policy

### GET `/api/v1/ai-governance/policies`
Get policy rules.

**Query Parameters**:
- `framework`: string (optional)

**Response**: Array of policies

### POST `/api/v1/ai-governance/policies/{rule_id}/evaluate`
Evaluate policy rule.

**Path Parameters**:
- `rule_id`: string

**Request Body**: Evaluation data

**Response**: Evaluation result

### POST `/api/v1/ai-governance/compliance/assess`
Assess compliance.

**Request Body**: Assessment parameters

**Response**: Assessment result

### GET `/api/v1/ai-governance/compliance/frameworks`
Get compliance frameworks.

**Response**: Array of frameworks

### GET `/api/v1/ai-governance/compliance/frameworks/{framework}/controls`
Get framework controls.

**Path Parameters**:
- `framework`: string

**Response**: Array of controls

### POST `/api/v1/ai-governance/lifecycle/process`
Process lifecycle stage.

**Request Body**: Lifecycle data

**Response**: Processing result

### GET `/api/v1/ai-governance/lifecycle/{system_id}/summary`
Get lifecycle summary.

**Path Parameters**:
- `system_id`: string

**Response**: Lifecycle summary

### GET `/api/v1/ai-governance/lifecycle/checks`
Get lifecycle checks.

**Response**: Array of checks

### POST `/api/v1/ai-governance/evidence/collect`
Collect evidence.

**Request Body**: Evidence collection parameters

**Response**: Collection result

### POST `/api/v1/ai-governance/evidence/upload`
Upload evidence.

**Request Body**: Evidence file/data

**Response**: Upload result

### GET `/api/v1/ai-governance/evidence/{system_id}`
Get evidence for system.

**Path Parameters**:
- `system_id`: string

**Response**: Evidence array

### POST `/api/v1/ai-governance/evidence/collections`
Create evidence collection.

**Request Body**: Collection data

**Response**: Created collection

### POST `/api/v1/ai-governance/reports/generate`
Generate report.

**Request Body**: Report generation parameters

**Response**: Report generation result

### GET `/api/v1/ai-governance/reports/{report_id}/export`
Export report.

**Path Parameters**:
- `report_id`: string

**Response**: Report file

### POST `/api/v1/ai-governance/risks/assess`
Assess risks.

**Request Body**: Risk assessment parameters

**Response**: Risk assessment result

### POST `/api/v1/ai-governance/incidents`
Create incident.

**Request Body**: Incident data

**Response**: Created incident

### PUT `/api/v1/ai-governance/incidents/{incident_id}/status`
Update incident status.

**Path Parameters**:
- `incident_id`: string

**Request Body**: Status update

**Response**: Updated incident

### GET `/api/v1/ai-governance/dashboard/risk`
Get risk dashboard.

**Response**: Risk dashboard data

### POST `/api/v1/ai-governance/ai-models/register`
Register AI model.

**Request Body**: Model registration data

**Response**: Registered model

### POST `/api/v1/ai-governance/ai-models/{model_id}/explainability`
Add explainability to model.

**Path Parameters**:
- `model_id`: string

**Request Body**: Explainability data

**Response**: Explainability result

### POST `/api/v1/ai-governance/ai-models/{model_id}/bias-detection`
Add bias detection to model.

**Path Parameters**:
- `model_id`: string

**Request Body**: Bias detection data

**Response**: Bias detection result

### GET `/api/v1/ai-governance/ai-models/{model_id}/explainability/summary`
Get explainability summary.

**Path Parameters**:
- `model_id`: string

**Response**: Explainability summary

### GET `/api/v1/ai-governance/ai-models/{model_id}/bias/summary`
Get bias summary.

**Path Parameters**:
- `model_id`: string

**Response**: Bias summary

### GET `/api/v1/ai-governance/status`
Get governance status.

**Response**: Status object

---

## Response Format

All API responses follow this standard format:

```json
{
  "success": true,
  "data": {},
  "message": "string",
  "error": "string"
}
```

## Error Handling

Errors are returned with appropriate HTTP status codes:

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "success": false,
  "error": "Error message",
  "detail": "Additional error details"
}
```

## Authentication

Most endpoints require authentication via JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Rate Limiting

API requests are rate-limited. Check response headers for rate limit information:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time

---

**Last Updated**: 2025-01-01  
**API Version**: v1

