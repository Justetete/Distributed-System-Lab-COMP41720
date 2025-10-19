from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel
import time
from datetime import datetime
import threading

# Configuration
NODES = [
    {'host': '127.0.0.1', 'port': 9042, 'name': 'Node-1', 'container': 'cassandra-1'},
    {'host': '127.0.0.1', 'port': 9043, 'name': 'Node-2', 'container': 'cassandra-2'},
    {'host': '127.0.0.1', 'port': 9044, 'name': 'Node-3', 'container': 'cassandra-3'}
]

KEYSPACE = 'test_rf_3'


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
        cluster = Cluster([host], port=port, connect_timeout=10)
        session = cluster.connect(keyspace)
        return {'cluster': cluster, 'session': session, 'name': name}
    except Exception as e:
        print_result(f"Failed to connect to {name}: {e}", success=False)
        return None


def write_data_eventual(session, user_id, username, email):
    """
    Write data with eventual consistency (CL=ONE)
    Returns: (success, latency_ms, timestamp)
    """
    statement = f"""
        INSERT INTO test_write_CL 
        (user_id, username, email, last_update_timestamp) 
        VALUES ({user_id}, '{username}', '{email}', toTimestamp(now()))
    """
    
    try:
        start = time.perf_counter()
        stmt = SimpleStatement(statement, consistency_level=ConsistencyLevel.ONE)
        session.execute(stmt)
        latency = (time.perf_counter() - start) * 1000
        write_timestamp = datetime.now()
        return (True, latency, write_timestamp)
    except Exception as e:
        return (False, 0, None)


def read_data_eventual(session, user_id):
    """
    Read data with eventual consistency (CL=ONE)
    Returns: (success, data, latency_ms)
    """
    query = f"""
        SELECT user_id, username, email, last_update_timestamp,
               WRITETIME(username) as write_timestamp
        FROM test_write_CL 
        WHERE user_id = {user_id}
    """
    
    try:
        start = time.perf_counter()
        stmt = SimpleStatement(query, consistency_level=ConsistencyLevel.ONE)
        result = session.execute(stmt)
        latency = (time.perf_counter() - start) * 1000
        row = result.one()
        return (True, row, latency)
    except Exception as e:
        return (False, None, 0)


def monitor_convergence(sessions, user_id, expected_username, max_attempts=50, interval=0.2):
    """
    Monitor data convergence across all nodes
    Returns: convergence timeline data
    """
    timeline = []
    converged = False
    attempt = 0
    
    print(f"\n{'Time(s)':<10} {'Attempt':<10} {'Node-1':<30} {'Node-2':<30} {'Node-3':<30}")
    print("-" * 110)
    
    start_time = time.time()
    
    while attempt < max_attempts and not converged:
        elapsed = time.time() - start_time
        attempt += 1
        
        node_data = []
        node_status = []
        
        for session_info in sessions:
            success, data, latency = read_data_eventual(session_info['session'], user_id)
            if success and data:
                node_data.append(data.username)
                node_status.append(data.username[:25])
            else:
                node_data.append(None)
                node_status.append("NOT FOUND")
        
        timeline.append({
            'time': elapsed,
            'attempt': attempt,
            'node_values': node_data.copy()
        })
        
        print(f"{elapsed:<10.3f} {attempt:<10} {node_status[0]:<30} {node_status[1]:<30} {node_status[2]:<30}")
        
        # Check convergence
        non_none_values = [v for v in node_data if v is not None]
        if len(non_none_values) == 3 and all(v == expected_username for v in non_none_values):
            converged = True
            print(f"\n>>> CONVERGENCE ACHIEVED at {elapsed:.3f}s (attempt {attempt})")
            break
        
        time.sleep(interval)
    
    print("-" * 110)
    
    if not converged:
        print(f"\n>>> CONVERGENCE NOT ACHIEVED after {max_attempts} attempts ({elapsed:.3f}s)")
    
    return timeline, converged, elapsed


