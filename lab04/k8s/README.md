# Kubernetes Manifests for Product Service

This directory contains Kubernetes manifests for deploying the Product microservice.

## Files

- `products-deployment.yaml` - Deployment configuration
- `products-service.yaml` - Service configuration

## Deployment Configuration Explained

### products-deployment.yaml

#### 1. **Metadata and Labels** (lines 3-7)
```yaml
metadata:
  name: product-service
  labels:
    app: product-service
    tier: backend
    component: microservice
```
- **name**: Unique identifier for the deployment
- **labels**: Organize and select resources
  - `app`: Identifies the application
  - `tier`: Separates backend from frontend services
  - `component`: Categorizes as a microservice

#### 2. **Replicas** (line 9)
```yaml
replicas: 2
```
- Runs **2 instances** for high availability
- Provides load balancing across pods
- Ensures zero downtime during updates

#### 3. **Selector** (lines 10-12)
```yaml
selector:
  matchLabels:
    app: product-service
```
- Defines which pods this deployment manages
- Must match the pod template labels

#### 4. **Rolling Update Strategy** (lines 13-16)
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```
- **RollingUpdate**: Updates pods gradually, not all at once
- **maxSurge: 1**: Can create 1 extra pod during update
- **maxUnavailable: 0**: Ensures no pods are unavailable (zero downtime)

#### 5. **Container Image** (lines 27-29)
```yaml
image: lab04-product-service:latest
imagePullPolicy: Never
```
- **imagePullPolicy: Never**: Uses local Minikube images only
- Assumes image was built and loaded into Minikube's Docker daemon
- For production, use `IfNotPresent` or `Always` with a registry

#### 6. **Environment Variables** (lines 33-50)
```yaml
env:
- name: SPRING_DATASOURCE_URL
  value: "jdbc:postgresql://product-db:5432/productdb"
- name: EUREKA_CLIENT_SERVICEURL_DEFAULTZONE
  value: "http://eureka-server:8761/eureka/"
```
- Configures database connection (assumes product-db service exists)
- Configures Eureka service discovery
- Uses Kubernetes DNS for service discovery (service names resolve automatically)

#### 7. **Resource Limits and Requests** (lines 51-57)
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```
- **requests**: Minimum resources guaranteed to the pod
  - 512MB RAM, 0.25 CPU cores
  - Used by Kubernetes scheduler for pod placement
- **limits**: Maximum resources the pod can use
  - 1GB RAM, 0.5 CPU cores
  - Pod will be throttled/killed if exceeding these limits

#### 8. **Health Probes**

##### Startup Probe (lines 79-88)
```yaml
startupProbe:
  httpGet:
    path: /actuator/health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 30
```
- **Purpose**: Gives slow-starting apps time to initialize
- **initialDelaySeconds: 30**: Waits 30 seconds before first check
- **periodSeconds: 10**: Checks every 10 seconds
- **failureThreshold: 30**: Allows up to 300 seconds (5 minutes) to start
- Spring Boot apps can take time to start, especially with database connections

##### Liveness Probe (lines 58-66)
```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 90
  periodSeconds: 10
  failureThreshold: 3
```
- **Purpose**: Detects if app is deadlocked or crashed
- **Action**: Restarts the container if probe fails
- **initialDelaySeconds: 90**: Waits 90 seconds after container starts
- **failureThreshold: 3**: Restarts after 3 consecutive failures (30 seconds)
- Uses Spring Boot Actuator's liveness endpoint

##### Readiness Probe (lines 67-76)
```yaml
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 10
  failureThreshold: 3
```
- **Purpose**: Determines if pod can accept traffic
- **Action**: Removes pod from service load balancer if probe fails
- **Use case**: Temporarily unavailable (e.g., database connection lost)
- Pod stays running but receives no traffic until ready again

#### 9. **Restart Policy** (line 89-90)
```yaml
restartPolicy: Always
terminationGracePeriodSeconds: 30
```
- **Always**: Restarts container if it crashes
- **terminationGracePeriodSeconds**: Gives pod 30 seconds to shut down gracefully

## Service Configuration Explained

### products-service.yaml

