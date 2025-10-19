"""
Leaderless Multi-Primary Concurrent Write Conflict Test
Demonstrates conflict resolution using Last Write Wins (LWW) strategy
"""
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel
import threading
import time
from datetime import datetime

# Configuration
NODES = [
    {'host': '127.0.0.1', 'port': 9042, 'name': 'Node-1'},
    {'host': '127.0.0.1', 'port': 9043, 'name': 'Node-2'},
    {'host': '127.0.0.1', 'port': 9044, 'name': 'Node-3'}
]

KEYSPACE = 'test_rf_3'
TEST_USER_ID = 999


def connect_to_nodes():
    """Connect to all Cassandra nodes"""
    connections = []
    
    print("=" * 80)
    print("Connecting to Cassandra Nodes".center(80))
    print("=" * 80)
    
    for node in NODES:
        try:
            cluster = Cluster([node['host']], port=node['port'])
            session = cluster.connect(KEYSPACE)
            connections.append({
                'cluster': cluster,
                'session': session,
                'name': node['name']
            })
            print(f"✓ Connected to {node['name']} ({node['host']}:{node['port']})")
        except Exception as e:
            print(f"✗ Failed to connect to {node['name']}: {e}")
            return None
    
    print("=" * 80 + "\n")
    return connections


def write_initial_data(session):
    """Write initial data before conflict test"""
    statement = f"""
        INSERT INTO test_write_CL 
        (user_id, username, email, last_update_timestamp) 
        VALUES ({TEST_USER_ID}, 'InitialUser', 'initial@example.com', toTimestamp(now()))
    """
    
    try:
        stmt = SimpleStatement(statement, consistency_level=ConsistencyLevel.QUORUM)
        session.execute(stmt)
        return True
    except Exception as e:
        print(f"✗ Initial write failed: {e}")
        return False


def read_user_data(session, user_id, consistency_level=ConsistencyLevel.ONE):
    """Read user data from Cassandra"""
    query = f"""
        SELECT user_id, username, email, last_update_timestamp, 
               WRITETIME(username) as write_timestamp
        FROM test_write_CL 
        WHERE user_id = {user_id}
    """
    
    try:
        stmt = SimpleStatement(query, consistency_level=consistency_level)
        result = session.execute(stmt)
        row = result.one()
        return row
    except Exception as e:
        print(f"✗ Read failed: {e}")
        return None


def concurrent_write(session, node_name, user_id, username, email, delay=0):
    """Perform a write operation with optional delay"""
    if delay > 0:
        time.sleep(delay)
    
    statement = f"""
        INSERT INTO test_write_CL 
        (user_id, username, email, last_update_timestamp) 
        VALUES ({user_id}, '{username}', '{email}', toTimestamp(now()))
    """
    
    try:
        start_time = time.perf_counter()
        stmt = SimpleStatement(statement, consistency_level=ConsistencyLevel.ONE)
        session.execute(stmt)
        latency = (time.perf_counter() - start_time) * 1000
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"  [{timestamp}] ✓ {node_name} wrote: '{username}' (latency: {latency:.2f}ms)")
        return True
    except Exception as e:
        print(f"  ✗ {node_name} write failed: {e}")
        return False


def display_data_across_nodes(connections, user_id, title):
    """Display data from all nodes"""
    print(f"\n{'=' * 80}")
    print(f"{title}".center(80))
    print("=" * 80)
    print(f"{'Node':<15} {'Username':<25} {'Email':<30} {'Write Timestamp':<15}")
    print("-" * 80)
    
    results = []
    for conn in connections:
        data = read_user_data(conn['session'], user_id)
        if data:
            print(f"{conn['name']:<15} {data.username:<25} {data.email:<30} {data.write_timestamp}")
            results.append(data.username)
        else:
            print(f"{conn['name']:<15} {'N/A':<25} {'N/A':<30} {'N/A':<15}")
            results.append(None)
    
    print("=" * 80)
    
    # Check consistency
    unique_values = set([r for r in results if r is not None])
    if len(unique_values) == 1:
        print(f"✓ CONSISTENT: All nodes have the same data")
    else:
        print(f"✗ INCONSISTENT: Nodes have different data")
    
    return len(unique_values) == 1


