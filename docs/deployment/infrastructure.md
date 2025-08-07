# Deployment Guide & Infrastructure

## 🚀 Deployment Overview

Fairmind v2 is designed for flexible deployment across multiple environments, from local development to enterprise-scale production. Our deployment strategy emphasizes:

- **Containerization**: Docker-based deployment for consistency
- **Scalability**: Kubernetes orchestration for production
- **Security**: End-to-end encryption and secure defaults
- **Monitoring**: Comprehensive observability stack
- **CI/CD**: Automated testing and deployment pipelines

## 🏗️ Infrastructure Architecture

### Production Architecture

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[Load Balancer<br/>AWS ALB / CloudFlare]
        CDN[CDN<br/>Static Assets]
    end
    
    subgraph "Application Layer"
        WEB1[Web App 1<br/>Next.js]
        WEB2[Web App 2<br/>Next.js]
        WEB3[Web App N<br/>Next.js]
        
        ML1[ML Service 1<br/>FastAPI]
        ML2[ML Service 2<br/>FastAPI]
        MLN[ML Service N<br/>FastAPI]
    end
    
    subgraph "Data Layer"
        DB[(Supabase<br/>PostgreSQL)]
        REDIS[(Redis<br/>Cache)]
        STORAGE[File Storage<br/>Supabase Storage]
    end
    
    subgraph "Monitoring"
        METRICS[Metrics<br/>Prometheus]
        LOGS[Logs<br/>ELK Stack]
        ALERTS[Alerts<br/>PagerDuty]
    end
    
    LB --> WEB1
    LB --> WEB2  
    LB --> WEB3
    
    WEB1 --> ML1
    WEB2 --> ML2
    WEB3 --> MLN
    
    ML1 --> DB
    ML2 --> DB
    MLN --> DB
    
    ML1 --> REDIS
    ML2 --> REDIS
    MLN --> REDIS
    
    WEB1 --> STORAGE
    ML1 --> STORAGE
    
    WEB1 --> METRICS
    ML1 --> METRICS
    METRICS --> ALERTS
```

## 🐳 Docker Configuration

### Web Application Dockerfile

```dockerfile
# apps/web/Dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json bun.lockb ./
RUN \
  if [ -f bun.lockb ]; then \
    corepack enable bun && bun install --frozen-lockfile; \
  else \
    echo "Lockfile not found." && exit 1; \
  fi

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Environment variables for build
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build application
RUN \
  if [ -f bun.lockb ]; then \
    corepack enable bun && bun run build; \
  else \
    npm run build; \
  fi

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### ML Service Dockerfile

```dockerfile
# apps/ml-service/Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create directories for models and data
RUN mkdir -p /app/models /app/datasets /app/logs \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - ML_SERVICE_URL=http://ml-service:8000
    depends_on:
      - ml-service
      - redis
    networks:
      - fairmind-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`app.fairmind.local`)"
      - "traefik.http.services.web.loadbalancer.server.port=3000"

  ml-service:
    build:
      context: ./apps/ml-service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ml-models:/app/models
      - ml-datasets:/app/datasets
      - ml-logs:/app/logs
    depends_on:
      - redis
    networks:
      - fairmind-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ml-service.rule=Host(`api.fairmind.local`) && PathPrefix(`/api/v1`)"
      - "traefik.http.services.ml-service.loadbalancer.server.port=8000"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - fairmind-network
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

  # Reverse proxy
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web-secure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-acme:/acme.json
    networks:
      - fairmind-network
    restart: unless-stopped

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - fairmind-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - fairmind-network
    restart: unless-stopped

volumes:
  ml-models:
  ml-datasets:
  ml-logs:
  redis-data:
  traefik-acme:
  prometheus-data:
  grafana-data:

networks:
  fairmind-network:
    driver: bridge
```

## ☸️ Kubernetes Deployment

### Namespace Configuration

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fairmind
  labels:
    name: fairmind
    environment: production
```

### Web Application Deployment

```yaml
# k8s/web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fairmind-web
  namespace: fairmind
  labels:
    app: fairmind-web
    version: v2.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fairmind-web
  template:
    metadata:
      labels:
        app: fairmind-web
        version: v2.0.0
    spec:
      containers:
      - name: web
        image: fairmind/web:v2.0.0
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: NEXT_PUBLIC_SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: fairmind-secrets
              key: supabase-url
        - name: NEXT_PUBLIC_SUPABASE_ANON_KEY
          valueFrom:
            secretKeyRef:
              name: fairmind-secrets
              key: supabase-anon-key
        - name: ML_SERVICE_URL
          value: "http://fairmind-ml-service:8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
      imagePullSecrets:
      - name: docker-registry-secret
---
apiVersion: v1
kind: Service
metadata:
  name: fairmind-web-service
  namespace: fairmind
