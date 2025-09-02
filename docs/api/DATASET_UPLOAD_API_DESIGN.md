# Dataset Upload & Simulation API Design

## 🎯 **Overview**
This document outlines the API design for Phase 1: Real Simulation Data Path, including dataset upload, management, and simulation execution.

## 🔗 **API Endpoints**

### **1. Dataset Management**

#### **POST /api/datasets/upload**
Upload a new dataset (CSV/Parquet file)

**Request:**
```http
POST /api/datasets/upload
Content-Type: multipart/form-data

file: [binary file]
name: string (optional)
description: string (optional)
```

**Response:**
```json
{
  "success": true,
  "dataset": {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "file_path": "string",
    "file_size": 12345,
    "file_type": "csv",
    "schema_json": {
      "columns": [
        {
          "name": "age",
          "type": "integer",
          "sample_values": [25, 30, 35]
        }
      ],
      "row_count": 1000,
      "column_count": 5
    },
    "created_at": "2024-09-03T10:00:00Z"
  }
}
```

#### **GET /api/datasets**
List user's datasets with pagination

**Request:**
```http
GET /api/datasets?page=1&limit=10&search=keyword
```

**Response:**
```json
{
  "success": true,
  "datasets": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "file_type": "csv",
      "row_count": 1000,
      "column_count": 5,
      "created_at": "2024-09-03T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "pages": 3
  }
}
```

#### **GET /api/datasets/{dataset_id}**
Get detailed dataset information

**Response:**
```json
{
  "success": true,
  "dataset": {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "file_path": "string",
    "file_size": 12345,
    "file_type": "csv",
    "schema_json": {
      "columns": [
        {
          "name": "age",
          "type": "integer",
          "min": 18,
          "max": 65,
          "mean": 35.2,
          "null_count": 0,
          "unique_count": 48
        }
      ],
      "row_count": 1000,
      "column_count": 5,
      "sample_data": [
        {"age": 25, "income": 50000, "gender": "M"},
        {"age": 30, "income": 75000, "gender": "F"}
      ]
    },
    "created_at": "2024-09-03T10:00:00Z",
    "updated_at": "2024-09-03T10:00:00Z"
  }
}
```

#### **DELETE /api/datasets/{dataset_id}**
Delete a dataset

**Response:**
```json
{
  "success": true,
  "message": "Dataset deleted successfully"
}
```

### **2. Simulation Management**

#### **POST /api/simulation/run**
Run a simulation with a model and dataset

**Request:**
```json
{
  "name": "string",
  "description": "string",
  "model_id": "uuid",
  "dataset_id": "uuid",
  "config": {
    "target_column": "income",
    "feature_columns": ["age", "education", "experience"],
    "protected_attributes": ["gender", "race"],
    "test_size": 0.2,
    "random_state": 42,
    "bias_detection": {
      "enabled": true,
      "methods": ["demographic_parity", "equal_opportunity"],
      "threshold": 0.1
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "simulation": {
    "id": "uuid",
    "name": "string",
    "status": "running",
    "started_at": "2024-09-03T10:00:00Z",
    "estimated_completion": "2024-09-03T10:05:00Z"
  }
}
```

#### **GET /api/simulation/{simulation_id}**
Get simulation status and results

**Response:**
```json
{
  "success": true,
  "simulation": {
    "id": "uuid",
    "name": "string",
    "status": "completed",
    "started_at": "2024-09-03T10:00:00Z",
    "completed_at": "2024-09-03T10:04:30Z",
    "execution_time_ms": 270000,
    "config": {
      "target_column": "income",
      "feature_columns": ["age", "education", "experience"],
      "protected_attributes": ["gender", "race"]
    },
    "results": {
      "performance_metrics": {
        "accuracy": 0.85,
        "precision": 0.83,
        "recall": 0.87,
        "f1_score": 0.85,
        "auc": 0.89
      },
      "fairness_metrics": {
        "demographic_parity": {
          "overall": 0.12,
          "by_attribute": {
            "gender": 0.08,
            "race": 0.15
          }
        },
        "equal_opportunity": {
          "overall": 0.09,
          "by_attribute": {
            "gender": 0.06,
            "race": 0.12
          }
        }
      },
      "bias_analysis": {
        "overall_bias_score": 0.105,
        "bias_breakdown": {
          "gender": {
            "bias_score": 0.07,
            "risk_level": "low",
            "recommendations": ["Consider feature engineering", "Review training data distribution"]
          },
          "race": {
            "bias_score": 0.135,
            "risk_level": "medium",
            "recommendations": ["Implement fairness constraints", "Collect more diverse training data"]
          }
        }
      }
    }
  }
}
```

#### **GET /api/simulation**
List user's simulation runs

**Request:**
```http
GET /api/simulation?page=1&limit=10&status=completed&model_id=uuid
```

