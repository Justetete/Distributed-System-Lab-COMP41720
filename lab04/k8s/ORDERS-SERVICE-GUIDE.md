# Orders Microservice - Kubernetes Deployment Guide

## Overview

This guide explains the Orders microservice deployment and how it communicates with the Products service using Kubernetes DNS-based service discovery.

## Files

- `orders-deployment.yaml` - Deployment configuration for Orders service
- `orders-service.yaml` - Service configuration for Orders service

## Key Differences from Products Service

### Port Configuration
- **Order Service**: Port `8081` (line 30 in deployment)
- **Product Service**: Port `8080`

### Database Configuration
- **Order Service**: Connects to `order-db:5432/orderdb`
- **Product Service**: Connects to `product-db:5432/productdb`

### Inter-Service Communication
Order service depends on Product service for:
- Validating product SKUs
- Checking stock availability
- Adjusting stock levels during order checkout

## Kubernetes DNS-Based Service Discovery

### How Kubernetes DNS Works

Kubernetes automatically creates DNS records for every Service resource. This enables pod-to-pod communication using service names instead of IP addresses.

### DNS Resolution Pattern

```
<service-name>.<namespace>.svc.cluster.local
```

For services in the **same namespace**, you can use the short form:
```
<service-name>
```

### Example: Orders → Products Communication

#### 1. Service Configuration (orders-deployment.yaml:53-54)

```yaml
env:
- name: PRODUCT_SERVICE_URL
  value: "http://product-service:8080"
```

**Breakdown:**
- `product-service` - Kubernetes Service name (from products-service.yaml)
- `8080` - Product service port
- Full DNS: `product-service.default.svc.cluster.local:8080`

#### 2. How DNS Resolution Works

```
┌─────────────────┐
│  Order Service  │
│      Pod        │
└────────┬────────┘
         │
         │ 1. Request to http://product-service:8080
         ↓
┌─────────────────┐
│  Kubernetes DNS │
│   (CoreDNS)     │
└────────┬────────┘
         │ 2. Resolves "product-service" → ClusterIP (e.g., 10.96.100.50)
         ↓
┌─────────────────┐
│ Product Service │
│ (ClusterIP)     │
│  10.96.100.50   │
└────────┬────────┘
         │ 3. Load balances to one of the Product Service pods
         ↓
┌─────────────────┐
│ Product Service │
│      Pod 1      │
│  10.244.1.5     │
└─────────────────┘
```

#### 3. Request Flow

```bash
# Inside Order Service Pod:
curl http://product-service:8080/products/PROD-001

# DNS Resolves to:
# product-service.default.svc.cluster.local → 10.96.100.50 (ClusterIP)

# Service load balances to one of 2 Product Service pods:
# - product-service-7d9f8c-abc12 (10.244.1.5)
# - product-service-7d9f8c-def34 (10.244.1.6)

# Request reaches pod and returns product data
```

### Benefits of Kubernetes DNS

1. **No IP Hardcoding**: Service names remain constant even when pod IPs change
2. **Automatic Load Balancing**: Requests distributed across all healthy pods
3. **Service Discovery**: No need for external service registry
4. **Namespace Isolation**: Services can have same name in different namespaces

## Orders Service Configuration Explained

### orders-deployment.yaml

#### Environment Variables (lines 34-56)

```yaml
# Database Configuration
- name: SPRING_DATASOURCE_URL
  value: "jdbc:postgresql://order-db:5432/orderdb"

# Eureka Configuration (for hybrid discovery)
- name: EUREKA_CLIENT_SERVICEURL_DEFAULTZONE
  value: "http://eureka-server:8761/eureka/"

# Product Service Communication (Kubernetes DNS)
- name: PRODUCT_SERVICE_URL
  value: "http://product-service:8080"
```

**Key Point**: All service URLs use **service names**, not IPs:
- `order-db` - Database service
- `eureka-server` - Service registry
- `product-service` - Product microservice

#### Port Configuration (lines 30-32)

```yaml
ports:
- containerPort: 8081
  name: http
  protocol: TCP
```

Order service runs on **port 8081** internally.

#### Health Checks (lines 64-93)

All health checks use port **8081**:
- Startup Probe: `/actuator/health` on port 8081
- Liveness Probe: `/actuator/health/liveness` on port 8081
- Readiness Probe: `/actuator/health/readiness` on port 8081

### orders-service.yaml

#### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service  # DNS name: order-service.default.svc.cluster.local
spec:
  type: ClusterIP      # Internal-only access
  ports:
  - port: 8081         # Service listens on 8081
    targetPort: 8081   # Forwards to pod's port 8081
  selector:
    app: order-service # Routes to pods with this label
