#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Kubernetes Cleanup Script     ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}Deleting all Kubernetes resources...${NC}"

# Delete client resources
echo -e "${BLUE}Deleting client resources...${NC}"
kubectl delete -f kubernetes/client/

# Delete backend resources
echo -e "${BLUE}Deleting backend resources...${NC}"
kubectl delete -f kubernetes/backend/

echo ""
echo -e "${GREEN}✓ Cleanup completed!${NC}"
echo ""

echo -e "${BLUE}Remaining resources:${NC}"
kubectl get all
echo ""