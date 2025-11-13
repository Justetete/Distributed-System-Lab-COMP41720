#!/bin/bash

# Kubernetes Deployment Script for E-Commerce Microservices
# This script builds Docker images, loads them into Minikube, and deploys all services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-flight checks
print_header "Pre-flight Checks"

# Check if kubectl is installed
if ! command_exists kubectl; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi
print_success "kubectl is installed"

# Check if minikube is installed
if ! command_exists minikube; then
    print_error "minikube is not installed. Please install minikube first."
    exit 1
fi
print_success "minikube is installed"

# Check if Docker is installed
if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

# Check if Minikube is running
if ! minikube status > /dev/null 2>&1; then
    print_warning "Minikube is not running. Starting Minikube..."
    minikube start
    if [ $? -ne 0 ]; then
        print_error "Failed to start Minikube"
        exit 1
    fi
    print_success "Minikube started successfully"
else
    print_success "Minikube is running"
fi

# Set Docker environment to use Minikube's Docker daemon
print_header "Configuring Docker Environment"
print_info "Setting Docker environment to use Minikube's Docker daemon..."
eval $(minikube docker-env)
print_success "Docker environment configured"

# Build Docker images
print_header "Building Docker Images"

# Array of services to build
declare -a services=("product-service" "order-service" "api-gateway")

for service in "${services[@]}"; do
    if [ -d "$service" ]; then
        print_info "Building $service..."
        docker build -t "lab04-$service:latest" "./$service"
        if [ $? -eq 0 ]; then
            print_success "$service image built successfully"
        else
            print_error "Failed to build $service image"
            exit 1
        fi
    else
        print_warning "Directory $service not found, skipping..."
    fi
done

# Verify images
print_header "Verifying Docker Images"
print_info "Checking built images..."
docker images | grep "lab04-"
echo ""

# Deploy to Kubernetes
print_header "Deploying to Kubernetes"

# Check if k8s directory exists
if [ ! -d "k8s" ]; then
    print_error "k8s directory not found"
    exit 1
fi

cd k8s

# Deploy Databases first (services depend on them)
print_info "Deploying PostgreSQL Databases..."
if [ -d "databases" ]; then
    if [ -f "databases/product-db.yaml" ]; then
        kubectl apply -f databases/product-db.yaml
        print_success "Product Database manifest applied"
    fi

    if [ -f "databases/order-db.yaml" ]; then
        kubectl apply -f databases/order-db.yaml
        print_success "Order Database manifest applied"
    fi

    echo ""
    print_info "Waiting for databases to be ready..."

    # Wait for product-db to be ready
    if kubectl get statefulset product-db > /dev/null 2>&1; then
        print_info "Waiting for product-db to be ready (timeout: 120s)..."
        if kubectl wait --for=condition=ready pod -l app=product-db --timeout=120s 2>/dev/null; then
            print_success "product-db is ready"
        else
            print_warning "product-db not ready yet, continuing anyway..."
        fi
    fi

    # Wait for order-db to be ready
    if kubectl get statefulset order-db > /dev/null 2>&1; then
        print_info "Waiting for order-db to be ready (timeout: 120s)..."
        if kubectl wait --for=condition=ready pod -l app=order-db --timeout=120s 2>/dev/null; then
            print_success "order-db is ready"
        else
            print_warning "order-db not ready yet, continuing anyway..."
        fi
    fi
else
    print_warning "databases directory not found, skipping database deployment"
fi

echo ""

# Deploy ConfigMaps (services depend on them)
print_info "Deploying ConfigMaps..."
if [ -f "configmaps.yaml" ]; then
    kubectl apply -f configmaps.yaml
    print_success "ConfigMaps deployed"
else
    print_warning "configmaps.yaml not found, services will use hardcoded env vars"
fi

echo ""

# Deploy Product Service
print_info "Deploying Product Service..."
if [ -f "products-deployment.yaml" ] && [ -f "products-service.yaml" ]; then
    kubectl apply -f products-deployment.yaml
    kubectl apply -f products-service.yaml
    print_success "Product Service deployed"
else
    print_warning "Product Service manifests not found, skipping..."
fi

# Wait a moment for Product Service to start
sleep 5

# Deploy Order Service
print_info "Deploying Order Service..."
if [ -f "orders-deployment.yaml" ] && [ -f "orders-service.yaml" ]; then
    kubectl apply -f orders-deployment.yaml
    kubectl apply -f orders-service.yaml
    print_success "Order Service deployed"
else
    print_warning "Order Service manifests not found, skipping..."
fi

# Wait a moment for Order Service to start
sleep 5

# Deploy API Gateway
print_info "Deploying API Gateway..."
if [ -f "gateway-deployment.yaml" ] && [ -f "gateway-service.yaml" ]; then
    kubectl apply -f gateway-deployment.yaml
    kubectl apply -f gateway-service.yaml
    print_success "API Gateway deployed"
else
    print_warning "API Gateway manifests not found, skipping..."
fi

cd ..

# Wait for deployments to be ready
print_header "Waiting for Deployments to be Ready"

# Function to wait for deployment with timeout
wait_for_deployment() {
    local deployment=$1
    local timeout=300  # 5 minutes

    print_info "Waiting for $deployment to be ready (timeout: ${timeout}s)..."

    if kubectl wait --for=condition=available --timeout=${timeout}s deployment/$deployment 2>/dev/null; then
        print_success "$deployment is ready"
        return 0
    else
        print_warning "$deployment is not ready yet (might need more time or check logs)"
        return 1
    fi
}

# Wait for each deployment
wait_for_deployment "product-service"
wait_for_deployment "order-service"
wait_for_deployment "api-gateway"

# Display deployment status
print_header "Deployment Status"

print_info "Pods:"
kubectl get pods -o wide

echo ""
print_info "Services:"
kubectl get svc

echo ""
print_info "Deployments:"
kubectl get deployments

# Get API Gateway URL
print_header "Service Endpoints"

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
print_info "Minikube IP: $MINIKUBE_IP"

# Get API Gateway NodePort
GATEWAY_PORT=$(kubectl get svc api-gateway -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)

if [ ! -z "$GATEWAY_PORT" ]; then
    GATEWAY_URL="http://$MINIKUBE_IP:$GATEWAY_PORT"
    echo ""
    print_success "API Gateway URL: $GATEWAY_URL"
    echo ""
    print_info "You can also use: minikube service api-gateway --url"
    echo ""

    # Test if gateway is responding
    print_info "Testing API Gateway connectivity..."
    sleep 10  # Give it a moment to fully start

    if curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/actuator/health" | grep -q "200"; then
        print_success "API Gateway is responding!"
        echo ""
        print_info "Try these endpoints:"
        echo "  - Health: $GATEWAY_URL/actuator/health"
        echo "  - Products: $GATEWAY_URL/api/products"
        echo "  - Orders: $GATEWAY_URL/api/orders"
    else
        print_warning "API Gateway not responding yet. It may need more time to start."
        print_info "Check status with: kubectl get pods"
        print_info "View logs with: kubectl logs -l app=api-gateway"
    fi
else
    print_warning "Could not get API Gateway NodePort"
fi

# Summary
print_header "Deployment Complete!"

echo ""
print_info "Quick Commands:"
echo "  View pods:        kubectl get pods"
echo "  View services:    kubectl get svc"
echo "  View logs:        kubectl logs -l app=<service-name>"
echo "  Gateway URL:      minikube service api-gateway --url"
echo "  Delete all:       ./cleanup.sh"
echo ""

print_success "Deployment completed successfully!"
echo ""
