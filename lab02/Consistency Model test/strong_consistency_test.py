from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel
from cassandra import Unavailable, WriteTimeout, ReadTimeout, OperationTimedOut
import time
import subprocess
from datetime import datetime

# Configuration
NODES = [
    {'host': '127.0.0.1', 'port': 9042, 'name': 'Node-1', 'container': 'cassandra-1'},
    {'host': '127.0.0.1', 'port': 9043, 'name': 'Node-2', 'container': 'cassandra-2'},
    {'host': '127.0.0.1', 'port': 9044, 'name': 'Node-3', 'container': 'cassandra-3'}
]

KEYSPACE = 'test_rf_3'
NETWORK_NAME = 'lab02_cassandra-net'  # Docker network name


def print_section(title, char="="):
    """Print formatted section header"""
    print(f"\n{char * 80}")
    print(f"{title}".center(80))
    print(f"{char * 80}\n")


def print_step(step_num, description):
    """Print formatted step"""
    print(f"[Step {step_num}] {description}")


def print_result(message, success=True):
    """Print result with status symbol"""
    symbol = "✓" if success else "✗"
    print(f"  {symbol} {message}")


def connect_to_node(host, port, name, keyspace=KEYSPACE):
    """Connect to a single Cassandra node"""
    try:
        cluster = Cluster([host], port=port, connect_timeout=10, control_connection_timeout=10)
        session = cluster.connect(keyspace)
        return {'cluster': cluster, 'session': session, 'name': name}
    except Exception as e:
        print_result(f"Failed to connect to {name}: {e}", success=False)
        return None


def write_data_strong_consistency(session, user_id, username, email, consistency_level):
    """
    Write data with specified strong consistency level
    Returns: (success, latency_ms, error_message)
    """
    statement = f"""
        INSERT INTO test_write_CL 
        (user_id, username, email, last_update_timestamp) 
        VALUES ({user_id}, '{username}', '{email}', toTimestamp(now()))
    """
    
    try:
        start = time.perf_counter()
        stmt = SimpleStatement(statement, consistency_level=consistency_level)
        session.execute(stmt)
        latency = (time.perf_counter() - start) * 1000
        return (True, latency, None)
    except Unavailable as e:
        return (False, 0, f"Unavailable: {e.consistency} requires {e.required_replicas} replicas but only {e.alive_replicas} available")
    except WriteTimeout as e:
        return (False, 0, f"WriteTimeout: {e}")
    except OperationTimedOut as e:
        return (False, 0, f"OperationTimedOut: {e}")
    except Exception as e:
        return (False, 0, f"Error: {type(e).__name__}: {e}")


def read_data_strong_consistency(session, user_id, consistency_level):
    """
    Read data with specified strong consistency level
    Returns: (success, data, latency_ms, error_message)
    """
    query = f"""
        SELECT user_id, username, email, last_update_timestamp,
               WRITETIME(username) as write_timestamp
        FROM test_write_CL 
        WHERE user_id = {user_id}
    """
    
    try:
        start = time.perf_counter()
        stmt = SimpleStatement(query, consistency_level=consistency_level)
        result = session.execute(stmt)
        latency = (time.perf_counter() - start) * 1000
        row = result.one()
        return (True, row, latency, None)
    except Unavailable as e:
        return (False, None, 0, f"Unavailable: {e.consistency} requires {e.required_replicas} replicas but only {e.alive_replicas} available")
    except ReadTimeout as e:
        return (False, None, 0, f"ReadTimeout: {e}")
    except OperationTimedOut as e:
        return (False, None, 0, f"OperationTimedOut: {e}")
    except Exception as e:
        return (False, None, 0, f"Error: {type(e).__name__}: {e}")


def display_data_table(data_dict):
    """Display read data in table format"""
    print(f"\n{'Node':<15} {'Status':<15} {'Username':<25} {'Email':<30} {'Latency(ms)':<12}")
    print("-" * 100)
    
    for node_name, result in data_dict.items():
        success, data, latency, error = result
        if success and data:
            print(f"{node_name:<15} {'SUCCESS':<15} {data.username:<25} {data.email:<30} {latency:<12.2f}")
        elif success and not data:
            print(f"{node_name:<15} {'NO DATA':<15} {'N/A':<25} {'N/A':<30} {latency:<12.2f}")
        else:
            print(f"{node_name:<15} {'FAILED':<15} {error:<56}")
    print("-" * 100)


