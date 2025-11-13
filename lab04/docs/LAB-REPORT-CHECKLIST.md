# Lab Report Testing Checklist

## E-Commerce Microservices - Kubernetes Deployment Verification

**Student Name:** ___________________
**Date:** ___________________
**Lab:** Microservices with Kubernetes

---

## Section 1: Environment Setup

| Task | Command | Status | Notes |
|------|---------|--------|-------|
| Minikube running | `minikube status` | ☐ | |
| Kubectl configured | `kubectl cluster-info` | ☐ | |
| Docker images built | `docker images \| grep lab04` | ☐ | Should show 3 images |

---

## Section 2: Deployment Verification

### 2.1 Resources Deployed

| Resource | Command | Expected | Status |
|----------|---------|----------|--------|
| ConfigMaps | `kubectl get configmaps` | 3 ConfigMaps | ☐ |
| Deployments | `kubectl get deployments` | 3 Deployments (2/2 ready) | ☐ |
| Services | `kubectl get svc` | 3 Services (product, order, gateway) | ☐ |
| Pods | `kubectl get pods` | 6 Pods (all Running) | ☐ |

**Command Output:**
```bash
kubectl get all
```

**Screenshot:** ☐ Attached

---

### 2.2 Pod Health Status

| Service | Command | Expected Output | Status |
|---------|---------|-----------------|--------|
| Product Service | `kubectl get pods -l app=product-service` | 2/2 pods Running | ☐ |
| Order Service | `kubectl get pods -l app=order-service` | 2/2 pods Running | ☐ |
| API Gateway | `kubectl get pods -l app=api-gateway` | 2/2 pods Running | ☐ |

**Verification:**
- [ ] All pods show STATUS: Running
- [ ] All pods show READY: 1/1
- [ ] RESTARTS count is 0 or very low

---

### 2.3 Service Endpoints

| Service | Command | Expected | Status |
|---------|---------|----------|--------|
| Product Service | `kubectl get endpoints product-service` | 2 IP addresses | ☐ |
| Order Service | `kubectl get endpoints order-service` | 2 IP addresses | ☐ |
| API Gateway | `kubectl get endpoints api-gateway` | 2 IP addresses | ☐ |

---

## Section 3: External Access

### 3.1 Gateway Access

**Get Gateway URL:**
```bash
export GATEWAY_URL=$(minikube service api-gateway --url)
echo $GATEWAY_URL
```

**Gateway URL:** _____________________

### 3.2 Health Check

| Endpoint | Command | Expected Response | Status |
|----------|---------|-------------------|--------|
| Gateway Health | `curl $GATEWAY_URL/actuator/health` | `{"status":"UP"}` | ☐ |
| Products Endpoint | `curl $GATEWAY_URL/api/products` | `[]` or JSON array | ☐ |
| Orders Endpoint | `curl $GATEWAY_URL/api/orders` | `[]` or JSON array | ☐ |

**Screenshot:** ☐ Health check response

---

## Section 4: Inter-Service Communication

### 4.1 DNS Resolution Test

**Test Order Service → Product Service DNS:**
```bash
ORDER_POD=$(kubectl get pods -l app=order-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec $ORDER_POD -- nslookup product-service
```

**Result:** ☐ Pass ☐ Fail

**DNS resolves to:** _____________________

### 4.2 HTTP Communication Test

**Test Order Service → Product Service HTTP:**
```bash
kubectl exec $ORDER_POD -- curl -s http://product-service:8080/actuator/health
```

**Response:** ☐ `{"status":"UP"}` ☐ Other: ___________

### 4.3 Communication Logs

**Check Order Service logs for Feign client activity:**
```bash
kubectl logs -l app=order-service --tail=50 | grep -i "feign\|product"
```

**Observations:**
- [ ] Feign client initialized
- [ ] HTTP requests to product-service visible
- [ ] No connection errors

**Screenshot:** ☐ Logs showing inter-service communication

---

## Section 5: Complete Request Flow

### 5.1 Create Product

**Command:**
```bash
curl -X POST $GATEWAY_URL/api/products/create \
  -H "Content-Type: application/json" \
  -d '{"sku":"LAB-001","name":"Test Product","price":99.99,"stockLevel":20}'
```

