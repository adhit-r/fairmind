# FairMind AI Model Storage Setup Guide

## Overview

FairMind uses **Supabase Storage Buckets** for AI model storage with local fallback for development. This guide explains the storage architecture and setup process.

## Storage Architecture

### 🪣 Storage Buckets vs 📂 File Storage

| Feature | Storage Buckets (Supabase) | File Storage (Local) |
|---------|---------------------------|---------------------|
| **Scalability** | ✅ Unlimited | ❌ Limited by disk |
| **Versioning** | ✅ Built-in | ❌ Manual |
| **Access Control** | ✅ Organization-based | ❌ Basic file permissions |
| **CDN** | ✅ Global distribution | ❌ No CDN |
| **Backup** | ✅ Automatic | ❌ Manual |
| **Security** | ✅ Encrypted, audit logs | ❌ Basic security |
| **Cost** | 💰 Pay per usage | ✅ Free |

### 🎯 Why Storage Buckets for AI Models?

**Perfect for AI models because:**
- ✅ **Large Files**: Handle GB-sized model files
- ✅ **Version Control**: Track model versions automatically
- ✅ **Access Control**: Organization-based permissions
- ✅ **Global Access**: CDN for fast model loading
- ✅ **Audit Trail**: Track who accessed what models
- ✅ **Compliance**: GDPR/AI Act compliant storage

## Setup Instructions

### 1. Supabase Storage Setup

#### Create Storage Bucket
```sql
-- In Supabase SQL Editor
INSERT INTO storage.buckets (id, name, public)
VALUES ('ai-models', 'ai-models', false);
```

#### Set Up Row Level Security (RLS)
```sql
-- Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy for organization-based access
CREATE POLICY "Organization-based model access" ON storage.objects
FOR ALL USING (
  bucket_id = 'ai-models' AND
  (storage.foldername(name))[1] = auth.jwt() ->> 'organization_id'
);
```

### 2. Environment Configuration

#### Backend Environment Variables
```bash
# .env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
STORAGE_BUCKET=ai-models
```

#### Frontend Environment Variables
```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### 3. Model Storage Structure

```
ai-models/
├── demo_org/
│   ├── credit_risk_v2.1.pkl
│   ├── fraud_detection_v1.5.2.h5
│   ├── customer_segmentation_v1.0.pkl
│   ├── sentiment_analysis_v1.2.1.pt
│   ├── chatbot_gpt4_finetuned.json
│   ├── claude_content_gen_v1.1.json
│   ├── medical_diagnosis_v1.0.h5
│   └── recommendation_engine_v1.4.pkl
└── admin_org/
    ├── loan_approval_v3.0.xgb
    ├── hiring_assistant_v2.2.h5
    ├── price_optimization_v1.3.pkl
    ├── inventory_forecast_v1.1.json
    ├── legal_assistant_gpt4.json
    └── code_reviewer_claude.json
```

## Model File Types

### 🤖 ML Models
- **`.pkl`**: scikit-learn models (pickle format)
- **`.h5`**: TensorFlow/Keras models (HDF5 format)
- **`.pt`**: PyTorch models (torch format)
- **`.xgb`**: XGBoost models (XGBoost format)
- **`.lgb`**: LightGBM models (LightGBM format)

### 🧠 LLM Configurations
- **`.json`**: LLM configuration files
  - Model parameters
  - System prompts
  - Fine-tuning data references
  - API configurations

### 📊 Time Series Models
- **`.json`**: Prophet/ARIMA configurations
- **`.pkl`**: Traditional time series models

## Usage Examples

### Upload Model
```python
from services.model_storage_service import model_storage_service

# Upload a model
with open('my_model.pkl', 'rb') as model_file:
    storage_info = await model_storage_service.upload_model(
        model_file=model_file,
        model_metadata={
            'name': 'My Credit Risk Model',
            'version': '1.0.0',
            'type': 'classification',
            'framework': 'scikit-learn'
        },
        organization_id='demo_org'
    )
```

### Download Model
```python
# Download a model
model_content = await model_storage_service.download_model(
    model_id='demo_org_credit_risk_v1',
    organization_id='demo_org'
)

# Load the model
import pickle
model = pickle.loads(model_content)
```

### List Models
```python
# List all models for an organization
models = await model_storage_service.list_models('demo_org')
for model in models:
    print(f"Model: {model['name']}, Type: {model['type']}")
```

## Security Features

### 🔐 Access Control
- **Organization Isolation**: Models are isolated by organization
- **Role-Based Access**: Different permissions for admins vs users
- **Audit Logging**: Track all model access and modifications

### 🛡️ Data Protection
- **Encryption**: All models encrypted at rest and in transit
- **Backup**: Automatic daily backups
- **Versioning**: Automatic version control for model updates

## Migration from Local to Cloud

### Step 1: Upload Existing Models
```bash
# Run the migration script
python scripts/migrate_models_to_cloud.py
```

### Step 2: Update Configuration
```python
# Update model registry paths
# From: "storage/models/demo_org/credit_risk_v2.1.pkl"
# To: "ai-models/demo_org/credit_risk_v2.1.pkl"
```

### Step 3: Test Cloud Access
```python
# Verify models are accessible from cloud
models = await model_storage_service.list_models('demo_org')
assert len(models) > 0
```

## Cost Optimization

### 💰 Storage Costs
- **Supabase Storage**: ~$0.021/GB/month
- **Bandwidth**: ~$0.09/GB
- **Typical AI Model**: 50MB-500MB

### 📊 Cost Estimation
```
100 models × 100MB average = 10GB
Monthly cost: ~$0.21 + bandwidth
```

## Troubleshooting

### Common Issues

#### 1. Storage Not Available
```python
# Check storage availability
if not model_storage_service.is_supabase_available():
    print("Using local storage fallback")
```

#### 2. Permission Denied
```sql
-- Check RLS policies
SELECT * FROM storage.objects 
WHERE bucket_id = 'ai-models' 
AND name LIKE 'demo_org/%';
```

#### 3. Model Not Found
```python
# Verify model exists
model_metadata = await model_storage_service._get_model_metadata_from_supabase(
    model_id, organization_id
)
if not model_metadata:
    print("Model not found or access denied")
```

## Best Practices

### ✅ Do's
- Use organization-specific folders
- Include model metadata with uploads
- Implement proper error handling
- Monitor storage usage
- Regular backup verification

### ❌ Don'ts
- Don't store sensitive data in model files
- Don't use public buckets for private models
- Don't skip metadata validation
- Don't ignore storage costs

## Monitoring & Analytics

### Storage Metrics
```sql
-- Monitor storage usage
SELECT 
    bucket_id,
    COUNT(*) as file_count,
    SUM(metadata->>'size') as total_size
FROM storage.objects 
WHERE bucket_id = 'ai-models'
GROUP BY bucket_id;
```

### Access Analytics
```sql
-- Track model access
SELECT 
    name,
    COUNT(*) as access_count,
    MAX(updated_at) as last_accessed
FROM storage.objects 
WHERE bucket_id = 'ai-models'
GROUP BY name
ORDER BY access_count DESC;
```

## Next Steps

1. **Set up Supabase Storage bucket**
2. **Configure RLS policies**
3. **Upload existing models**
4. **Test cloud access**
5. **Monitor usage and costs**

For questions or issues, refer to the [Supabase Storage Documentation](https://supabase.com/docs/guides/storage).
