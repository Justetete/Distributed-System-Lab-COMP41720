# LAB 3: Designing for Resilience and Observability

A distributed systems project demonstrating resilience patterns including Circuit Breaker, Retry with Exponential Backoff, and Chaos Engineering experiments.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Testing](#testing)
- [Resilience Patterns](#resilience-patterns)
- [Chaos Engineering](#chaos-engineering)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This project implements a distributed microservices architecture with:
- **Backend Service**: RESTful API with fault injection capabilities
- **Client Service**: Consumer service with resilience patterns
- **Resilience Patterns**: Circuit Breaker, Retry Logic with Exponential Backoff and Jitter
- **Chaos Engineering**: Experiments to validate system resilience
- **Kubernetes Deployment**: Container orchestration with Minikube

### Learning Objectives

- Understand common failure modes in distributed systems
- Implement key resilience patterns (Circuit Breaker, Retries, Backoff)
- Apply chaos engineering to test fault tolerance
- Analyze architectural trade-offs in system design

---

## 🏗️ Architecture
```
┌─────────────────┐         HTTP          ┌─────────────────┐
│                 │  ─────────────────>   │                 │
│ Client Service  │                        │ Backend Service │
│  (Port 8080)    │  <─────────────────   │  (Port 5000)    │
│                 │       Responses        │                 │
└─────────────────┘                        └─────────────────┘
        │                                           │
        │ - Circuit Breaker                         │ - Fault Injection
        │ - Retry Logic                             │ - User CRUD API
        │ - Exponential Backoff                     │ - Controllable Failures
        └───────────────────────────────────────────┘
```

**Key Features:**
- **Client Service**: Implements resilience patterns to handle backend failures
- **Backend Service**: Simulates failures (delays, errors, timeouts) for testing
- **Service Discovery**: Kubernetes DNS-based service discovery
- **Health Checks**: Both services expose `/health` endpoints

---

## 📁 Project Structure
```
lab03/
├── services/                    # Microservices
│   ├── backend_services/        # Backend Service
│   │   ├── src/
│   │   │   ├── app.py          # Flask application with fault injection
│   │   │   ├── models.py       # User data models
│   │   │   ├── fault_injector.py   # Fault injection decorator
│   │   │   └── users.json      # Initial user data
│   │   ├── test/
│   │   │   ├── test_backend.py     # Backend API tests
│   │   │   └── test_fault_injection.py  # Fault injection tests
│   │   ├── Dockerfile          # Backend container definition
│   │   └── requirements.txt    # Python dependencies
│   │
│   └── client_services/         # Client Service
│       ├── src/
│       │   ├── client_app.py   # Flask application (client endpoints)
│       │   ├── backend_client.py    # HTTP client for backend
│       │   ├── circuit_breaker.py   # Circuit Breaker implementation
│       │   ├── retry_logic.py  # Retry with exponential backoff
│       │   └── config.py       # Configuration management
│       ├── test/
│       │   └── test_client_service.py  # Client service tests
│       ├── Dockerfile          # Client container definition
│       └── requirements.txt    # Python dependencies
│
├── kubernetes/                  # Kubernetes manifests
│   ├── backend/
│   │   ├── deployment.yaml     # Backend deployment config
│   │   └── service.yaml        # Backend ClusterIP service
│   ├── client/
│   │   ├── deployment.yaml     # Client deployment config
│   │   └── service.yaml        # Client NodePort service
│   ├── deploy.sh               # Automated deployment script
│   ├── cleanup.sh              # Cleanup script
│   └── README.md               # Kubernetes deployment guide
│
├── chao_experiments/            # Chaos Engineering
│   ├── network_partition.yaml  # Network partition experiment
│   ├── pod-failure.yaml        # Pod failure experiment
│   └── experiment_results.log  # Experiment logs
│
├── docs/                        # Documentation
│   └── Baseline_Tests.md       # Manual testing guide
│
├── docker-compose.yaml          # Docker Compose setup (local dev)
├── redeploy.sh                  # Quick redeploy script
└── README.md                    # This file
```

### 📄 Key Files Description

#### Backend Service Files
- **`app.py`**: Main Flask application with user CRUD endpoints and fault injection control
- **`models.py`**: User data model with in-memory storage
- **`fault_injector.py`**: Decorator-based fault injection (delays, errors, timeouts)
- **`users.json`**: Initial seed data (15 users)

#### Client Service Files
- **`client_app.py`**: Flask application exposing client endpoints
- **`backend_client.py`**: HTTP client wrapper with resilience patterns
- **`circuit_breaker.py`**: Circuit Breaker pattern implementation
- **`retry_logic.py`**: Retry logic with exponential backoff and jitter (using Tenacity)
- **`config.py`**: Environment-based configuration

#### Kubernetes Files
- **`deployment.yaml`**: Pod specifications, replicas, health checks, resource limits
- **`service.yaml`**: Service discovery configuration (ClusterIP for backend, NodePort for client)
- **`deploy.sh`**: Automated script for building images and deploying to Minikube

---

## 🛠️ Prerequisites

### Required Software

1. **Docker** (v20.10+)
```bash
   docker --version
```

2. **Minikube** (v1.25+)
```bash
   minikube version
```

3. **kubectl** (v1.23+)
```bash
   kubectl version --client
```

4. **Python 3.9+** (for local development)
```bash
   python3 --version
```

### Installation Guides

**Docker:**
- macOS: `brew install docker` or [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Linux: Follow [official guide](https://docs.docker.com/engine/install/)
- Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/)

**Minikube:**
```bash
# macOS
brew install minikube

# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Windows (PowerShell as Administrator)
choco install minikube
```

**kubectl:**
```bash
# macOS
brew install kubectl

# Linux
sudo apt-get install -y kubectl

# Windows
choco install kubernetes-cli
```

---

## 🚀 Quick Start

### Option 1: Kubernetes Deployment (Recommended)

#### 1. Start Minikube
```bash
# Start Minikube with sufficient resources
minikube start --cpus=4 --memory=4096

# Verify Minikube is running
minikube status
```

#### 2. Deploy Services
```bash
# Navigate to kubernetes directory
cd kubernetes

# Run automated deployment script
./deploy.sh
```

The script will:
- ✅ Build Docker images
- ✅ Deploy Backend and Client services
- ✅ Wait for pods to be ready
- ✅ Display access URLs

#### 3. Access the Application
```bash
# Get Client Service URL
minikube service client-service --url

# Or use in variable
CLIENT_URL=$(minikube service client-service --url)
echo $CLIENT_URL
```

#### 4. Test the Application
```bash
# Health check
curl $CLIENT_URL/health

# Get all users
curl $CLIENT_URL/client/users

# Get specific user
curl $CLIENT_URL/client/users/1
```

---

### Option 2: Docker Compose (Local Development)
```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Test services
curl http://localhost:8080/health  # Client
curl http://localhost:5000/health  # Backend

# Stop services
docker-compose down
```

---

### Option 3: Local Python Development

#### Backend Service
```bash
cd services/backend_services

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python src/app.py
```

Backend will run on: `http://localhost:5000`

#### Client Service
```bash
cd services/client_services

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set backend URL
export BACKEND_URL=http://localhost:5000

# Run client
python src/client_app.py
```

Client will run on: `http://localhost:8080`

---

## 🧪 Testing

### Run Backend Tests
```bash
cd services/backend_services/test

# Test basic functionality
python test_backend.py

# Test fault injection
python test_fault_injection.py
```

### Run Client Tests
```bash
cd services/client_services/test

# Test client service
python test_client_service.py
```

### Manual Testing with Kubernetes

Follow the comprehensive guide in `docs/Baseline_Tests.md` for:
- Normal operation tests
- Delay injection tests
- Error injection tests
- Complete backend failure tests

---

## 🛡️ Resilience Patterns

### 1. Circuit Breaker

**Purpose**: Prevent cascading failures by failing fast when a service is unhealthy

**Implementation**: `services/client_services/src/circuit_breaker.py`

**States**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service is failing, requests fail immediately
- **HALF-OPEN**: Testing if service has recovered

**Configuration**:
```python
failure_threshold = 5      # Open after 5 failures
recovery_timeout = 30      # Wait 30s before trying again
success_threshold = 2      # Close after 2 successes
```

### 2. Retry Logic with Exponential Backoff

**Purpose**: Automatically retry transient failures with increasing delays

**Implementation**: `services/client_services/src/retry_logic.py`

**Features**:
- Exponential backoff: 1s → 2s → 4s → 8s
- Jitter: Random variation to prevent thundering herd
- Retries only on transient errors (429, 503, 504, timeouts)

**Configuration**:
```python
max_attempts = 3           # Retry up to 3 times
min_wait = 1.0            # Start with 1 second
max_wait = 10.0           # Maximum 10 seconds
multiplier = 2.0          # Double each time
```

### 3. Fault Injection

**Purpose**: Simulate failures for testing resilience patterns

**Implementation**: `services/backend_services/src/fault_injector.py`

**Capabilities**:
- Delay injection (slow responses)
- Error injection (HTTP 500)
- Timeout injection (very long delays)

**Control Endpoints**:
```bash
# Configure failure rate
curl -X POST http://localhost:5000/configfailure \
  -H "Content-Type: application/json" \
  -d '{"failure_rate": 0.5}'

# Configure latency
curl -X POST http://localhost:5000/configlatency \
  -H "Content-Type: application/json" \
  -d '{"delay_ms": 2000, "delay_rate": 0.5}'
```

---

## 💥 Chaos Engineering

### Pod Failure Experiment

**Scenario**: Kill backend pods to test circuit breaker
```bash
# Scale backend to 0 (simulate crash)
kubectl scale deployment/backend-deployment --replicas=0

# Observe client behavior
kubectl logs -f deployment/client-deployment

# Restore backend
kubectl scale deployment/backend-deployment --replicas=1
```

**Expected Behavior**:
1. ⚠️ Client detects failures
2. 🔄 Retries kick in
3. 🔴 Circuit breaker opens (fail fast)
4. ⏳ Wait for recovery timeout
5. 🟡 Half-open state (test request)
6. ✅ Circuit closes (system recovered)

### Network Partition Experiment

Chaos experiments are defined in `chao_experiments/` directory.
```bash
# Run network partition experiment
chaos run chao_experiments/network_partition.yaml
```

---

## 🔍 Monitoring

### View Logs
```bash
# Client logs
kubectl logs -f deployment/client-deployment

# Backend logs
kubectl logs -f deployment/backend-deployment

# Filter for retry events
kubectl logs deployment/client-deployment | grep -i retry

# Filter for circuit breaker events
kubectl logs deployment/client-deployment | grep -i circuit
```

### Check Pod Status
```bash
# Get all pods
kubectl get pods

# Describe pod details
kubectl describe pod <pod-name>

# Get services
kubectl get svc
```

### Health Checks
```bash
# Client health
curl $CLIENT_URL/health

# Backend health (via port-forward)
kubectl port-forward service/backend-service 5000:5000
curl http://localhost:5000/health
```

---

## 🐛 Troubleshooting

### Pods Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Common issues:
# - ImagePullBackOff: Run `eval $(minikube docker-env)` before building
# - CrashLoopBackOff: Check application logs for errors
```

### Cannot Access Services
```bash
# Ensure Minikube is running
minikube status

# Get service URL
minikube service client-service --url

# Alternative: Port forwarding
kubectl port-forward service/client-service 8080:8080
```

### Client Cannot Connect to Backend
```bash
# Verify backend service exists
kubectl get service backend-service

# Check DNS resolution from client pod
CLIENT_POD=$(kubectl get pods -l app=client -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $CLIENT_POD -- nslookup backend-service
```

### Docker Build Issues
```bash
# Set Minikube Docker environment
eval $(minikube docker-env)

# Verify you're using Minikube's Docker
docker ps

# Rebuild images
cd kubernetes
./deploy.sh
```

---

## 📊 API Documentation

### Client Service Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/client/users` | Get all users |
| GET | `/client/users/<id>` | Get specific user |
| POST | `/client/users` | Create user |
| PUT | `/client/users/<id>` | Update user |
| DELETE | `/client/users/<id>` | Delete user |

### Backend Service Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/users` | Get all users |
| GET | `/api/users/<id>` | Get specific user |
| POST | `/api/users` | Create user |
| PUT | `/api/users/<id>` | Update user |
| DELETE | `/api/users/<id>` | Delete user |
| POST | `/configfailure` | Configure error rate |
| POST | `/configlatency` | Configure delay rate |

---

## 🧹 Cleanup

### Remove Kubernetes Resources
```bash
# Use cleanup script
cd kubernetes
./cleanup.sh

# Or manually
kubectl delete -f kubernetes/client/
kubectl delete -f kubernetes/backend/
```

### Stop Minikube
```bash
minikube stop

# Or delete cluster entirely
minikube delete
```

### Stop Docker Compose
```bash
docker-compose down

# Remove volumes
docker-compose down -v
```

---

## 📚 Additional Resources

- **Lab Instructions**: `COMP41720_Distributed_Systems_Lab_3_2025.docx`
- **Hints**: `Hints_for_Solving_Lab_3.docx`
- **Baseline Testing Guide**: `docs/Baseline_Tests.md`
- **Kubernetes Guide**: `kubernetes/README.md`

---

## 👥 Contributors

- **Course**: COMP41720 Distributed Systems
- **Institution**: University College Dublin
- **Academic Year**: 2024-2025

---

## 📝 License

This project is for educational purposes as part of COMP41720 Distributed Systems course.

---

## 🎓 Key Takeaways

1. **Resilience Patterns are Essential**: Circuit breakers and retries dramatically improve system reliability
2. **Trade-offs Matter**: Every pattern has costs (complexity, latency, resource usage)
3. **Fail Fast vs. Retry**: Know when to give up quickly vs. when to persist
4. **Graceful Degradation**: Systems should degrade gracefully, not catastrophically
5. **Test Your Assumptions**: Chaos engineering validates resilience patterns work as expected

---

**Good luck with your submission! 🚀**