def experiment_1_basic_eventual_consistency():
    """
    Experiment 1: Observe Stale Reads in Eventual Consistency
    Demonstrate that ONE write + ONE read can return stale data
    """
    print_section("EXPERIMENT 1: Observing Stale Reads with Eventual Consistency")
    
    print_step(1, "Connecting to all nodes")
    connections = []
    for node in NODES:
        conn = connect_to_node(node['host'], node['port'], node['name'])
        if conn:
            connections.append(conn)
            print_result(f"Connected to {node['name']}")
    
    if len(connections) < 3:
        print_result("Need all 3 nodes for this experiment", success=False)
        return
    
    # Setup: Write initial data
    test_user_id = 4001
    initial_username = "InitialEventualUser"
    
    print_step(2, "Writing initial data with CL=ONE to Node-1")
    success, latency, timestamp = write_data_eventual(
        connections[0]['session'],
        test_user_id,
        initial_username,
        "initial@eventual.com"
    )
    
    if success:
        print_result(f"Initial write succeeded (latency: {latency:.2f}ms)")
    else:
        print_result("Initial write failed", success=False)
        return
    
    # Wait for propagation
    print_result("Waiting 3 seconds for data to propagate...")
    time.sleep(3)
    
    # Verify initial state
    print_step(3, "Verifying initial state across all nodes")
    print()
    for conn in connections:
        success, data, latency = read_data_eventual(conn['session'], test_user_id)
        if success and data:
            print_result(f"{conn['name']}: {data.username} (latency: {latency:.2f}ms)")
        else:
            print_result(f"{conn['name']}: NO DATA", success=False)
    
    # Update data
    updated_username = "UpdatedEventualUser"
    
    print_step(4, "Writing UPDATE with CL=ONE to Node-1")
    success, write_latency, write_timestamp = write_data_eventual(
        connections[0]['session'],
        test_user_id,
        updated_username,
        "updated@eventual.com"
    )
    
    if success:
        print_result(f"Update write succeeded (latency: {write_latency:.2f}ms)")
        print_result(f"Write timestamp: {write_timestamp.strftime('%H:%M:%S.%f')[:-3]}")
    else:
        print_result("Update write failed", success=False)
        return
    
    # Immediately read from different nodes
    print_step(5, "IMMEDIATELY reading from all nodes (no delay)")
    print_result("Testing if stale data is visible...")
    print()
    
    stale_detected = False
    immediate_results = []
    
    for conn in connections:
        success, data, latency = read_data_eventual(conn['session'], test_user_id)
        read_timestamp = datetime.now()
        
        if success and data:
            is_stale = data.username == initial_username
            status = "STALE DATA" if is_stale else "LATEST DATA"
            immediate_results.append({
                'node': conn['name'],
                'username': data.username,
                'status': status,
                'latency': latency
            })
            
            if is_stale:
                stale_detected = True
                time_diff = (read_timestamp - write_timestamp).total_seconds() * 1000
                print_result(f"{conn['name']}: {data.username} [{status}] (read {time_diff:.0f}ms after write)")
            else:
                print_result(f"{conn['name']}: {data.username} [{status}]")
        else:
            immediate_results.append({
                'node': conn['name'],
                'username': None,
                'status': 'NO DATA',
                'latency': 0
            })
            print_result(f"{conn['name']}: NO DATA", success=False)
    
    # Analysis
    print_step(6, "Analysis of Eventual Consistency Behavior")
    print()
    
    if stale_detected:
        print_result("STALE DATA DETECTED - Eventual consistency window observed")
        print_result("This demonstrates that CL=ONE provides NO immediate consistency guarantee")
    else:
        print_result("No stale data detected (data propagated very quickly)")
        print_result("Note: This does NOT mean strong consistency - just fast propagation")
    
    print()
    print("Key Observations:")
    print("  1. Write with CL=ONE returns immediately after writing to 1 replica")
    print("  2. Read with CL=ONE returns immediately from any 1 replica")
    print("  3. No coordination between write and read - can access different replicas")
    print("  4. Stale reads are possible during propagation window")
    print(f"  5. Write latency with CL=ONE: {write_latency:.2f}ms (very fast)")
    
    # Cleanup
    for conn in connections:
        conn['cluster'].shutdown()
    
    print()


