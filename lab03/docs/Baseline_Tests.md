# Baseline Test - Manual Testing Guide

This guide provides step-by-step instructions for conducting baseline tests WITHOUT resilience patterns.

## 🎯 Purpose

The baseline test establishes a "control group" to compare system behavior:
- **Before**: Without resilience patterns (this test)
- **After**: With Circuit Breaker and Retry patterns (Part B)

## 📋 Prerequisites

1. Kubernetes services running:
   ```bash
   kubectl get pods
   kubectl get svc
   ```

2. Minikube service tunnel active in a separate terminal:
   ```bash
   minikube service client-service
   ```

3. Get the Client Service URL:
   ```bash
   CLIENT_URL=$(minikube service client-service --url)
   echo $CLIENT_URL
   ```

## 🧪 Test Scenarios

### Scenario 1: Normal Operation (Baseline) ✅

**Purpose**: Establish baseline performance and prove system works correctly.

**Steps**:
```bash
# 1. Health check
curl $CLIENT_URL/health

# 2. Get all users (should return 15 users)
curl $CLIENT_URL/client/users

# 3. Get single user
curl $CLIENT_URL/client/users/1

# 4. Create a new user
curl -X POST $CLIENT_URL/client/users \
  -H "Content-Type: application/json" \
  -d '{"id": 100, "name": "Baseline Test", "email": "baseline@test.com"}'
```

**Expected Results**:
- ✅ All requests return HTTP 200
- ✅ Response time: < 500ms
- ✅ Data is correct

**What to Document**:
- Screenshot of successful responses
- Note the response times
- Client logs showing successful requests

---

### Scenario 2: Backend Delay (Slow Response) 🐌

**Purpose**: Observe how delays affect the client WITHOUT retry logic.

**Steps**:

1. **Configure 100% delay rate with 3-second delays**:
   
   You need to access the backend directly. First, set up port-forwarding:
   ```bash
   # In a new terminal
   kubectl port-forward service/backend-service 5000:5000
   ```
   
   Then configure delays:
   ```bash
   # In another terminal
   curl -X POST http://localhost:5000/configlatency \
     -H "Content-Type: application/json" \
     -d '{"delay_ms": 3000, "delay_rate": 1.0}'
   ```

2. **Make requests and observe the delay**:
   ```bash
   # This should take ~3+ seconds
   time curl $CLIENT_URL/client/users
   
   # Try multiple requests - each one blocks!
   for i in {1..3}; do
     echo "Request $i:"
     time curl $CLIENT_URL/client/users/$i
   done
   ```

**Expected Results**:
- ⚠️ Each request takes 3+ seconds
- ⚠️ Client waits (blocks) for the entire duration
- ⚠️ No automatic retry
- ⚠️ Poor user experience

**What to Document**:
- Screenshot showing long response times
- Client logs showing blocking behavior
- Note: "Without retry logic, a single slow request blocks the entire operation"

**Watch the logs**:
```bash
# In separate terminals
kubectl logs -f deployment/client-deployment
kubectl logs -f deployment/backend-deployment
```

---

### Scenario 3: Backend Errors (500) ❌

**Purpose**: Observe how errors propagate WITHOUT circuit breaker.

**Steps**:

1. **Configure 100% error rate**:
   ```bash
   curl -X POST http://localhost:5000/configfailure \
     -H "Content-Type: application/json" \
     -d '{"failure_rate": 1.0}'
   ```

2. **Make requests and observe failures**:
   ```bash
   # Should receive 500 error
   curl $CLIENT_URL/client/users
   
   # Try multiple times - keeps hitting failing backend!
   for i in {1..5}; do
     echo "Request $i:"
     curl $CLIENT_URL/client/users
     echo ""
   done
   ```

**Expected Results**:
- ❌ All requests fail with 500 errors
- ❌ Client keeps trying the failing backend
- ❌ No circuit breaker to stop the requests
- ❌ Errors propagate directly to user

**What to Document**:
- Screenshot of error responses
- Backend logs showing "FAULT INJECTED: 500 Error"
- Client logs showing errors passed through
- Note: "Without circuit breaker, client continues hitting failing service"

---

### Scenario 4: Mixed Failures (Realistic) ⚠️

**Purpose**: Simulate realistic conditions with intermittent failures.

**Steps**:

1. **Configure mixed failures** (30% errors, 30% delays):
   ```bash
   # Set error rate
   curl -X POST http://localhost:5000/configfailure \
     -H "Content-Type: application/json" \
     -d '{"failure_rate": 0.3}'
   
   # Set delay rate
   curl -X POST http://localhost:5000/configlatency \
     -H "Content-Type: application/json" \
     -d '{"delay_ms": 2000, "delay_rate": 0.3}'
   ```

