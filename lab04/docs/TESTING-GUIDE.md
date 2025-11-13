# Kubernetes Testing Strategy - Comprehensive Guide

This guide provides step-by-step testing procedures to verify your microservices deployment works correctly.

## Table of Contents

1. [Deployment and Verification](#deployment-and-verification)
2. [Inter-Service Communication Testing](#inter-service-communication-testing)
3. [Complete Request Flow Testing](#complete-request-flow-testing)
4. [Kubernetes Features Demonstration](#kubernetes-features-demonstration)
5. [Troubleshooting](#troubleshooting)
6. [Testing Checklist for Lab Report](#testing-checklist-for-lab-report)

---

## 1. Deployment and Verification

### Step 1: Deploy All Services

```bash
# Use automated deployment script
./deploy.sh
```

**Expected Output:**
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

### Step 2: Verify All Pods are Running

```bash
# Check pod status
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

**Verification Checklist:**
- ✅ All pods show `STATUS: Running`
- ✅ All pods show `READY: 1/1`
- ✅ `RESTARTS` should be 0 or low
- ✅ 2 replicas per service

**If pods are not running:**
```bash
# Check pod details
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name>
```

### Step 3: Check Service Endpoints

```bash
# List all services
kubectl get svc

# Expected output:
# NAME              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
# kubernetes        ClusterIP   10.96.0.1        <none>        443/TCP          10m
# product-service   ClusterIP   10.96.100.50     <none>        8080/TCP         2m
# order-service     ClusterIP   10.96.200.100    <none>        8081/TCP         2m
# api-gateway       NodePort    10.96.150.50     <none>        8080:30080/TCP   2m
```

**Verification Checklist:**
- ✅ `product-service` has ClusterIP and port 8080
- ✅ `order-service` has ClusterIP and port 8081
- ✅ `api-gateway` has NodePort and port 8080:30080

```bash
# Check service endpoints (shows pod IPs)
kubectl get endpoints

# Expected output:
# NAME              ENDPOINTS                                AGE
# product-service   10.244.1.5:8080,10.244.1.6:8080         2m
# order-service     10.244.2.7:8081,10.244.2.8:8081         2m
# api-gateway       10.244.3.9:8080,10.244.3.10:8080        2m
```

**Verification:**
- ✅ Each service shows 2 endpoints (2 replicas)
- ✅ Endpoints are not empty

### Step 4: Verify ConfigMaps

```bash
# List ConfigMaps
kubectl get configmaps

# Expected output:
# NAME                      DATA   AGE
# product-service-config    15     2m
# order-service-config      18     2m
# api-gateway-config        25     2m

# View ConfigMap details
kubectl describe configmap product-service-config
```

### Step 5: Access Gateway from Local Machine

#### Method 1: Using minikube service (Recommended)

```bash
# Get gateway URL
minikube service api-gateway --url

# Example output: http://192.168.49.2:30080

# Store in variable
export GATEWAY_URL=$(minikube service api-gateway --url)
echo "Gateway URL: $GATEWAY_URL"
```

#### Method 2: Using Minikube IP + NodePort

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# Gateway is accessible at: http://MINIKUBE_IP:30080
export GATEWAY_URL="http://$MINIKUBE_IP:30080"
echo "Gateway URL: $GATEWAY_URL"
```

#### Test Gateway Health

```bash
# Test gateway health endpoint
curl $GATEWAY_URL/actuator/health

# Expected response:
# {"status":"UP"}
```

**If health check fails:**
```bash
# Check gateway pods
kubectl get pods -l app=api-gateway

# Check gateway logs
kubectl logs -l app=api-gateway --tail=50

# Wait a moment and retry (pods may still be starting)
sleep 30
curl $GATEWAY_URL/actuator/health
```

---

## 2. Inter-Service Communication Testing

### Test 1: DNS Resolution Between Services

#### Check Product Service → Order Service DNS

```bash
# Get a product service pod name
PRODUCT_POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')
echo "Product Pod: $PRODUCT_POD"

# Test DNS resolution for order-service
kubectl exec $PRODUCT_POD -- nslookup order-service

# Expected output:
# Server:         10.96.0.10
# Address:        10.96.0.10:53
#
# Name:   order-service.default.svc.cluster.local
# Address: 10.96.200.100
```

**Verification:**
- ✅ DNS resolves successfully
- ✅ Shows ClusterIP address

#### Check Order Service → Product Service DNS

```bash
# Get an order service pod name
ORDER_POD=$(kubectl get pods -l app=order-service -o jsonpath='{.items[0].metadata.name}')
echo "Order Pod: $ORDER_POD"

# Test DNS resolution for product-service
kubectl exec $ORDER_POD -- nslookup product-service

# Expected output:
# Name:   product-service.default.svc.cluster.local
# Address: 10.96.100.50
```

### Test 2: HTTP Communication Between Services

#### Order Service → Product Service

```bash
# From order pod, curl product service
kubectl exec $ORDER_POD -- curl -s http://product-service:8080/actuator/health

# Expected response:
# {"status":"UP"}

# Test product endpoint
kubectl exec $ORDER_POD -- curl -s http://product-service:8080/products

# Expected response:
# []  (empty array if no products created yet)
```

**Verification:**
- ✅ HTTP request succeeds
- ✅ Returns valid JSON response
- ✅ No connection errors

#### Gateway → Product Service

```bash
# Get gateway pod
GATEWAY_POD=$(kubectl get pods -l app=api-gateway -o jsonpath='{.items[0].metadata.name}')

# Test gateway to product service
kubectl exec $GATEWAY_POD -- curl -s http://product-service:8080/actuator/health

# Expected: {"status":"UP"}
```

#### Gateway → Order Service

```bash
# Test gateway to order service
kubectl exec $GATEWAY_POD -- curl -s http://order-service:8081/actuator/health

# Expected: {"status":"UP"}
```

### Test 3: View Logs to Verify Communication

#### Check Order Service Logs (Feign calls to Product Service)

```bash
# View order service logs with filtering
kubectl logs -l app=order-service --tail=100 | grep -i "feign\|product"

# Look for:
# - Feign client configuration
# - HTTP requests to product-service
# - Successful responses
```

#### Check Product Service Logs (Incoming requests)

```bash
# View product service logs
kubectl logs -l app=product-service --tail=50

# Look for:
# - Incoming HTTP requests
# - Database operations
# - No error messages
```

#### Check Gateway Logs (Routing)

```bash
# View gateway logs
kubectl logs -l app=api-gateway --tail=50 | grep -i "route"

# Look for:
# - Route mappings
# - Forwarding requests
# - Load balancing
```

### Test 4: Network Communication Test

```bash
# Install debugging pod with network tools
kubectl run nettest --rm -it --image=nicolaka/netshoot -- /bin/bash

# Inside the pod:
# Test product service
curl http://product-service:8080/actuator/health

# Test order service
curl http://order-service:8081/actuator/health

# Test gateway
curl http://api-gateway:8080/actuator/health

# Exit
exit
```

---

## 3. Complete Request Flow Testing

### Test Flow: Gateway → Order Service → Product Service

This demonstrates the complete microservices communication chain.

#### Step 1: Create Products via Gateway

```bash
# Create first product
curl -X POST $GATEWAY_URL/api/products/create \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "MacBook Pro 16",
    "price": 2499.99,
    "stockLevel": 10
  }'

# Expected response: JSON with created product
```

```bash
# Create multiple products
curl -X POST $GATEWAY_URL/api/products/bulk_create \
  -H "Content-Type: application/json" \
  -d '[
    {
      "sku": "PHONE-001",
      "name": "iPhone 15 Pro",
      "price": 999.99,
      "stockLevel": 50
    },
    {
      "sku": "TABLET-001",
      "name": "iPad Air",
      "price": 599.99,
      "stockLevel": 30
    },
    {
      "sku": "WATCH-001",
      "name": "Apple Watch Ultra",
      "price": 799.99,
      "stockLevel": 20
    }
  ]'
```

#### Step 2: Verify Products Created

```bash
# List all products
curl $GATEWAY_URL/api/products

# Expected: JSON array with 4 products

# Get specific product
curl $GATEWAY_URL/api/products/LAPTOP-001

# Expected: JSON object with product details
```

**Verification:**
- ✅ Products created successfully
- ✅ Can retrieve product list
- ✅ Can retrieve individual products

#### Step 3: Check Product Stock Levels

```bash
# Check initial stock for LAPTOP-001
curl $GATEWAY_URL/api/products/LAPTOP-001 | grep -o '"stockLevel":[0-9]*'

# Expected: "stockLevel":10
```

#### Step 4: Create Order (Tests Order → Product Communication)

```bash
# Create an order
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "refNumber": "ORD-2025-001",
    "customerId": "CUST-123",
    "items": [
      {
        "sku": "LAPTOP-001",
        "quantity": 2
      },
      {
        "sku": "PHONE-001",
        "quantity": 3
      }
    ]
  }'

# Expected: JSON with created order
```

**What happens internally:**
1. Gateway receives request → routes to Order Service
2. Order Service validates order
3. Order Service calls Product Service to check stock
4. Product Service verifies stock availability
5. Order Service calls Product Service to adjust stock
6. Product Service reduces stock levels
7. Order Service saves order to database
8. Response returned through Gateway to client

#### Step 5: Verify Stock Adjustment

```bash
# Check updated stock for LAPTOP-001
curl $GATEWAY_URL/api/products/LAPTOP-001 | grep -o '"stockLevel":[0-9]*'

# Expected: "stockLevel":8 (reduced by 2)

# Check PHONE-001 stock
curl $GATEWAY_URL/api/products/PHONE-001 | grep -o '"stockLevel":[0-9]*'

# Expected: "stockLevel":47 (reduced by 3)
```

**Verification:**
- ✅ Stock levels decreased correctly
- ✅ Order creation triggered product updates
- ✅ Inter-service communication working

#### Step 6: Verify Order Created

```bash
# List all orders
curl $GATEWAY_URL/api/orders

# Expected: JSON array with 1 order

# Get specific order
curl $GATEWAY_URL/api/orders/ORD-2025-001

# Expected: JSON object with order details including items
```

#### Step 7: Monitor Logs During Request

```bash
# Watch gateway logs in real-time
kubectl logs -f -l app=api-gateway &

# Watch order service logs
kubectl logs -f -l app=order-service &

# Watch product service logs
kubectl logs -f -l app=product-service &

# Make a request
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "refNumber": "ORD-2025-002",
    "customerId": "CUST-456",
    "items": [{"sku": "TABLET-001", "quantity": 1}]
  }'

# Stop log watching (Ctrl+C for each)
```

**Look for in logs:**
- Gateway: Route matching and forwarding
- Order Service: Feign client calls to Product Service
- Product Service: Stock adjustment operations

---

## 4. Kubernetes Features Demonstration

### Feature 1: Scaling Deployments

#### Scale Up

```bash
# Scale product service to 4 replicas
kubectl scale deployment product-service --replicas=4

# Watch pods scaling
kubectl get pods -l app=product-service -w

# Wait for all pods to be running
kubectl wait --for=condition=ready pod -l app=product-service --timeout=120s

# Verify
kubectl get pods -l app=product-service
```

**Expected output:**
```
NAME                               READY   STATUS    RESTARTS   AGE
product-service-7d9f8c-abc12       1/1     Running   0          5m
product-service-7d9f8c-def34       1/1     Running   0          5m
product-service-7d9f8c-new01       1/1     Running   0          30s
product-service-7d9f8c-new02       1/1     Running   0          30s
```

**Test load balancing:**
```bash
# Make multiple requests and check which pod handles them
for i in {1..10}; do
  curl -s $GATEWAY_URL/api/products | head -1
done

# Check access logs across all pods
kubectl logs -l app=product-service --tail=5
```

#### Scale Down

```bash
# Scale back to 2 replicas
kubectl scale deployment product-service --replicas=2

# Watch pods terminating
kubectl get pods -l app=product-service -w

# Verify
kubectl get pods -l app=product-service
```

**Verification:**
- ✅ Pods scale up/down successfully
- ✅ Service remains available during scaling
- ✅ Load balancing works across pods

### Feature 2: Rolling Update Simulation

#### Simulate Configuration Update

```bash
# 1. Check current log level
kubectl get configmap product-service-config -o jsonpath='{.data.LOGGING_LEVEL_ROOT}'
# Output: INFO

# 2. Update log level
kubectl patch configmap product-service-config \
  -p '{"data":{"LOGGING_LEVEL_ROOT":"DEBUG"}}'

# 3. Trigger rolling update
kubectl rollout restart deployment product-service

# 4. Watch rolling update
kubectl rollout status deployment product-service

# Expected output:
# Waiting for deployment "product-service" rollout to finish: 1 out of 2 new replicas have been updated...
# Waiting for deployment "product-service" rollout to finish: 1 old replicas are pending termination...
# deployment "product-service" successfully rolled out
```

#### Verify Zero Downtime

```bash
# Start continuous requests in background
while true; do
  curl -s $GATEWAY_URL/api/products > /dev/null && echo "Success" || echo "Failed"
  sleep 1
done &
CURL_PID=$!

# Trigger rolling update
kubectl rollout restart deployment product-service

# Watch output - should see no failures
# Stop after rollout completes
kill $CURL_PID
```

**Verification:**
- ✅ Rolling update completes successfully
- ✅ No downtime during update
- ✅ New configuration applied

#### Check Rollout History

```bash
# View rollout history
kubectl rollout history deployment product-service

# Expected output:
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>

# View specific revision
kubectl rollout history deployment product-service --revision=2
```

#### Rollback (Optional Test)

```bash
# Rollback to previous version
kubectl rollout undo deployment product-service

# Watch rollback
kubectl rollout status deployment product-service

# Verify rollback
kubectl get configmap product-service-config -o jsonpath='{.data.LOGGING_LEVEL_ROOT}'
# Should show original value
```

### Feature 3: Check Resource Usage

#### View Pod Resource Usage

```bash
# Enable metrics server (if not enabled)
minikube addons enable metrics-server

# Wait for metrics to be available (30-60 seconds)
sleep 60

# View pod resource usage
kubectl top pods

# Expected output:
# NAME                               CPU(cores)   MEMORY(bytes)
# product-service-7d9f8c-abc12       10m          450Mi
# product-service-7d9f8c-def34       8m           420Mi
# order-service-5b8d7f-xyz89         12m          480Mi
# order-service-5b8d7f-qwe45         9m           440Mi
# api-gateway-9c6f5e-uvw78           15m          350Mi
# api-gateway-9c6f5e-rst56           13m          340Mi
```

#### View Node Resource Usage

```bash
# View node resources
kubectl top nodes

# Expected output:
# NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# minikube   500m         25%    4000Mi          50%
```

#### Check Resource Limits and Requests

```bash
# View resource configuration
kubectl describe deployment product-service | grep -A 10 "Limits\|Requests"

# Expected output:
#     Limits:
#       cpu:     500m
#       memory:  1Gi
#     Requests:
#       cpu:     250m
#       memory:  512Mi
```

### Feature 4: Pod Auto-Healing

#### Simulate Pod Failure

```bash
# Delete a pod (Kubernetes will recreate it)
PRODUCT_POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')
echo "Deleting pod: $PRODUCT_POD"

kubectl delete pod $PRODUCT_POD

# Watch pod recreation
kubectl get pods -l app=product-service -w

# Expected: New pod created automatically
```

**Verification:**
- ✅ Pod is deleted
- ✅ New pod created immediately
- ✅ Service remains available (other replica handles traffic)

### Feature 5: Service Discovery

#### Test Service Discovery Updates

```bash
# Scale up product service
kubectl scale deployment product-service --replicas=5

# Check endpoints immediately
kubectl get endpoints product-service

# Expected: 5 pod IPs listed

# Test from order service (should automatically discover all pods)
ORDER_POD=$(kubectl get pods -l app=order-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec $ORDER_POD -- nslookup product-service

# Make requests (load balanced across all 5 pods)
for i in {1..10}; do
  curl -s $GATEWAY_URL/api/products | head -1
done
```

---

## 5. Troubleshooting

### Issue 1: Pods Not Starting

#### Check Pod Status

```bash
# Get pod status
kubectl get pods

# Common statuses:
# - Pending: Waiting for resources/scheduling
# - ContainerCreating: Pulling image/creating container
# - ImagePullBackOff: Cannot pull image
# - CrashLoopBackOff: Container keeps crashing
# - Error: Container failed
```

#### Debug ImagePullBackOff

```bash
# Describe pod
kubectl describe pod <pod-name> | grep -A 10 "Events"

# Look for:
# Failed to pull image "lab04-product-service:latest": rpc error: code = Unknown desc = Error response from daemon: pull access denied

# Fix: Ensure using Minikube's Docker
eval $(minikube docker-env)
docker images | grep lab04

# If image missing, rebuild
docker build -t lab04-product-service:latest ./product-service

# Delete pod to retry
kubectl delete pod <pod-name>
```

#### Debug CrashLoopBackOff

```bash
# View pod logs
kubectl logs <pod-name>

# View previous container logs (if restarted)
kubectl logs <pod-name> --previous

# Common causes:
# 1. Application error (check logs)
# 2. Missing ConfigMap
# 3. Cannot connect to database
# 4. Port already in use
```

#### Check Pod Events

```bash
# View all events
kubectl get events --sort-by=.metadata.creationTimestamp

# View events for specific pod
kubectl describe pod <pod-name> | grep -A 20 "Events"
```

### Issue 2: Service Not Accessible

#### Check Service Configuration

```bash
# Verify service exists
kubectl get svc product-service

# Check service details
kubectl describe svc product-service

# Verify selector matches pod labels
kubectl get svc product-service -o jsonpath='{.spec.selector}'
kubectl get pods -l app=product-service --show-labels
```

#### Check Service Endpoints

```bash
# View endpoints
kubectl get endpoints product-service

# If empty, pods don't match selector or aren't ready
# Check pod readiness
kubectl get pods -l app=product-service

# Check readiness probe
kubectl describe pod <pod-name> | grep -A 5 "Readiness"
```

#### Test Service from Inside Cluster

```bash
# Run test pod
kubectl run test-curl --rm -it --image=curlimages/curl -- /bin/sh

# Inside pod:
curl http://product-service:8080/actuator/health
curl http://order-service:8081/actuator/health
curl http://api-gateway:8080/actuator/health

exit
```

### Issue 3: Gateway Not Accessible Externally

#### Check NodePort Service

```bash
# Verify NodePort service
kubectl get svc api-gateway

# Should show TYPE: NodePort and PORT(S): 8080:30080/TCP

# Get Minikube IP
minikube ip

# Test connection
curl http://$(minikube ip):30080/actuator/health
```

#### Alternative: Use Port Forward

```bash
# Forward local port to service
kubectl port-forward service/api-gateway 8080:8080

# In another terminal
curl http://localhost:8080/actuator/health
```

### Issue 4: Inter-Service Communication Failing

#### Test DNS Resolution

```bash
# Get pod name
POD=$(kubectl get pods -l app=order-service -o jsonpath='{.items[0].metadata.name}')

# Test DNS
kubectl exec $POD -- nslookup product-service

# Should resolve successfully
```

#### Test HTTP Connectivity

```bash
# Test connection
kubectl exec $POD -- curl -v http://product-service:8080/actuator/health

# Look for:
# - DNS resolution
# - TCP connection
# - HTTP response
```

#### Check Network Policies

```bash
# Check if network policies are blocking
kubectl get networkpolicies

# If any exist, verify they allow traffic
kubectl describe networkpolicy <policy-name>
```

### Issue 5: Configuration Not Applied

#### Check ConfigMap Exists

```bash
# List ConfigMaps
kubectl get configmaps

# View ConfigMap
kubectl get configmap product-service-config -o yaml
```

#### Verify Pod Using ConfigMap

```bash
# Check pod environment variables
POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- env | grep -E 'SPRING|LOGGING'

# Should show all ConfigMap values
```

#### Trigger ConfigMap Reload

```bash
# Restart deployment
kubectl rollout restart deployment product-service
```

---

## 6. Testing Checklist for Lab Report

### ✅ Pre-Deployment Checks

- [ ] Minikube is running: `minikube status`
- [ ] kubectl is configured: `kubectl cluster-info`
- [ ] Docker images built: `docker images | grep lab04`

### ✅ Deployment Verification

- [ ] ConfigMaps deployed: `kubectl get configmaps`
- [ ] All deployments created: `kubectl get deployments`
- [ ] All pods running: `kubectl get pods` (STATUS: Running, READY: 1/1)
- [ ] All services created: `kubectl get svc`
- [ ] Service endpoints populated: `kubectl get endpoints`

### ✅ Health Checks

- [ ] Product Service health: `curl http://$(minikube service api-gateway --url)/api/products`
- [ ] Order Service health: `curl http://$(minikube service api-gateway --url)/api/orders`
- [ ] Gateway health: `curl http://$(minikube service api-gateway --url)/actuator/health`

### ✅ Inter-Service Communication

- [ ] DNS resolution working:
  ```bash
  kubectl exec <order-pod> -- nslookup product-service
  ```
- [ ] HTTP communication working:
  ```bash
  kubectl exec <order-pod> -- curl http://product-service:8080/actuator/health
  ```
- [ ] Logs show successful communication:
  ```bash
  kubectl logs -l app=order-service | grep -i "product\|feign"
  ```

### ✅ Complete Request Flow

- [ ] Create products via Gateway:
  ```bash
  curl -X POST $(minikube service api-gateway --url)/api/products/create \
    -H "Content-Type: application/json" \
    -d '{"sku":"TEST-001","name":"Test","price":99.99,"stockLevel":10}'
  ```
- [ ] List products:
  ```bash
  curl $(minikube service api-gateway --url)/api/products
  ```
- [ ] Create order (triggers inter-service call):
  ```bash
  curl -X POST $(minikube service api-gateway --url)/api/orders/checkout \
    -H "Content-Type: application/json" \
    -d '{"refNumber":"ORD-001","customerId":"CUST-001","items":[{"sku":"TEST-001","quantity":2}]}'
  ```
- [ ] Verify stock adjusted:
  ```bash
  curl $(minikube service api-gateway --url)/api/products/TEST-001
  # Check stockLevel reduced by 2
  ```
- [ ] List orders:
  ```bash
  curl $(minikube service api-gateway --url)/api/orders
  ```

### ✅ Kubernetes Features

- [ ] Scaling works:
  ```bash
  kubectl scale deployment product-service --replicas=4
  kubectl get pods -l app=product-service
  ```
- [ ] Rolling update works:
  ```bash
  kubectl rollout restart deployment product-service
  kubectl rollout status deployment product-service
  ```
- [ ] Auto-healing works:
  ```bash
  kubectl delete pod <pod-name>
  kubectl get pods -l app=product-service
  # New pod created automatically
  ```
- [ ] Resource usage visible:
  ```bash
  kubectl top pods
  ```
- [ ] ConfigMap updates work:
  ```bash
  kubectl edit configmap product-service-config
  kubectl rollout restart deployment product-service
  ```

### ✅ Load Balancing

- [ ] Multiple replicas running: `kubectl get pods -l app=product-service`
- [ ] Load distributed across pods:
  ```bash
  for i in {1..10}; do curl -s $(minikube service api-gateway --url)/api/products; done
  kubectl logs -l app=product-service --tail=20
  # Check logs show requests distributed
  ```

### ✅ Configuration Management

- [ ] ConfigMaps exist: `kubectl get configmaps`
- [ ] Pods use ConfigMaps: `kubectl exec <pod> -- env | grep SPRING`
- [ ] Can update config without rebuild:
  ```bash
  kubectl patch configmap product-service-config -p '{"data":{"LOGGING_LEVEL_ROOT":"DEBUG"}}'
  kubectl rollout restart deployment product-service
  ```

### ✅ Documentation for Lab Report

**Include these screenshots/outputs:**

1. **Deployment Success:**
   ```bash
   kubectl get all
   ```

2. **All Pods Running:**
   ```bash
   kubectl get pods -o wide
   ```

3. **Service Endpoints:**
   ```bash
   kubectl get svc
   kubectl get endpoints
   ```

4. **Successful API Request:**
   ```bash
   curl $(minikube service api-gateway --url)/api/products
   ```

5. **Inter-Service Communication:**
   ```bash
   kubectl logs -l app=order-service --tail=50
   ```

6. **Scaling Demonstration:**
   ```bash
   kubectl scale deployment product-service --replicas=4
   kubectl get pods -l app=product-service
   ```

7. **Rolling Update:**
   ```bash
   kubectl rollout status deployment product-service
   ```

8. **Resource Usage:**
   ```bash
   kubectl top pods
   ```

9. **ConfigMap Usage:**
   ```bash
   kubectl get configmap product-service-config -o yaml
   ```

10. **Complete Request Flow:**
    - Create product request + response
    - Create order request + response
    - Verify stock adjusted

---

## Summary

This testing strategy covers:

1. ✅ **Deployment Verification** - All services running correctly
2. ✅ **Service Discovery** - DNS and HTTP communication working
3. ✅ **Complete Request Flow** - Gateway → Order → Product chain working
4. ✅ **Kubernetes Features** - Scaling, rolling updates, auto-healing
5. ✅ **Configuration Management** - ConfigMaps working correctly
6. ✅ **Troubleshooting** - Commands to debug issues

For your lab report, follow the testing checklist and include relevant command outputs and screenshots demonstrating that your microservices deployment is fully functional.
