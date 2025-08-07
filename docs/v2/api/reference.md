# API Reference & Specifications

## 🔗 API Overview

The Fairmind v2 API provides comprehensive access to AI governance and bias detection capabilities through RESTful endpoints. Our API is designed for:

- **Developer-Friendly**: Clear, consistent interface with comprehensive documentation
- **Type-Safe**: Full TypeScript/Python type definitions
- **Scalable**: Rate-limited and optimized for high-throughput scenarios
- **Secure**: JWT authentication with fine-grained permissions
- **Standards-Compliant**: OpenAPI 3.0 specification

### Base URLs

- **Production**: `https://api.fairmind.ai/api/v1`
- **Staging**: `https://staging-api.fairmind.ai/api/v1`
- **Development**: `http://localhost:8000/api/v1`

### Authentication

All API requests require JWT authentication via the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## 📋 OpenAPI Specification

### Core API Schema

```yaml
# api-spec.yaml
openapi: 3.0.3
info:
  title: Fairmind v2 API
  description: AI Governance and Bias Detection API
  version: 2.0.0
  contact:
    name: Fairmind API Support
    url: https://fairmind.ai/support
    email: api-support@fairmind.ai
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.fairmind.ai/api/v1
    description: Production server
  - url: https://staging-api.fairmind.ai/api/v1
    description: Staging server
  - url: http://localhost:8000/api/v1
    description: Development server

security:
  - JWTAuth: []

components:
  securitySchemes:
    JWTAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT authentication token

  schemas:
    Error:
      type: object
      required:
        - detail
        - status_code
      properties:
        detail:
          type: string
          description: Error message
        status_code:
          type: integer
          description: HTTP status code
        request_id:
          type: string
          description: Unique request identifier
        timestamp:
          type: string
          format: date-time
          description: Error timestamp

    BiasAnalysisRequest:
      type: object
      required:
        - model_id
        - dataset_id
        - protected_attributes
        - target_column
      properties:
        model_id:
          type: string
          format: uuid
          description: Unique identifier for the model
        dataset_id:
          type: string
          format: uuid
          description: Unique identifier for the dataset
        analysis_type:
          type: string
          enum: [demographic_parity, equalized_odds, individual_fairness, comprehensive]
          default: comprehensive
          description: Type of bias analysis to perform
        protected_attributes:
          type: array
          items:
            type: string
          description: List of protected/sensitive attributes
          example: ["gender", "race", "age_group"]
        target_column:
          type: string
          description: Name of the target/outcome variable
        prediction_column:
          type: string
          description: Name of the prediction column
        thresholds:
          type: object
          additionalProperties:
            type: number
            minimum: 0
            maximum: 1
          description: Bias thresholds for different metrics
          example:
            demographic_parity: 0.1
            equalized_odds: 0.1
        enable_intersectional_analysis:
          type: boolean
          default: true
          description: Enable intersectional bias analysis
        confidence_level:
          type: number
          minimum: 0.5
          maximum: 0.99
          default: 0.95
          description: Confidence level for statistical tests
        bootstrap_samples:
          type: integer
          minimum: 100
          maximum: 10000
          default: 1000
          description: Number of bootstrap samples for confidence intervals

    BiasMetric:
      type: object
      required:
        - name
        - value
        - threshold
        - status
        - description
      properties:
        name:
          type: string
          description: Name of the bias metric
        value:
          type: number
          description: Calculated metric value
        threshold:
          type: number
          description: Threshold for the metric
        status:
          type: string
          enum: [pass, warning, fail]
          description: Status based on threshold comparison
        confidence_interval:
          type: object
          properties:
            lower:
              type: number
            upper:
              type: number
            level:
              type: number
          description: Confidence interval for the metric
        description:
          type: string
          description: Human-readable description of the metric

    GroupMetrics:
      type: object
      required:
        - group_name
        - group_size
        - metrics
        - comparison_metrics
      properties:
        group_name:
          type: string
          description: Name of the demographic group
        group_size:
          type: integer
          description: Number of samples in the group
        metrics:
          type: object
          additionalProperties:
            type: number
          description: Performance metrics for the group
        comparison_metrics:
          type: object
          additionalProperties:
            type: number
          description: Bias comparison metrics

    BiasAnalysisResponse:
      type: object
      required:
        - analysis_id
        - model_id
        - dataset_id
        - status
        - overall_bias_score
        - compliance_score
      properties:
        analysis_id:
          type: string
          format: uuid
          description: Unique identifier for the analysis
        model_id:
          type: string
          format: uuid
          description: Model identifier
        dataset_id:
          type: string
          format: uuid
          description: Dataset identifier
        status:
          type: string
          enum: [queued, running, completed, failed, cancelled]
          description: Current status of the analysis
        overall_bias_score:
          type: number
          minimum: 0
          maximum: 1
          description: Overall bias score (0 = no bias, 1 = maximum bias)
        compliance_score:
          type: number
          minimum: 0
          maximum: 100
          description: Compliance score percentage
        demographic_parity:
          $ref: '#/components/schemas/BiasMetric'
        equalized_odds:
          $ref: '#/components/schemas/BiasMetric'
        individual_fairness:
          $ref: '#/components/schemas/BiasMetric'
        group_metrics:
          type: array
          items:
            $ref: '#/components/schemas/GroupMetrics'
          description: Detailed metrics for each demographic group
        intersectional_analysis:
          type: object
          description: Results of intersectional bias analysis
        recommendations:
          type: array
          items:
            type: object
            required:
              - type
              - priority
              - description
              - action
            properties:
              type:
                type: string
                description: Type of recommendation
              priority:
                type: string
                enum: [low, medium, high, critical]
                description: Priority level
              description:
                type: string
                description: Description of the issue
              action:
                type: string
                description: Recommended action
          description: List of recommendations for addressing bias
        risk_assessment:
          type: object
          description: Risk assessment results
        analysis_metadata:
          type: object
          description: Analysis metadata and parameters
        created_at:
          type: string
          format: date-time
          description: Analysis creation timestamp
        completed_at:
          type: string
          format: date-time
          description: Analysis completion timestamp

paths:
  /health:
    get:
      summary: Health Check
      description: Check the health status of the API
      tags:
        - Health
      security: []
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: healthy
                  version:
                    type: string
                    example: 2.0.0
                  environment:
                    type: string
                    example: production

  /analysis/bias:
    post:
      summary: Create Bias Analysis
      description: Create a new bias analysis for a model
      tags:
        - Bias Analysis
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BiasAnalysisRequest'
      responses:
        '202':
          description: Analysis created and queued for processing
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BiasAnalysisResponse'
        '400':
          description: Invalid request parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Insufficient permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limit exceeded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /analysis/bias/{analysis_id}:
    get:
      summary: Get Bias Analysis
      description: Retrieve bias analysis results by ID
      tags:
        - Bias Analysis
      parameters:
        - name: analysis_id
          in: path
          required: true
          description: Analysis identifier
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Analysis results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BiasAnalysisResponse'
        '404':
          description: Analysis not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

    delete:
      summary: Delete Bias Analysis
      description: Delete a bias analysis
      tags:
        - Bias Analysis
      parameters:
        - name: analysis_id
          in: path
          required: true
          description: Analysis identifier
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Analysis deleted successfully
        '404':
          description: Analysis not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Insufficient permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /analysis/bias/model/{model_id}:
    get:
      summary: Get Model Analyses
      description: Get all bias analyses for a specific model
      tags:
        - Bias Analysis
      parameters:
        - name: model_id
          in: path
          required: true
          description: Model identifier
          schema:
            type: string
            format: uuid
        - name: limit
          in: query
          description: Maximum number of results
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
        - name: offset
          in: query
          description: Number of results to skip
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: status
          in: query
          description: Filter by analysis status
          schema:
            type: string
            enum: [queued, running, completed, failed, cancelled]
      responses:
        '200':
          description: List of model analyses
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/BiasAnalysisResponse'
        '403':
          description: Insufficient permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

tags:
  - name: Health
    description: Health check endpoints
  - name: Bias Analysis
    description: Bias detection and analysis endpoints
  - name: Model Explanation
    description: Model explainability endpoints
  - name: Compliance
    description: Compliance assessment endpoints
  - name: Monitoring
    description: Model monitoring endpoints
```