2. **Make multiple requests**:
   ```bash
   for i in {1..10}; do
     echo "Request $i:"
     time curl $CLIENT_URL/client/users/1
     echo ""
     sleep 0.5
   done
   ```

**Expected Results**:
- 🎲 ~30% of requests succeed quickly
- 🐌 ~30% of requests take 2+ seconds
- ❌ ~30% of requests fail with 500
- 🎲 ~10% may have combined issues
- ⚠️ **Unpredictable user experience!**

**What to Document**:
- Mix of success, delays, and errors
- Logs showing random behavior
- Note: "Unpredictable behavior creates poor UX"

---

### Scenario 5: Complete Backend Failure (Pod Down) 💥

**Purpose**: Observe catastrophic failure WITHOUT resilience patterns.

**⚠️ Warning**: This is a destructive test!

**Steps**:

1. **Scale backend to 0 (simulate crash)**:
   ```bash
   kubectl scale deployment/backend-deployment --replicas=0
   
   # Wait a few seconds
   sleep 5
   ```

2. **Try to access the service**:
   ```bash
   # Should timeout or connection refused
   curl $CLIENT_URL/client/users
   
   # Check health
   curl $CLIENT_URL/health
   ```

3. **Check logs** (in separate terminals):
   ```bash
   kubectl logs -f deployment/client-deployment
   ```
   
   You should see errors like:
   - "Backend service unavailable"
   - "Connection refused"
   - "Timeout"

4. **Restore backend**:
   ```bash
   kubectl scale deployment/backend-deployment --replicas=1
   
   # Wait for it to be ready
   kubectl wait --for=condition=available --timeout=60s deployment/backend-deployment
   ```

5. **Test recovery**:
   ```bash
   # Should work now
   curl $CLIENT_URL/client/users
   ```

**Expected Results**:
- ❌ Complete service failure when backend is down
- ❌ Connection errors, timeouts
- ❌ Client cannot handle backend unavailability
- ✅ System recovers when backend comes back
- ⚠️ **But: No graceful degradation during outage!**

**What to Document**:
- Screenshot of connection errors
- Client logs showing "Backend service unavailable"
- Note: "Without circuit breaker, client has no fallback mechanism"

---

## 📊 Data Collection Checklist

For your lab report, collect the following for EACH scenario:

### Screenshots:
- [ ] Terminal output showing responses
- [ ] `kubectl logs` from client-deployment
- [ ] `kubectl logs` from backend-deployment
- [ ] Response times (use `time curl ...`)

### Observations:
- [ ] Behavior when backend is slow
- [ ] Behavior when backend returns errors
- [ ] Behavior when backend is completely down
- [ ] User experience impact
- [ ] Resource utilization (optional)

### Metrics:
- [ ] Response times for each scenario
- [ ] Error rates
- [ ] Number of failed requests

---

## 🎯 Key Observations for Report

After running all scenarios, document these architectural insights:

### 1. **No Retry Logic**
- Single transient error = complete failure
- No automatic recovery from temporary issues
- Poor resilience to network blips

### 2. **No Circuit Breaker**
- Client keeps hitting failing backend
- Wastes resources on doomed requests
- No "fail fast" mechanism
- Backend cannot recover under load

### 3. **No Graceful Degradation**
- Service either works or fails completely
- No fallback responses
- No cached data option
- Poor user experience during issues

### 4. **Direct Error Propagation**
- Backend errors become client errors
- No error transformation or handling
- Raw 500 errors exposed to users

### 5. **Blocking Behavior**
- Slow backend = slow client
- No timeout protection (beyond socket timeout)
- Resources tied up waiting

---

## 🚀 Next Steps

After completing baseline tests:

1. **Document all observations** in your report
2. **Save all logs and screenshots**
3. **Move to Part B**: Implement resilience patterns
4. **Compare**: Run same tests with Circuit Breaker and Retry
5. **Analyze trade-offs**: Document the improvements AND costs

---

## 💡 Tips

1. **Keep logs**: Don't delete test logs - you'll need them for comparison
2. **Take many screenshots**: Better to have too many than too few
3. **Note timestamps**: Helps correlate logs across services
4. **Be systematic**: Test one scenario at a time
5. **Reset between tests**: Clear fault injection between scenarios

---

## 🐛 Troubleshooting

### Port-forward not working?
```bash
# Check if service exists
kubectl get svc backend-service

# Try different port
kubectl port-forward service/backend-service 5001:5000
```

### Cannot configure backend?
```bash
# Check if backend pod is running
kubectl get pods -l app=backend

# Check backend logs
kubectl logs -l app=backend
```

### Client URL not accessible?
```bash
# Ensure tunnel is running
minikube service client-service

# Or use port-forward
kubectl port-forward service/client-service 8080:8080
```

---

Good luck with your baseline tests! 🚀
Remember: The more detailed your observations now, the better your analysis in Part B will be!