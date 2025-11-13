# API Gateway - Kubernetes Deployment Guide

## Overview

The API Gateway serves as the **single entry point** for all client requests to your microservices. It routes traffic to the appropriate backend services (Product Service, Order Service) and provides features like load balancing, service discovery, and centralized routing.

## Files

- `gateway-deployment.yaml` - Deployment configuration for API Gateway
- `gateway-service.yaml` - NodePort Service for external access

## Architecture

```
┌─────────────────────────────────────────────────────┐
│             External Client (Browser/curl)          │
└────────────────────┬────────────────────────────────┘
                     │
                     │ HTTP Request
                     ▼
┌─────────────────────────────────────────────────────┐
│              Minikube / Kubernetes                  │
│                                                     │
│  ┌───────────────────────────────────────────┐    │
│  │     NodePort Service (30080)              │    │
│  │     External Port: 30080                  │    │
│  │     Internal Port: 8080                   │    │
│  └──────────────┬────────────────────────────┘    │
│                 │                                   │
│         ┌───────▼──────────┐                       │
│         │   API Gateway    │  ClusterIP            │
│         │   (Service)      │  10.96.150.50:8080    │
│         └───────┬──────────┘                       │
│                 │                                   │
│          ┌──────┴──────┐                           │
│  ┌───────▼─────┐  ┌────▼────────┐                 │
│  │   Gateway   │  │   Gateway   │                 │
│  │   Pod 1     │  │   Pod 2     │                 │
│  │   :8080     │  │   :8080     │                 │
│  └──────┬──────┘  └──────┬──────┘                 │
│         │                 │                         │
│         │  Routes traffic to:                      │
│         │                                           │
│         ├─────────────► product-service:8080       │
│         │                                           │
│         └─────────────► order-service:8081         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Gateway Deployment Configuration

### gateway-deployment.yaml

#### 1. **Gateway-Specific Labels** (lines 5-8)
```yaml
metadata:
  name: api-gateway
  labels:
    app: api-gateway
    tier: gateway
    component: api-gateway
```
- `tier: gateway` - Identifies this as the gateway layer (vs backend)
- Different from backend services which use `tier: backend`

#### 2. **Environment Variables** (lines 34-56)

##### Eureka Configuration
```yaml
- name: EUREKA_CLIENT_SERVICEURL_DEFAULTZONE
  value: "http://eureka-server:8761/eureka/"
- name: EUREKA_INSTANCE_HOSTNAME
  value: "api-gateway"
```
- Registers with Eureka for service discovery
- Other services can discover the gateway

##### Gateway Discovery Configuration
```yaml
- name: SPRING_CLOUD_GATEWAY_DISCOVERY_LOCATOR_ENABLED
  value: "true"
- name: SPRING_CLOUD_GATEWAY_DISCOVERY_LOCATOR_LOWERCASESERVICEID
  value: "true"