def experiment_2_convergence_demonstration():
    """
    Experiment 2: Demonstrate Eventual Convergence
    Implement polling loop to show how system eventually becomes consistent
    """
    print_section("EXPERIMENT 2: Demonstrating Eventual Convergence")
    
    print_step(1, "Connecting to all nodes")
    connections = []
    for node in NODES:
        conn = connect_to_node(node['host'], node['port'], node['name'])
        if conn:
            connections.append(conn)
            print_result(f"Connected to {node['name']}")
    
    if len(connections) < 3:
        print_result("Need all 3 nodes for this experiment", success=False)
        return
    
    test_user_id = 4002
    test_username = "ConvergenceTestUser"
    
    print_step(2, "Writing data with CL=ONE to Node-1")
    success, write_latency, write_timestamp = write_data_eventual(
        connections[0]['session'],
        test_user_id,
        test_username,
        "convergence@test.com"
    )
    
    if success:
        print_result(f"Write succeeded (latency: {write_latency:.2f}ms)")
        print_result(f"Write timestamp: {write_timestamp.strftime('%H:%M:%S.%f')[:-3]}")
    else:
        print_result("Write failed", success=False)
        return
    
    print_step(3, "Monitoring convergence across all nodes")
    print_result("Polling every 200ms until all nodes return consistent data...")
    
    timeline, converged, convergence_time = monitor_convergence(
        connections,
        test_user_id,
        test_username,
        max_attempts=50,
        interval=0.2
    )
    
    # Statistical analysis
    print_step(4, "Convergence Analysis")
    print()
    
    if converged:
        print_result(f"Convergence Time: {convergence_time:.3f} seconds")
        print_result(f"Number of polling attempts: {len(timeline)}")
        print_result(f"Average time per attempt: {(convergence_time / len(timeline)):.3f} seconds")
    else:
        print_result("System did not converge within observation period", success=False)
    
    print()
    print("Convergence Mechanism in Cassandra:")
    print("  1. Gossip Protocol: Nodes exchange state information every 1 second")
    print("  2. Hinted Handoff: Coordinator stores hints for unavailable replicas")
    print("  3. Read Repair: Inconsistencies detected during reads are fixed")
    print("  4. Anti-Entropy Repair: Background process synchronizes data")
    
    # Cleanup
    for conn in connections:
        conn['cluster'].shutdown()
    
    print()