def isolate_node(container_name, network_name):
    """Disconnect a container from Docker network"""
    try:
        cmd = f"docker network disconnect {network_name} {container_name}"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
        else:
            print_result(f"Failed to isolate {container_name}: {result.stderr}", success=False)
            return False
    except Exception as e:
        print_result(f"Error isolating {container_name}: {e}", success=False)
        return False


def reconnect_node(container_name, network_name):
    """Reconnect a container to Docker network"""
    try:
        cmd = f"docker network connect {network_name} {container_name}"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
        else:
            print_result(f"Failed to reconnect {container_name}: {result.stderr}", success=False)
            return False
    except Exception as e:
        print_result(f"Error reconnecting {container_name}: {e}", success=False)
        return False


def experiment_1_strong_consistency_normal():
    """
    Experiment 1: Strong Consistency in Normal Conditions
    Verify that QUORUM reads immediately see QUORUM writes
    """
    print_section("EXPERIMENT 1: Strong Consistency - Normal Operation")
    
    print_step(1, "Connecting to all nodes")
    connections = []
    for node in NODES:
        conn = connect_to_node(node['host'], node['port'], node['name'])
        if conn:
            connections.append(conn)
            print_result(f"Connected to {node['name']}")
        else:
            print_result(f"Failed to connect to {node['name']}", success=False)
    
    if len(connections) < 2:
        print_result("Need at least 2 nodes for this experiment", success=False)
        return
    
    # Test configuration
    test_user_id = 1001
    test_username = "StrongConsistencyUser"
    test_email = "strong@example.com"
    
    print_step(2, "Writing with QUORUM consistency to Node-1")
    write_node = connections[0]
    
    success, write_latency, error = write_data_strong_consistency(
        write_node['session'],
        test_user_id,
        test_username,
        test_email,
        ConsistencyLevel.QUORUM
    )
    
    if success:
        print_result(f"Write succeeded with QUORUM (latency: {write_latency:.2f}ms)")
    else:
        print_result(f"Write failed: {error}", success=False)
        return
    
    print_step(3, "Immediately reading from ALL nodes with QUORUM consistency")
    print("  Testing if data is immediately consistent (no propagation delay)\n")
    
    # Read immediately (no delay)
    read_results = {}
    for conn in connections:
        success, data, latency, error = read_data_strong_consistency(
            conn['session'],
            test_user_id,
            ConsistencyLevel.QUORUM
        )
        read_results[conn['name']] = (success, data, latency, error)
    
    display_data_table(read_results)
    
    # Verify consistency
    print_step(4, "Verifying Strong Consistency")
    
    all_success = all(result[0] for result in read_results.values())
    all_data_present = all(result[1] is not None for result in read_results.values())
    
    if all_success and all_data_present:
        usernames = [result[1].username for result in read_results.values()]
        if len(set(usernames)) == 1 and usernames[0] == test_username:
            print_result("✅ STRONG CONSISTENCY VERIFIED")
            print_result("All nodes immediately returned the same data with QUORUM reads")
        else:
            print_result("❌ Data inconsistency detected", success=False)
    else:
        print_result("Some reads failed or returned no data", success=False)
    
    print_section("Analysis - Experiment 1", char="-")
    print("🔑 Key Observations:")
    print("  1. QUORUM write ensures data is written to majority (2 out of 3 nodes)")
    print("  2. QUORUM read ensures reading from majority (2 out of 3 nodes)")
    print("  3. Overlap guarantees at least one node has the latest data")
    print("  4. NO propagation delay needed - data immediately consistent")
    print()
    print("📊 CAP Theorem Perspective:")
    print("  • Consistency: STRONG ✓ (guaranteed by quorum overlap)")
    print("  • Availability: HIGH ✓ (can tolerate 1 node failure)")
    print("  • Partition Tolerance: LIMITED (requires majority quorum)")
    
    # Cleanup
    for conn in connections:
        conn['cluster'].shutdown()
    
    print()


