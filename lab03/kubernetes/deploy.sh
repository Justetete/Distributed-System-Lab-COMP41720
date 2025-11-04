#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Kubernetes Deployment Script  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get the project root directory (parent of kubernetes folder)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}Project root: ${PROJECT_ROOT}${NC}"
cd "$PROJECT_ROOT"
echo ""

# Check if minikube is running
echo -e "${YELLOW}[1/6]${NC} Checking Minikube status..."
if ! minikube status &> /dev/null; then
    echo -e "${RED}Error: Minikube is not running!${NC}"
    echo -e "${YELLOW}Please start Minikube first: minikube start${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Minikube is running${NC}"
echo ""

# Set docker environment to minikube
echo -e "${YELLOW}[2/6]${NC} Setting Docker environment to Minikube..."
eval $(minikube docker-env)
echo -e "${GREEN}✓ Docker environment set${NC}"
echo ""

# Build Docker images
echo -e "${YELLOW}[3/6]${NC} Building Docker images..."
echo -e "${BLUE}Building backend-service...${NC}"
if [ ! -f "services/backend_services/Dockerfile" ]; then
    echo -e "${RED}Error: services/backend_services/Dockerfile not found!${NC}"
    echo -e "${YELLOW}Please create the Dockerfile first.${NC}"
    exit 1
fi
docker build -t backend-service:latest -f services/backend_services/Dockerfile services/backend_services/
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build backend-service${NC}"
    exit 1
fi
echo -e "${GREEN}✓ backend-service built successfully${NC}"

echo -e "${BLUE}Building client-service...${NC}"
if [ ! -f "services/client_services/Dockerfile" ]; then
    echo -e "${RED}Error: services/client_services/Dockerfile not found!${NC}"
    echo -e "${YELLOW}Please create the Dockerfile first.${NC}"
    exit 1
fi
docker build -t client-service:latest -f services/client_services/Dockerfile services/client_services/
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build client-service${NC}"
    exit 1
fi
echo -e "${GREEN}✓ client-service built successfully${NC}"
echo ""

# Deploy Backend
echo -e "${YELLOW}[4/6]${NC} Deploying Backend Service..."
kubectl apply -f kubernetes/backend/deployment.yaml
kubectl apply -f kubernetes/backend/service.yaml
echo -e "${GREEN}✓ Backend deployed${NC}"
echo ""

# Deploy Client
echo -e "${YELLOW}[5/6]${NC} Deploying Client Service..."
kubectl apply -f kubernetes/client/deployment.yaml
kubectl apply -f kubernetes/client/service.yaml
echo -e "${GREEN}✓ Client deployed${NC}"
echo ""

# Wait for deployments
echo -e "${YELLOW}[6/6]${NC} Waiting for deployments to be ready..."
echo -e "${BLUE}Waiting for backend-deployment...${NC}"
kubectl wait --for=condition=available --timeout=60s deployment/backend-deployment
echo -e "${GREEN}✓ Backend is ready${NC}"

echo -e "${BLUE}Waiting for client-deployment...${NC}"
kubectl wait --for=condition=available --timeout=60s deployment/client-deployment
echo -e "${GREEN}✓ Client is ready${NC}"
echo ""

# Display status
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Deployment Completed! 🎉${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

echo -e "${BLUE}Pod Status:${NC}"
kubectl get pods -l app=backend -o wide
kubectl get pods -l app=client -o wide
echo ""

echo -e "${BLUE}Service Status:${NC}"
kubectl get services
echo ""

# Get client service URL
echo -e "${BLUE}Access URLs:${NC}"
echo -e "Client Service: ${GREEN}$(minikube service client-service --url)${NC}"
echo ""

echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  - Check logs: ${BLUE}kubectl logs -f <pod-name>${NC}"
echo -e "  - View pods: ${BLUE}kubectl get pods${NC}"
echo -e "  - View services: ${BLUE}kubectl get svc${NC}"
echo -e "  - Delete all: ${BLUE}kubectl delete -f kubernetes/${NC}"
echo ""