def experiment_3_concurrent_writes_eventual():
    """
    Experiment 3: Multiple Concurrent Writes with Eventual Consistency
    Show how system handles conflicts with eventual consistency
    """
    print_section("EXPERIMENT 3: Concurrent Writes with Eventual Consistency")
    
    print_step(1, "Connecting to nodes")
    connections = []
    for i in range(2):  # Only need 2 nodes for this test
        conn = connect_to_node(NODES[i]['host'], NODES[i]['port'], NODES[i]['name'])
        if conn:
            connections.append(conn)
            print_result(f"Connected to {NODES[i]['name']}")
    
    if len(connections) < 2:
        print_result("Need at least 2 nodes for this experiment", success=False)
        return
    
    test_user_id = 4003
    
    print_step(2, "Performing concurrent writes to different nodes with CL=ONE")
    print_result("Both writes target the same user_id with different values...")
    print()
    
    write_results = []
    
    def concurrent_write(session, node_name, username, results_list):
        success, latency, timestamp = write_data_eventual(
            session,
            test_user_id,
            username,
            f"{username.lower()}@concurrent.com"
        )
        results_list.append({
            'node': node_name,
            'username': username,
            'success': success,
            'latency': latency,
            'timestamp': timestamp
        })
        if success:
            ts_str = timestamp.strftime('%H:%M:%S.%f')[:-3]
            print_result(f"{node_name} wrote '{username}' at {ts_str} (latency: {latency:.2f}ms)")
    
    # Create threads for concurrent writes
    threads = []
    usernames = ["ConcurrentWrite_Node1", "ConcurrentWrite_Node2"]
    
    for i, username in enumerate(usernames):
        thread = threading.Thread(
            target=concurrent_write,
            args=(connections[i]['session'], connections[i]['name'], username, write_results)
        )
        threads.append(thread)
    
    # Start all threads simultaneously
    print_result("Starting concurrent writes NOW...")
    start = time.time()
    for thread in threads:
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    total_time = (time.time() - start) * 1000
    print()
    print_result(f"All writes completed in {total_time:.2f}ms total")
    
    # Immediate reads
    print_step(3, "Reading immediately from all nodes")
    time.sleep(0.1)  # Very brief delay
    
    print()
    print(f"{'Node':<15} {'Username':<30} {'Status'}")
    print("-" * 70)
    
    immediate_values = []
    for conn in connections:
        success, data, latency = read_data_eventual(conn['session'], test_user_id)
        if success and data:
            immediate_values.append(data.username)
            print(f"{conn['name']:<15} {data.username:<30} READ SUCCESS")
        else:
            immediate_values.append(None)
            print(f"{conn['name']:<15} {'NO DATA':<30} READ FAILED")
    
    print("-" * 70)
    
    # Check if nodes see different values
    unique_values = set([v for v in immediate_values if v is not None])
    if len(unique_values) > 1:
        print()
        print_result("INCONSISTENCY DETECTED - Different nodes see different values")
        print_result("This is expected behavior with eventual consistency")
    else:
        print()
        print_result("All nodes currently see the same value")
    
    # Wait and observe convergence
    print_step(4, "Waiting for convergence (5 seconds)")
    time.sleep(5)
    
    print()
    print("Final State:")
    print(f"{'Node':<15} {'Username':<30}")
    print("-" * 50)
    
    final_values = []
    for conn in connections:
        success, data, latency = read_data_eventual(conn['session'], test_user_id)
        if success and data:
            final_values.append(data.username)
            print(f"{conn['name']:<15} {data.username:<30}")
    
    print("-" * 50)
    
    # Analysis
    print_step(5, "Analysis: Eventual Consistency with Concurrent Writes")
    print()
    
    if len(set(final_values)) == 1:
        winner = final_values[0]
        print_result(f"System CONVERGED to: {winner}")
        print_result("Last Write Wins (LWW) conflict resolution applied")
    else:
        print_result("System has not fully converged yet", success=False)
    
    print()
    print("Conflict Resolution with Eventual Consistency:")
    print("  1. Both writes succeed locally (CL=ONE requires only 1 replica)")
    print("  2. No coordination between writes - both accepted immediately")
    print("  3. Conflicts resolved asynchronously using timestamps (LWW)")
    print("  4. System eventually converges to consistent state")
    print("  5. One write's data is lost (acceptable in many use cases)")
    
    # Cleanup
    for conn in connections:
        conn['cluster'].shutdown()
    
    print()