def experiment_2_consistency_levels_comparison():
    """
    Experiment 2: Compare Different Consistency Levels
    Show trade-offs between ONE, QUORUM, and ALL
    """
    print_section("EXPERIMENT 2: Consistency Level Comparison")
    
    print_step(1, "Connecting to Node-1")
    write_node = connect_to_node(NODES[0]['host'], NODES[0]['port'], NODES[0]['name'])
    if not write_node:
        return
    
    read_node = connect_to_node(NODES[1]['host'], NODES[1]['port'], NODES[1]['name'])
    if not read_node:
        write_node['cluster'].shutdown()
        return
    
    print_result("Connected to write and read nodes")
    
    consistency_levels = [
        (ConsistencyLevel.ONE, "ONE"),
        (ConsistencyLevel.QUORUM, "QUORUM"),
        (ConsistencyLevel.ALL, "ALL")
    ]
    
    print_step(2, "Testing Write and Read with different consistency levels")
    print()
    
    results_table = []
    
    for i, (write_cl, write_name) in enumerate(consistency_levels):
        for j, (read_cl, read_name) in enumerate(consistency_levels):
            test_user_id = 2000 + i * 10 + j
            test_username = f"User_W{write_name}_R{read_name}"
            test_email = f"w{write_name.lower()}_r{read_name.lower()}@test.com"
            
            # Write
            write_success, write_latency, write_error = write_data_strong_consistency(
                write_node['session'],
                test_user_id,
                test_username,
                test_email,
                write_cl
            )
            
            # Immediate read
            read_success, read_data, read_latency, read_error = read_data_strong_consistency(
                read_node['session'],
                test_user_id,
                read_cl
            )
            
            # Check consistency
            is_consistent = False
            if write_success and read_success and read_data:
                is_consistent = read_data.username == test_username
            
            results_table.append({
                'write_cl': write_name,
                'read_cl': read_name,
                'write_success': write_success,
                'read_success': read_success,
                'consistent': is_consistent,
                'write_latency': write_latency,
                'read_latency': read_latency
            })
    
    print_step(3, "Results Summary")
    print()
    print(f"{'Write CL':<12} {'Read CL':<12} {'Write':<10} {'Read':<10} {'Consistent':<12} {'W-Latency(ms)':<15} {'R-Latency(ms)':<15}")
    print("-" * 100)
    
    for r in results_table:
        write_status = "✓ OK" if r['write_success'] else "✗ FAIL"
        read_status = "✓ OK" if r['read_success'] else "✗ FAIL"
        consistent_status = "✓ YES" if r['consistent'] else "✗ NO"
        
        print(f"{r['write_cl']:<12} {r['read_cl']:<12} {write_status:<10} {read_status:<10} "
              f"{consistent_status:<12} {r['write_latency']:<15.2f} {r['read_latency']:<15.2f}")
    
    print("-" * 100)
    
    print_section("Analysis - Experiment 2", char="-")
    print("🔑 Strong Consistency Guarantees:")
    print("  ✓ QUORUM Write + QUORUM Read = Immediate consistency")
    print("  ✓ ALL Write + ANY Read = Immediate consistency")
    print("  ✓ ANY Write + ALL Read = Immediate consistency")
    print()
    print("⚠️  Weak Consistency Examples:")
    print("  ✗ ONE Write + ONE Read = May read stale data")
    print("  ✗ ONE Write + QUORUM Read = May read stale data briefly")
    print()
    print("⚖️  Trade-offs:")
    print("  • ONE: Fast, available, but inconsistent")
    print("  • QUORUM: Balanced - consistent and reasonably available")
    print("  • ALL: Strongly consistent but less available (single node failure breaks it)")
    
    # Cleanup
    write_node['cluster'].shutdown()
    read_node['cluster'].shutdown()
    
    print()