**Result:** ☐ Success ☐ Failed
**Product SKU:** LAB-001
**Initial Stock:** 20

**Screenshot:** ☐ Product creation response

---

### 5.2 List Products

**Command:**
```bash
curl $GATEWAY_URL/api/products
```

**Result:** ☐ Product visible in list

---

### 5.3 Create Order (Tests Order → Product Communication)

**Command:**
```bash
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "refNumber": "ORD-LAB-001",
    "customerId": "CUST-001",
    "items": [{"sku": "LAB-001", "quantity": 5}]
  }'
```

**Result:** ☐ Success ☐ Failed
**Order Reference:** ORD-LAB-001
**Quantity Ordered:** 5

**Screenshot:** ☐ Order creation response

---

### 5.4 Verify Stock Adjustment

**Command:**
```bash
curl $GATEWAY_URL/api/products/LAB-001
```

**Initial Stock:** 20
**Ordered Quantity:** 5
**Expected Stock:** 15
**Actual Stock:** _____

**Result:** ☐ Stock correctly adjusted ☐ Stock not adjusted

---

### 5.5 Verify Order Created

**Command:**
```bash
curl $GATEWAY_URL/api/orders
```

**Result:** ☐ Order visible in list

---

### 5.6 Request Flow Verification

**This test demonstrates:**
- [x] Gateway routing to Order Service
- [x] Order Service calling Product Service (Feign client)
- [x] Product Service adjusting stock
- [x] Successful response chain back to client

**Screenshot:** ☐ Complete request flow working

---

## Section 6: Kubernetes Features

### 6.1 Horizontal Scaling

**Scale Up:**
```bash
kubectl scale deployment product-service --replicas=4
kubectl get pods -l app=product-service
```

**Before Scaling:** 2 pods
**After Scaling:** _____ pods
**Result:** ☐ Success ☐ Failed

**Screenshot:** ☐ 4 product-service pods running

---

**Scale Down:**
```bash
kubectl scale deployment product-service --replicas=2
```

**Result:** ☐ Scaled back to 2 pods

---

### 6.2 Rolling Update

**Trigger Rolling Update:**
```bash
kubectl patch configmap product-service-config \
  -p '{"data":{"LOGGING_LEVEL_ROOT":"DEBUG"}}'
kubectl rollout restart deployment product-service
kubectl rollout status deployment product-service
```

**Observations:**
- [ ] Pods updated one at a time
- [ ] No downtime during update
- [ ] New configuration applied

**Screenshot:** ☐ Rolling update status

---

### 6.3 Auto-Healing

**Delete Pod:**
```bash
PRODUCT_POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $PRODUCT_POD
kubectl get pods -l app=product-service
```

**Deleted Pod:** _____________________
**New Pod Created:** _____________________
**Result:** ☐ New pod automatically created

---

### 6.4 Resource Monitoring

**Check Resource Usage:**
```bash
minikube addons enable metrics-server
sleep 60
kubectl top pods
```

| Service | CPU Usage | Memory Usage |
|---------|-----------|--------------|
| product-service | _____ | _____ |
| order-service | _____ | _____ |
| api-gateway | _____ | _____ |

**Screenshot:** ☐ Resource usage output

---

### 6.5 Load Balancing

**Test Load Distribution:**
```bash
for i in {1..10}; do
  curl -s $GATEWAY_URL/api/products > /dev/null
done
kubectl logs -l app=product-service --tail=20
```

**Observations:**
- [ ] Requests distributed across multiple pods
- [ ] All pods handling requests
- [ ] Load balancing working

---

## Section 7: Configuration Management

### 7.1 ConfigMap Verification

**List ConfigMaps:**
```bash
kubectl get configmaps
```

**ConfigMaps Present:**
- [ ] product-service-config
- [ ] order-service-config
- [ ] api-gateway-config

---

### 7.2 ConfigMap Usage

**Verify Pod Using ConfigMap:**
```bash
PRODUCT_POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec $PRODUCT_POD -- env | grep -E 'SPRING_APPLICATION_NAME|LOGGING_LEVEL'
```

**Result:** ☐ Environment variables from ConfigMap visible

---

### 7.3 ConfigMap Update Test

