# PostgreSQL Databases for Microservices

This directory contains Kubernetes manifests for PostgreSQL databases used by the microservices.

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│  Product Service    │────▶│   product-db        │
│  (Port 8080)        │     │   (PostgreSQL)      │
└─────────────────────┘     └─────────────────────┘
                                    ↓
                            productdb database
                            (tables: products)

┌─────────────────────┐     ┌─────────────────────┐
│  Order Service      │────▶│   order-db          │
│  (Port 8081)        │     │   (PostgreSQL)      │
└─────────────────────┘     └─────────────────────┘
                                    ↓
                            orderdb database
                            (tables: orders)
```

## Database Details

### Product Database (`product-db`)
- **Database Name:** productdb
- **User:** postgres
- **Password:** password (stored in plain text for lab purposes)
- **Port:** 5432
- **Service Name:** product-db (DNS resolvable within cluster)
- **Storage:** 1Gi persistent volume

### Order Database (`order-db`)
- **Database Name:** orderdb
- **User:** postgres
- **Password:** password (stored in plain text for lab purposes)
- **Port:** 5432
- **Service Name:** order-db (DNS resolvable within cluster)
- **Storage:** 1Gi persistent volume

## StatefulSet vs Deployment

We use **StatefulSets** instead of Deployments for databases because:

1. **Stable Network Identity:** Each database pod gets a predictable name (product-db-0)
2. **Persistent Storage:** Each pod maintains its own persistent volume
3. **Ordered Deployment:** Pods are created sequentially (important for databases)
4. **Headless Service:** Direct pod-to-pod communication without load balancing

## Deployment Order

Databases must be deployed **before** the microservices:

```bash
# 1. Deploy databases first
kubectl apply -f k8s/databases/product-db.yaml
kubectl apply -f k8s/databases/order-db.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=product-db --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-db --timeout=300s

# 2. Then deploy services
kubectl apply -f k8s/products-deployment.yaml
kubectl apply -f k8s/orders-deployment.yaml
kubectl apply -f k8s/gateway-deployment.yaml
```

## Resource Allocation

Each database pod:
- **Memory:** 256Mi (request) / 512Mi (limit)
- **CPU:** 250m (request) / 500m (limit)
- **Storage:** 1Gi persistent volume

## Health Checks

### Liveness Probe
- **Command:** `pg_isready -U postgres`
- **Initial Delay:** 30 seconds
- **Period:** 10 seconds
- **Timeout:** 5 seconds

### Readiness Probe
- **Command:** `pg_isready -U postgres`
- **Initial Delay:** 5 seconds
- **Period:** 5 seconds
- **Timeout:** 3 seconds

## Verification Commands

### Check Database Pods
```bash
# Check if pods are running
kubectl get pods -l tier=database

# Check StatefulSet status
kubectl get statefulsets
```

### Check Database Services
```bash
# View database services
kubectl get svc -l tier=database

# Describe product-db service
kubectl describe svc product-db
```

### Connect to Database
```bash
# Connect to product-db pod
kubectl exec -it product-db-0 -- psql -U postgres -d productdb

# Connect to order-db pod
kubectl exec -it order-db-0 -- psql -U postgres -d orderdb
```

### Test Database Connectivity from Service Pods
```bash
# Get product-service pod name
PRODUCT_POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')

# Test DNS resolution
kubectl exec $PRODUCT_POD -- nslookup product-db

# Test database connection (requires psql client in service pod)
kubectl exec $PRODUCT_POD -- curl -v telnet://product-db:5432
```

## Database Schema

### Product Database Tables
The `product-service` creates these tables automatically:

```sql
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Order Database Tables
The `order-service` creates these tables automatically:

```sql
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    ref_number VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES orders(id),
    sku VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2)
);
```

## Troubleshooting

### Pod Not Starting
```bash
# Check pod events
kubectl describe pod product-db-0

# Check logs
kubectl logs product-db-0
```

### Persistent Volume Issues
```bash
# Check persistent volumes
kubectl get pv

# Check persistent volume claims
kubectl get pvc
```

### Connection Refused from Services
```bash
# Verify service is running
kubectl get svc product-db

# Check if port 5432 is open
kubectl exec product-db-0 -- netstat -tlnp | grep 5432

# Test connection from a service pod
PRODUCT_POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec $PRODUCT_POD -- nc -zv product-db 5432
```

### Database Performance
```bash
# Check resource usage
kubectl top pods -l tier=database

# View detailed resource metrics
kubectl describe pod product-db-0 | grep -A 5 "Limits:"
```

## Security Notes

⚠️ **For Lab Purposes Only:**
- Passwords are stored in plain text in manifests
- No encryption at rest
- No network policies restricting access

🔒 **Production Best Practices:**
1. Use Kubernetes Secrets for passwords:
   ```yaml
   env:
   - name: POSTGRES_PASSWORD
     valueFrom:
       secretKeyRef:
         name: product-db-secret
         key: password
   ```

2. Enable TLS/SSL for database connections
3. Implement Network Policies to restrict database access
4. Use managed database services (AWS RDS, Google Cloud SQL)
5. Enable encryption at rest for persistent volumes

## Cleanup

To remove databases:

```bash
# Delete databases
kubectl delete -f k8s/databases/order-db.yaml
kubectl delete -f k8s/databases/product-db.yaml

# Delete persistent volume claims (optional - removes data)
kubectl delete pvc postgres-storage-product-db-0
kubectl delete pvc postgres-storage-order-db-0
```

## Why PostgreSQL?

We use PostgreSQL because:
1. **Production-Ready:** Industry-standard relational database
2. **Feature-Rich:** ACID compliance, transactions, constraints
3. **Kubernetes Native:** Official Docker images, StatefulSet compatible
4. **Microservices Pattern:** Each service has its own database (database-per-service pattern)

This demonstrates the **Database-per-Service** pattern in microservices architecture, where each service owns its data and cannot directly access another service's database.