## 🚀 Client SDKs

### TypeScript SDK

```typescript
// sdk/typescript/src/client.ts
export interface FairmindClientConfig {
  baseUrl: string
  apiKey: string
  timeout?: number
  retries?: number
}

export interface BiasAnalysisRequest {
  modelId: string
  datasetId: string
  analysisType?: 'demographic_parity' | 'equalized_odds' | 'individual_fairness' | 'comprehensive'
  protectedAttributes: string[]
  targetColumn: string
  predictionColumn?: string
  thresholds?: Record<string, number>
  enableIntersectionalAnalysis?: boolean
  confidenceLevel?: number
  bootstrapSamples?: number
}

export interface BiasAnalysisResponse {
  analysisId: string
  modelId: string
  datasetId: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  overallBiasScore: number
  complianceScore: number
  demographicParity: BiasMetric
  equalizedOdds: BiasMetric
  individualFairness?: BiasMetric
  groupMetrics: GroupMetrics[]
  intersectionalAnalysis?: any
  recommendations: Recommendation[]
  riskAssessment: any
  analysisMetadata: any
  createdAt: string
  completedAt?: string
}

export class FairmindClient {
  private config: FairmindClientConfig
  private baseHeaders: Record<string, string>

  constructor(config: FairmindClientConfig) {
    this.config = {
      timeout: 30000,
      retries: 3,
      ...config
    }
    
    this.baseHeaders = {
      'Authorization': `Bearer ${config.apiKey}`,
      'Content-Type': 'application/json',
      'User-Agent': 'fairmind-sdk-typescript/2.0.0'
    }
  }

  async createBiasAnalysis(request: BiasAnalysisRequest): Promise<BiasAnalysisResponse> {
    return this.request('POST', '/analysis/bias', request)
  }

  async getBiasAnalysis(analysisId: string): Promise<BiasAnalysisResponse> {
    return this.request('GET', `/analysis/bias/${analysisId}`)
  }

  async getModelAnalyses(
    modelId: string, 
    options?: {
      limit?: number
      offset?: number
      status?: string
    }
  ): Promise<BiasAnalysisResponse[]> {
    const params = new URLSearchParams()
    if (options?.limit) params.set('limit', options.limit.toString())
    if (options?.offset) params.set('offset', options.offset.toString())
    if (options?.status) params.set('status', options.status)
    
    const url = `/analysis/bias/model/${modelId}${params.toString() ? `?${params}` : ''}`
    return this.request('GET', url)
  }

  async deleteBiasAnalysis(analysisId: string): Promise<void> {
    await this.request('DELETE', `/analysis/bias/${analysisId}`)
  }

  async waitForAnalysis(
    analysisId: string, 
    options?: {
      timeout?: number
      pollInterval?: number
    }
  ): Promise<BiasAnalysisResponse> {
    const timeout = options?.timeout || 300000 // 5 minutes
    const pollInterval = options?.pollInterval || 5000 // 5 seconds
    const startTime = Date.now()

    while (Date.now() - startTime < timeout) {
      const analysis = await this.getBiasAnalysis(analysisId)
      
      if (analysis.status === 'completed' || analysis.status === 'failed') {
        return analysis
      }
      
      await new Promise(resolve => setTimeout(resolve, pollInterval))
    }
    
    throw new Error(`Analysis ${analysisId} did not complete within ${timeout}ms`)
  }

  private async request<T>(
    method: string, 
    path: string, 
    body?: any
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`
    
    let lastError: Error
    
    for (let attempt = 0; attempt < this.config.retries!; attempt++) {
      try {
        const response = await fetch(url, {
          method,
          headers: this.baseHeaders,
          body: body ? JSON.stringify(body) : undefined,
          signal: AbortSignal.timeout(this.config.timeout!)
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new FairmindAPIError(
            errorData.detail || `HTTP ${response.status}`,
            response.status,
            errorData.request_id
          )
        }
        
        if (method === 'DELETE' && response.status === 204) {
          return undefined as T
        }

        return await response.json()
      } catch (error) {
        lastError = error as Error
        
        if (attempt < this.config.retries! - 1) {
          await new Promise(resolve => 
            setTimeout(resolve, Math.pow(2, attempt) * 1000)
          )
        }
      }
    }
    
    throw lastError!
  }
}

