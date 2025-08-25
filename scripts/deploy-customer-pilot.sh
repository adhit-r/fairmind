#!/bin/bash

# FairMind Customer Pilot Deployment Script
# This script automates the deployment of FairMind for customer pilots

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CUSTOMER_NAME=""
ENVIRONMENT="development"
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true
DEPLOY_WEBSITE=true
USE_DOCKER=false
USE_KUBERNETES=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if required tools are installed
    command -v python3 >/dev/null 2>&1 || { print_error "Python 3 is required but not installed."; exit 1; }
    command -v bun >/dev/null 2>&1 || { print_error "Bun is required but not installed."; exit 1; }
    command -v git >/dev/null 2>&1 || { print_error "Git is required but not installed."; exit 1; }
    
    if [ "$USE_DOCKER" = true ]; then
        command -v docker >/dev/null 2>&1 || { print_error "Docker is required but not installed."; exit 1; }
    fi
    
    if [ "$USE_KUBERNETES" = true ]; then
        command -v kubectl >/dev/null 2>&1 || { print_error "kubectl is required but not installed."; exit 1; }
    fi
    
    print_success "Prerequisites check passed"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment for customer: $CUSTOMER_NAME"
    
    # Create customer-specific directories
    mkdir -p config/customers/$CUSTOMER_NAME
    mkdir -p logs/$CUSTOMER_NAME
    mkdir -p data/$CUSTOMER_NAME
    
    # Copy environment templates
    if [ ! -f config/customers/$CUSTOMER_NAME/.env ]; then
        cp apps/backend/config/env.example config/customers/$CUSTOMER_NAME/.env
        print_warning "Please configure environment variables in config/customers/$CUSTOMER_NAME/.env"
    fi
    
    if [ ! -f apps/frontend/.env.local ]; then
        cp apps/frontend/.env.example apps/frontend/.env.local
        print_warning "Please configure frontend environment variables in apps/frontend/.env.local"
    fi
    
    print_success "Environment setup completed"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    cd apps/backend
    
    # Check if database connection is working
    if python scripts/check_database.py; then
        print_success "Database connection verified"
    else
        print_error "Database connection failed. Please check your configuration."
        exit 1
    fi
    
    # Run database migrations
    print_status "Running database migrations..."
    python scripts/init_database.py
    
    # Seed initial data
    print_status "Seeding initial data..."
    python scripts/create_sample_models.py
    python scripts/create_sample_datasets.py
    
    cd ../..
    print_success "Database setup completed"
}

# Function to deploy backend
deploy_backend() {
    print_status "Deploying backend..."
    
    cd apps/backend
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Run tests
    print_status "Running backend tests..."
    python -m pytest tests/ -v --tb=short
    
    # Start backend server
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Starting production backend server..."
        gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --daemon
    else
        print_status "Starting development backend server..."
        uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --daemon
    fi
    
    cd ../..
    
    # Wait for backend to start
    sleep 5
    
    # Check if backend is running
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend deployed successfully"
    else
        print_error "Backend deployment failed"
        exit 1
    fi
}

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying frontend..."
    
    cd apps/frontend
    
    # Install dependencies
    print_status "Installing frontend dependencies..."
    bun install
    
    # Build frontend
    print_status "Building frontend..."
    bun run build
    
    # Start frontend server
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Starting production frontend server..."
        bun run start --daemon
    else
        print_status "Starting development frontend server..."
        bun run dev --daemon
    fi
    
    cd ../..
    
    # Wait for frontend to start
    sleep 10
    
    # Check if frontend is running
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend deployed successfully"
    else
        print_error "Frontend deployment failed"
        exit 1
    fi
}

# Function to deploy website
deploy_website() {
    print_status "Deploying website..."
    
    cd apps/website
    
    # Install dependencies
    print_status "Installing website dependencies..."
    bun install
    
    # Build website
    print_status "Building website..."
    bun run build
    
    # Start website server
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Starting production website server..."
        bun run preview --daemon
    else
        print_status "Starting development website server..."
        bun run dev --daemon
    fi
    
    cd ../..
    
    # Wait for website to start
    sleep 5
    
    # Check if website is running
    if curl -f http://localhost:4321 >/dev/null 2>&1; then
        print_success "Website deployed successfully"
    else
        print_error "Website deployment failed"
        exit 1
    fi
}

# Function to deploy with Docker
deploy_docker() {
    print_status "Deploying with Docker..."
    
    # Build Docker images
    print_status "Building Docker images..."
    docker build -t fairmind-backend:$CUSTOMER_NAME apps/backend/
    docker build -t fairmind-frontend:$CUSTOMER_NAME apps/frontend/
    docker build -t fairmind-website:$CUSTOMER_NAME apps/website/
    
    # Stop existing containers
    docker stop fairmind-backend-$CUSTOMER_NAME fairmind-frontend-$CUSTOMER_NAME fairmind-website-$CUSTOMER_NAME 2>/dev/null || true
    docker rm fairmind-backend-$CUSTOMER_NAME fairmind-frontend-$CUSTOMER_NAME fairmind-website-$CUSTOMER_NAME 2>/dev/null || true
    
    # Run containers
    print_status "Starting Docker containers..."
    docker run -d --name fairmind-backend-$CUSTOMER_NAME -p 8000:8000 --env-file config/customers/$CUSTOMER_NAME/.env fairmind-backend:$CUSTOMER_NAME
    docker run -d --name fairmind-frontend-$CUSTOMER_NAME -p 3000:3000 --env-file apps/frontend/.env.local fairmind-frontend:$CUSTOMER_NAME
    docker run -d --name fairmind-website-$CUSTOMER_NAME -p 4321:4321 fairmind-website:$CUSTOMER_NAME
    
    print_success "Docker deployment completed"
}

