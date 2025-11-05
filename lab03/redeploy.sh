#!/bin/bash

# Script to rebuild and redeploy client service with retry fix

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Rebuild and Redeploy Client Service  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo -e "${YELLOW}Project root: ${PROJECT_ROOT}${NC}"
cd "$PROJECT_ROOT"
echo ""

# Set docker environment to minikube
echo -e "${YELLOW}[1/4] Setting Docker environment to Minikube...${NC}"
eval $(minikube docker-env)
echo -e "${GREEN}✓ Docker environment set${NC}"
echo ""

# Rebuild client service image
echo -e "${YELLOW}[2/4] Rebuilding client-service image...${NC}"
docker build -t client-service:latest -f services/client_services/Dockerfile services/client_services/
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build client-service${NC}"
    exit 1
fi
echo -e "${GREEN}✓ client-service rebuilt successfully${NC}"
echo ""

# Restart client deployment
echo -e "${YELLOW}[3/4] Restarting client deployment...${NC}"
kubectl rollout restart deployment/client-deployment
echo -e "${GREEN}✓ Deployment restart initiated${NC}"
echo ""

# Wait for rollout to complete
echo -e "${YELLOW}[4/4] Waiting for rollout to complete...${NC}"
kubectl rollout status deployment/client-deployment
echo -e "${GREEN}✓ Rollout complete${NC}"
echo ""

# Show new pods
echo -e "${BLUE}New pods:${NC}"
kubectl get pods -l app=client
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Redeploy Complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${YELLOW}Now test retry functionality:${NC}"
echo -e "  1. Configure backend errors:"
echo -e "     ${BLUE}curl -X POST http://localhost:5000/configfailure \\${NC}"
echo -e "     ${BLUE}  -H 'Content-Type: application/json' \\${NC}"
echo -e "     ${BLUE}  -d '{\"failure_rate\": 0.5}'${NC}"
echo ""
echo -e "  2. Make requests:"
echo -e "     ${BLUE}CLIENT_URL=\$(minikube service client-service --url)${NC}"
echo -e "     ${BLUE}curl \$CLIENT_URL/client/users/1${NC}"
echo ""
echo -e "  3. Watch logs for retry:"
echo -e "     ${BLUE}kubectl logs -f deployment/client-deployment | grep -i retry${NC}"
echo ""