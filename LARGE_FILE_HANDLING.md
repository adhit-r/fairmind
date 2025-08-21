# Large File Handling Guide for FairMind

This guide explains how FairMind handles AI model files of different sizes and provides solutions for files larger than the default limits.

## Current File Size Limits

| Component | Limit | Description |
|-----------|-------|-------------|
| **Backend Validation** | 100MB | Maximum file size allowed by the backend |
| **Supabase Storage** | 50MB | Current bucket file size limit |
| **Local Storage** | Unlimited | No size limit for local storage |

## File Size Categories

### Small Files (≤ 50MB)
- ✅ **Supabase Storage**: Fully supported
- ✅ **Local Storage**: Fully supported
- ✅ **Upload Method**: Direct upload
- ✅ **Performance**: Fast upload/download

### Medium Files (50MB - 100MB)
- ⚠️ **Supabase Storage**: Requires bucket limit update
- ✅ **Local Storage**: Fully supported
- ⚠️ **Upload Method**: May fail until bucket is updated
- ⚠️ **Performance**: Slower but manageable

### Large Files (> 100MB)
- ❌ **Supabase Storage**: Not supported (backend validation)
- ✅ **Local Storage**: Fully supported
- ❌ **Upload Method**: Rejected by backend
- ⚠️ **Performance**: May be slow

## Solutions for Large Files

### Option 1: Update Supabase Bucket Limits (Recommended)

**For files up to 100MB:**

1. **Via Supabase Dashboard:**
   ```
   1. Go to your Supabase dashboard
   2. Navigate to Storage > Buckets
   3. Click on the ai-models bucket
   4. Update the file size limit to 100MB or higher
   5. Save the changes
   ```

2. **Via Supabase CLI:**
   ```bash
   supabase storage update-bucket ai-models --file-size-limit 104857600
   ```

3. **Test the update:**
   ```bash
   cd tools/scripts
   node update-bucket-limits.js
   ```

### Option 2: Implement Chunked Uploads

**For files > 100MB:**

The system automatically handles chunked uploads for files between 50MB and 100MB when Supabase is available. For larger files, you can implement true chunked uploads:

```python
# Example chunked upload implementation
async def upload_large_model_in_chunks(self, file_path: str, chunk_size: int = 10 * 1024 * 1024):
    """Upload large model file in chunks"""
    file_size = os.path.getsize(file_path)
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    
    with open(file_path, 'rb') as f:
        for chunk_num in range(total_chunks):
            chunk_data = f.read(chunk_size)
            chunk_filename = f"{file_path}.part{chunk_num:03d}"
            
            # Upload chunk
            await self._upload_chunk(chunk_data, chunk_filename)
            
            # Update progress
            progress = (chunk_num + 1) / total_chunks * 100
            logger.info(f"Upload progress: {progress:.1f}%")
```

### Option 3: Use Local Storage for Large Files

**For files > 100MB:**

The system automatically falls back to local storage when:
- Supabase is not available
- File size exceeds Supabase limits
- Upload to Supabase fails

```python
# The ModelStorageService automatically handles this:
storage_info = await model_storage_service.upload_model(
    model_file, 
    model_metadata, 
    organization_id
)

# Check storage type
if storage_info['storage_type'] == 'local':
    print("File stored locally due to size or availability")
elif storage_info['storage_type'] == 'supabase_chunked':
    print("File stored in Supabase using chunked upload")
else:
    print("File stored in Supabase using direct upload")
```

### Option 4: Model Compression

**Reduce file size before upload:**

```python
import gzip
import pickle

def compress_model(model, file_path: str):
    """Compress model before storage"""
    with gzip.open(file_path + '.gz', 'wb') as f:
        pickle.dump(model, f)
    
    # Check compressed size
    compressed_size = os.path.getsize(file_path + '.gz')
    original_size = os.path.getsize(file_path)
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"Compression ratio: {compression_ratio:.1f}%")
    return file_path + '.gz'

def decompress_model(file_path: str):
    """Decompress model after download"""
    with gzip.open(file_path, 'rb') as f:
        return pickle.load(f)
```

## Configuration Options

### Update Backend Limits

To change the backend file size limit, modify `backend/config/settings.py`:

