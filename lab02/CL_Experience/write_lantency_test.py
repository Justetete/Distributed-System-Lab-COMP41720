from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel
import time

# Connecting to Cassandra
cluster = Cluster(['127.0.0.1'])
session = cluster.connect('test_rf_3')

# Test parameters
NUM_TEST = 100
CONSISTENCY_LEVELS = [
    ConsistencyLevel.QUORUM,
    ConsistencyLevel.ONE,
    ConsistencyLevel.ALL
]


def test_write_latency(consistency_level, num_tests=NUM_TEST):
    """Test write latency for a specific consistency level"""
    
    total_time = 0
    errors = 0
    latencies = []  # Record each latency for analysis
    
    print(f"\n{'='*50}")
    print(f"Testing Consistency Level: {consistency_level}")
    print(f"{'='*50}")
    
    for i in range(num_tests):
        # Prepare INSERT statement
        statement = f"""
            INSERT INTO user_profiles_writing_test_latency 
            (user_id, username, email, last_update_timestamp) 
            VALUES (uuid(), 'test_user_{i}', 'test_{i}@email.com', toTimestamp(now()))
        """
        
        try:
            # Create Statement with specified consistency level
            stmt = SimpleStatement(
                statement, 
                consistency_level=consistency_level
            )
            
            # Precise timing: only measure execution time
            start = time.perf_counter()
            session.execute(stmt)
            end = time.perf_counter()
            
            # Record latency (convert to milliseconds)
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)
            total_time += latency_ms
            
            # Print progress every 10 iterations
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{num_tests} completed")
                
        except Exception as e:
            errors += 1
            print(f"  ❌ Write #{i+1} failed: {e}")
    
    # Calculate statistics
    success_count = num_tests - errors
    success_rate = (success_count / num_tests) * 100
    
    if success_count > 0:
        avg_latency = total_time / success_count
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        # Calculate median
        sorted_latencies = sorted(latencies)
        median_latency = sorted_latencies[len(sorted_latencies) // 2]
        
        # Print results
        print(f"\n{'─'*50}")
        print(f"📊 Test Results:")
        print(f"{'─'*50}")
        print(f"  Total tests:        {num_tests}")
        print(f"  Successful writes:  {success_count}")
        print(f"  Failed writes:      {errors}")
        print(f"  Success rate:       {success_rate:.2f}%")
        print(f"  Average latency:    {avg_latency:.2f} ms")
        print(f"  Median latency:     {median_latency:.2f} ms")
        print(f"  Min latency:        {min_latency:.2f} ms")
        print(f"  Max latency:        {max_latency:.2f} ms")
        print(f"{'─'*50}\n")
        
        return {
            'consistency_level': consistency_level,
            'total_tests': num_tests,
            'success_count': success_count,
            'errors': errors,
            'success_rate': success_rate,
            'avg_latency_ms': avg_latency,
            'median_latency_ms': median_latency,
            'min_latency_ms': min_latency,
            'max_latency_ms': max_latency
        }
    else:
        print(f"  ⚠️ All writes failed!")
        return None

# Main program: test all consistency levels
if __name__ == "__main__":
    results = []
    
    print("Starting Cassandra Write Latency Test")
    print(f"Keyspace: test_RF_3")
    print(f"Testing {NUM_TEST} writes per consistency level\n")
    
    for cl in CONSISTENCY_LEVELS:
        result = test_write_latency(cl, NUM_TEST)
        if result:
            results.append(result)
    
    # Print comparison table
    print("\n" + "="*80)
    print("📈 Consistency Level Comparison")
    print("="*80)
    print(f"{'Consistency Level':<12} {'Success Rate':<15} {'Avg Latency(ms)':<18} {'Median(ms)':<15} {'Max Latency(ms)':<15}")
    print("-"*80)
    
    for r in results:
        print(f"{r['consistency_level']:<12} "
              f"{r['success_rate']:<14.2f}% "
              f"{r['avg_latency_ms']:<18.2f} "
              f"{r['median_latency_ms']:<15.2f} "
              f"{r['max_latency_ms']:<15.2f}")
    
    print("="*80)
    
    # Close connection
    cluster.shutdown()