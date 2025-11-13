# Kubernetes Deployment Guide

Complete guide for deploying the E-Commerce microservices to Kubernetes using Minikube.

## Prerequisites

### Required Tools

1. **Minikube** - Local Kubernetes cluster
```bash
# Install on macOS
brew install minikube

# Install on Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

2. **kubectl** - Kubernetes CLI
```bash
# Install on macOS
brew install kubectl

# Install on Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/kubectl
```

3. **Docker** - Container runtime
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
```

### Verify Installation

```bash
minikube version
kubectl version --client
docker --version
```

## Quick Start

### 1. Deploy Everything

```bash
# Make scripts executable (first time only)
chmod +x deploy.sh cleanup.sh

# Deploy all services
./deploy.sh
```

This script will:
- ✅ Start Minikube (if not running)
- ✅ Build Docker images
- ✅ Load images into Minikube
- ✅ Deploy all services in correct order
- ✅ Wait for pods to be ready
- ✅ Display service endpoints

**Expected output:**
```
========================================
Deployment Complete!
========================================

[SUCCESS] API Gateway URL: http://192.168.49.2:30080

Try these endpoints:
  - Health: http://192.168.49.2:30080/actuator/health
  - Products: http://192.168.49.2:30080/api/products
  - Orders: http://192.168.49.2:30080/api/orders
```

### 2. Clean Up Everything

```bash
# Remove all deployed resources
./cleanup.sh
```

This will prompt for confirmation before deleting all resources.

## Manual Deployment (Step by Step)

If you prefer manual deployment or need to troubleshoot:

### Step 1: Start Minikube

```bash
minikube start

# Verify Minikube is running
minikube status
```

### Step 2: Build Docker Images

```bash
# Configure Docker to use Minikube's Docker daemon
eval $(minikube docker-env)

# Build images
docker build -t lab04-product-service:latest ./product-service
docker build -t lab04-order-service:latest ./order-service
docker build -t lab04-api-gateway:latest ./api-gateway

# Verify images
docker images | grep lab04
```

### Step 3: Deploy Services

```bash
cd k8s

# Deploy Product Service
kubectl apply -f products-deployment.yaml
kubectl apply -f products-service.yaml

# Deploy Order Service
kubectl apply -f orders-deployment.yaml
kubectl apply -f orders-service.yaml

# Deploy API Gateway
kubectl apply -f gateway-deployment.yaml
kubectl apply -f gateway-service.yaml

cd ..
```

### Step 4: Wait for Pods to be Ready

```bash
# Watch pods starting
kubectl get pods -w

# Wait for specific deployments
kubectl wait --for=condition=available --timeout=300s deployment/product-service
kubectl wait --for=condition=available --timeout=300s deployment/order-service
kubectl wait --for=condition=available --timeout=300s deployment/api-gateway
```

## Checking Deployment Status

### View All Resources

```bash
# View all pods
kubectl get pods

# Expected output:
# NAME                               READY   STATUS    RESTARTS   AGE
# product-service-7d9f8c-abc12       1/1     Running   0          2m
# product-service-7d9f8c-def34       1/1     Running   0          2m
# order-service-5b8d7f-xyz89         1/1     Running   0          2m
# order-service-5b8d7f-qwe45         1/1     Running   0          2m
# api-gateway-9c6f5e-uvw78           1/1     Running   0          2m
# api-gateway-9c6f5e-rst56           1/1     Running   0          2m
```

```bash
# View all services
kubectl get svc

# Expected output:
# NAME              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
# kubernetes        ClusterIP   10.96.0.1        <none>        443/TCP          10m
# product-service   ClusterIP   10.96.100.50     <none>        8080/TCP         2m
# order-service     ClusterIP   10.96.200.100    <none>        8081/TCP         2m
# api-gateway       NodePort    10.96.150.50     <none>        8080:30080/TCP   2m
```

```bash
# View all deployments
kubectl get deployments

# View detailed info
kubectl get all
```

### Check Pod Details

```bash
# Describe a specific pod
kubectl describe pod <pod-name>

# Example
kubectl describe pod product-service-7d9f8c-abc12

# Get pod logs
kubectl logs <pod-name>

# Follow logs in real-time
kubectl logs -f <pod-name>

# Get logs from all pods of a service
kubectl logs -l app=product-service

# Get logs with timestamps
kubectl logs <pod-name> --timestamps

# Get last 50 lines
kubectl logs <pod-name> --tail=50
```

### Check Service Status

```bash
# Get service details
kubectl describe service product-service

# Get service endpoints
kubectl get endpoints product-service

# Should show pod IPs:
# NAME              ENDPOINTS                       AGE
# product-service   10.244.1.5:8080,10.244.1.6:8080  2m
```

## Accessing the API Gateway

### Method 1: Using minikube service (Easiest)

```bash
# Open gateway in browser
minikube service api-gateway

# Get URL without opening browser
minikube service api-gateway --url
```

### Method 2: Using Minikube IP + NodePort

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo $MINIKUBE_IP
# Output: 192.168.49.2

