# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the distributed application (Backend and Client services) on Minikube.

## 📂 Directory Structure

```
kubernetes/
├── backend/
│   ├── deployment.yaml    # Backend Deployment configuration
│   └── service.yaml       # Backend Service (ClusterIP)
├── client/
│   ├── deployment.yaml    # Client Deployment configuration
│   └── service.yaml       # Client Service (NodePort)
├── deploy.sh              # Automated deployment script
├── cleanup.sh             # Cleanup script
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Minikube installed and running**
   ```bash
   minikube start
   ```

2. **Docker installed**

3. **kubectl configured** (should be automatic with Minikube)

### Automated Deployment (Recommended)

Simply run the deployment script:

```bash
cd kubernetes
./deploy.sh
```

This script will:
- ✅ Check Minikube status
- ✅ Configure Docker environment
- ✅ Build Docker images
- ✅ Deploy Backend and Client services
- ✅ Wait for pods to be ready
- ✅ Display access URLs

### Manual Deployment

If you prefer to deploy manually:

```bash
# 1. Set Docker environment to Minikube
eval $(minikube docker-env)

# 2. Build Docker images
docker build -t backend-service:latest -f services/backend_services/Dockerfile services/backend_services/
docker build -t client-service:latest -f services/client_services/Dockerfile services/client_services/

# 3. Deploy Backend
kubectl apply -f kubernetes/backend/deployment.yaml
kubectl apply -f kubernetes/backend/service.yaml

# 4. Deploy Client
kubectl apply -f kubernetes/client/deployment.yaml
kubectl apply -f kubernetes/client/service.yaml

# 5. Wait for pods
kubectl wait --for=condition=available --timeout=60s deployment/backend-deployment
kubectl wait --for=condition=available --timeout=60s deployment/client-deployment
```

## 🔍 Verify Deployment

### Check Pod Status
```bash
kubectl get pods
```

Expected output:
```
NAME                                  READY   STATUS    RESTARTS   AGE
backend-deployment-xxxxx-xxxxx        1/1     Running   0          1m
client-deployment-xxxxx-xxxxx         1/1     Running   0          1m
```

### Check Service Status
```bash
kubectl get services
```

Expected output:
```
NAME              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
backend-service   ClusterIP   10.96.xxx.xxx   <none>        5000/TCP         1m
client-service    NodePort    10.96.xxx.xxx   <none>        8080:30080/TCP   1m
```

### Get Access URL
```bash
minikube service client-service --url
```

## 🧪 Testing the Application

### Test Client Service
```bash
# Get the URL
CLIENT_URL=$(minikube service client-service --url)

# Test health endpoint
curl $CLIENT_URL/health

# Get all users
curl $CLIENT_URL/client/users

# Get specific user
curl $CLIENT_URL/client/users/1

# Create a new user
curl -X POST $CLIENT_URL/client/users \
  -H "Content-Type: application/json" \
  -d '{"id": 100, "name": "Test User", "email": "test@example.com"}'
```

### Check Service Communication

Verify that Client can communicate with Backend through Kubernetes Service DNS:

```bash
# Get client pod name
CLIENT_POD=$(kubectl get pods -l app=client -o jsonpath='{.items[0].metadata.name}')

# Exec into client pod and test backend connection
kubectl exec -it $CLIENT_POD -- curl http://backend-service:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "backend-service",
  "user_count": 15,
  "fault_injection": {...}
}
```

## 📊 Monitoring and Debugging

### View Logs

**Backend logs:**
```bash
kubectl logs -f deployment/backend-deployment
```

**Client logs:**
```bash
kubectl logs -f deployment/client-deployment
```

### Describe Resources

**Describe pod:**
```bash
kubectl describe pod <pod-name>
```

**Describe service:**
```bash
kubectl describe service backend-service
kubectl describe service client-service
```

### Port Forwarding (Alternative Access Method)

Instead of using NodePort, you can use port-forwarding:

```bash
# Forward client service to localhost:8080
kubectl port-forward service/client-service 8080:8080

# Now access at http://localhost:8080
```

## 🔧 Configuration Details

### Backend Service

- **Type**: ClusterIP (internal only)
- **Port**: 5000
- **DNS Name**: `backend-service`
- **Fault Injection**: Enabled (configurable via environment variables)

### Client Service

- **Type**: NodePort (externally accessible)
- **Internal Port**: 8080
- **NodePort**: 30080
- **Backend URL**: `http://backend-service:5000` (uses Kubernetes DNS)

## 🧹 Cleanup

To remove all deployed resources:

```bash
./cleanup.sh
```

Or manually:
```bash
kubectl delete -f kubernetes/client/
kubectl delete -f kubernetes/backend/
```

## 🐛 Troubleshooting

### Pod is not starting

```bash
# Check pod events
kubectl describe pod <pod-name>

# Common issues:
# - ImagePullBackOff: Image not found (check docker-env)
# - CrashLoopBackOff: Application error (check logs)
```

### Cannot access Client Service

```bash
# Verify minikube is running
minikube status

# Get the correct URL
minikube service client-service --url

# Check if port 30080 is accessible
minikube service client-service
```

### Client cannot connect to Backend

```bash
# Check if backend service exists
kubectl get service backend-service

# Check if backend pods are running
kubectl get pods -l app=backend

# Verify DNS resolution from client pod
CLIENT_POD=$(kubectl get pods -l app=client -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $CLIENT_POD -- nslookup backend-service
```

### Images not found

Make sure you're using Minikube's Docker daemon:

```bash
# Set environment
eval $(minikube docker-env)

# Rebuild images
docker build -t backend-service:latest -f services/backend_services/Dockerfile services/backend_services/
docker build -t client-service:latest -f services/client_services/Dockerfile services/client_services/

# Verify images exist
docker images | grep service
```

## 📚 Key Learning Points

1. **Service Discovery**: Client uses `http://backend-service:5000` instead of Pod IPs
2. **ClusterIP vs NodePort**: Backend uses ClusterIP (internal), Client uses NodePort (external)
3. **Health Checks**: Both services have liveness and readiness probes
4. **Image Pull Policy**: Set to `Never` for local Minikube images
5. **Environment Variables**: Configuration passed via Kubernetes env

## 🎯 Next Steps

After successful deployment:
1. ✅ Verify baseline functionality (Part A of Lab)
2. ✅ Implement Circuit Breaker pattern (Part B)
3. ✅ Implement Retry logic (Part B)
4. ✅ Run Chaos Engineering experiments (Part C)

---

For more information, refer to:
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- Lab 3 Instructions