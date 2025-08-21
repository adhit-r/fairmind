# Fairmind Backend API Deployment Guide

## 🚀 **Production Deployment to https://api.fairmind.xyz**

### **Overview**
This guide covers deploying the Fairmind AI Governance Platform backend API to production with proper configuration for the frontend at `https://app-demo.fairmind.xyz`.

### **✅ Pre-Deployment Checklist**
- [x] FastAPI application ready
- [x] All dependencies listed in requirements.txt
- [x] Health check endpoint implemented
- [x] CORS configured for frontend domain
- [x] Environment variables documented
- [x] Docker configuration ready

### **🌐 Recommended Deployment Platforms**

#### **1. Railway (Recommended)**
**Best for**: Python APIs, easy deployment, good free tier

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up

# Set custom domain
railway domain
```

**Advantages:**
- ✅ Native Python support
- ✅ Automatic HTTPS
- ✅ Easy environment variable management
- ✅ Good free tier
- ✅ Built-in monitoring

#### **2. Heroku**
**Best for**: Traditional deployment, good documentation

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create fairmind-api

# Deploy
git push heroku main

# Set custom domain
heroku domains:add api.fairmind.xyz
```

#### **3. DigitalOcean App Platform**
**Best for**: Scalability, good pricing

```bash
# Use DigitalOcean CLI or web interface
# Upload code and configure environment
```

#### **4. Google Cloud Run**
**Best for**: Serverless, pay-per-use

```bash
# Build and push Docker image
docker build -t gcr.io/PROJECT_ID/fairmind-api .
docker push gcr.io/PROJECT_ID/fairmind-api

# Deploy to Cloud Run
gcloud run deploy fairmind-api \
  --image gcr.io/PROJECT_ID/fairmind-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### **🔧 Environment Variables**

#### **Required Environment Variables**
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

# Security
JWT_SECRET=your-jwt-secret-key
ENVIRONMENT=production

# CORS Configuration
ALLOWED_ORIGINS=https://app-demo.fairmind.xyz,http://localhost:3000

# Optional: Email Service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### **Setting Environment Variables**

**Railway:**
```bash
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_KEY=your-service-role-key
```

**Heroku:**
```bash
heroku config:set SUPABASE_URL=https://your-project.supabase.co
heroku config:set SUPABASE_KEY=your-service-role-key
```

### **🐳 Docker Deployment**

#### **Local Docker Build**
```bash
# Build image
docker build -t fairmind-api .

# Run container
docker run -p 8000:8000 \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_KEY=your-service-role-key \
  fairmind-api
```

#### **Docker Compose**
```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f api
```

### **🔒 Security Configuration**

#### **CORS Settings**
The API is configured to allow requests from:
- `https://app-demo.fairmind.xyz` (Production frontend)
- `http://localhost:3000` (Development frontend)

#### **Health Check Endpoint**
- **URL**: `/health`
- **Method**: GET
- **Response**: `{"status": "healthy"}`

#### **API Documentation**
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

### **📊 API Endpoints**

#### **Core Endpoints**
```
GET  /health                    - Health check
GET  /models                    - List AI models
POST /models/upload             - Upload model
GET  /datasets                  - List datasets
POST /datasets/upload           - Upload dataset
POST /bias/analyze              - Bias analysis
POST /simulation/run            - Run simulation
```

#### **AI Governance Endpoints**
```
GET  /bom/scan                  - Scan project BOM
GET  /bom/list                  - List BOM documents
POST /owasp/analyze             - OWASP security analysis
GET  /owasp/tests               - List OWASP tests
POST /geographic-bias/analyze   - Geographic bias analysis
```

#### **Monitoring Endpoints**
```
GET  /metrics                   - Application metrics
GET  /logs                      - Application logs
GET  /status                    - System status
```

### **🚨 Troubleshooting**

#### **Common Issues**

1. **CORS Errors**
   ```bash
   # Check CORS configuration in main.py
   # Ensure frontend domain is in allowed origins
   ```

2. **Database Connection Issues**
   ```bash
   # Verify DATABASE_URL format
   # Check database accessibility
   # Test connection locally
   ```

3. **Supabase Connection Issues**
   ```bash
   # Verify SUPABASE_URL and SUPABASE_KEY
   # Check Supabase project status
   # Test connection with Supabase CLI
   ```

4. **Port Issues**
   ```bash
   # Ensure PORT environment variable is set
   # Check if port is available
   # Use $PORT for cloud platforms
   ```

#### **Debug Commands**
```bash
# Test API locally
curl http://localhost:8000/health

# Check environment variables
echo $SUPABASE_URL
echo $DATABASE_URL

# View application logs
docker logs <container-id>
```

### **📈 Monitoring & Analytics**

#### **Health Monitoring**
- **Endpoint**: `/health`
- **Frequency**: Every 30 seconds
- **Expected Response**: `{"status": "healthy"}`

#### **Performance Monitoring**
- **Response Time**: Monitor API response times
- **Error Rate**: Track 4xx and 5xx errors
- **Throughput**: Monitor requests per second

#### **Logging**
- **Application Logs**: Structured JSON logging
- **Error Tracking**: Automatic error capture
- **Request Logging**: HTTP request/response logging

### **🔄 Continuous Deployment**

#### **GitHub Actions Workflow**
```yaml
name: Deploy API
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        uses: railway/deploy@v1
        with:
          service: api
```

#### **Automatic Deployments**
- **Railway**: Automatic deployment on git push
- **Heroku**: Automatic deployment on git push to heroku remote
- **Cloud Run**: Automatic deployment on image push

### **🔗 Frontend Integration**

#### **API Base URL**
```javascript
// Frontend configuration
const API_BASE_URL = 'https://api.fairmind.xyz'
```

#### **CORS Configuration**
```python
# Backend CORS settings
origins = [
    "https://app-demo.fairmind.xyz",
    "http://localhost:3000"
]
```

### **📞 Support**

#### **Deployment Issues**
- Check platform-specific documentation
- Verify environment variables
- Test API endpoints locally
- Review application logs

#### **API Issues**
- Check health endpoint: `https://api.fairmind.xyz/health`
- Review API documentation: `https://api.fairmind.xyz/docs`
- Monitor error logs

---

## 🎯 **Next Steps**

1. **Choose Deployment Platform**: Select Railway, Heroku, or other platform
2. **Set Environment Variables**: Configure all required environment variables
3. **Deploy Application**: Follow platform-specific deployment instructions
4. **Configure Custom Domain**: Set up `api.fairmind.xyz`
5. **Test Integration**: Verify frontend can connect to API
6. **Monitor Performance**: Set up monitoring and alerting

**Your Fairmind Backend API is ready for production deployment!** 🚀

The API will be accessible at `https://api.fairmind.xyz` once deployment is complete.
