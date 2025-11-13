# ConfigMap Guide - Externalizing Configuration in Kubernetes

## Overview

This guide explains how to use Kubernetes ConfigMaps to externalize configuration from your microservices, demonstrating best practices for configuration management in containerized environments.

## What are ConfigMaps?

ConfigMaps are Kubernetes resources that allow you to **decouple configuration** from container images. They store configuration data as **key-value pairs** that can be consumed by pods as environment variables, command-line arguments, or configuration files.

## Benefits of ConfigMaps vs Hardcoded Environment Variables

### 1. **Separation of Concerns**

**Without ConfigMaps (Hardcoded):**
```yaml
# Deployment file contains configuration
env:
- name: SPRING_DATASOURCE_URL
  value: "jdbc:postgresql://product-db:5432/productdb"
- name: LOGGING_LEVEL_ROOT
  value: "INFO"
- name: EUREKA_CLIENT_SERVICEURL_DEFAULTZONE
  value: "http://eureka-server:8761/eureka/"
```

**With ConfigMaps (Externalized):**
```yaml
# Deployment file references ConfigMap
envFrom:
- configMapRef:
    name: product-service-config

# Configuration is in separate ConfigMap file
apiVersion: v1
kind: ConfigMap
metadata:
  name: product-service-config
data:
  SPRING_DATASOURCE_URL: "jdbc:postgresql://product-db:5432/productdb"
  LOGGING_LEVEL_ROOT: "INFO"
  EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: "http://eureka-server:8761/eureka/"
```

**Benefit**: Configuration and deployment logic are separated, making both easier to manage.

### 2. **Update Configuration Without Rebuilding Images**

**Problem with Hardcoded Values:**
- Change configuration → Modify deployment → Apply → Pods recreated
- Same image, but requires pod restart

**Solution with ConfigMaps:**
- Change ConfigMap → Apply → Pods recreated automatically
- **OR** update without restart (see "Hot Reload" section)

**Example:**
```bash
# Change log level from INFO to DEBUG
kubectl edit configmap product-service-config
# Change LOGGING_LEVEL_ROOT: "INFO" to "DEBUG"

# Pods pick up new configuration on restart
kubectl rollout restart deployment product-service
```

### 3. **Environment-Specific Configuration**

**Development vs Production:**
```yaml
# dev-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: product-service-config
data:
  LOGGING_LEVEL_ROOT: "DEBUG"
  SPRING_JPA_SHOW_SQL: "true"

# prod-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: product-service-config
data:
  LOGGING_LEVEL_ROOT: "WARN"
  SPRING_JPA_SHOW_SQL: "false"
```

**Benefit**: Same deployment manifest, different ConfigMaps per environment.

### 4. **Centralized Configuration Management**

**Multiple Services, Shared Configuration:**
```yaml
# Shared Eureka configuration for all services
apiVersion: v1
kind: ConfigMap
metadata:
  name: eureka-config
data:
  EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: "http://eureka-server:8761/eureka/"
  EUREKA_CLIENT_REGISTER_WITH_EUREKA: "true"
  EUREKA_CLIENT_FETCH_REGISTRY: "true"
```

**Each service can reference:**
```yaml
envFrom:
- configMapRef:
    name: eureka-config  # Shared
- configMapRef:
    name: product-service-config  # Service-specific
```

### 5. **Version Control and Auditing**

ConfigMaps can be:
- ✅ Stored in Git alongside manifests
- ✅ Reviewed in pull requests
- ✅ Tracked with version history
- ✅ Rolled back if needed

**Example Git Commit:**
```
feat: increase database connection pool

Modified: k8s/configmaps.yaml
- HIKARI_MAXIMUM_POOL_SIZE: "10"
+ HIKARI_MAXIMUM_POOL_SIZE: "20"
```

### 6. **Reduced Image Size and Complexity**

**Hardcoded in Image:**
- Configuration baked into image
- Separate images per environment
- Larger image registry

**Externalized with ConfigMaps:**
- Same image for all environments
- Configuration injected at runtime
- Smaller, reusable images