# Access gateway at: http://192.168.49.2:30080
export GATEWAY_URL="http://$(minikube ip):30080"
echo $GATEWAY_URL

# Test gateway
curl $GATEWAY_URL/actuator/health
```

### Method 3: Port Forwarding

```bash
# Forward local port to gateway
kubectl port-forward service/api-gateway 8080:8080

# Access via localhost (in another terminal)
curl http://localhost:8080/actuator/health
```

## Testing the Application

### Get Gateway URL

```bash
# Get and store gateway URL
export GATEWAY_URL=$(minikube service api-gateway --url)
echo "Gateway URL: $GATEWAY_URL"
```

### Test Health Endpoints

```bash
# Test API Gateway health
curl $GATEWAY_URL/actuator/health

# Expected response:
# {"status":"UP"}
```

### Test Product Service

```bash
# List all products (initially empty)
curl $GATEWAY_URL/api/products
# Expected: []

# Create a product
curl -X POST $GATEWAY_URL/api/products/create \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "MacBook Pro 16",
    "price": 2499.99,
    "stockLevel": 10
  }'

# List products again
curl $GATEWAY_URL/api/products

# Get specific product
curl $GATEWAY_URL/api/products/LAPTOP-001

# Create multiple products
curl -X POST $GATEWAY_URL/api/products/bulk_create \
  -H "Content-Type: application/json" \
  -d '[
    {"sku": "PHONE-001", "name": "iPhone 15 Pro", "price": 999.99, "stockLevel": 50},
    {"sku": "TABLET-001", "name": "iPad Air", "price": 599.99, "stockLevel": 30},
    {"sku": "WATCH-001", "name": "Apple Watch Ultra", "price": 799.99, "stockLevel": 20}
  ]'
```

### Test Order Service

```bash
# List all orders (initially empty)
curl $GATEWAY_URL/api/orders
# Expected: []

# Create an order
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "refNumber": "ORD-2025-001",
    "customerId": "CUST-123",
    "items": [
      {
        "sku": "LAPTOP-001",
        "quantity": 1
      },
      {
        "sku": "PHONE-001",
        "quantity": 2
      }
    ]
  }'

# List all orders
curl $GATEWAY_URL/api/orders

# Get specific order
curl $GATEWAY_URL/api/orders/ORD-2025-001
```

### Test Inter-Service Communication

The order service communicates with the product service internally:

```bash
# 1. Check initial stock
curl $GATEWAY_URL/api/products/LAPTOP-001
# Note the stockLevel

# 2. Create an order (Order service calls Product service to adjust stock)
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "refNumber": "ORD-2025-002",
    "customerId": "CUST-456",
    "items": [
      {
        "sku": "LAPTOP-001",
        "quantity": 2
      }
    ]
  }'

# 3. Check updated stock
curl $GATEWAY_URL/api/products/LAPTOP-001
# Stock should be reduced by 2
```

## Viewing Logs

### View Logs by Pod

```bash
# Get pod name
kubectl get pods

# View logs
kubectl logs product-service-7d9f8c-abc12

# Follow logs in real-time
kubectl logs -f product-service-7d9f8c-abc12

# View last 100 lines
kubectl logs product-service-7d9f8c-abc12 --tail=100

# View logs with timestamps
kubectl logs product-service-7d9f8c-abc12 --timestamps
```

### View Logs by Service (All Pods)

```bash
# Product Service logs
kubectl logs -l app=product-service --tail=50

# Order Service logs
kubectl logs -l app=order-service --tail=50

# API Gateway logs
kubectl logs -l app=api-gateway --tail=50

# Follow all gateway logs
kubectl logs -l app=api-gateway -f
```

### View Logs from Previous Container Instance

```bash
# Useful when a container has restarted
kubectl logs <pod-name> --previous
```

## Scaling Services

### Scale Replicas

```bash
# Scale Product Service to 3 replicas
kubectl scale deployment product-service --replicas=3

# Scale Order Service to 4 replicas
kubectl scale deployment order-service --replicas=4

# Scale API Gateway to 3 replicas
kubectl scale deployment api-gateway --replicas=3

# Verify
kubectl get pods
```

### Autoscaling (Horizontal Pod Autoscaler)

```bash
# Create HPA for Product Service
kubectl autoscale deployment product-service --cpu-percent=70 --min=2 --max=5

# View HPA status
kubectl get hpa

# Delete HPA
kubectl delete hpa product-service
```

## Updating Deployments

### Update Image

```bash
# Rebuild image with changes
eval $(minikube docker-env)
docker build -t lab04-product-service:latest ./product-service

# Restart deployment to use new image
kubectl rollout restart deployment product-service

# Watch rollout status
kubectl rollout status deployment product-service
```

### Edit Deployment

```bash
# Edit deployment directly
kubectl edit deployment product-service

# Apply changes from file
kubectl apply -f k8s/products-deployment.yaml
```

### Rollout History

```bash
# View rollout history
kubectl rollout history deployment product-service

# Rollback to previous version
kubectl rollout undo deployment product-service

# Rollback to specific revision
kubectl rollout undo deployment product-service --to-revision=2
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods

# Describe pod to see events
kubectl describe pod <pod-name>

# Common issues:
# - ImagePullBackOff: Image not found in Minikube
# - CrashLoopBackOff: Application crashing on startup
# - Pending: Insufficient resources
```

**Fix ImagePullBackOff:**
```bash
# Ensure you're using Minikube's Docker daemon
eval $(minikube docker-env)

# Rebuild images
docker build -t lab04-product-service:latest ./product-service

# Verify image exists
docker images | grep lab04
```

### Service Not Accessible

```bash
# Check if service exists
kubectl get svc api-gateway

# Check service endpoints
kubectl get endpoints api-gateway

# If no endpoints, pods might not be ready
kubectl get pods -l app=api-gateway

# Test from inside cluster
kubectl run test-pod --rm -it --image=busybox -- wget -O- http://api-gateway:8080/actuator/health
```

### Logs Show Errors

```bash
# View logs with more context
kubectl logs <pod-name> --tail=200

# Check for common issues:
# - Database connection errors (need database pods)
# - Eureka connection errors (need Eureka server)
# - Memory/CPU limits exceeded
```

### Increase Resource Limits

Edit deployment and increase resources:
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Debug Inside Container

```bash
# Execute shell in running container
kubectl exec -it <pod-name> -- /bin/sh

# Check network connectivity
kubectl exec -it <pod-name> -- curl http://product-service:8080/actuator/health

# Check environment variables
kubectl exec -it <pod-name> -- env | grep -E 'SPRING|EUREKA|DATASOURCE'
```

## Monitoring and Observability

### Watch Resources in Real-Time

```bash
# Watch pods
kubectl get pods -w

# Watch all resources
kubectl get all -w

# Watch specific deployment
kubectl get deployment product-service -w
```

### Resource Usage

```bash
# Top pods (requires metrics-server)
kubectl top pods

# Top nodes
kubectl top nodes

# Enable metrics-server in Minikube
minikube addons enable metrics-server
```

### Events

```bash
# View all events
kubectl get events --sort-by=.metadata.creationTimestamp

# View events for specific pod
kubectl get events --field-selector involvedObject.name=<pod-name>
```

## Useful Commands Reference

### Quick Status Checks

```bash
# Everything in one view
kubectl get all

# Check specific service
kubectl get all -l app=product-service

# Wide output (more details)
kubectl get pods -o wide

# YAML output
kubectl get deployment product-service -o yaml

# JSON output
kubectl get service api-gateway -o json
```

### Debugging Commands

```bash
# Describe resource
kubectl describe pod <pod-name>
kubectl describe svc <service-name>
kubectl describe deployment <deployment-name>

# Get logs
kubectl logs <pod-name>
kubectl logs -f <pod-name>  # Follow
kubectl logs <pod-name> --previous  # Previous container

# Execute commands in pod
kubectl exec <pod-name> -- <command>
kubectl exec -it <pod-name> -- /bin/sh

# Port forwarding
kubectl port-forward pod/<pod-name> 8080:8080
kubectl port-forward service/<service-name> 8080:8080
```

### Cleanup Commands

```bash
# Delete specific resource
kubectl delete pod <pod-name>
kubectl delete service <service-name>
kubectl delete deployment <deployment-name>

# Delete all resources for a service
kubectl delete all -l app=product-service

# Delete by label
kubectl delete deployments,services -l tier=backend

# Delete everything (use with caution)
kubectl delete all --all
```

## Production Considerations

For production deployments, consider:

1. **ConfigMaps and Secrets**
   - Externalize configuration
   - Store sensitive data securely

2. **Persistent Storage**
   - Use PersistentVolumeClaims for databases
   - Backup strategies

3. **Ingress Controller**
   - Use Ingress instead of NodePort
   - SSL/TLS termination

4. **Resource Limits**
   - Set appropriate CPU/memory limits
   - Use ResourceQuotas per namespace

5. **Health Checks**
   - Configure liveness and readiness probes
   - Add startup probes for slow-starting apps

6. **Monitoring**
   - Prometheus and Grafana
   - Centralized logging (ELK, Loki)

7. **Security**
   - Network Policies
   - Pod Security Policies
   - RBAC

## Next Steps

- [ ] Deploy PostgreSQL databases for persistence
- [ ] Deploy Eureka Server for service discovery
- [ ] Set up Ingress for production-like routing
- [ ] Configure ConfigMaps for externalized config
- [ ] Add Secrets for sensitive data
- [ ] Set up monitoring with Prometheus
- [ ] Implement CI/CD pipeline

## Support

For issues or questions:
- Check pod logs: `kubectl logs <pod-name>`
- Describe resources: `kubectl describe pod <pod-name>`
- View events: `kubectl get events`
- Check this guide's troubleshooting section

## Summary

Your microservices are now running in Kubernetes! Use these key commands:

```bash
# Deploy everything
./deploy.sh

# Check status
kubectl get pods
kubectl get svc

# Access gateway
minikube service api-gateway --url

# View logs
kubectl logs -l app=<service-name>

# Clean up
./cleanup.sh
```