# Function to deploy with Kubernetes
deploy_kubernetes() {
    print_status "Deploying with Kubernetes..."
    
    # Create namespace
    kubectl create namespace fairmind-$CUSTOMER_NAME --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    kubectl apply -f infrastructure/kubernetes/ -n fairmind-$CUSTOMER_NAME
    
    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/fairmind-backend -n fairmind-$CUSTOMER_NAME
    kubectl wait --for=condition=available --timeout=300s deployment/fairmind-frontend -n fairmind-$CUSTOMER_NAME
    kubectl wait --for=condition=available --timeout=300s deployment/fairmind-website -n fairmind-$CUSTOMER_NAME
    
    print_success "Kubernetes deployment completed"
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Backend health check
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend health check passed"
    else
        print_error "Backend health check failed"
        return 1
    fi
    
    # Frontend health check
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend health check passed"
    else
        print_error "Frontend health check failed"
        return 1
    fi
    
    # Website health check
    if curl -f http://localhost:4321 >/dev/null 2>&1; then
        print_success "Website health check passed"
    else
        print_error "Website health check failed"
        return 1
    fi
    
    print_success "All health checks passed"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Create monitoring directory
    mkdir -p monitoring/$CUSTOMER_NAME
    
    # Copy monitoring configuration
    cp infrastructure/monitoring/prometheus.yml monitoring/$CUSTOMER_NAME/
    cp infrastructure/monitoring/grafana-dashboard.json monitoring/$CUSTOMER_NAME/
    
    # Start monitoring stack
    docker-compose -f infrastructure/monitoring/docker-compose.yml -p fairmind-$CUSTOMER_NAME up -d
    
    print_success "Monitoring setup completed"
}

# Function to create customer user
create_customer_user() {
    print_status "Creating customer user..."
    
    cd apps/backend
    
    # Create admin user
    python scripts/create_customer_user.py --customer $CUSTOMER_NAME --email admin@$CUSTOMER_NAME.com --role admin
    
    cd ../..
    
    print_success "Customer user created"
}

# Function to display deployment summary
show_deployment_summary() {
    print_success "Deployment completed successfully!"
    echo
    echo "=== Deployment Summary ==="
    echo "Customer: $CUSTOMER_NAME"
    echo "Environment: $ENVIRONMENT"
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo "Website: http://localhost:4321"
    echo "API Documentation: http://localhost:8000/docs"
    echo
    echo "=== Next Steps ==="
    echo "1. Configure customer-specific settings"
    echo "2. Import customer models and datasets"
    echo "3. Setup user accounts and permissions"
    echo "4. Run initial bias and security tests"
    echo "5. Schedule customer onboarding"
    echo
    echo "=== Support ==="
    echo "Documentation: https://docs.fairmind.ai"
    echo "Support: support@fairmind.ai"
    echo "Issues: https://github.com/fairmind/ethical-sandbox/issues"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -c, --customer NAME     Customer name (required)"
    echo "  -e, --environment ENV   Environment (development|production) [default: development]"
    echo "  -b, --backend           Deploy backend only"
    echo "  -f, --frontend          Deploy frontend only"
    echo "  -w, --website           Deploy website only"
    echo "  -d, --docker            Use Docker deployment"
    echo "  -k, --kubernetes        Use Kubernetes deployment"
    echo "  -h, --help              Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -c acme-corp                    # Deploy all services for ACME Corp"
    echo "  $0 -c acme-corp -e production      # Production deployment"
    echo "  $0 -c acme-corp -d                 # Docker deployment"
    echo "  $0 -c acme-corp -b                 # Backend only"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--customer)
            CUSTOMER_NAME="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--backend)
            DEPLOY_FRONTEND=false
            DEPLOY_WEBSITE=false
            shift
            ;;
        -f|--frontend)
            DEPLOY_BACKEND=false
            DEPLOY_WEBSITE=false
            shift
            ;;
        -w|--website)
            DEPLOY_BACKEND=false
            DEPLOY_FRONTEND=false
            shift
            ;;
        -d|--docker)
            USE_DOCKER=true
            shift
            ;;
        -k|--kubernetes)
            USE_KUBERNETES=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$CUSTOMER_NAME" ]; then
    print_error "Customer name is required"
    show_usage
    exit 1
fi

# Main deployment process
main() {
    print_status "Starting deployment for customer: $CUSTOMER_NAME"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Setup database
    setup_database
    
    # Deploy services
    if [ "$USE_DOCKER" = true ]; then
        deploy_docker
    elif [ "$USE_KUBERNETES" = true ]; then
        deploy_kubernetes
    else
        if [ "$DEPLOY_BACKEND" = true ]; then
            deploy_backend
        fi
        
        if [ "$DEPLOY_FRONTEND" = true ]; then
            deploy_frontend
        fi
        
        if [ "$DEPLOY_WEBSITE" = true ]; then
            deploy_website
        fi
    fi
    
    # Run health checks
    run_health_checks
    
    # Setup monitoring
    setup_monitoring
    
    # Create customer user
    create_customer_user
    
    # Show deployment summary
    show_deployment_summary
}

# Run main function
main "$@"