export class FairmindAPIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public requestId?: string
  ) {
    super(message)
    this.name = 'FairmindAPIError'
  }
}

// Usage example
const client = new FairmindClient({
  baseUrl: 'https://api.fairmind.ai/api/v1',
  apiKey: 'your-api-key'
})

// Create analysis
const analysis = await client.createBiasAnalysis({
  modelId: 'model-uuid',
  datasetId: 'dataset-uuid',
  analysisType: 'comprehensive',
  protectedAttributes: ['gender', 'race'],
  targetColumn: 'approved'
})

// Wait for completion
const result = await client.waitForAnalysis(analysis.analysisId)
console.log('Bias analysis completed:', result)
```

### Python SDK

```python
# sdk/python/fairmind_sdk/client.py
import asyncio
import json
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

class AnalysisType(str, Enum):
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUALIZED_ODDS = "equalized_odds"
    INDIVIDUAL_FAIRNESS = "individual_fairness"
    COMPREHENSIVE = "comprehensive"

class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BiasAnalysisRequest:
    model_id: str
    dataset_id: str
    protected_attributes: List[str]
    target_column: str
    analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE
    prediction_column: Optional[str] = None
    thresholds: Optional[Dict[str, float]] = None
    enable_intersectional_analysis: bool = True
    confidence_level: float = 0.95
    bootstrap_samples: int = 1000

