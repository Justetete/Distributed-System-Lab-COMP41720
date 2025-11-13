# Quick Start Guide - Kubernetes Deployment

Fast track to deploy your e-commerce microservices to Kubernetes.

## TL;DR

```bash
# 1. Deploy everything
./deploy.sh

# 2. Get gateway URL
export GATEWAY_URL=$(minikube service api-gateway --url)

# 3. Test
curl $GATEWAY_URL/actuator/health
curl $GATEWAY_URL/api/products
curl $GATEWAY_URL/api/orders

# 4. Clean up when done
./cleanup.sh
```

## Prerequisites

- Minikube installed and running
- kubectl installed
- Docker installed

## Deployment

### One-Command Deploy

```bash
./deploy.sh
```

This automatically:
- ✅ Starts Minikube (if needed)
- ✅ Builds all Docker images
- ✅ Loads images into Minikube
- ✅ Deploys all services
- ✅ Waits for pods to be ready
- ✅ Shows gateway URL

### Expected Output

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

## Quick Testing

### Set Gateway URL

```bash
export GATEWAY_URL=$(minikube service api-gateway --url)
```

### Test Health

```bash
curl $GATEWAY_URL/actuator/health
# Expected: {"status":"UP"}
```

### Create a Product

```bash
curl -X POST $GATEWAY_URL/api/products/create \
  -H "Content-Type: application/json" \
  -d '{"sku":"TEST-001","name":"Test Product","price":99.99,"stockLevel":10}'
```

### List Products

```bash
curl $GATEWAY_URL/api/products
```

### Create an Order

```bash
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{"refNumber":"ORD-001","customerId":"CUST-001","items":[{"sku":"TEST-001","quantity":2}]}'
```

### List Orders

```bash
curl $GATEWAY_URL/api/orders
```

## Essential Commands

### Check Status

```bash
# All pods
kubectl get pods

# All services
kubectl get svc

# Everything
kubectl get all
```

### View Logs

```bash
# Product Service
kubectl logs -l app=product-service --tail=50

# Order Service
kubectl logs -l app=order-service --tail=50

# API Gateway
kubectl logs -l app=api-gateway --tail=50

# Follow logs in real-time
kubectl logs -l app=product-service -f
```

### Access Gateway

```bash
# Method 1: Auto-open in browser
minikube service api-gateway

# Method 2: Get URL
minikube service api-gateway --url

# Method 3: Port forward
kubectl port-forward service/api-gateway 8080:8080
# Then access: http://localhost:8080
```

## Troubleshooting

### Pods Not Running?

```bash
# Check pod status
kubectl get pods

# Describe problematic pod
kubectl describe pod <pod-name>

# View pod logs
kubectl logs <pod-name>
```

### Image Not Found?

```bash
# Use Minikube's Docker
eval $(minikube docker-env)

# Rebuild images
docker build -t lab04-product-service:latest ./product-service
docker build -t lab04-order-service:latest ./order-service
docker build -t lab04-api-gateway:latest ./api-gateway

# Restart deployments
kubectl rollout restart deployment product-service
kubectl rollout restart deployment order-service
kubectl rollout restart deployment api-gateway
```

### Gateway Not Accessible?

```bash
# Check if gateway service exists
kubectl get svc api-gateway

# Check if pods are ready
kubectl get pods -l app=api-gateway

# Use minikube service (always works)
minikube service api-gateway
```

## Cleanup

```bash
# Remove all deployed resources
./cleanup.sh
```

Prompts for confirmation before deleting.

## What's Deployed?

| Service | Replicas | Port | Type |
|---------|----------|------|------|
| **Product Service** | 2 | 8080 | ClusterIP |
| **Order Service** | 2 | 8081 | ClusterIP |
| **API Gateway** | 2 | 8080 (30080) | NodePort |

## Architecture

```
Client
  │
  ↓
API Gateway (NodePort 30080)
  ├─→ Product Service (ClusterIP :8080)
  └─→ Order Service (ClusterIP :8081)
        └─→ Product Service (internal call)
```

## Files

- **deploy.sh** - Deployment automation script
- **cleanup.sh** - Cleanup script
- **KUBERNETES-DEPLOYMENT.md** - Full deployment guide
- **k8s/*.yaml** - Kubernetes manifests

## Next Steps

1. ✅ Deploy services: `./deploy.sh`
2. ✅ Test endpoints: `curl $GATEWAY_URL/api/products`
3. ⬜ Add databases (PostgreSQL)
4. ⬜ Add Eureka server
5. ⬜ Set up Ingress
6. ⬜ Configure monitoring

## More Information

- **Full Guide**: See [KUBERNETES-DEPLOYMENT.md](KUBERNETES-DEPLOYMENT.md)
- **Product Service**: See [k8s/README.md](k8s/README.md)
- **Order Service**: See [k8s/ORDERS-SERVICE-GUIDE.md](k8s/ORDERS-SERVICE-GUIDE.md)
- **API Gateway**: See [k8s/API-GATEWAY-GUIDE.md](k8s/API-GATEWAY-GUIDE.md)

## Summary

Your microservices are deployed to Kubernetes and accessible via the API Gateway at the NodePort. All inter-service communication uses Kubernetes DNS for service discovery. Clean up with `./cleanup.sh` when done.

Happy testing! 🚀