## ConfigMap Structure in This Project

### Product Service ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: product-service-config
  labels:
    app: product-service
    tier: backend
data:
  # Application Configuration
  SPRING_APPLICATION_NAME: "product-service"
  SERVER_PORT: "8080"

  # Database Configuration
  SPRING_DATASOURCE_URL: "jdbc:postgresql://product-db:5432/productdb"
  SPRING_DATASOURCE_USERNAME: "postgres"

  # Eureka Configuration
  EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: "http://eureka-server:8761/eureka/"
  EUREKA_INSTANCE_HOSTNAME: "product-service"

  # JVM Configuration
  JAVA_OPTS: "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"

  # Logging Configuration
  LOGGING_LEVEL_ROOT: "INFO"
  LOGGING_LEVEL_COM_MYPRODUCT: "DEBUG"
```

**Note**: Sensitive data (passwords) should use **Secrets**, not ConfigMaps.

### Order Service ConfigMap

Includes Product Service integration:
```yaml
data:
  # Product Service Integration
  PRODUCT_SERVICE_URL: "http://product-service:8080"

  # Feign Configuration
  FEIGN_CLIENT_CONFIG_DEFAULT_CONNECTTIMEOUT: "5000"
  FEIGN_CLIENT_CONFIG_DEFAULT_READTIMEOUT: "10000"
```

### API Gateway ConfigMap

Includes routing configuration:
```yaml
data:
  # Gateway Routes
  SPRING_CLOUD_GATEWAY_ROUTES_0_ID: "product-service"
  SPRING_CLOUD_GATEWAY_ROUTES_0_URI: "lb://product-service"
  SPRING_CLOUD_GATEWAY_ROUTES_0_PREDICATES_0: "Path=/api/products/**"
  SPRING_CLOUD_GATEWAY_ROUTES_0_FILTERS_0: "StripPrefix=1"
```

## Deployment Workflow

### 1. Deploy ConfigMaps First

```bash
# Deploy all ConfigMaps
kubectl apply -f k8s/configmaps.yaml