```
- **ENABLED: true** - Automatically creates routes from Eureka-registered services
- **LOWERCASESERVICEID: true** - Converts service names to lowercase in URLs
- Example: `PRODUCT-SERVICE` becomes accessible at `/product-service/**`

##### Backend Service URLs
```yaml
- name: PRODUCT_SERVICE_URL
  value: "http://product-service:8080"
- name: ORDER_SERVICE_URL
  value: "http://order-service:8081"
```
- Uses **Kubernetes DNS** for service discovery
- Gateway can route directly or through Eureka

#### 3. **Port Configuration** (lines 30-32)
```yaml
ports:
- containerPort: 8080
  name: http
  protocol: TCP
```
- Gateway listens on port **8080**
- Same as Product Service (different from Order Service's 8081)

#### 4. **Resource Allocation** (lines 57-63)
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```
- Same resources as other services
- Gateway is typically lightweight (just routing)

## Gateway Service Configuration

### gateway-service.yaml

#### Service Type: NodePort (lines 11)

```yaml
spec:
  type: NodePort
```

**NodePort vs ClusterIP vs LoadBalancer:**

| Type | Access | Use Case | Port Range |
|------|--------|----------|------------|
| **NodePort** | External | Development (Minikube) | 30000-32767 |
| **ClusterIP** | Internal Only | Backend services | Any |
| **LoadBalancer** | External | Production (Cloud) | Any |

#### Port Configuration (lines 14-18)

```yaml
ports:
- name: http
  port: 8080         # Service port (internal)
  targetPort: 8080   # Pod port
  nodePort: 30080    # External port (Node)
  protocol: TCP
```

**Port Mapping Explained:**

```
External Request → NodePort (30080) → Service (8080) → Pod (8080)
```

- **nodePort: 30080** - Accessible from **outside** the cluster
- **port: 8080** - Service listens internally
- **targetPort: 8080** - Pod container port

**Why 30080?**
- Must be in range 30000-32767 (Kubernetes NodePort range)
- Easy to remember: 30080 maps to internal 8080
- Can be omitted (Kubernetes auto-assigns), but explicit is clearer

## Accessing the Gateway from Outside Kubernetes

### Method 1: Minikube Service Command (Recommended)

The **easiest** way to access the API Gateway in Minikube:

```bash
# Open API Gateway in browser (auto-opens browser with correct URL)
minikube service api-gateway

# Example output:
# |-----------|-------------|-------------|---------------------------|
# | NAMESPACE |    NAME     | TARGET PORT |            URL            |
# |-----------|-------------|-------------|---------------------------|
# | default   | api-gateway | http/8080   | http://192.168.49.2:30080 |
# |-----------|-------------|-------------|---------------------------|
# 🎉  Opening service default/api-gateway in default browser...
```

**Get URL without opening browser:**
```bash
minikube service api-gateway --url

# Output: http://192.168.49.2:30080
```

**Test from command line:**
```bash
# Get the URL
GATEWAY_URL=$(minikube service api-gateway --url)

# Test API Gateway health
curl $GATEWAY_URL/actuator/health

# Test product service through gateway
curl $GATEWAY_URL/api/products

# Test order service through gateway
curl $GATEWAY_URL/api/orders
```

### Method 2: Minikube IP + NodePort

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo $MINIKUBE_IP
# Output: 192.168.49.2

# Access gateway
curl http://192.168.49.2:30080/actuator/health
curl http://192.168.49.2:30080/api/products
curl http://192.168.49.2:30080/api/orders
```

**Store in environment variable:**
```bash
export GATEWAY_URL="http://$(minikube ip):30080"
echo $GATEWAY_URL

# Use it
curl $GATEWAY_URL/api/products
```

### Method 3: Port Forwarding (Alternative)

Useful if NodePort doesn't work or you want to use localhost:

```bash
# Forward local port 8080 to gateway service
kubectl port-forward service/api-gateway 8080:8080

# Access via localhost (in another terminal)
curl http://localhost:8080/actuator/health
curl http://localhost:8080/api/products
curl http://localhost:8080/api/orders
```

**Advantages:**
- Uses `localhost` instead of Minikube IP
- Works even if NodePort is disabled
- No need to remember NodePort number

**Disadvantages:**
- Must keep terminal open
- Only accessible from local machine
- Single connection (no load balancing)

### Method 4: Ingress (Production-Like)

For a more production-like setup:

```bash
# Enable Ingress addon
minikube addons enable ingress

# Create Ingress resource (example below)
kubectl apply -f k8s/gateway-ingress.yaml

# Access via hostname
curl http://myapp.local/api/products
```

**Example Ingress (gateway-ingress.yaml):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-gateway-ingress
spec:
  rules:
  - host: myapp.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8080
```

## Complete Deployment Workflow

### Step 1: Build Docker Image

```bash
# Start Minikube
minikube start

# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build Gateway image
docker build -t lab04-api-gateway:latest ./api-gateway

# Verify
docker images | grep api-gateway
```

### Step 2: Deploy Dependencies

API Gateway depends on these services:

```bash
# 1. Deploy Eureka (optional but recommended)
kubectl apply -f k8s/eureka-deployment.yaml
kubectl apply -f k8s/eureka-service.yaml

# 2. Deploy Product Service
kubectl apply -f k8s/products-deployment.yaml
kubectl apply -f k8s/products-service.yaml

# 3. Deploy Order Service
kubectl apply -f k8s/orders-deployment.yaml
kubectl apply -f k8s/orders-service.yaml

# Wait for all services to be ready
kubectl wait --for=condition=ready pod -l app=product-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-service --timeout=300s
```

### Step 3: Deploy API Gateway

```bash
# Deploy Gateway
kubectl apply -f k8s/gateway-deployment.yaml
kubectl apply -f k8s/gateway-service.yaml

# Watch pods starting
kubectl get pods -l app=api-gateway -w

# Wait for gateway to be ready
kubectl wait --for=condition=ready pod -l app=api-gateway --timeout=300s
```

### Step 4: Verify Deployment

```bash
# Check all gateway resources
kubectl get all -l app=api-gateway

# Expected output:
# NAME                              READY   STATUS    RESTARTS   AGE
# pod/api-gateway-xxxxx-yyyyy       1/1     Running   0          2m
# pod/api-gateway-xxxxx-zzzzz       1/1     Running   0          2m
#
# NAME                  TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
# service/api-gateway   NodePort   10.96.150.50    <none>        8080:30080/TCP   2m
#
# NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
# deployment.apps/api-gateway   2/2     2            2           2m

# Check gateway logs
kubectl logs -l app=api-gateway --tail=50

# Check gateway health
kubectl exec -it $(kubectl get pod -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') -- curl localhost:8080/actuator/health
```

## Testing the API Gateway

### 1. Access Gateway Externally

```bash
# Get gateway URL
GATEWAY_URL=$(minikube service api-gateway --url)
echo "Gateway URL: $GATEWAY_URL"

# Test gateway health
curl $GATEWAY_URL/actuator/health

# Expected response:
# {"status":"UP"}
```

### 2. Test Product Service Routes

```bash
# List all products (through gateway)
curl $GATEWAY_URL/api/products

# Create a product
curl -X POST $GATEWAY_URL/api/products/create \
  -H "Content-Type: application/json" \
  -d '{"sku":"PROD-001","name":"Test Product","price":29.99,"stockLevel":100}'

# Get specific product
curl $GATEWAY_URL/api/products/PROD-001
```

### 3. Test Order Service Routes

```bash
# List all orders (through gateway)
curl $GATEWAY_URL/api/orders

# Create an order
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "refNumber": "ORD-001",
    "customerId": "CUST-001",
    "items": [
      {
        "sku": "PROD-001",
        "quantity": 2
      }
    ]
  }'

# Get specific order
curl $GATEWAY_URL/api/orders/ORD-001
```

### 4. Test Gateway Routes

```bash
# View all configured routes
curl $GATEWAY_URL/actuator/gateway/routes

# View gateway route details
curl $GATEWAY_URL/actuator/gateway/routes/product-service

# Refresh gateway routes
curl -X POST $GATEWAY_URL/actuator/gateway/refresh
```

## Gateway Routing Configuration

The gateway routes are configured in `api-gateway/src/main/resources/application.properties`:

```properties
# Product Service Routes
spring.cloud.gateway.routes[0].id=product-service
spring.cloud.gateway.routes[0].uri=lb://product-service
spring.cloud.gateway.routes[0].predicates[0]=Path=/api/products/**
spring.cloud.gateway.routes[0].filters[0]=StripPrefix=1

# Order Service Routes
spring.cloud.gateway.routes[1].id=order-service
spring.cloud.gateway.routes[1].uri=lb://order-service
spring.cloud.gateway.routes[1].predicates[0]=Path=/api/orders/**
spring.cloud.gateway.routes[1].filters[0]=StripPrefix=1
```

**How Routing Works:**

```
1. Client Request: http://gateway:30080/api/products/PROD-001

2. Gateway matches route:
   - Predicate: Path=/api/products/**  ✓ Match
   - Route ID: product-service

3. StripPrefix filter removes "/api":
   - Before: /api/products/PROD-001
   - After:  /products/PROD-001

4. Gateway forwards to: http://product-service:8080/products/PROD-001

5. Product Service responds → Gateway returns to client
```

## NodePort vs LoadBalancer vs Ingress

### When to Use Each

| Scenario | Service Type | Reason |
|----------|--------------|--------|
| **Minikube/Local Dev** | NodePort | Simple, built-in, no external dependencies |
| **Cloud (AWS/GCP/Azure)** | LoadBalancer | Automatic cloud load balancer provisioning |
| **Production Multi-Service** | Ingress | Advanced routing, SSL/TLS, single entry point |
| **Testing/Debug** | Port Forward | Quick access without changing configs |

### Converting to LoadBalancer (Cloud)

For cloud deployments, change service type:

```yaml
# gateway-service.yaml (Cloud version)
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  type: LoadBalancer  # Changed from NodePort
  selector:
    app: api-gateway
  ports:
  - name: http
    port: 80           # External port (standard HTTP)
    targetPort: 8080   # Pod port
    protocol: TCP
```

**Advantages:**
- Cloud provider automatically provisions load balancer
- Gets public IP address
- Standard ports (80/443)
- Better for production

## Troubleshooting

### Gateway Not Accessible from Outside

**Issue:** Cannot access http://MINIKUBE_IP:30080

**Solutions:**

1. **Verify NodePort Service:**
```bash
kubectl get svc api-gateway
# Should show TYPE: NodePort and PORT(S): 8080:30080/TCP
```

2. **Check Minikube IP:**
```bash
minikube ip
# Should return IP like 192.168.49.2
```

3. **Test from inside cluster:**
```bash
kubectl run test-pod --rm -it --image=busybox -- wget -O- http://api-gateway:8080/actuator/health
```

4. **Use minikube service:**
```bash
# This should work even if direct access doesn't
minikube service api-gateway
```

### Gateway Can't Reach Backend Services

**Issue:** Gateway returns 503 Service Unavailable

**Check service discovery:**

```bash
# Check if backend services are registered
kubectl get svc product-service order-service

# Check if pods are ready
kubectl get pods -l app=product-service
kubectl get pods -l app=order-service

# Test DNS from gateway pod
GATEWAY_POD=$(kubectl get pod -l app=api-gateway -o jsonpath='{.items[0].metadata.name}')
kubectl exec $GATEWAY_POD -- nslookup product-service
kubectl exec $GATEWAY_POD -- curl http://product-service:8080/actuator/health
```

### Route Not Found (404)

**Issue:** Gateway returns 404 for /api/products

**Debug steps:**

```bash
# Check configured routes
curl $(minikube service api-gateway --url)/actuator/gateway/routes

# Check gateway logs
kubectl logs -l app=api-gateway --tail=100

# Verify route configuration
kubectl exec $(kubectl get pod -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') -- env | grep GATEWAY
```

## Security Considerations

For production deployments:

1. **Remove NodePort** - Use LoadBalancer or Ingress
2. **Add TLS/SSL** - Use Ingress with cert-manager
3. **Add Authentication** - JWT validation at gateway
4. **Rate Limiting** - Prevent abuse
5. **CORS Configuration** - Control cross-origin requests

## Performance Tips

1. **Increase Replicas** during high traffic:
```bash
kubectl scale deployment api-gateway --replicas=5
```

2. **Adjust Resources** for traffic patterns:
```yaml
resources:
  requests:
    memory: "1Gi"    # Increased
    cpu: "500m"      # Increased
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

3. **Enable Connection Pooling** in gateway config

## Summary

### Access Methods Comparison

| Method | Command | When to Use |
|--------|---------|-------------|
| **minikube service** | `minikube service api-gateway` | Easiest, recommended for Minikube |
| **Minikube IP + NodePort** | `curl http://$(minikube ip):30080` | Scripting, automation |
| **Port Forward** | `kubectl port-forward svc/api-gateway 8080:8080` | Localhost access, debugging |
| **Ingress** | `curl http://myapp.local` | Production-like setup |

### Key Points

1. ✅ **API Gateway is the single entry point** for all client requests
2. ✅ **NodePort (30080)** exposes gateway externally in Minikube
3. ✅ **Kubernetes DNS** for backend service discovery (product-service, order-service)
4. ✅ **Load balancing** across gateway pods automatically
5. ✅ **StripPrefix filter** removes /api prefix before forwarding

### Quick Access

```bash
# The fastest way to access your gateway:
minikube service api-gateway

# Or get the URL:
export GATEWAY_URL=$(minikube service api-gateway --url)
curl $GATEWAY_URL/api/products
```

Your API Gateway is now deployed and accessible from outside the Kubernetes cluster!
