#!/bin/bash

# Kubernetes Cleanup Script for E-Commerce Microservices
# This script removes all deployed resources from Kubernetes

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

# Check if kubectl is installed
if ! command_exists kubectl; then
    print_error "kubectl is not installed"
    exit 1
fi

# Confirmation prompt
print_header "Cleanup Confirmation"
echo ""
print_warning "This will delete all microservices from Kubernetes:"
echo "  - API Gateway"
echo "  - Order Service"
echo "  - Product Service"
echo "  - All associated pods, services, and deployments"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Cleanup cancelled"
    exit 0
fi

# Delete resources
print_header "Deleting Kubernetes Resources"

# Check if k8s directory exists
if [ -d "k8s" ]; then
    cd k8s

    # Delete API Gateway (reverse order from deployment)
    print_info "Deleting API Gateway..."
    if [ -f "gateway-service.yaml" ]; then
        kubectl delete -f gateway-service.yaml --ignore-not-found=true
    fi
    if [ -f "gateway-deployment.yaml" ]; then
        kubectl delete -f gateway-deployment.yaml --ignore-not-found=true
    fi
    print_success "API Gateway deleted"

    # Delete Order Service
    print_info "Deleting Order Service..."
    if [ -f "orders-service.yaml" ]; then
        kubectl delete -f orders-service.yaml --ignore-not-found=true
    fi
    if [ -f "orders-deployment.yaml" ]; then
        kubectl delete -f orders-deployment.yaml --ignore-not-found=true
    fi
    print_success "Order Service deleted"

    # Delete Product Service
    print_info "Deleting Product Service..."
    if [ -f "products-service.yaml" ]; then
        kubectl delete -f products-service.yaml --ignore-not-found=true
    fi
    if [ -f "products-deployment.yaml" ]; then
        kubectl delete -f products-deployment.yaml --ignore-not-found=true
    fi
    print_success "Product Service deleted"

    # Delete ConfigMaps
    print_info "Deleting ConfigMaps..."
    if [ -f "configmaps.yaml" ]; then
        kubectl delete -f configmaps.yaml --ignore-not-found=true
    fi
    print_success "ConfigMaps deleted"

    # Delete Databases (last, after all services)
    print_info "Deleting PostgreSQL Databases..."
    if [ -d "databases" ]; then
        if [ -f "databases/order-db.yaml" ]; then
            kubectl delete -f databases/order-db.yaml --ignore-not-found=true
        fi
        if [ -f "databases/product-db.yaml" ]; then
            kubectl delete -f databases/product-db.yaml --ignore-not-found=true
        fi
        print_success "Databases deleted"
    fi

    cd ..
else
    print_warning "k8s directory not found"
fi

# Alternative: Delete by label (more robust)
print_info "Cleaning up any remaining resources..."
kubectl delete deployments,services -l tier=backend --ignore-not-found=true
kubectl delete deployments,services -l tier=gateway --ignore-not-found=true
kubectl delete configmaps -l tier=backend --ignore-not-found=true
kubectl delete configmaps -l tier=gateway --ignore-not-found=true
kubectl delete statefulsets,services -l tier=database --ignore-not-found=true

# Wait for pods to terminate
print_info "Waiting for pods to terminate..."
sleep 5

# Verify cleanup
print_header "Cleanup Status"

echo ""
print_info "Remaining pods:"
PODS=$(kubectl get pods 2>/dev/null | grep -E "product-service|order-service|api-gateway" || echo "None")
if [ "$PODS" == "None" ]; then
    print_success "No microservice pods remaining"
else
    echo "$PODS"
    print_warning "Some pods are still terminating (this is normal)"
fi

echo ""
print_info "Remaining services:"
SERVICES=$(kubectl get svc 2>/dev/null | grep -E "product-service|order-service|api-gateway" || echo "None")
if [ "$SERVICES" == "None" ]; then
    print_success "No microservice services remaining"
else
    echo "$SERVICES"
fi

echo ""
print_info "Remaining deployments:"
DEPLOYMENTS=$(kubectl get deployments 2>/dev/null | grep -E "product-service|order-service|api-gateway" || echo "None")
if [ "$DEPLOYMENTS" == "None" ]; then
    print_success "No microservice deployments remaining"
else
    echo "$DEPLOYMENTS"
fi

# Optional: Clean up Docker images
echo ""
print_header "Docker Image Cleanup (Optional)"
echo ""
read -p "Do you want to remove Docker images as well? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Setting Docker environment to Minikube..."
    if command_exists minikube; then
        eval $(minikube docker-env)

        print_info "Removing Docker images..."
        docker rmi lab04-product-service:latest --force 2>/dev/null || print_warning "product-service image not found"
        docker rmi lab04-order-service:latest --force 2>/dev/null || print_warning "order-service image not found"
        docker rmi lab04-api-gateway:latest --force 2>/dev/null || print_warning "api-gateway image not found"

        print_success "Docker images removed"
    else
        print_warning "Minikube not found, skipping Docker cleanup"
    fi
else
    print_info "Docker images preserved"
fi

# Optional: Clean up Persistent Volume Claims (Database Data)
echo ""
print_header "Database Persistent Volume Cleanup (Optional)"
echo ""
print_warning "This will delete all database data permanently!"
read -p "Do you want to remove database persistent volumes? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Removing persistent volume claims..."
    kubectl delete pvc -l tier=database --ignore-not-found=true 2>/dev/null || print_warning "No database PVCs found"
    print_success "Persistent volume claims removed"
else
    print_info "Database persistent volumes preserved (data retained)"
fi

# Summary
print_header "Cleanup Complete!"

echo ""
print_info "All microservices have been removed from Kubernetes"
echo ""
print_info "To redeploy, run: ./deploy.sh"
echo ""

print_success "Cleanup completed successfully!"
echo ""
