# Dataset Storage Implementation

## Overview

This implementation provides persistent storage for uploaded CSV datasets used in bias detection analysis. It supports both **Supabase (cloud)** and **local file system** storage, with automatic fallback to local storage if Supabase is not configured.

## Features

✅ **Persistent Storage**: Datasets are saved permanently (not in-memory)  
✅ **Dual Storage Support**: Supabase Storage (cloud) or local file system  
✅ **Metadata Tracking**: Full metadata including columns, types, row count, file hash  
✅ **User Isolation**: Each user can only access their own datasets  
✅ **Deduplication**: MD5 hash prevents duplicate uploads  
✅ **Preview Support**: First 10 rows cached for quick preview  
✅ **CRUD Operations**: Upload, list, retrieve, delete datasets  
✅ **Automatic Cleanup**: Orphaned files are prevented with transactional operations  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                                │
│  /bias-v2/upload-dataset                                    │
│  /bias-v2/datasets (list)                                   │
│  /bias-v2/datasets/{id} (get metadata)                      │
│  /bias-v2/datasets/{id} (delete)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            DatasetStorageService                             │
│  - upload_dataset()                                          │
│  - get_dataset()                                             │
│  - list_datasets()                                           │
│  - delete_dataset()                                          │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌──────────────────────────────┐
│  Supabase Storage      │   │  Local File System           │
│  - Storage Bucket      │   │  - ./uploads/datasets/       │
│  - Database Table      │   │  - {user_id}/{dataset_id}    │
│  - RLS Policies        │   │  - .csv + .json files        │
└────────────────────────┘   └──────────────────────────────┘
```

## Setup

### Option 1: Supabase (Recommended for Production)

1. **Set Environment Variables**:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export SUPABASE_STORAGE_BUCKET="datasets"
```

2. **Run Database Migration**:
```bash
# In Supabase SQL Editor, run:
cat apps/backend/supabase/datasets_storage_setup.sql
```

3. **Create Storage Bucket** (via Supabase Dashboard):
   - Go to Storage → Create Bucket
   - Name: `datasets`
   - Public: `false`
   - File size limit: `50MB` (adjust as needed)

### Option 2: Local File System (Development)

1. **Set Environment Variable** (optional):
```bash
export DATASET_STORAGE_PATH="./uploads/datasets"  # default
```

2. **No additional setup required** - directories are created automatically

## Usage

### 1. Upload a Dataset

```bash
curl -X POST "http://localhost:8000/api/v1/bias-v2/upload-dataset" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@credit_data.csv"
```

**Response:**
```json
{
  "dataset_id": "ds_20251122103045_a1b2c3d4",
  "rows": 1000,
  "columns": ["prediction", "gender", "race", "ground_truth"],
  "preview": [
    {"prediction": 1, "gender": "female", "race": "asian", "ground_truth": 1},
    ...
  ]
}
```

### 2. List Your Datasets

```bash
curl "http://localhost:8000/api/v1/bias-v2/datasets?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "datasets": [
    {
      "id": "ds_20251122103045_a1b2c3d4",
      "filename": "credit_data.csv",
      "rows": 1000,
      "columns": ["prediction", "gender", "race"],
      "uploaded_at": "2025-11-22T10:30:45Z",
      "file_size_bytes": 45678
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### 3. Get Dataset Metadata

```bash
curl "http://localhost:8000/api/v1/bias-v2/datasets/ds_20251122103045_a1b2c3d4" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Run Bias Detection with Stored Dataset

```bash
curl -X POST "http://localhost:8000/api/v1/bias-v2/detect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "credit-model-v1",
    "dataset_id": "ds_20251122103045_a1b2c3d4",
    "protected_attribute": "gender",
    "prediction_column": "prediction",
    "ground_truth_column": "ground_truth",
    "metrics": ["demographic_parity", "equalized_odds"]
  }'
```

### 5. Delete a Dataset

```bash
curl -X DELETE "http://localhost:8000/api/v1/bias-v2/datasets/ds_20251122103045_a1b2c3d4" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Dataset ID Format

Dataset IDs follow the pattern: `ds_{timestamp}_{hash}`

- `ds_`: Prefix for dataset
- `{timestamp}`: YYYYMMDDHHMMSS format
- `{hash}`: 8-character MD5 hash for uniqueness

Example: `ds_20251122103045_a1b2c3d4`

## Storage Structure

### Supabase Storage
```
datasets/
├── user_123/
│   ├── ds_20251122103045_a1b2c3d4.csv
│   └── ds_20251122104530_e5f6g7h8.csv
└── user_456/
    └── ds_20251122105015_i9j0k1l2.csv
```

### Local File System
```
./uploads/datasets/
├── user_123/
│   ├── ds_20251122103045_a1b2c3d4.csv
│   ├── ds_20251122103045_a1b2c3d4.json (metadata)
│   ├── ds_20251122104530_e5f6g7h8.csv
│   └── ds_20251122104530_e5f6g7h8.json
└── user_456/
    ├── ds_20251122105015_i9j0k1l2.csv
    └── ds_20251122105015_i9j0k1l2.json