```

**Access Pattern:**
- Internal: `http://order-service:8081/orders`
- External: Not accessible (ClusterIP)

## Service Communication Examples

### 1. Order Service → Product Service (Feign Client)

**In Order Service Code:**
```java
@FeignClient(name = "product-service", url = "${PRODUCT_SERVICE_URL}")
public interface ProductServiceClient {
    @GetMapping("/products/{sku}")
    Product getProduct(@PathVariable String sku);

    @PostMapping("/products/adjust_stock")
    AdjustStockResponse adjustStock(@RequestBody List<AdjustStockRequest> requests);
}
```

**Environment Variable (set in deployment):**
```yaml
- name: PRODUCT_SERVICE_URL
  value: "http://product-service:8080"
```

**Runtime Behavior:**
```
Order Service Pod → DNS Lookup → product-service → ClusterIP → Product Pod
```

### 2. API Gateway → Order Service

```yaml
# In API Gateway configuration
spring.cloud.gateway.routes[1].uri=lb://order-service
spring.cloud.gateway.routes[1].predicates[0]=Path=/api/orders/**
```

**Request Flow:**
```
Client → API Gateway → DNS Lookup → order-service:8081 → Order Pod
```

## Testing Service Communication

### 1. Deploy Both Services

```bash
# Deploy Product Service first
kubectl apply -f k8s/products-deployment.yaml
kubectl apply -f k8s/products-service.yaml

# Wait for Product Service to be ready
kubectl wait --for=condition=ready pod -l app=product-service --timeout=300s

# Deploy Order Service
kubectl apply -f k8s/orders-deployment.yaml
kubectl apply -f k8s/orders-service.yaml

# Wait for Order Service to be ready
kubectl wait --for=condition=ready pod -l app=order-service --timeout=300s
```

### 2. Verify DNS Resolution

```bash
# Get an Order Service pod name
ORDER_POD=$(kubectl get pods -l app=order-service -o jsonpath='{.items[0].metadata.name}')

# Test DNS resolution inside the pod
kubectl exec $ORDER_POD -- nslookup product-service

# Expected output:
# Name:      product-service.default.svc.cluster.local
# Address 1: 10.96.100.50 product-service.default.svc.cluster.local
```

### 3. Test Service Communication

```bash
# Exec into Order Service pod
kubectl exec -it $ORDER_POD -- /bin/sh

# Test calling Product Service from inside Order pod
curl http://product-service:8080/products
curl http://product-service:8080/actuator/health

# Should return product data (empty array [] or product list)
```

### 4. Check Service Endpoints

```bash
# View Product Service endpoints
kubectl get endpoints product-service

# Should show 2 pod IPs (2 replicas)
# NAME              ENDPOINTS                       AGE
# product-service   10.244.1.5:8080,10.244.1.6:8080  5m

# View Order Service endpoints
kubectl get endpoints order-service

# Should show 2 pod IPs (2 replicas)
# NAME            ENDPOINTS                       AGE
# order-service   10.244.2.7:8081,10.244.2.8:8081  5m
```

## Complete Deployment Workflow

### Step 1: Build Docker Images

```bash
# Start Minikube
minikube start

# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build both images
docker build -t lab04-product-service:latest ./product-service
docker build -t lab04-order-service:latest ./order-service

# Verify images
docker images | grep lab04
```

### Step 2: Deploy Infrastructure Services

```bash
# Deploy databases (create these manifests first)
kubectl apply -f k8s/product-db-deployment.yaml
kubectl apply -f k8s/order-db-deployment.yaml

# Deploy Eureka (optional, for hybrid discovery)
kubectl apply -f k8s/eureka-deployment.yaml

# Wait for databases
kubectl wait --for=condition=ready pod -l app=product-db --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-db --timeout=300s
```

### Step 3: Deploy Microservices

```bash
# Deploy Product Service first (Order depends on it)
kubectl apply -f k8s/products-deployment.yaml
kubectl apply -f k8s/products-service.yaml

# Wait for Product Service
kubectl wait --for=condition=ready pod -l app=product-service --timeout=300s

# Deploy Order Service
kubectl apply -f k8s/orders-deployment.yaml
kubectl apply -f k8s/orders-service.yaml

# Wait for Order Service
kubectl wait --for=condition=ready pod -l app=order-service --timeout=300s
```

### Step 4: Verify Deployment

