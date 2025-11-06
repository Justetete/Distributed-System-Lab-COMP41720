# Part C: Chaos Engineering - Experiment Plan

## 1. Introduction to Chaos Engineering

### 1.1 What is Chaos Engineering?

Chaos Engineering is the discipline of experimenting on a distributed system to build confidence in the system's capability to withstand turbulent conditions in production. Rather than waiting for failures to happen naturally, we **proactively inject failures** in a controlled manner to:

1. **Discover weaknesses** before they manifest in production
2. **Validate resilience patterns** actually work under real failure conditions
3. **Build confidence** in system's ability to handle unexpected events
4. **Improve incident response** through practice

### 1.2 Core Principles

The four principles of Chaos Engineering:

1. **Build a Hypothesis around Steady State Behavior**
   - Define what "normal" looks like
   - Example: "Client service successfully retrieves users with <500ms latency"

2. **Vary Real-World Events**
   - Simulate realistic failures (pod crashes, network issues, resource exhaustion)
   - Not artificial test scenarios

3. **Run Experiments in Production** (or production-like environments)
   - Lab environment is acceptable for learning
   - Real production is the ultimate test

4. **Automate Experiments to Run Continuously**
   - Part of CI/CD pipeline
   - Ongoing validation, not one-time tests

### 1.3 Our Chaos Experiments

We will conduct **three core experiments** to validate our resilience patterns:

| Experiment | Failure Type | Tests | Expected Outcome |
|-----------|--------------|-------|------------------|
| **Experiment 1** | Pod Failure | Circuit Breaker + Recovery | Circuit opens, system recovers |
| **Experiment 2** | Network Latency | Retry Logic | Retries handle delays |
| **Experiment 3** | Complete Network Partition | Both Patterns | Combined resilience |

---

## 2. Experiment Prerequisites

### 2.1 Environment Setup Checklist

- [ ] Kubernetes cluster running (Minikube)
- [ ] Backend service deployed and healthy
- [ ] Client service deployed with Circuit Breaker + Retry
- [ ] Both services accessible
- [ ] kubectl configured and working
- [ ] Load generator script ready

### 2.2 Verification Commands

```bash
# Check all pods are running
kubectl get pods

# Expected output:
# backend-deployment-xxxxx   1/1   Running
# client-deployment-xxxxx    1/1   Running

# Check services
kubectl get svc

# Verify client can reach backend
CLIENT_URL=$(minikube service client-service --url)
curl $CLIENT_URL/health
```

### 2.3 Baseline Metrics

Before starting chaos experiments, record baseline metrics:

```bash
# Make 10 requests and record:
# - Success rate
# - Average response time
# - Circuit breaker state

for i in {1..10}; do
  curl -w "Time: %{time_total}s\n" $CLIENT_URL/client/users/1
  sleep 1
done
```

**Expected Baseline**:
- Success Rate: 100%
- Average Response Time: <100ms
- Circuit State: CLOSED

---

## 3. Experiment Design

### Experiment 1: Pod Failure (Backend Crash)

#### 3.1.1 Hypothesis
**"When the backend pod is deleted (simulating a crash), the client service's circuit breaker will open after detecting persistent failures, causing subsequent requests to fail fast rather than timeout. When the backend pod recovers, the circuit breaker will automatically detect recovery and close, restoring normal operation."**

#### 3.1.2 Steady State
- Client service making successful requests to backend
- Circuit breaker in CLOSED state
- Response time < 200ms
- 100% success rate

#### 3.1.3 Experiment Steps

**Setup**:
```bash
# Terminal 1: Start load generator (continuous requests)
./load_generator.sh

# Terminal 2: Monitor client logs
kubectl logs -f deployment/client-deployment

# Terminal 3: Monitor backend pods
watch -n 1 kubectl get pods
```

**Execute Chaos**:
```bash
# Terminal 4: Delete backend pod
kubectl delete pod -l app=backend

# Observe:
# - Client logs show failures
# - Circuit breaker opens after 5 failures
# - Subsequent requests fail immediately (0.000s)
# - Backend pod automatically recreates (Kubernetes self-healing)
# - Circuit breaker detects recovery after 30s
# - Circuit closes after 2 successful tests
```

**Timeline**:
```
0s:    Steady state (all requests succeeding)
5s:    DELETE backend pod
7s:    Client detects failures, circuit starts counting
15s:   Circuit breaker OPENS (after 5 failures)
20s:   New backend pod starting (Kubernetes)
35s:   New backend pod ready
45s:   Circuit transitions to HALF_OPEN (30s after opening)
47s:   Test calls succeed, circuit CLOSES
50s:   Normal operation restored
```

#### 3.1.4 Success Criteria
- ✅ Circuit breaker opens within 20 seconds of pod deletion
- ✅ Requests fail fast (<10ms) while circuit is OPEN
- ✅ No client service crash or hang
- ✅ Circuit automatically closes when backend recovers
- ✅ No manual intervention required

#### 3.1.5 Data to Collect
- Screenshots of:
  - Load generator output showing failures then recovery
  - Client logs showing circuit breaker state changes
  - Pod status during failure