def experiment_4_performance_comparison():
    """
    Experiment 4: Performance Comparison - Eventual vs Strong Consistency
    Compare latency and throughput between CL=ONE and CL=QUORUM
    """
    print_section("EXPERIMENT 4: Performance Comparison (Eventual vs Strong)")
    
    print_step(1, "Connecting to Node-1")
    conn = connect_to_node(NODES[0]['host'], NODES[0]['port'], NODES[0]['name'])
    if not conn:
        return
    
    num_operations = 100
    
    print_step(2, f"Performing {num_operations} writes with CL=ONE (Eventual Consistency)")
    
    one_latencies = []
    start_time = time.time()
    
    for i in range(num_operations):
        success, latency, _ = write_data_eventual(
            conn['session'],
            5000 + i,
            f"EventualUser_{i}",
            f"eventual_{i}@test.com"
        )
        if success:
            one_latencies.append(latency)
    
    one_total_time = time.time() - start_time
    
    print_result(f"Completed {len(one_latencies)} operations in {one_total_time:.2f}s")
    print_result(f"Average latency: {sum(one_latencies)/len(one_latencies):.2f}ms")
    print_result(f"Throughput: {len(one_latencies)/one_total_time:.2f} ops/sec")
    
    print_step(3, f"Performing {num_operations} writes with CL=QUORUM (Strong Consistency)")
    
    quorum_latencies = []
    start_time = time.time()
    
    for i in range(num_operations):
        statement = f"""
            INSERT INTO test_write_CL 
            (user_id, username, email, last_update_timestamp) 
            VALUES ({6000 + i}, 'StrongUser_{i}', 'strong_{i}@test.com', toTimestamp(now()))
        """
        try:
            stmt_start = time.perf_counter()
            stmt = SimpleStatement(statement, consistency_level=ConsistencyLevel.QUORUM)
            conn['session'].execute(stmt)
            latency = (time.perf_counter() - stmt_start) * 1000
            quorum_latencies.append(latency)
        except Exception:
            pass
    
    quorum_total_time = time.time() - start_time
    
    print_result(f"Completed {len(quorum_latencies)} operations in {quorum_total_time:.2f}s")
    print_result(f"Average latency: {sum(quorum_latencies)/len(quorum_latencies):.2f}ms")
    print_result(f"Throughput: {len(quorum_latencies)/quorum_total_time:.2f} ops/sec")
    
    # Comparison
    print_step(4, "Performance Comparison Summary")
    print()
    
    print(f"{'Metric':<30} {'CL=ONE (Eventual)':<25} {'CL=QUORUM (Strong)':<25} {'Speedup':<15}")
    print("-" * 95)
    
    avg_one = sum(one_latencies)/len(one_latencies)
    avg_quorum = sum(quorum_latencies)/len(quorum_latencies)
    latency_speedup = avg_quorum / avg_one
    
    throughput_one = len(one_latencies)/one_total_time
    throughput_quorum = len(quorum_latencies)/quorum_total_time
    throughput_speedup = throughput_one / throughput_quorum
    
    print(f"{'Average Latency (ms)':<30} {avg_one:<25.2f} {avg_quorum:<25.2f} {latency_speedup:<15.2f}x slower")
    print(f"{'Throughput (ops/sec)':<30} {throughput_one:<25.2f} {throughput_quorum:<25.2f} {throughput_speedup:<15.2f}x faster")
    print(f"{'Total Time (sec)':<30} {one_total_time:<25.2f} {quorum_total_time:<25.2f} {quorum_total_time/one_total_time:<15.2f}x slower")
    
    print("-" * 95)
    
    # Cleanup
    conn['cluster'].shutdown()
    
    print()


