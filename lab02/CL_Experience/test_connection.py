from cassandra.cluster import Cluster

try:
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()
    print("✓ Successfully connected to Cassandra")
    
    # Display nodes information
    print(f"✓ Cluster name: {cluster.metadata.cluster_name}")
    print(f"✓ Cassandra version: {list(cluster.metadata.all_hosts())[0].release_version}")
    
    cluster.shutdown()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("  Make sure Cassandra is running on localhost:9042")