- Metrics:
  - Time from failure to circuit opening
  - Time from recovery to circuit closing
  - Number of fast-fails during OPEN state
  - Total recovery time

---

### Experiment 2: Network Latency Injection

#### 3.2.1 Hypothesis
**"When network latency is injected causing slow responses from the backend (but not complete failures), the retry logic with exponential backoff will handle these delays gracefully, and the circuit breaker will remain CLOSED because successes eventually occur."**

#### 3.2.2 Steady State
- Normal network conditions
- Response time < 200ms
- Circuit breaker CLOSED
- 100% success rate

#### 3.2.3 Experiment Steps

**Method 1: Using Backend Fault Injection** (Simpler)
```bash
# Configure backend to inject 100% delays (2 seconds)
kubectl port-forward service/backend-service 5000:5000

# In another terminal:
curl -X POST http://localhost:5000/configlatency \
  -H "Content-Type: application/json" \
  -d '{"delay_ms": 2000, "delay_rate": 1.0}'

# Start load generator
./load_generator.sh

# Observe:
# - All requests take 2+ seconds (delayed)
# - Retry logic does NOT trigger (no failures)
# - Circuit breaker stays CLOSED (requests succeed, just slow)
# - User experience: slower but functional
```

**Method 2: Using Chaos Toolkit** (More realistic)
```bash
# Install Chaos Toolkit (if not already)
pip install chaostoolkit chaostoolkit-kubernetes

# Run network latency experiment
chaos run experiments/network_latency.yaml

# This injects actual network delay at Kubernetes level
```

#### 3.2.4 Success Criteria
- ✅ Requests complete successfully despite delays
- ✅ Circuit breaker remains CLOSED (delays ≠ failures)
- ✅ No timeout errors
- ✅ System remains functional, just slower

#### 3.2.5 Data to Collect
- Response time distribution (before/during/after)
- Circuit breaker state (should stay CLOSED)
- Success rate (should stay 100%)
- Logs showing slow but successful requests

---

### Experiment 3: Complete Network Partition

#### 3.3.1 Hypothesis
**"When network communication between client and backend is completely blocked (simulating network partition), the circuit breaker will open after detecting failures, and the retry logic will exhaust attempts before circuit detection. When network is restored, the system will automatically recover."**

#### 3.3.2 Steady State
- Normal network connectivity
- Successful communication
- Circuit breaker CLOSED

#### 3.3.3 Experiment Steps

**Method 1: Scale Backend to Zero** (Simplest, most reliable)
```bash
# This simulates complete backend unavailability
# (same effect as network partition from client perspective)

# Start load generator
./load_generator.sh

# Execute chaos: Scale backend to 0
kubectl scale deployment/backend-deployment --replicas=0

# Observe:
# - Retry logic attempts each request 3 times
# - Each attempt times out (5 seconds)
# - Circuit breaker counts failures
# - After 5 failed requests, circuit OPENS
# - Subsequent requests fail immediately

# Wait 30 seconds, then restore:
kubectl scale deployment/backend-deployment --replicas=1

# Observe:
# - Backend pod starts
# - Circuit remains OPEN initially
# - After 30s total, circuit goes HALF_OPEN
# - Test calls succeed
# - Circuit CLOSES
```

**Method 2: Using Network Policies** (More realistic)
```bash
# Apply network policy to block traffic
kubectl apply -f experiments/network_policy_block.yaml

# This creates a NetworkPolicy that denies all traffic
# between client and backend

# Restore network
kubectl delete -f experiments/network_policy_block.yaml
```

#### 3.3.4 Success Criteria
- ✅ Retry logic attempts multiple times before giving up
- ✅ Circuit breaker opens after pattern of failures
- ✅ System doesn't crash or hang indefinitely
- ✅ Recovery is automatic after network restoration
- ✅ No data corruption or inconsistent state

#### 3.3.5 Data to Collect
- Time from network partition to circuit opening
- Number of retry attempts before circuit opens
- Fast-fail response times during OPEN state
- Recovery time after network restoration
- Logs showing entire failure → recovery cycle

---

## 4. Tools and Scripts

### 4.1 Load Generator Script

We need a script that continuously sends requests to observe system behavior during chaos:

**Purpose**:
- Send requests every 1-2 seconds
- Log results (success/failure, response time)
- Show circuit breaker state
- Run continuously during chaos experiments

**See**: `load_generator.sh` (will be created next)

### 4.2 Chaos Toolkit Experiments

Chaos Toolkit provides declarative YAML files for experiments:

**Benefits**:
- Repeatable experiments
- Automatic rollback on failure
- Observability built-in
- Version controllable

**See**: `experiments/*.yaml` (will be created next)

### 4.3 Monitoring Commands

**Real-time monitoring during experiments**:

```bash
# Terminal 1: Load generator
./load_generator.sh

# Terminal 2: Client logs (watch circuit breaker)
kubectl logs -f deployment/client-deployment | grep -i "circuit\|breaker\|retry"

# Terminal 3: Backend logs
kubectl logs -f deployment/backend-deployment

# Terminal 4: Pod status
watch -n 1 'kubectl get pods; echo ""; kubectl get svc'

# Terminal 5: Execute chaos
# (run chaos commands here)
```

