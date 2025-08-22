# 🚀 FairMind Supabase Storage Setup Guide

This guide will walk you through setting up Supabase storage for FairMind AI model storage.

## 📋 Prerequisites

1. **Supabase Account**: Create a free account at [supabase.com](https://supabase.com)
2. **Supabase Project**: Create a new project in your Supabase dashboard
3. **Python Environment**: Ensure you have Python 3.8+ with required packages

## 🔧 Step 1: Get Supabase Credentials

### 1.1 Get Project URL and Keys

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy the following values:
   - **Project URL** (e.g., `https://your-project.supabase.co`)
   - **Service Role Key** (starts with `eyJ...`)
   - **Anon Key** (starts with `eyJ...`)

### 1.2 Set Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_ANON_KEY=your_anon_key_here

# Storage Configuration
STORAGE_BUCKET=ai-models
STORAGE_REGION=us-east-1

# Backend Configuration
BACKEND_URL=http://localhost:8000
UPLOAD_DIR=uploads
DATASET_DIR=datasets
MODEL_REGISTRY=models_registry.json
SIM_RESULTS=simulation_results.json

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

## 🗄️ Step 2: Set Up Supabase Storage

### 2.1 Option A: Automated Setup (Recommended)

Run the automated setup script:

```bash
cd backend
python scripts/setup_supabase_storage.py
```

This script will:
- ✅ Create the `ai-models` storage bucket
- ✅ Set up Row Level Security (RLS) policies
- ✅ Create organization folder structure
- ✅ Test storage access
- ✅ Migrate existing models

### 2.2 Option B: Manual SQL Setup

If the automated script doesn't work, run the SQL script manually:

1. Go to your Supabase dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `backend/scripts/supabase_storage_setup.sql`
4. Click **Run** to execute the script

## 🔄 Step 3: Migrate Existing Models

If you have existing models in local storage, migrate them to Supabase:

```bash
cd backend
python scripts/migrate_to_supabase.py
```

This script will:
- ✅ Upload all local models to Supabase
- ✅ Update the model registry with Supabase paths
- ✅ Verify migration success
- ✅ Create a backup of the original registry

## 🧪 Step 4: Test Storage Functionality

Run the comprehensive test suite:

```bash
cd backend
python scripts/test_supabase_storage.py
```

This will test:
- ✅ Supabase connection
- ✅ Storage service availability
- ✅ Bucket access
- ✅ Upload/download functionality
- ✅ Model storage service
- ✅ Organization isolation
- ✅ Different file types

## 🔍 Step 5: Verify Setup

### 5.1 Check Storage Status

```bash
cd backend
python -c "from services.model_storage_service import model_storage_service; print('Supabase available:', model_storage_service.is_supabase_available()); print('Storage info:', model_storage_service.get_storage_info())"
```

Expected output:
```
Supabase available: True
Storage info: {'storage_type': 'supabase', 'bucket_name': 'ai-models', 'local_path': 'storage/models', 'available': True}
```

### 5.2 Check Dashboard

1. Start your backend server: `python main.py`
2. Start your frontend: `cd frontend && bun dev`
3. Visit `http://localhost:3000`
4. Verify that dashboard shows real data from Supabase

## 📊 Step 6: Monitor Storage Usage

### 6.1 Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **Storage** → **Buckets**
3. Click on the `ai-models` bucket
4. Monitor:
   - File count
   - Storage usage
   - Access patterns

### 6.2 Storage Analytics

Run this SQL query in Supabase SQL Editor to get storage statistics:

```sql
SELECT 
    (storage.foldername(name))[1] as organization_id,
    COUNT(*) as total_models,
    COALESCE(SUM((metadata->>'size')::bigint), 0) as total_size_bytes,
    COUNT(DISTINCT metadata->>'mimetype') as unique_file_types,
    MIN(created_at) as first_model_upload,
    MAX(created_at) as last_model_upload
FROM storage.objects
WHERE bucket_id = 'ai-models'
GROUP BY (storage.foldername(name))[1];
```

## 🔐 Step 7: Security Configuration

### 7.1 Row Level Security (RLS)

The setup script automatically configures RLS policies that:
- ✅ Isolate models by organization
- ✅ Allow service role access for backend operations
- ✅ Restrict user access to their organization's models
- ✅ Enable audit logging

### 7.2 Access Control

Users can only:
- 📁 **View** models in their organization
- 📤 **Upload** models to their organization
- 📝 **Update** models in their organization
- 🗑️ **Delete** models in their organization

### 7.3 Audit Logging

All model operations are logged in the `model_audit_logs` table:
- Upload operations
- Download operations
- Delete operations
- Update operations

## 🚨 Troubleshooting

### Common Issues

#### 1. "Supabase not connected" Error

**Solution**: Check your environment variables
```bash
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY
```

#### 2. "Bucket not found" Error

**Solution**: Run the setup script again
```bash
python scripts/setup_supabase_storage.py
```

#### 3. "Permission denied" Error

**Solution**: Check RLS policies in Supabase dashboard
- Go to **Storage** → **Policies**
- Ensure policies are enabled for the `ai-models` bucket

#### 4. "File upload failed" Error

**Solution**: Check file size limits
- Default limit: 50MB per file
- Increase in Supabase dashboard if needed

### Debug Commands

```bash
# Test Supabase connection
python -c "from supabase_client import SupabaseService; s = SupabaseService(); print('Connected:', s.is_connected())"

# Test storage service
python -c "from services.model_storage_service import model_storage_service; print('Available:', model_storage_service.is_supabase_available())"

# List storage buckets
python -c "from supabase_client import SupabaseService; s = SupabaseService(); print(s.client.storage.list_buckets())"
```

## 📈 Performance Optimization

### 1. CDN Configuration

Supabase automatically provides CDN for faster file access:
- Global edge locations
- Automatic caching
- Optimized delivery

### 2. File Compression

For large models, consider compression:
```python
import gzip

# Compress before upload
with gzip.open('model.pkl.gz', 'wb') as f:
    f.write(model_content)

# Decompress after download
with gzip.open('model.pkl.gz', 'rb') as f:
    model_content = f.read()
```

### 3. Batch Operations

For multiple files, use batch operations:
```python
# Batch upload
files = [('file1.pkl', content1), ('file2.pkl', content2)]
for filename, content in files:
    await model_storage_service.upload_model(...)
```

## 💰 Cost Optimization

### 1. Storage Costs

- **Supabase Storage**: ~$0.021/GB/month
- **Bandwidth**: ~$0.09/GB
- **Typical AI Model**: 50MB-500MB

### 2. Cost Estimation

```
100 models × 100MB average = 10GB
Monthly cost: ~$0.21 + bandwidth
```

### 3. Cost Monitoring

Monitor costs in Supabase dashboard:
- **Billing** → **Usage**
- Set up alerts for high usage
- Use storage analytics to optimize

## 🔄 Migration from Local to Cloud

### Before Migration

1. **Backup local models**:
```bash
cp -r storage/models storage/models_backup
cp models_registry.json models_registry.json.backup
```

2. **Test migration**:
```bash
python scripts/migrate_to_supabase.py
```

3. **Verify migration**:
```bash
python scripts/test_supabase_storage.py
```

### After Migration

1. **Update configuration**:
```python
# Models now use Supabase paths
# From: "storage/models/demo_org/model.pkl"
# To: "ai-models/demo_org/model.pkl"
```

2. **Test functionality**:
- Upload new models
- Download existing models
- List models by organization

3. **Monitor performance**:
- Check upload/download speeds
- Monitor storage usage
- Verify organization isolation

## 🎯 Next Steps

1. **Production Deployment**:
   - Set up production environment variables
   - Configure monitoring and alerts
   - Set up backup strategies

2. **Advanced Features**:
   - Implement model versioning
   - Add model metadata search
   - Set up automated backups

3. **Integration**:
   - Connect with CI/CD pipelines
   - Integrate with monitoring tools
   - Set up automated testing

## 📞 Support

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Review Supabase documentation**: [supabase.com/docs](https://supabase.com/docs)
3. **Check FairMind logs**: `backend/logs/`
4. **Run diagnostic scripts**: `python scripts/test_supabase_storage.py`

## ✅ Success Checklist

- [ ] Supabase project created
- [ ] Environment variables configured
- [ ] Storage bucket created (`ai-models`)
- [ ] RLS policies configured
- [ ] Organization folders created
- [ ] Existing models migrated
- [ ] Storage tests passed
- [ ] Dashboard shows real data
- [ ] Organization isolation working
- [ ] Audit logging enabled

🎉 **Congratulations! Your FairMind Supabase storage is now fully configured and ready for production use.**