spec:
  selector:
    app: fairmind-web
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP
```

### ML Service Deployment

```yaml
# k8s/ml-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fairmind-ml
  namespace: fairmind
  labels:
    app: fairmind-ml
    version: v2.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fairmind-ml
  template:
    metadata:
      labels:
        app: fairmind-ml
        version: v2.0.0
    spec:
      containers:
      - name: ml-service
        image: fairmind/ml-service:v2.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fairmind-secrets
              key: database-url
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: fairmind-secrets
              key: supabase-url
        - name: SUPABASE_SERVICE_KEY
          valueFrom:
            secretKeyRef:
              name: fairmind-secrets
              key: supabase-service-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: fairmind-secrets
              key: jwt-secret
        - name: REDIS_URL
          value: "redis://fairmind-redis:6379/0"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: ml-models
          mountPath: /app/models
        - name: ml-datasets
          mountPath: /app/datasets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: ml-models
        persistentVolumeClaim:
          claimName: ml-models-pvc
      - name: ml-datasets
        persistentVolumeClaim:
          claimName: ml-datasets-pvc
      imagePullSecrets:
      - name: docker-registry-secret
---
apiVersion: v1
kind: Service
metadata:
  name: fairmind-ml-service
  namespace: fairmind
spec:
  selector:
    app: fairmind-ml
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fairmind-ingress
  namespace: fairmind
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - app.fairmind.ai
    - api.fairmind.ai
    secretName: fairmind-tls
  rules:
  - host: app.fairmind.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fairmind-web-service
            port:
              number: 80
  - host: api.fairmind.ai
    http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: fairmind-ml-service
            port:
              number: 8000
```

### Persistent Volume Claims

```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ml-models-pvc
  namespace: fairmind
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 50Gi
  storageClassName: efs-sc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ml-datasets-pvc
  namespace: fairmind
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: efs-sc
```

## 🔐 Secrets Management

### Kubernetes Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: fairmind-secrets
  namespace: fairmind
type: Opaque
data:
  # Base64 encoded values
  database-url: <base64-encoded-database-url>
  supabase-url: <base64-encoded-supabase-url>
  supabase-anon-key: <base64-encoded-supabase-anon-key>
  supabase-service-key: <base64-encoded-supabase-service-key>
  jwt-secret: <base64-encoded-jwt-secret>
  grafana-password: <base64-encoded-grafana-password>
```

### Environment Configuration

```bash
# .env.production
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# ML Service Configuration
ML_SERVICE_URL=https://api.fairmind.ai
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET_KEY=your-jwt-secret-key

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Monitoring Configuration
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
GRAFANA_PASSWORD=secure-password

# Security Configuration
ALLOWED_ORIGINS=https://app.fairmind.ai,https://fairmind.ai
CORS_CREDENTIALS=true

# Performance Configuration
MAX_CONCURRENT_ANALYSES=10
CACHE_TTL_SECONDS=3600
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy Fairmind v2

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: fairmind

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20]
        python-version: [3.11]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        npm ci
        pip install -r apps/ml-service/requirements.txt
    
    - name: Run linting
      run: |
        npm run lint
        flake8 apps/ml-service/
    
    - name: Run type checking
      run: |
        npm run type-check
        mypy apps/ml-service/
    
    - name: Run tests
      run: |
        npm run test
        pytest apps/ml-service/tests/
    
    - name: Run security scan
      run: |
        npm audit --audit-level moderate
        safety check -r apps/ml-service/requirements.txt

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    permissions:
      contents: read
      packages: write
    
    strategy:
      matrix:
        component: [web, ml-service]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.component }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./apps/${{ matrix.component }}
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.28.0'
    
    - name: Setup Helm
      uses: azure/setup-helm@v3
      with:
        version: 'v3.12.0'
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --region us-west-2 --name fairmind-cluster
    
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
        kubectl rollout status deployment/fairmind-web -n fairmind
        kubectl rollout status deployment/fairmind-ml -n fairmind
    
    - name: Verify deployment
      run: |
        kubectl get pods -n fairmind
        kubectl get services -n fairmind
        kubectl get ingress -n fairmind
    
    - name: Run smoke tests
      run: |
        chmod +x scripts/smoke-test.sh
        ./scripts/smoke-test.sh https://app.fairmind.ai
```

## 📊 Monitoring & Observability

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'fairmind-web'
    static_configs:
      - targets: ['fairmind-web-service:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 30s

  - job_name: 'fairmind-ml'
    static_configs:
      - targets: ['fairmind-ml-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['fairmind-redis:6379']

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Fairmind v2 - Application Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}} - {{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "ML Analysis Queue",
        "type": "stat",
        "targets": [
          {
            "expr": "ml_analysis_queue_size",
            "legendFormat": "Queued Analyses"
          }
        ]
      },
      {
        "title": "Bias Detection Accuracy",
        "type": "gauge",
        "targets": [
          {
            "expr": "avg(bias_detection_accuracy)",
            "legendFormat": "Average Accuracy"
          }
        ]
      }
    ]
  }
}
```

This comprehensive deployment documentation provides everything needed to deploy and manage Fairmind v2 in production environments with proper security, monitoring, and scalability considerations.