# Verify ConfigMaps created
kubectl get configmaps
```

**Expected Output:**
```
NAME                      DATA   AGE
product-service-config    15     10s
order-service-config      18     10s
api-gateway-config        25     10s
```

### 2. Deploy Services

```bash
# Deploy services (they reference ConfigMaps)
kubectl apply -f k8s/products-deployment.yaml
kubectl apply -f k8s/orders-deployment.yaml
kubectl apply -f k8s/gateway-deployment.yaml
```

### 3. Verify Configuration Loaded

```bash
# Check environment variables in pod
PRODUCT_POD=$(kubectl get pods -l app=product-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec $PRODUCT_POD -- env | grep SPRING

# Should show all environment variables from ConfigMap
```

## Updating Configuration

### Method 1: Edit ConfigMap Directly

```bash
# Edit ConfigMap
kubectl edit configmap product-service-config

# Change values, save, and exit

# Restart deployment to pick up changes
kubectl rollout restart deployment product-service

# Verify update
kubectl rollout status deployment product-service
```

### Method 2: Apply Updated File

```bash
# Modify k8s/configmaps.yaml
# Change: LOGGING_LEVEL_ROOT: "INFO"
# To:     LOGGING_LEVEL_ROOT: "DEBUG"

# Apply changes
kubectl apply -f k8s/configmaps.yaml

# Restart deployment
kubectl rollout restart deployment product-service
```

### Method 3: Patch ConfigMap

```bash
# Update single value
kubectl patch configmap product-service-config \
  -p '{"data":{"LOGGING_LEVEL_ROOT":"DEBUG"}}'

# Restart deployment
kubectl rollout restart deployment product-service
```

## Viewing ConfigMap Data

### View All ConfigMaps

```bash
kubectl get configmaps
```

### View ConfigMap Details

```bash
# View full ConfigMap
kubectl describe configmap product-service-config

# View as YAML
kubectl get configmap product-service-config -o yaml

# View specific key
kubectl get configmap product-service-config -o jsonpath='{.data.LOGGING_LEVEL_ROOT}'
```

## Hot Reload (Update Without Restart)

Some applications support **hot reload** of configuration without restart.

### Using Mounted ConfigMaps

```yaml
# Mount ConfigMap as volume
volumes:
- name: config
  configMap:
    name: product-service-config

volumeMounts:
- name: config
  mountPath: /config
  readOnly: true
```

**Application reads from file:**
```properties
spring.config.import=file:/config/application.properties
```

**Update ConfigMap:**
```bash
kubectl apply -f k8s/configmaps.yaml
# Pods automatically see updated files (may take 60s)
```

**Note**: Application must support file-based hot reload (Spring Cloud Config, etc.)

## ConfigMaps vs Secrets

| Feature | ConfigMap | Secret |
|---------|-----------|--------|
| **Purpose** | Non-sensitive config | Sensitive data |
| **Storage** | Plain text | Base64 encoded |
| **Use Cases** | URLs, timeouts, flags | Passwords, API keys, certificates |
| **Best Practice** | Public config data | Private credentials |

### Example: Separating Secrets

**ConfigMap (non-sensitive):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: product-service-config
data:
  SPRING_DATASOURCE_URL: "jdbc:postgresql://product-db:5432/productdb"
  SPRING_DATASOURCE_USERNAME: "postgres"
```

**Secret (sensitive):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: product-service-secret
type: Opaque
data:
  SPRING_DATASOURCE_PASSWORD: cGFzc3dvcmQ=  # base64 encoded
```

**Deployment uses both:**
```yaml
envFrom:
- configMapRef:
    name: product-service-config
- secretRef:
    name: product-service-secret
```

## Best Practices

### 1. ✅ **Use Descriptive Names**

```yaml
# Good
name: product-service-config
name: order-service-config

# Bad
name: config
name: app-config
```

### 2. ✅ **Label ConfigMaps**

```yaml
metadata:
  name: product-service-config
  labels:
    app: product-service
    tier: backend
    env: production
```

### 3. ✅ **Document Configuration**

```yaml
data:
  # Database connection timeout in milliseconds
  SPRING_DATASOURCE_HIKARI_CONNECTION_TIMEOUT: "30000"

  # Maximum database connections in pool
  SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE: "10"
```

### 4. ✅ **Use Separate ConfigMaps per Service**

```yaml
# Don't: Single ConfigMap for all services
name: microservices-config

# Do: Separate ConfigMaps
name: product-service-config
name: order-service-config
name: api-gateway-config
```

### 5. ✅ **Never Store Secrets in ConfigMaps**

```yaml
# ❌ Bad - Plain text password
data:
  DATABASE_PASSWORD: "mypassword123"

# ✅ Good - Use Secret
apiVersion: v1
kind: Secret
data:
  DATABASE_PASSWORD: bXlwYXNzd29yZDEyMw==
```

### 6. ✅ **Version ConfigMaps for Critical Changes**

```yaml
# ConfigMap v1
metadata:
  name: product-service-config-v1

# ConfigMap v2
metadata:
  name: product-service-config-v2

# Deployment references specific version
envFrom:
- configMapRef:
    name: product-service-config-v2
```

## Comparison: Before and After ConfigMaps

### Before (Hardcoded in Deployment)

**products-deployment.yaml:**
```yaml
spec:
  containers:
  - name: product-service
    image: lab04-product-service:latest
    env:
    - name: SPRING_APPLICATION_NAME
      value: "product-service"
    - name: SPRING_DATASOURCE_URL
      value: "jdbc:postgresql://product-db:5432/productdb"
    - name: SPRING_DATASOURCE_USERNAME
      value: "postgres"
    - name: SPRING_DATASOURCE_PASSWORD
      value: "password"
    - name: EUREKA_CLIENT_SERVICEURL_DEFAULTZONE
      value: "http://eureka-server:8761/eureka/"
    - name: LOGGING_LEVEL_ROOT
      value: "INFO"
```

**Problems:**
- ❌ Configuration mixed with deployment logic
- ❌ Hard to update (need to edit deployment)
- ❌ No centralized config management
- ❌ Difficult to manage across environments

### After (ConfigMap)

**products-deployment.yaml:**
```yaml
spec:
  containers:
  - name: product-service
    image: lab04-product-service:latest
    envFrom:
    - configMapRef:
        name: product-service-config
    env:
    - name: SPRING_DATASOURCE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: product-service-secret
          key: password
```

**configmaps.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: product-service-config
data:
  SPRING_APPLICATION_NAME: "product-service"
  SPRING_DATASOURCE_URL: "jdbc:postgresql://product-db:5432/productdb"
  SPRING_DATASOURCE_USERNAME: "postgres"
  EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: "http://eureka-server:8761/eureka/"
  LOGGING_LEVEL_ROOT: "INFO"
```

**Benefits:**
- ✅ Clean separation of config and deployment
- ✅ Easy to update (edit ConfigMap)
- ✅ Centralized configuration
- ✅ Environment-specific configs

## Testing ConfigMap Changes

### Scenario: Change Log Level from INFO to DEBUG

```bash
# 1. View current log level
kubectl get configmap product-service-config -o jsonpath='{.data.LOGGING_LEVEL_ROOT}'
# Output: INFO

# 2. Update ConfigMap
kubectl patch configmap product-service-config \
  -p '{"data":{"LOGGING_LEVEL_ROOT":"DEBUG"}}'

# 3. Verify change
kubectl get configmap product-service-config -o jsonpath='{.data.LOGGING_LEVEL_ROOT}'
# Output: DEBUG

# 4. Restart deployment to apply
kubectl rollout restart deployment product-service

# 5. Check pod logs for debug output
kubectl logs -l app=product-service --tail=50 | grep DEBUG
```

## Summary: ConfigMaps vs Hardcoded Comparison

| Aspect | Hardcoded | ConfigMap |
|--------|-----------|-----------|
| **Location** | Deployment manifest | Separate ConfigMap resource |
| **Update Method** | Edit deployment, apply | Edit ConfigMap, restart |
| **Reusability** | ❌ Duplicated per deployment | ✅ Reusable across pods |
| **Environment Mgmt** | ❌ Hard (multiple deployments) | ✅ Easy (swap ConfigMap) |
| **Version Control** | ⚠️ Mixed with deployment | ✅ Separate, trackable |
| **Maintainability** | ❌ Scattered config | ✅ Centralized |
| **Testing** | ❌ Requires deployment changes | ✅ Just update ConfigMap |

## Commands Quick Reference

```bash
# Deploy ConfigMaps
kubectl apply -f k8s/configmaps.yaml

# View ConfigMaps
kubectl get configmaps
kubectl describe configmap product-service-config

# View ConfigMap data
kubectl get configmap product-service-config -o yaml

# Update ConfigMap
kubectl edit configmap product-service-config
kubectl apply -f k8s/configmaps.yaml

# Patch single value
kubectl patch configmap product-service-config \
  -p '{"data":{"LOGGING_LEVEL_ROOT":"DEBUG"}}'

# Restart deployment to apply changes
kubectl rollout restart deployment product-service

# Verify pod picked up new config
kubectl exec <pod-name> -- env | grep LOGGING_LEVEL_ROOT

# Delete ConfigMap
kubectl delete configmap product-service-config
```

## For Lab Report

### Key Points to Highlight

1. **Separation of Concerns**: Configuration is decoupled from deployment logic
2. **Flexibility**: Update config without rebuilding images
3. **Environment Management**: Same image, different configs per environment
4. **Best Practice**: Industry standard for containerized applications
5. **Maintainability**: Centralized configuration management
6. **Version Control**: Configuration changes tracked in Git

### Demonstration Steps

1. Deploy services with ConfigMaps
2. Update log level via ConfigMap
3. Restart deployment to apply changes
4. Show logs reflecting new configuration
5. Compare before/after deployment manifests

This approach demonstrates modern cloud-native configuration management practices suitable for production environments.