```

## Metadata Schema

```json
{
  "dataset_id": "ds_20251122103045_a1b2c3d4",
  "filename": "credit_data.csv",
  "user_id": "user_123",
  "file_hash": "5d41402abc4b2a76b9719d911017c592",
  "rows": 1000,
  "columns": ["prediction", "gender", "race", "ground_truth"],
  "column_types": {
    "prediction": "int64",
    "gender": "object",
    "race": "object",
    "ground_truth": "int64"
  },
  "file_size_bytes": 45678,
  "uploaded_at": "2025-11-22T10:30:45.123456Z",
  "metadata": {
    "uploaded_by": "user@example.com",
    "upload_source": "api"
  },
  "preview": [
    {"prediction": 1, "gender": "female", "race": "asian", "ground_truth": 1},
    ...
  ]
}
```

## Security

### Row Level Security (RLS)

Supabase RLS policies ensure:
- Users can only view their own datasets
- Users can only upload datasets to their own folder
- Users can only delete their own datasets
- Admin users can access all datasets (optional)

### File Validation

- Only `.csv` files are accepted
- File size limits can be configured
- MD5 hash prevents duplicate uploads
- Malformed CSV files are rejected with clear error messages

## Error Handling

The service provides clear error messages for common scenarios:

- **404**: Dataset not found
- **400**: Invalid CSV format, missing columns
- **500**: Storage service unavailable
- **413**: File too large (if configured)

## Performance Considerations

### Metadata Caching
- Preview data (first 10 rows) is cached in metadata
- Column types are pre-computed and stored
- Avoids loading full dataset for list/preview operations

### Pagination
- List endpoints support `limit` and `offset` parameters
- Default limit: 50 datasets
- Maximum limit: 1000 datasets per request

### File Size Limits
- Recommended max: 50MB per file
- Configurable via Supabase Storage settings
- Large files should be processed asynchronously

## Monitoring & Logging

All operations are logged with:
- User ID and email
- Dataset ID
- Operation type (upload, retrieve, delete)
- Success/failure status
- Error details (if applicable)

Example log:
```
INFO: Dataset uploaded by user@example.com: ds_20251122103045_a1b2c3d4
INFO: Loaded dataset ds_20251122103045_a1b2c3d4 for analysis
INFO: Dataset deleted by user@example.com: ds_20251122103045_a1b2c3d4
```

## Migration from In-Memory Storage

If you have existing code using in-memory storage:

**Before:**
```python
# Old code - in-memory only
dataset_id = f"dataset-{datetime.now().strftime('%Y%m%d%H%M%S')}"
# Data lost after server restart
```

**After:**
```python
# New code - persistent storage
dataset_id, dataset_info = await dataset_storage.upload_dataset(
    file_content=contents,
    filename=file.filename,
    user_id=current_user.user_id
)
# Data persists across server restarts
```

## Testing

### Local Testing
```bash
# Start backend
cd apps/backend
source venv/bin/activate
uvicorn api.main:app --reload --port 8000

# Upload a test dataset
curl -X POST "http://localhost:8000/api/v1/bias-v2/upload-dataset" \
  -H "Authorization: Bearer $(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' -H 'Content-Type: application/json' -d '{"email":"admin@fairmind.ai","password":"admin123"}' | jq -r .access_token)" \
  -F "file=@test_data.csv"
```

### Verify Storage
```bash
# Local file system
ls -la ./uploads/datasets/admin/

# Supabase (via dashboard)
# Go to Storage → datasets bucket → Browse files
```

## Troubleshooting

### Issue: "Dataset not found" error
**Solution**: Verify the dataset_id is correct and belongs to the current user

### Issue: Supabase upload fails
**Solution**: 
1. Check environment variables are set correctly
2. Verify storage bucket exists and is named "datasets"
3. Check RLS policies are configured
4. Ensure service role key has storage permissions

### Issue: Local storage permission denied
**Solution**: 
```bash
chmod 755 ./uploads/datasets
```

### Issue: CSV parsing error
**Solution**: Ensure CSV file:
- Has a header row
- Uses comma as delimiter
- Is UTF-8 encoded
- Has no malformed rows

## Future Enhancements

- [ ] Support for Parquet/Arrow formats
- [ ] Automatic data profiling and quality checks
- [ ] Dataset versioning and history
- [ ] Collaborative dataset sharing
- [ ] Automatic schema validation
- [ ] Data sampling for large datasets
- [ ] Compression for storage optimization
- [ ] Async processing for large files

## Related Documentation

- [Bias Detection API](../docs/API_ENDPOINTS.md)
- [Supabase Storage Guide](https://supabase.com/docs/guides/storage)
- [Authentication Setup](../config/auth.py)