**Response:**
```json
{
  "success": true,
  "simulations": [
    {
      "id": "uuid",
      "name": "string",
      "status": "completed",
      "model_name": "string",
      "dataset_name": "string",
      "started_at": "2024-09-03T10:00:00Z",
      "completed_at": "2024-09-03T10:04:30Z",
      "execution_time_ms": 270000
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 15,
    "pages": 2
  }
}
```

### **3. Enhanced Bias Detection**

#### **POST /api/bias/detect**
Run bias detection on simulation results

**Request:**
```json
{
  "simulation_id": "uuid",
  "bias_types": ["demographic_parity", "equal_opportunity", "equalized_odds"],
  "protected_attributes": ["gender", "race", "age_group"],
  "threshold": 0.1
}
```

**Response:**
```json
{
  "success": true,
  "bias_analysis": {
    "overall_bias_score": 0.105,
    "bias_breakdown": {
      "demographic_parity": {
        "score": 0.12,
        "risk_level": "medium",
        "details": "Model shows preference for certain demographic groups"
      },
      "equal_opportunity": {
        "score": 0.09,
        "risk_level": "low",
        "details": "Model provides similar opportunities across groups"
      }
    },
    "recommendations": [
      "Implement fairness constraints during training",
      "Review training data distribution",
      "Consider post-processing bias mitigation"
    ]
  }
}
```

## 🔒 **Authentication & Security**

### **JWT Token Required**
All endpoints require valid JWT token in Authorization header:
```http
Authorization: Bearer <jwt_token>
```

### **Row Level Security (RLS)**
- Users can only access their own datasets and simulations
- Organization members can access org-level resources
- No public access to sensitive data

### **File Upload Security**
- File type validation (CSV, Parquet only)
- File size limits (configurable, default 100MB)
- Virus scanning (optional)
- Secure file storage with signed URLs

## 📊 **Data Models**

### **Dataset Schema**
```typescript
interface Dataset {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  file_path: string;
  file_size: number;
  file_type: 'csv' | 'parquet';
  schema_json: DatasetSchema;
  row_count: number;
  column_count: number;
  created_at: string;
  updated_at: string;
}

interface DatasetSchema {
  columns: ColumnDefinition[];
  row_count: number;
  column_count: number;
  sample_data?: Record<string, any>[];
}

interface ColumnDefinition {
  name: string;
  type: string;
  min?: number;
  max?: number;
  mean?: number;
  null_count: number;
  unique_count: number;
  sample_values?: any[];
}
```

### **Simulation Schema**
```typescript
interface Simulation {
  id: string;
  owner_id: string;
  model_id: string;
  dataset_id: string;
  name: string;
  description?: string;
  config_json: SimulationConfig;
  results_json?: SimulationResults;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  error_message?: string;
  execution_time_ms?: number;
  created_at: string;
  updated_at: string;
}

interface SimulationConfig {
  target_column: string;
  feature_columns: string[];
  protected_attributes: string[];
  test_size: number;
  random_state: number;
  bias_detection: BiasDetectionConfig;
}

interface SimulationResults {
  performance_metrics: PerformanceMetrics;
  fairness_metrics: FairnessMetrics;
  bias_analysis: BiasAnalysis;
}
```

## 🚀 **Implementation Notes**

### **File Processing**
- Use pandas for CSV/Parquet reading
- Implement streaming for large files
- Cache schema information for performance
- Validate data types and ranges

### **Simulation Engine**
- Async processing for long-running simulations
- Progress tracking and status updates
- Error handling and retry logic
- Resource cleanup on completion

### **Performance Optimization**
- Database indexing on frequently queried columns
- JSONB columns for flexible metadata storage
- Connection pooling for database operations
- Caching for frequently accessed data

## 📈 **Monitoring & Logging**

### **Metrics to Track**
- File upload success/failure rates
- Simulation execution times
- API response times
- Error rates by endpoint
- User activity patterns

### **Logging**
- All API requests and responses
- File processing steps
- Simulation execution details
- Error details with stack traces
- User actions for audit trail

## 🔄 **Error Handling**

### **HTTP Status Codes**
- 200: Success
- 400: Bad Request (validation errors)
- 401: Unauthorized (invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 413: Payload Too Large (file too big)
- 422: Unprocessable Entity (file format issues)
- 500: Internal Server Error

### **Error Response Format**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid file format. Only CSV and Parquet files are supported.",
    "details": {
      "file_type": "txt",
      "allowed_types": ["csv", "parquet"]
    }
  }
}
```

## 🎯 **Next Steps**

1. **Implement database migration** using the migration plan
2. **Create dataset service** with file upload and schema inference
3. **Build simulation engine** with ML model execution
4. **Develop API endpoints** following this design
5. **Add comprehensive testing** and error handling
6. **Integrate with existing bias detection system**