def experiment_concurrent_conflict(connections):
    """
    Main experiment: Concurrent writes to the same user from different nodes
    """
    print("\n" + "=" * 80)
    print("EXPERIMENT: Concurrent Write Conflicts".center(80))
    print("=" * 80)
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Scenario: Two nodes write different values simultaneously")
    print("=" * 80 + "\n")
    
    # Step 1: Write initial data
    print("[Step 1] Writing initial data...")
    if write_initial_data(connections[0]['session']):
        print("✓ Initial data written successfully\n")
        time.sleep(2)  # Wait for propagation
    else:
        print("✗ Failed to write initial data")
        return
    
    # Step 2: Verify initial state
    print("[Step 2] Verifying initial state across all nodes...")
    time.sleep(1)
    display_data_across_nodes(connections, TEST_USER_ID, "Initial State")
    
    # Step 3: Concurrent conflicting writes
    print("\n[Step 3] Performing concurrent conflicting writes...")
    print("  Node-1 will write: 'UpdatedByNode1'")
    print("  Node-2 will write: 'UpdatedByNode2'")
    print("  Both writes happen simultaneously\n")
    
    # Create threads for simultaneous writes
    thread1 = threading.Thread(
        target=concurrent_write,
        args=(connections[0]['session'], 'Node-1', TEST_USER_ID, 
              'UpdatedByNode1', 'node1@example.com', 0)
    )
    
    thread2 = threading.Thread(
        target=concurrent_write,
        args=(connections[1]['session'], 'Node-2', TEST_USER_ID, 
              'UpdatedByNode2', 'node2@example.com', 0)
    )
    
    # Start both threads at the same time
    print("Starting concurrent writes NOW:")
    start = time.time()
    thread1.start()
    thread2.start()
    
    # Wait for both to complete
    thread1.join()
    thread2.join()
    total_time = (time.time() - start) * 1000
    
    print(f"\n✓ Both writes completed in {total_time:.2f}ms total\n")
    
    # Step 4: Immediately read from all nodes (before convergence)
    print("[Step 4] Reading IMMEDIATELY after conflict (checking for inconsistency)...")
    time.sleep(0.1)  # Very short delay
    immediate_consistent = display_data_across_nodes(
        connections, TEST_USER_ID, 
        "Immediate State (T+0.1s)"
    )
    
    # Step 5: Wait and read again (after convergence)
    print("\n[Step 5] Waiting 5 seconds for data convergence...")
    time.sleep(5)
    
    print("Reading AFTER convergence period...")
    final_consistent = display_data_across_nodes(
        connections, TEST_USER_ID, 
        "Final State (T+5s)"
    )
    
    # Step 6: Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS & OBSERVATIONS".center(80))
    print("=" * 80)
    
    print("\n📊 Consistency Analysis:")
    print(f"  • Immediate consistency (T+0.1s): {'YES ✓' if immediate_consistent else 'NO ✗'}")
    print(f"  • Final consistency (T+5s):       {'YES ✓' if final_consistent else 'NO ✗'}")
    
    if final_consistent:
        final_data = read_user_data(connections[0]['session'], TEST_USER_ID)
        if final_data:
            print(f"\n🏆 Winning Write: '{final_data.username}'")
            print(f"  Write Timestamp: {final_data.write_timestamp}")
    
    print("\n" + "=" * 80 + "\n")


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("LEADERLESS MULTI-PRIMARY ARCHITECTURE".center(80))
    print("Concurrent Write Conflict Experiment".center(80))
    print("=" * 80 + "\n")
    
    # Connect to all nodes
    connections = connect_to_nodes()
    if not connections:
        print("✗ Failed to connect to Cassandra cluster")
        return
    
    try:
        # Run the experiment
        experiment_concurrent_conflict(connections)
        
    finally:
        # Cleanup
        print("Closing connections...")
        for conn in connections:
            conn['cluster'].shutdown()
        print("✓ All connections closed\n")


if __name__ == "__main__":
    main()