---

## 5. Expected Results Summary

### Experiment 1: Pod Failure
| Metric | Expected Value | Why This Matters |
|--------|---------------|------------------|
| Circuit Opening Time | <20 seconds | Demonstrates fast failure detection |
| Fast-Fail Response Time | <0.01 seconds | Proves resource protection |
| Recovery Time | 30-60 seconds | Shows automatic recovery |
| Manual Intervention | None | Validates self-healing |

### Experiment 2: Network Latency
| Metric | Expected Value | Why This Matters |
|--------|---------------|------------------|
| Success Rate | 100% | System tolerates delays |
| Circuit State | CLOSED | Doesn't falsely trigger on slow responses |
| Response Time | 2-3 seconds | Requests complete despite delay |

### Experiment 3: Network Partition
| Metric | Expected Value | Why This Matters |
|--------|---------------|------------------|
| Retries per Request | 3 attempts | Retry exhausts before giving up |
| Failures to Open Circuit | 5 requests | Circuit detects persistent pattern |
| Time to Recovery | 40-70 seconds | Complete failure → recovery cycle |

---

## 6. Comparison: With vs Without Resilience Patterns

### Scenario: Backend Pod Deleted

**WITHOUT Resilience Patterns**:
```
Request 1:  Timeout (5s) → Error
Request 2:  Timeout (5s) → Error  
Request 3:  Timeout (5s) → Error
... continues for all requests ...
Request 20: Timeout (5s) → Error

Total wasted time: 100+ seconds
User experience: Every request takes 5s to fail
System impact: All threads blocked waiting
```

**WITH Circuit Breaker + Retry**:
```
Request 1:  Retry × 3 → Fail (7s)  [Circuit: 1/5]
Request 2:  Retry × 3 → Fail (7s)  [Circuit: 2/5]
Request 3:  Retry × 3 → Fail (7s)  [Circuit: 3/5]
Request 4:  Retry × 3 → Fail (7s)  [Circuit: 4/5]
Request 5:  Retry × 3 → Fail (7s)  [Circuit: OPEN]
Request 6:  Fast Fail (0.000s) ⚡
Request 7:  Fast Fail (0.000s) ⚡
... all subsequent requests fail fast ...
Request 20: Fast Fail (0.000s) ⚡

Total time for 20 requests: ~35s vs 100s
Improvement: 65% faster
User experience: Fast error feedback after detection
System impact: Minimal, threads not blocked
```

**KEY INSIGHT**: The chaos experiment **proves** that our resilience patterns provide real protection, not just theoretical benefits.

---

## 7. Safety Considerations

### 7.1 Experiment Safety Checklist

Before running chaos experiments:

- [ ] **Isolated Environment**: Using Minikube (local), not production
- [ ] **Backup Plan**: Know how to restore system (kubectl rollout restart)
- [ ] **Time Box**: Set maximum experiment duration (10 minutes)
- [ ] **Rollback Ready**: Have cleanup commands prepared
- [ ] **Monitoring**: All logging terminals ready
- [ ] **Documentation**: Recording what you do for the report

### 7.2 Blast Radius Limitation

Our experiments are safe because:
- ✅ Local Minikube cluster (not affecting others)
- ✅ No real user traffic
- ✅ No data persistence (in-memory only)
- ✅ Kubernetes will auto-restart failed pods
- ✅ Can fully reset with `kubectl delete` + `kubectl apply`

### 7.3 Emergency Rollback

If something goes wrong:

```bash
# Stop load generator (Ctrl+C)

# Restore backend if needed
kubectl scale deployment/backend-deployment --replicas=1

# Restart client if hung
kubectl rollout restart deployment/client-deployment

# Nuclear option: restart everything
kubectl delete -f kubernetes/
./kubernetes/deploy.sh

# Or reset entire Minikube
minikube delete
minikube start
```

---

## 8. Report Structure for Part C

Your chaos engineering report should include:

### 8.1 Introduction
- Brief explanation of chaos engineering
- Why we use it
- What we're testing (resilience patterns)

### 8.2 For Each Experiment
- **Hypothesis**: What we expect to happen
- **Setup**: Environment and tools
- **Execution**: Step-by-step what we did
- **Observations**: What actually happened (with logs/screenshots)
- **Analysis**: Why it happened, what it proves
- **Comparison**: With vs without resilience patterns

### 8.3 Overall Analysis
- How experiments validated resilience patterns
- Architectural insights gained
- Trade-offs observed in practice
- Recommendations for production

### 8.4 Conclusion
- Summary of key findings
- Confidence gained in system resilience
- Areas for future improvement

---

## 9. Next Steps

Now let's create the actual scripts and experiment files:

1. ✅ Load generator script
2. ✅ Chaos Toolkit experiment definitions
3. ✅ Network policy YAML
4. ✅ Test execution guide
5. ✅ Results template

Ready to create these? 🚀