#### 1. **Service Type** (line 11)
```yaml
type: ClusterIP
```
- **ClusterIP**: Internal-only access (default)
- Creates a stable internal IP address
- Other pods can access via service name: `http://product-service:8080`
- Not accessible from outside the cluster
- Use `LoadBalancer` or `NodePort` for external access

#### 2. **Selector** (lines 12-13)
```yaml
selector:
  app: product-service
```
- Routes traffic to pods with label `app: product-service`
- Must match deployment's pod template labels
- Automatically load balances across all matching pods

#### 3. **Ports** (lines 14-17)
```yaml
ports:
- name: http
  port: 8080
  targetPort: 8080
  protocol: TCP
```
- **port: 8080**: Service listens on this port
- **targetPort: 8080**: Forwards traffic to pod's port 8080
- Other services call: `http://product-service:8080/products`

#### 4. **Session Affinity** (line 18)
```yaml
sessionAffinity: None
```
- Distributes requests evenly across pods
- Each request can go to a different pod
- For sticky sessions, use `ClientIP`

## Deploying to Minikube

### Prerequisites

```bash
# Start Minikube
minikube start

# Build Docker image in Minikube's environment
eval $(minikube docker-env)
cd product-service
docker build -t lab04-product-service:latest .
```

### Deploy Product Service

```bash
# Apply manifests
kubectl apply -f k8s/products-deployment.yaml
kubectl apply -f k8s/products-service.yaml

# Verify deployment
kubectl get deployments
kubectl get pods
kubectl get services

# Check pod logs
kubectl logs -l app=product-service --tail=50

# Check pod details
kubectl describe pod -l app=product-service
```

### Testing

```bash
# Port forward to test locally
kubectl port-forward service/product-service 8080:8080

# Test in another terminal
curl http://localhost:8080/products
curl http://localhost:8080/actuator/health
```

### Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment product-service --replicas=3

# Verify
kubectl get pods -l app=product-service
```

### Updating

```bash
# After building new image
kubectl rollout restart deployment product-service

# Check rollout status
kubectl rollout status deployment product-service

# View rollout history
kubectl rollout history deployment product-service

# Rollback if needed
kubectl rollout undo deployment product-service
```

### Troubleshooting

```bash
# Check pod status
kubectl get pods -l app=product-service

# View pod logs
kubectl logs -l app=product-service --tail=100 -f

# Describe pod (shows events)
kubectl describe pod -l app=product-service

# Execute commands in pod
kubectl exec -it <pod-name> -- /bin/sh

# Check service endpoints
kubectl get endpoints product-service

# View all events
kubectl get events --sort-by=.metadata.creationTimestamp
```

## Dependencies

The Product Service requires these other services:

1. **PostgreSQL Database** (`product-db`)
   - Service name: `product-db`
   - Port: 5432
   - Create deployment and service for PostgreSQL

2. **Eureka Server** (`eureka-server`)
   - Service name: `eureka-server`
   - Port: 8761
   - Create deployment and service for Eureka

## Best Practices Applied

1. ✅ **Resource Limits**: Prevents resource starvation
2. ✅ **Health Checks**: Automatic failure detection and recovery
3. ✅ **Rolling Updates**: Zero-downtime deployments
4. ✅ **Multiple Replicas**: High availability
5. ✅ **Labels**: Organized resource management
6. ✅ **Graceful Shutdown**: 30-second termination period
7. ✅ **Security Context**: Non-root user (configured in Dockerfile)
8. ✅ **Environment Variables**: Externalized configuration

## Production Considerations

For production deployments, consider:

1. **ConfigMaps**: Store non-sensitive configuration
2. **Secrets**: Store sensitive data (passwords, keys)
3. **Horizontal Pod Autoscaler**: Auto-scale based on CPU/memory
4. **Network Policies**: Restrict pod-to-pod communication
5. **Service Mesh**: Istio or Linkerd for advanced traffic management
6. **Monitoring**: Prometheus and Grafana
7. **Logging**: Centralized logging with ELK or Loki
8. **Image Registry**: Use private registry instead of local images

## Next Steps

1. Create manifests for Order Service
2. Create manifests for API Gateway
3. Create manifests for PostgreSQL databases
4. Create manifests for Eureka Server
5. Create a complete deployment script
6. Set up Ingress for external access
