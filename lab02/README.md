# COMP41720 Distributed Systems - Lab 2
## Distributed Data Management and Consistency Models

### Author
XINCHI JIAN

### Project Overview
This lab explores fundamental architectural principles and challenges in storing and managing data across distributed systems. The project implements various replication strategies and consistency models using Apache Cassandra, demonstrating practical trade-offs in the context of the CAP Theorem.

---

## Table of Contents
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Running Experiments](#running-experiments)
- [Configuration Details](#configuration-details)
- [Key Findings](#key-findings)
- [Stopping the Cluster](#stopping-the-cluster)
- [Troubleshooting](#troubleshooting)

---

## System Architecture

This project implements a **3-node Apache Cassandra cluster** to demonstrate:
- **Replication Strategies**: Configurable replication factors and write concerns
- **Consistency Models**: Strong consistency and eventual consistency
- **Leaderless Architecture**: Multi-primary model with conflict resolution
- **Fault Tolerance**: Node failure simulation and partition tolerance

**Database Choice**: Apache Cassandra
- Tunable consistency levels
- Leaderless replication model
- Excellent demonstration of CAP theorem trade-offs

---

## Prerequisites

Before running this project, ensure you have installed:
- **Docker** (version 20.0 or higher)
- **Docker Compose** (version 1.29 or higher)
- **Python** (version 3.8 or higher)
- **Python packages**: cassandra-driver, pandas (installed via requirements.txt)

---

## Quick Start

### 1. Start the Cassandra Cluster

```bash
# Navigate to project root directory
cd lab02

# Start the 3-node Cassandra cluster using Docker Compose
docker-compose up -d

# Wait for cluster initialization (approximately 60-90 seconds)
# Verify cluster status
docker exec -it cassandra-node1 nodetool status
```

**Expected Output**: All 3 nodes should show status `UN` (Up/Normal)

### 2. Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Initialize Database Connection

```bash
cd CL_Experience
python test_connection.py
```

This script verifies the cluster connection and creates the necessary keyspace and tables.

---

## Project Structure

```
lab02/
├── docker-compose.yml              # Cassandra 3-node cluster configuration
├── README.md                       # This file
├── Lab02_Report_XINCHI_JIAN.pdf   # Detailed analysis and findings
│
├── CL_Experience/                  # Part B: Replication Strategy Experiments
│   ├── test_connection.py         # Database connection verification
│   └── write_lantency_test.py     # Write concern and latency analysis
│
├── Consistency Model test/         # Part C: Consistency Model Experiments
│   ├── strong_consistency_test.py # Strong consistency demonstration
│   └── eventual_consistency_test.py # Eventual consistency demonstration
│
└── Leaderless model test/          # Additional: Concurrent Conflict Tests
    └── concurrent_conflict_test.py # Write conflict and resolution demo
```

---

## Running Experiments

### Part A: Verify Cluster Setup

```bash
# Check cluster status
docker exec -it cassandra-node1 nodetool status

# Access Cassandra Query Language Shell
docker exec -it cassandra-node1 cqlsh

# Create a keyspace for testing
create keyspace if not exists test_rf_3 with replication = {'class':'SimpleStrategy', 'replication_factor':3};

DESCRIBE KEYSPACES;

USE test_rf_3;

# Create initial data model
CREATE TABLE IF NOT EXISTS user_profiles (
	user_id int PRIMARY KEY, 
	username text,
	email text,
	last_update_timestamp timestamp 
);

DESCRIBE TABLES;
```

---

### Part B: Replication Strategy Experiments

#### Experiment 1: Write Latency vs. Consistency Levels

```bash
cd CL_Experience
python write_lantency_test.py
```

**What This Tests**:
- Write latency comparison across different consistency levels (ONE, QUORUM, ALL)
- Trade-offs between durability and performance
- Impact of replication factor on write operations

---

### Part C: Consistency Model Experiments

#### Experiment 2: Strong Consistency

```bash
cd "Consistency Model test"
python strong_consistency_test.py
```

**What This Tests**:
- Immediate read consistency after writes
- Write and read at QUORUM level
- Data visibility across different nodes
- Behavior during network partition simulation

**Key Observation**: Demonstrates the **CP** (Consistency + Partition Tolerance) trade-off

---

#### Experiment 3: Eventual Consistency

```bash
cd "Consistency Model test"
python eventual_consistency_test.py
```

**What This Tests**:
- Write at ONE, read at ONE consistency level
- Potential for stale reads immediately after writes
- Convergence time for data propagation
- Polling loop to observe eventual convergence

**Key Observation**: Demonstrates the **AP** (Availability + Partition Tolerance) trade-off

---

### Additional Experiments

#### Experiment 4: Concurrent Write Conflicts

```bash
cd "Leaderless model test"
python concurrent_conflict_test.py
```

**What This Tests**:
- Simultaneous writes to the same key from different nodes
- Last-Write-Wins (LWW) conflict resolution
- Timestamp-based ordering in leaderless architecture

---

## Configuration Details

### Cassandra Cluster Configuration

**docker-compose.yml** defines:
- **3 nodes**: cassandra-node1, cassandra-node2, cassandra-node3
- **Replication Strategy**: NetworkTopologyStrategy
- **Replication Factor**: 3 (configurable in experiments)
- **Consistency Levels**: Tunable (ONE, QUORUM, ALL)

### Keyspace Configuration

```cql
create keyspace if not exists test_rf_3 with replication = {'class':'SimpleStrategy', 'replication_factor':3};
```

### Data Model

**UserProfile Table**:
```cql
CREATE TABLE IF NOT EXISTS user_profiles (
	user_id int PRIMARY KEY, 
	username text,
	email text,
	last_update_timestamp timestamp 
);
```

---

## Key Findings

### 1. CAP Theorem Trade-offs
- **Strong Consistency (CP)**: Ensures data correctness but reduces availability during partitions
- **Eventual Consistency (AP)**: Maximizes availability and performance at the cost of temporary inconsistency

### 2. Write Latency Analysis
- **ONE**: ~5-10ms average latency
- **QUORUM**: ~15-25ms average latency  
- **ALL**: ~30-50ms average latency

### 3. Use Case Recommendations
- **Strong Consistency**: Financial transactions, inventory management
- **Eventual Consistency**: Social media feeds, analytics, sensor data

For detailed analysis, architectural justifications, and comprehensive experimental results, please refer to **Lab02_Report_XINCHI_JIAN.pdf**.

---

## Stopping the Cluster

```bash
# Stop all containers
docker-compose down

# Remove volumes (clean slate for next run)
docker-compose down -v
```

---

## Troubleshooting

### Common Issues

**Issue**: Cluster nodes not connecting
```bash
# Check logs
docker logs cassandra-node1

# Restart cluster
docker-compose down
docker-compose up -d
```

**Issue**: Python connection timeout
- Ensure cluster has fully initialized (wait 90 seconds)
- Verify ports 9042, 9043, 9044 are not in use

**Issue**: "Unable to connect to Cassandra"
```bash
# Check if all nodes are up
docker ps

# Restart specific node
docker restart cassandra-node1
```

---

## Additional Resources

- [Apache Cassandra Documentation](https://cassandra.apache.org/doc/latest/)
- [CAP Theorem Explained](https://en.wikipedia.org/wiki/CAP_theorem)
- [Cassandra Consistency Levels](https://docs.datastax.com/en/cassandra-oss/3.x/cassandra/dml/dmlConfigConsistency.html)