def experiment_3_network_partition():
    """
    Experiment 3: Network Partition with Strong Consistency
    Demonstrate CAP theorem: Can't have both Consistency and Availability during Partition
    """
    print_section("EXPERIMENT 3: Network Partition - CAP Theorem Demonstration")
    
    print("⚠️  WARNING: This experiment requires Docker network manipulation")
    print("⚠️  Make sure you have permission to run Docker commands\n")
    
    print_step(1, "Connecting to all nodes (before partition)")
    connections = []
    for node in NODES:
        conn = connect_to_node(node['host'], node['port'], node['name'])
        if conn:
            connections.append(conn)
            print_result(f"Connected to {node['name']}")
    
    if len(connections) < 3:
        print_result("Need all 3 nodes for partition experiment", success=False)
        return
    
    # Baseline test
    print_step(2, "Baseline: Writing with QUORUM (normal operation)")
    baseline_user_id = 3001
    
    success, latency, error = write_data_strong_consistency(
        connections[0]['session'],
        baseline_user_id,
        "BaselineUser",
        "baseline@test.com",
        ConsistencyLevel.QUORUM
    )
    
    if success:
        print_result(f"Baseline write succeeded (latency: {latency:.2f}ms)")
    else:
        print_result(f"Baseline write failed: {error}", success=False)
    
    # Create partition
    print_step(3, "Creating network partition - Isolating Node-3")
    print(f"  Disconnecting {NODES[2]['container']} from network...\n")
    
    if not isolate_node(NODES[2]['container'], NETWORK_NAME):
        print_result("Failed to create partition - skipping partition tests", success=False)
        for conn in connections:
            conn['cluster'].shutdown()
        return
    
    print_result(f"Node-3 ({NODES[2]['container']}) isolated")
    print("  Current state: Node-1 and Node-2 can communicate, Node-3 is isolated")
    
    time.sleep(3)  # Wait for partition to take effect
    
    # Test 1: Write with QUORUM during partition (should succeed)
    print_step(4, "Test 1: Writing with QUORUM during partition")
    print("  Expectation: Should SUCCEED (2 nodes available = majority)")
    
    partition_user_id_1 = 3002
    success, latency, error = write_data_strong_consistency(
        connections[0]['session'],
        partition_user_id_1,
        "PartitionQuorumUser",
        "quorum@partition.com",
        ConsistencyLevel.QUORUM
    )
    
    if success:
        print_result(f"✅ QUORUM write SUCCEEDED during partition (latency: {latency:.2f}ms)")
        print_result("System chose AVAILABILITY with guaranteed CONSISTENCY (via majority)")
    else:
        print_result(f"❌ QUORUM write FAILED: {error}", success=False)
    
    # Test 2: Write with ALL during partition (should fail)
    print_step(5, "Test 2: Writing with ALL during partition")
    print("  Expectation: Should FAIL (need 3 nodes, only 2 available)")
    
    partition_user_id_2 = 3003
    success, latency, error = write_data_strong_consistency(
        connections[0]['session'],
        partition_user_id_2,
        "PartitionAllUser",
        "all@partition.com",
        ConsistencyLevel.ALL
    )
    
    if not success:
        print_result(f"✅ ALL write FAILED as expected: {error}")
        print_result("System chose CONSISTENCY over AVAILABILITY (strict requirement not met)")
    else:
        print_result(f"❌ Unexpected: ALL write succeeded (latency: {latency:.2f}ms)", success=False)
    
    # Test 3: Read from isolated node with QUORUM
    print_step(6, "Test 3: Attempting to read from isolated Node-3 with QUORUM")
    print("  Expectation: Should FAIL (node can't reach majority)")
    
    # Try to reconnect to Node-3 (will fail to reach cluster)
    print("  Attempting operations on isolated node...\n")
    
    success, data, latency, error = read_data_strong_consistency(
        connections[2]['session'],
        baseline_user_id,
        ConsistencyLevel.QUORUM
    )
    
    if not success:
        print_result(f"✅ Read from isolated node FAILED as expected: {error}")
        print_result("Isolated node cannot satisfy QUORUM requirement")
    else:
        print_result(f"❌ Unexpected: Read succeeded on isolated node", success=False)
    
    # Restore network
    print_step(7, "Healing partition - Reconnecting Node-3")
    
    if reconnect_node(NODES[2]['container'], NETWORK_NAME):
        print_result(f"Node-3 ({NODES[2]['container']}) reconnected")
        print("  Waiting 10 seconds for cluster to stabilize...")
        time.sleep(10)
        
        # Reconnect session
        connections[2]['cluster'].shutdown()
        connections[2] = connect_to_node(NODES[2]['host'], NODES[2]['port'], NODES[2]['name'])
        
        if connections[2]:
            print_result("Re-established connection to Node-3")
            
            # Verify data propagated
            print_step(8, "Verifying data consistency after partition healing")
            
            success, data, latency, error = read_data_strong_consistency(
                connections[2]['session'],
                partition_user_id_1,
                ConsistencyLevel.ONE
            )
            
            if success and data:
                print_result(f"Data written during partition is now visible on Node-3: {data.username}")
                print_result("Cluster has healed and converged to consistent state")
            else:
                print_result("Data not yet propagated to Node-3", success=False)
    
    # Analysis
    print_section("Analysis - Experiment 3: CAP Theorem in Action", char="=")
    
    print("🎯 CAP Theorem Observations:\n")
    
    print("1️⃣  During Network Partition:")
    print("  • QUORUM (Majority) Operations:")
    print("    ✓ Writes to majority partition: AVAILABLE + CONSISTENT")
    print("    ✗ Operations on minority: UNAVAILABLE (maintains consistency)")
    print()
    print("  • ALL Operations:")
    print("    ✗ Cannot proceed: UNAVAILABLE (prioritizes consistency)")
    print()
    print("  • ONE Operations (not tested, but predictable):")
    print("    ✓ Would succeed: AVAILABLE but potentially INCONSISTENT")
    print()
    
    print("2️⃣  CAP Trade-off Decisions:\n")
    print("  ┌─────────────────┬──────────────┬────────────────┐")
    print("  │ Consistency LVL │   Available? │  Consistent?   │")
    print("  ├─────────────────┼──────────────┼────────────────┤")
    print("  │ ONE             │      ✓       │       ✗        │")
    print("  │ QUORUM          │    ✓ (AP)    │     ✓ (CP)     │")
    print("  │ ALL             │      ✗       │       ✓        │")
    print("  └─────────────────┴──────────────┴────────────────┘")
    print()
    
    print("3️⃣  Consistency vs Availability Trade-off:")
    print("  • Strong Consistency (QUORUM/ALL): Requires majority → May become unavailable")
    print("  • High Availability (ONE): Always available → May read stale data")
    print("  • Cassandra allows tuning this trade-off per operation")
    print()
    
    print("4️⃣  Real-World Implications:")
    print("  ✓ Financial transactions: Use QUORUM or ALL (consistency critical)")
    print("  ✓ Social media likes: Use ONE (availability more important)")
    print("  ✓ E-commerce inventory: Use QUORUM (balance needed)")
    print()
    
    print("5️⃣  Why QUORUM is Often the Best Choice:")
    print("  • Provides strong consistency (majority overlap)")
    print("  • Maintains availability during single node failures")
    print("  • Balances read and write performance")
    print("  • Represents a pragmatic CP (Consistency + Partition tolerance) approach")
    
    # Cleanup
    for conn in connections:
        if conn:
            conn['cluster'].shutdown()
    
    print()


def main():
    """Main experiment runner"""
    print_section("STRONG CONSISTENCY EXPERIMENTS WITH CASSANDRA", char="=")
    print("Demonstrating CAP Theorem Trade-offs and Consistency Guarantees\n")
    
    experiments = [
        ("1", "Strong Consistency in Normal Operation", experiment_1_strong_consistency_normal),
        ("2", "Consistency Level Comparison", experiment_2_consistency_levels_comparison),
        ("3", "Network Partition - CAP Theorem", experiment_3_network_partition)
    ]
    
    print("Available Experiments:")
    for num, desc, _ in experiments:
        print(f"  {num}. {desc}")
    print("  4. Run All Experiments")
    print("  0. Exit")
    
    choice = input("\nSelect experiment to run (0-4): ").strip()
    
    if choice == "0":
        print("Exiting...")
        return
    elif choice == "4":
        for _, desc, func in experiments:
            func()
            input("\nPress Enter to continue to next experiment...")
    elif choice in ["1", "2", "3"]:
        idx = int(choice) - 1
        experiments[idx][2]()
    else:
        print("Invalid choice")
    
    print_section("ALL EXPERIMENTS COMPLETED", char="=")


if __name__ == "__main__":
    main()