def print_use_case_analysis():
    """
    Print detailed analysis of when eventual consistency is appropriate
    """
    print_section("USE CASE ANALYSIS: When to Choose Eventual Consistency")
    
    print("APPROPRIATE USE CASES for Eventual Consistency:\n")
    
    print("1. Social Media Interactions")
    print("   Examples: Likes, shares, comments, view counts")
    print("   Justification:")
    print("     - Slight delays in counter updates are imperceptible to users")
    print("     - High write volume requires maximum throughput")
    print("     - System availability is more critical than perfect accuracy")
    print("     - Users expect real-time interaction, not real-time global consistency")
    print("   Benefits: 10-100x higher write throughput, zero coordination overhead\n")
    
    print("2. Sensor Data and IoT Systems")
    print("   Examples: Temperature readings, GPS locations, device telemetry")
    print("   Justification:")
    print("     - Data is inherently time-series and append-only")
    print("     - Later readings supersede earlier ones naturally")
    print("     - Massive write volume from thousands of devices")
    print("     - Brief inconsistency windows do not affect analytics")
    print("   Benefits: Handles millions of writes/sec, geographic distribution\n")
    
    print("3. Shopping Cart Systems")
    print("   Examples: Add/remove items, update quantities")
    print("   Justification:")
    print("     - User's most recent action represents their true intent")
    print("     - Cart is single-user resource (no concurrent modifications by others)")
    print("     - Cart updates are non-critical (not financial transactions)")
    print("     - Fast response time improves user experience")
    print("   Benefits: Sub-10ms response times, high availability\n")
    
    print("4. Content Delivery and Caching")
    print("   Examples: CDN content, cached web pages, thumbnail images")
    print("   Justification:")
    print("     - Slightly stale content is acceptable for short periods")
    print("     - Read-heavy workload benefits from aggressive caching")
    print("     - Content updates are infrequent relative to reads")
    print("     - Geographic distribution requires local writes")
    print("   Benefits: Global distribution, minimal latency for users\n")
    
    print("5. Activity Feeds and Timelines")
    print("   Examples: News feeds, notification lists, activity logs")
    print("   Justification:")
    print("     - Feeds are eventually consistent by nature")
    print("     - Missing a post briefly is acceptable")
    print("     - High write volume from many users")
    print("     - Personalized feeds can tolerate ordering variations")
    print("   Benefits: Scales to billions of users, handles viral content\n")
    
    print("\nINAPPROPRIATE USE CASES for Eventual Consistency:\n")
    
    print("1. Financial Transactions")
    print("   Why not: Account balances must be accurate; lost updates = lost money\n")
    
    print("2. Inventory Management")
    print("   Why not: Overselling occurs if decrements are lost or delayed\n")
    
    print("3. Seat/Room Reservations")
    print("   Why not: Double-booking results from optimistic concurrent reservations\n")
    
    print("4. Access Control Systems")
    print("   Why not: Security vulnerabilities if permission revocations delay\n")
    
    print("\nKEY DECISION FACTORS:\n")
    print("  Choose Eventual Consistency when:")
    print("    - Availability and performance are more critical than immediate accuracy")
    print("    - Lost updates are acceptable (idempotent or naturally superseding data)")
    print("    - Data is single-user or conflicts are rare")
    print("    - Convergence latency (seconds) is tolerable")
    print()
    print("  Choose Strong Consistency when:")
    print("    - Data accuracy is critical (financial, inventory, security)")
    print("    - Lost updates are unacceptable")
    print("    - Operations are not idempotent or commutative")
    print("    - Coordination overhead is acceptable for correctness")
    
    print()


def main():
    """Main experiment runner"""
    print_section("EVENTUAL CONSISTENCY EXPERIMENTS WITH CASSANDRA", char="=")
    print("Demonstrating Convergence Patterns and Performance Trade-offs\n")
    
    experiments = [
        ("1", "Observing Stale Reads", experiment_1_basic_eventual_consistency),
        ("2", "Convergence Demonstration", experiment_2_convergence_demonstration),
        ("3", "Concurrent Writes", experiment_3_concurrent_writes_eventual),
        ("4", "Performance Comparison", experiment_4_performance_comparison),
        ("5", "Use Case Analysis", lambda: print_use_case_analysis())
    ]
    
    print("Available Experiments:")
    for num, desc, _ in experiments:
        print(f"  {num}. {desc}")
    print("  6. Run All Experiments")
    print("  0. Exit")
    
    choice = input("\nSelect experiment to run (0-6): ").strip()
    
    if choice == "0":
        print("Exiting...")
        return
    elif choice == "6":
        for _, desc, func in experiments:
            func()
            if _ != "5":  # Don't pause after analysis
                input("\nPress Enter to continue to next experiment...")
    elif choice in ["1", "2", "3", "4", "5"]:
        idx = int(choice) - 1
        experiments[idx][2]()
    else:
        print("Invalid choice")
    
    print_section("ALL EXPERIMENTS COMPLETED", char="=")


if __name__ == "__main__":
    main()