@dataclass
class BiasMetric:
    name: str
    value: float
    threshold: float
    status: str
    description: str
    confidence_interval: Optional[Dict[str, float]] = None

@dataclass
class GroupMetrics:
    group_name: str
    group_size: int
    metrics: Dict[str, float]
    comparison_metrics: Dict[str, float]

@dataclass
class BiasAnalysisResponse:
    analysis_id: str
    model_id: str
    dataset_id: str
    status: AnalysisStatus
    overall_bias_score: float
    compliance_score: float
    demographic_parity: BiasMetric
    equalized_odds: BiasMetric
    individual_fairness: Optional[BiasMetric] = None
    group_metrics: List[GroupMetrics] = None
    intersectional_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    analysis_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class FairmindAPIError(Exception):
    def __init__(self, message: str, status_code: int, request_id: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id

class FairmindClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'fairmind-sdk-python/2.0.0'
        }
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers=self.headers
        )

    async def create_bias_analysis(
        self, 
        request: BiasAnalysisRequest
    ) -> BiasAnalysisResponse:
        """Create a new bias analysis"""
        response = await self._request(
            'POST',
            '/analysis/bias',
            json=asdict(request)
        )
        return BiasAnalysisResponse(**response)

    async def get_bias_analysis(self, analysis_id: str) -> BiasAnalysisResponse:
        """Get bias analysis results by ID"""
        response = await self._request('GET', f'/analysis/bias/{analysis_id}')
        return BiasAnalysisResponse(**response)

    async def get_model_analyses(
        self,
        model_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[AnalysisStatus] = None
    ) -> List[BiasAnalysisResponse]:
        """Get all analyses for a model"""
        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        if status is not None:
            params['status'] = status.value

        response = await self._request(
            'GET',
            f'/analysis/bias/model/{model_id}',
            params=params
        )
        return [BiasAnalysisResponse(**item) for item in response]

    async def delete_bias_analysis(self, analysis_id: str) -> None:
        """Delete a bias analysis"""
        await self._request('DELETE', f'/analysis/bias/{analysis_id}')

    async def wait_for_analysis(
        self,
        analysis_id: str,
        timeout: float = 300.0,
        poll_interval: float = 5.0
    ) -> BiasAnalysisResponse:
        """Wait for analysis to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            analysis = await self.get_bias_analysis(analysis_id)
            
            if analysis.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                return analysis
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Analysis {analysis_id} did not complete within {timeout} seconds")

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make HTTP request with retries"""
        url = f"{self.base_url}{path}"
        
        last_exception = None
        
        for attempt in range(self.retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params
                )
                
                if response.status_code >= 400:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except:
                        pass
                    
                    raise FairmindAPIError(
                        error_data.get('detail', f'HTTP {response.status_code}'),
                        response.status_code,
                        error_data.get('request_id')
                    )
                
                if method == 'DELETE' and response.status_code == 204:
                    return None
                
                return response.json()
                
            except (httpx.RequestError, FairmindAPIError) as e:
                last_exception = e
                
                if attempt < self.retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise last_exception

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Usage example
async def main():
    async with FairmindClient(
        base_url='https://api.fairmind.ai/api/v1',
        api_key='your-api-key'
    ) as client:
        
        # Create analysis
        request = BiasAnalysisRequest(
            model_id='model-uuid',
            dataset_id='dataset-uuid',
            protected_attributes=['gender', 'race'],
            target_column='approved',
            analysis_type=AnalysisType.COMPREHENSIVE
        )
        
        analysis = await client.create_bias_analysis(request)
        print(f"Created analysis: {analysis.analysis_id}")
        
        # Wait for completion
        result = await client.wait_for_analysis(analysis.analysis_id)
        print(f"Analysis completed with score: {result.compliance_score}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📖 Usage Examples

### Webhook Integration

```typescript
// webhook-handler.ts
import { NextRequest, NextResponse } from 'next/server'
import { FairmindClient } from '@fairmind/sdk'

export async function POST(request: NextRequest) {
  const payload = await request.json()
  
  // Verify webhook signature
  const signature = request.headers.get('X-Fairmind-Signature')
  if (!verifyWebhookSignature(payload, signature)) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
  }
  
  const { event_type, data } = payload
  
  switch (event_type) {
    case 'analysis.completed':
      await handleAnalysisCompleted(data)
      break
    case 'analysis.failed':
      await handleAnalysisFailed(data)
      break
    case 'compliance.violation':
      await handleComplianceViolation(data)
      break
  }
  
  return NextResponse.json({ received: true })
}

async function handleAnalysisCompleted(data: any) {
  const { analysis_id, compliance_score } = data
  
  if (compliance_score < 70) {
    // Send alert for low compliance score
    await sendSlackAlert(`Low compliance score detected: ${compliance_score}%`)
  }
  
  // Update database
  await updateAnalysisStatus(analysis_id, 'completed', data)
}
```

### Batch Processing

```python
# batch_processor.py
import asyncio
from typing import List
from fairmind_sdk import FairmindClient, BiasAnalysisRequest, AnalysisType

async def batch_analyze_models(
    client: FairmindClient,
    requests: List[BiasAnalysisRequest],
    max_concurrent: int = 5
) -> List[BiasAnalysisResponse]:
    """Process multiple analyses concurrently"""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single(request: BiasAnalysisRequest):
        async with semaphore:
            analysis = await client.create_bias_analysis(request)
            return await client.wait_for_analysis(analysis.analysis_id)
    
    tasks = [process_single(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [r for r in results if not isinstance(r, Exception)]

# Usage
async def main():
    async with FairmindClient(base_url=API_URL, api_key=API_KEY) as client:
        requests = [
            BiasAnalysisRequest(
                model_id=f'model-{i}',
                dataset_id=f'dataset-{i}',
                protected_attributes=['gender', 'race'],
                target_column='approved'
            )
            for i in range(10)
        ]
        
        results = await batch_analyze_models(client, requests)
        print(f"Processed {len(results)} analyses")
```

This comprehensive API documentation provides developers with everything needed to integrate Fairmind v2's AI governance capabilities into their applications and workflows.