**Update Configuration:**
```bash
kubectl edit configmap product-service-config
# Change LOGGING_LEVEL_ROOT from INFO to DEBUG
kubectl rollout restart deployment product-service
```

**Result:** ☐ Configuration updated without rebuilding image

**Screenshot:** ☐ ConfigMap edit and restart

---

## Section 8: Service Architecture

### 8.1 Architecture Diagram

**Draw or attach diagram showing:**
- [ ] API Gateway (NodePort)
- [ ] Product Service (ClusterIP)
- [ ] Order Service (ClusterIP)
- [ ] Inter-service communication arrows
- [ ] External client access

**Diagram:** ☐ Attached

---

### 8.2 Communication Flow

**Document the request flow:**

1. Client → Gateway (NodePort 30080)
2. Gateway → Order Service (ClusterIP:8081)
3. Order Service → Product Service (ClusterIP:8080)
4. Product Service → Response
5. Response chain back to Client

**Verified:** ☐ Yes ☐ No

---

## Section 9: Troubleshooting Demonstration

### 9.1 View Pod Logs

**Command:**
```bash
kubectl logs -l app=product-service --tail=50
```

**Result:** ☐ Logs viewable

---

### 9.2 Describe Pod

**Command:**
```bash
kubectl describe pod <pod-name>
```

**Result:** ☐ Detailed pod information visible

---

### 9.3 Execute Commands in Pod

**Command:**
```bash
kubectl exec -it <pod-name> -- /bin/sh
```

**Result:** ☐ Can access pod shell

---

## Section 10: Cleanup Verification

**Run Cleanup:**
```bash
./cleanup.sh
```

**Verification:**
```bash
kubectl get all
```

**Result:** ☐ All microservices removed

---

## Summary

### Components Tested

- [x] 3 Microservices (Product, Order, Gateway)
- [x] 6 Pods (2 replicas each)
- [x] 3 Services (ClusterIP + NodePort)
- [x] 3 ConfigMaps
- [x] Inter-service communication (DNS + HTTP)
- [x] Complete request flow (Gateway → Order → Product)
- [x] Kubernetes features (scaling, rolling updates, auto-healing)
- [x] Configuration management (ConfigMaps)
- [x] Load balancing
- [x] External access (NodePort)

### Key Achievements

- ☐ All pods running successfully
- ☐ Services accessible internally and externally
- ☐ Inter-service communication working (Order ↔ Product)
- ☐ Complete order flow working (stock adjustment verified)
- ☐ Kubernetes features demonstrated (scaling, updates, healing)
- ☐ ConfigMaps working (externalized configuration)
- ☐ Zero-downtime rolling updates
- ☐ Load balancing across replicas

### Issues Encountered

1. _____________________________________________________
2. _____________________________________________________
3. _____________________________________________________

### Lessons Learned

1. _____________________________________________________
2. _____________________________________________________
3. _____________________________________________________

---

## Appendix: Key Commands Reference

```bash
# Deployment
./deploy.sh

# Status Check
kubectl get all
kubectl get pods
kubectl get svc

# Gateway URL
export GATEWAY_URL=$(minikube service api-gateway --url)

# Health Check
curl $GATEWAY_URL/actuator/health

# Create Product
curl -X POST $GATEWAY_URL/api/products/create \
  -H "Content-Type: application/json" \
  -d '{"sku":"TEST","name":"Test","price":99,"stockLevel":10}'

# List Products
curl $GATEWAY_URL/api/products

# Create Order
curl -X POST $GATEWAY_URL/api/orders/checkout \
  -H "Content-Type: application/json" \
  -d '{"refNumber":"ORD-001","customerId":"C1","items":[{"sku":"TEST","quantity":2}]}'

# List Orders
curl $GATEWAY_URL/api/orders

# Scale
kubectl scale deployment product-service --replicas=4

# Rolling Update
kubectl rollout restart deployment product-service
kubectl rollout status deployment product-service

# View Logs
kubectl logs -l app=product-service

# Resource Usage
kubectl top pods

# Cleanup
./cleanup.sh
```

---

**Signature:** ___________________
**Date:** ___________________

**Lab Completion Status:** ☐ Completed ☐ Incomplete

**Overall Grade:** _____/100