```python
# File Upload Settings
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB (increase as needed)
```

### Update Storage Service Limits

To change storage service limits, modify `backend/services/model_storage_service.py`:

```python
class ModelStorageService:
    def __init__(self):
        # File size limits
        self.max_file_size = 200 * 1024 * 1024  # 200MB (backend limit)
        self.supabase_file_size_limit = 100 * 1024 * 1024  # 100MB (Supabase limit)
        self.chunk_size = 10 * 1024 * 1024  # 10MB chunks for large files
```

## Best Practices

### 1. File Size Optimization

- **Use model compression** (gzip, pickle compression)
- **Consider model quantization** (reduce precision)
- **Remove unnecessary metadata** from model files
- **Use efficient serialization formats** (ONNX, TensorFlow SavedModel)

### 2. Upload Strategy

```python
# Recommended upload flow
async def upload_model_with_fallback(self, model_file, metadata, org_id):
    try:
        # Try Supabase first
        result = await self.upload_model(model_file, metadata, org_id)
        return result
    except ValueError as e:
        if "exceeds maximum allowed size" in str(e):
            # File too large, use local storage
            logger.warning(f"File too large for Supabase, using local storage: {e}")
            return await self._upload_to_local_only(model_file, metadata, org_id)
        else:
            raise
```

### 3. Monitoring and Alerts

```python
# Add monitoring for large file uploads
async def upload_model_with_monitoring(self, model_file, metadata, org_id):
    file_size = len(model_file.read())
    model_file.seek(0)  # Reset file pointer
    
    # Log file size for monitoring
    logger.info(f"Uploading model: {metadata.get('name')} ({file_size} bytes)")
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        logger.warning(f"Large model detected: {file_size} bytes")
        # Send alert to admin
        await self._send_large_file_alert(metadata, file_size, org_id)
    
    return await self.upload_model(model_file, metadata, org_id)
```

## Troubleshooting

### Common Issues

1. **"File size exceeds maximum allowed size"**
   - **Solution**: Update backend `MAX_FILE_SIZE` or compress the file

2. **"The object exceeded the maximum allowed size"**
   - **Solution**: Update Supabase bucket file size limit

3. **"Upload timeout"**
   - **Solution**: Implement chunked uploads or use local storage

4. **"Memory error during upload"**
   - **Solution**: Use streaming uploads instead of loading entire file into memory

### Performance Optimization

```python
# Use streaming for large files
async def upload_large_file_streaming(self, file_path: str, metadata: dict):
    """Upload large file using streaming to avoid memory issues"""
    file_size = os.path.getsize(file_path)
    
    with open(file_path, 'rb') as f:
        # Upload in chunks without loading entire file
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        uploaded_bytes = 0
        
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
                
            # Upload chunk
            await self._upload_chunk(chunk, f"chunk_{uploaded_bytes}")
            uploaded_bytes += len(chunk)
            
            # Update progress
            progress = (uploaded_bytes / file_size) * 100
            logger.info(f"Upload progress: {progress:.1f}%")
```

## Cost Considerations

### Supabase Storage Costs
- **Storage**: ~$0.021/GB/month
- **Bandwidth**: ~$0.09/GB
- **Large files**: Higher bandwidth costs

### Local Storage Costs
- **Storage**: Free (uses server disk space)
- **Bandwidth**: Lower (no external transfer)
- **Backup**: Consider backup strategy

## Recommendations

1. **For files ≤ 50MB**: Use Supabase storage (fast, reliable)
2. **For files 50MB-100MB**: Update bucket limits and use Supabase
3. **For files > 100MB**: Use local storage or implement chunked uploads
4. **For production**: Implement hybrid storage strategy
5. **For cost optimization**: Compress models before upload

## Testing Large File Uploads

```bash
# Test different file sizes
cd tools/scripts
node update-bucket-limits.js

# Test backend upload
cd ../../backend
python -c "
from services.model_storage_service import model_storage_service
import io

# Test 1MB file
test_data = b'x' * (1 * 1024 * 1024)
test_file = io.BytesIO(test_data)
result = await model_storage_service.upload_model(
    test_file, 
    {'name': 'test_model', 'version': '1.0.0'}, 
    'test_org'
)
print(f'Upload result: {result}')
"
```