```bash
# Check all resources
kubectl get all -l tier=backend

# Check pod status
kubectl get pods -l app=product-service
kubectl get pods -l app=order-service

# Check service endpoints
kubectl get svc product-service order-service

# Check logs
kubectl logs -l app=order-service --tail=50
```

## Troubleshooting Inter-Service Communication

### Issue: Order Service Can't Reach Product Service

**Symptoms:**
```
Connection refused to http://product-service:8080
```

**Debug Steps:**

1. **Check Product Service is running:**
```bash
kubectl get pods -l app=product-service
kubectl get svc product-service
```

2. **Verify DNS resolution:**
```bash
ORDER_POD=$(kubectl get pods -l app=order-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec $ORDER_POD -- nslookup product-service
```

3. **Test connectivity:**
```bash
kubectl exec $ORDER_POD -- curl -v http://product-service:8080/actuator/health
```

4. **Check service endpoints:**
```bash
kubectl get endpoints product-service
# Should show pod IPs, not empty
```

5. **Verify network policies:**
```bash
kubectl get networkpolicies
# Ensure no policies block order → product communication
```

### Issue: Service Returns 503 or Connection Timeout

**Possible Causes:**
1. Product Service pods not ready (check readiness probe)
2. Product Service crashes (check logs)
3. Network policy blocking traffic
4. Service selector doesn't match pod labels

**Solutions:**
```bash
# Check pod readiness
kubectl get pods -l app=product-service -o wide

# Check pod logs for errors
kubectl logs -l app=product-service --tail=100

# Describe pod to see events
kubectl describe pod -l app=product-service

# Verify selector matches
kubectl get svc product-service -o yaml | grep selector
kubectl get pods -l app=product-service --show-labels
```

## Kubernetes vs Eureka Service Discovery

Your microservices use **both** Kubernetes DNS and Eureka:

### Kubernetes DNS (Native)
- **Scope**: Within Kubernetes cluster only
- **Registration**: Automatic via Service resources
- **Discovery**: Built-in DNS (CoreDNS)
- **Best for**: Pod-to-pod communication in K8s

### Eureka (Spring Cloud)
- **Scope**: Can work across multiple clusters
- **Registration**: Application-level registration
- **Discovery**: Eureka client queries registry
- **Best for**: Multi-cloud, hybrid deployments

### Hybrid Approach

```yaml
# Order Service can use BOTH:

# Option 1: Direct Kubernetes DNS (Simpler)
PRODUCT_SERVICE_URL=http://product-service:8080

# Option 2: Through Eureka (More flexible)
eureka.client.service-url.defaultZone=http://eureka-server:8761/eureka/
# Feign client discovers via Eureka
```

**Recommendation for Kubernetes:**
- Use **Kubernetes DNS** for simplicity
- Keep Eureka if you need cross-cluster discovery

## Resource Comparison

| Feature | Product Service | Order Service |
|---------|----------------|---------------|
| **Port** | 8080 | 8081 |
| **Replicas** | 2 | 2 |
| **Database** | product-db | order-db |
| **Memory Request** | 512Mi | 512Mi |
| **Memory Limit** | 1Gi | 1Gi |
| **CPU Request** | 250m | 250m |
| **CPU Limit** | 500m | 500m |
| **Dependencies** | product-db, eureka | order-db, eureka, product-service |

## Next Steps

1. ✅ Deploy Product Service
2. ✅ Deploy Order Service
3. ⬜ Deploy API Gateway
4. ⬜ Deploy PostgreSQL databases
5. ⬜ Deploy Eureka Server (optional)
6. ⬜ Create Ingress for external access
7. ⬜ Set up monitoring and logging

## Best Practices Applied

✅ **Service Discovery**: Using Kubernetes DNS for internal communication
✅ **Health Checks**: Comprehensive startup, liveness, and readiness probes
✅ **Resource Management**: Defined requests and limits
✅ **High Availability**: 2 replicas per service
✅ **Zero Downtime**: Rolling update strategy
✅ **Labels**: Consistent labeling for organization
✅ **ClusterIP**: Internal-only access for security
✅ **Environment Variables**: Externalized configuration

## Summary

The Orders microservice communicates with the Products microservice using **Kubernetes DNS-based service discovery**:

1. Order Service uses the service name `product-service` in its configuration
2. Kubernetes DNS automatically resolves `product-service` to the ClusterIP
3. The ClusterIP load balances requests across all healthy Product Service pods
4. No IP addresses are hardcoded; service names provide stable discovery
5. Changes to pod IPs (restarts, scaling) are handled automatically

This approach provides **reliable, automatic service discovery** without external dependencies!
