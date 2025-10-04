import time
import requests
import grpc
import statistics
from concurrent.futures import ThreadPoolExecutor


import sys
sys.path.insert(0,'/python_grpc_lab/generated')
from python_grpc_lab.generated import user_service_pb2, user_service_pb2_grpc


# Configuration
REST_BASE_URL = "http://localhost:5000/api/users"
GRPC_HOST = "localhost:50051"
NUM_REQUESTS = 100
NUM_CONCURRENT = 10

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def benchmark_rest_create():
    """Benchmark REST API - Create User"""
    latencies = []
    errors = 0
    
    for i in range(NUM_REQUESTS):
        user_data = {
            "name": f"TestUser{i}",
            "id": i,
            "email": f"test{i}@example.com"
        }
        
        start = time.time()
        try:
            response = requests.post(REST_BASE_URL, json=user_data, timeout=5)
            latency = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code in [200, 201]:
                latencies.append(latency)
            else:
                errors += 1
        except Exception as e:
            errors += 1
            print(f"REST Create Error: {e}")
    
    return latencies, errors

def benchmark_rest_read():
    """Benchmark REST API - Read User"""
    latencies = []
    errors = 0
    
    for i in range(NUM_REQUESTS):
        start = time.time()
        try:
            response = requests.get(f"{REST_BASE_URL}/{i}", timeout=5)
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                latencies.append(latency)
            else:
                errors += 1
        except Exception as e:
            errors += 1
    
    return latencies, errors

def benchmark_grpc_create():
    """Benchmark gRPC - Create User"""
    latencies = []
    errors = 0
    
    try:
        channel = grpc.insecure_channel(GRPC_HOST)
        stub = user_service_pb2_grpc.UserServiceStub(channel)
        
        for i in range(NUM_REQUESTS):
            request = user_service_pb2.CreateUserRequest(
                name=f"TestUser{i}",
                email=f"test{i}@example.com"
            )
            
            start = time.time()
            try:
                response = stub.CreateUser(request, timeout=5)
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            except Exception as e:
                errors += 1
                print(f"gRPC Create Error: {e}")
        
        channel.close()
    except Exception as e:
        print(f"gRPC Connection Error: {e}")
        return [], NUM_REQUESTS
    
    return latencies, errors

def benchmark_grpc_read():
    """Benchmark gRPC - Read User"""
    latencies = []
    errors = 0
    
    try:
        channel = grpc.insecure_channel(GRPC_HOST)
        stub = user_service_pb2_grpc.UserServiceStub(channel)
        
        for i in range(NUM_REQUESTS):
            request = user_service_pb2.GetUserRequest(id= i)
            
            start = time.time()
            try:
                response = stub.GetUser(request, timeout=5)
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            except Exception as e:
                errors += 1
        
        channel.close()
    except Exception as e:
        print(f"gRPC Connection Error: {e}")
        return [], NUM_REQUESTS
    
    return latencies, errors

def benchmark_rest_concurrent():
    """Benchmark REST with concurrent requests"""
    latencies = []
    errors = 0
    
    def make_request(i):
        user_data = {
            "name": f"ConcurrentUser{i}",
            "id": f"{i}",
            "email": f"concurrent{i}@example.com"
        }
        start = time.time()
        try:
            response = requests.post(REST_BASE_URL, json=user_data, timeout=5)
            latency = (time.time() - start) * 1000
            return latency if response.status_code in [200, 201] else None
        except:
            return None
    
    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT) as executor:
        results = list(executor.map(make_request, range(NUM_REQUESTS)))
    
    latencies = [r for r in results if r is not None]
    errors = NUM_REQUESTS - len(latencies)
    
    return latencies, errors

def benchmark_grpc_concurrent():
    """Benchmark gRPC with concurrent requests"""
    latencies = []
    errors = 0
    
    def make_request(i):
        try:
            channel = grpc.insecure_channel(GRPC_HOST)
            stub = user_service_pb2_grpc.UserServiceStub(channel)
            
            request = user_service_pb2.CreateUserRequest(
                name=f"ConcurrentUser{i}",
                email=f"concurrent{i}@example.com"
            )
            
            start = time.time()
            response = stub.CreateUser(request, timeout=5)
            latency = (time.time() - start) * 1000
            channel.close()
            return latency
        except:
            return None
    
    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT) as executor:
        results = list(executor.map(make_request, range(NUM_REQUESTS)))
    
    latencies = [r for r in results if r is not None]
    errors = NUM_REQUESTS - len(latencies)
    
    return latencies, errors

def calculate_stats(latencies):
    """Calculate statistics from latency measurements"""
    if not latencies:
        return None
    
    return {
        'mean': statistics.mean(latencies),
        'median': statistics.median(latencies),
        'min': min(latencies),
        'max': max(latencies),
        'stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0,
        'p95': sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0],
        'p99': sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
    }

def print_results(name, stats, errors, total_requests):
    """Print benchmark results in a formatted way"""
    if stats is None:
        print(f"{Colors.FAIL}❌ {name}: All requests failed{Colors.ENDC}")
        return
    
    success_rate = ((total_requests - errors) / total_requests) * 100
    
    print(f"{Colors.OKBLUE}{Colors.BOLD}{name}{Colors.ENDC}")
    print(f"  Success Rate:  {Colors.OKGREEN if success_rate > 95 else Colors.WARNING}{success_rate:.2f}%{Colors.ENDC} ({total_requests - errors}/{total_requests})")
    print(f"  Mean Latency:  {Colors.OKCYAN}{stats['mean']:.2f} ms{Colors.ENDC}")
    print(f"  Median:        {stats['median']:.2f} ms")
    print(f"  Min:           {stats['min']:.2f} ms")
    print(f"  Max:           {stats['max']:.2f} ms")
    print(f"  Std Dev:       {stats['stdev']:.2f} ms")
    print(f"  95th %ile:     {stats['p95']:.2f} ms")
    print(f"  99th %ile:     {stats['p99']:.2f} ms")
    print()

def print_comparison(rest_stats, grpc_stats):
    """Print comparison between REST and gRPC"""
    if rest_stats is None or grpc_stats is None:
        print(f"{Colors.WARNING}Cannot compare - one or both benchmarks failed{Colors.ENDC}")
        return
    
    print_header("PERFORMANCE COMPARISON")
    
    improvement = ((rest_stats['mean'] - grpc_stats['mean']) / rest_stats['mean']) * 100
    
    print(f"Mean Latency Comparison:")
    print(f"  REST:  {rest_stats['mean']:.2f} ms")
    print(f"  gRPC:  {grpc_stats['mean']:.2f} ms")
    
    if improvement > 0:
        print(f"  {Colors.OKGREEN}✓ gRPC is {improvement:.1f}% faster{Colors.ENDC}")
    else:
        print(f"  {Colors.WARNING}✓ REST is {abs(improvement):.1f}% faster{Colors.ENDC}")
    
    print(f"\nThroughput Comparison (requests/second):")
    rest_throughput = 1000 / rest_stats['mean']
    grpc_throughput = 1000 / grpc_stats['mean']
    print(f"  REST:  {rest_throughput:.2f} req/s")
    print(f"  gRPC:  {grpc_throughput:.2f} req/s")
    print()

def main():
    print_header("DISTRIBUTED SYSTEMS LAB")
    print_header("REST vs gRPC Performance Benchmark")
    
    print(f"Configuration:")
    print(f"  Number of requests: {NUM_REQUESTS}")
    print(f"  Concurrent workers: {NUM_CONCURRENT}")
    print(f"  REST endpoint: {REST_BASE_URL}")
    print(f"  gRPC endpoint: {GRPC_HOST}")
    
    # Sequential Create Operations
    print_header("SEQUENTIAL CREATE OPERATIONS")
    
    print("Running REST API benchmark (Create)...")
    rest_create_latencies, rest_create_errors = benchmark_rest_create()
    rest_create_stats = calculate_stats(rest_create_latencies)
    print_results("REST API - Create User", rest_create_stats, rest_create_errors, NUM_REQUESTS)
    
    print("Running gRPC benchmark (Create)...")
    grpc_create_latencies, grpc_create_errors = benchmark_grpc_create()
    grpc_create_stats = calculate_stats(grpc_create_latencies)
    print_results("gRPC - Create User", grpc_create_stats, grpc_create_errors, NUM_REQUESTS)
    
    print_comparison(rest_create_stats, grpc_create_stats)
    
    # Sequential Read Operations
    print_header("SEQUENTIAL READ OPERATIONS")
    
    print("Running REST API benchmark (Read)...")
    rest_read_latencies, rest_read_errors = benchmark_rest_read()
    rest_read_stats = calculate_stats(rest_read_latencies)
    print_results("REST API - Read User", rest_read_stats, rest_read_errors, NUM_REQUESTS)
    
    print("Running gRPC benchmark (Read)...")
    grpc_read_latencies, grpc_read_errors = benchmark_grpc_read()
    grpc_read_stats = calculate_stats(grpc_read_latencies)
    print_results("gRPC - Read User", grpc_read_stats, grpc_read_errors, NUM_REQUESTS)
    
    print_comparison(rest_read_stats, grpc_read_stats)
    
    # Concurrent Operations
    print_header("CONCURRENT OPERATIONS")
    
    print("Running REST API benchmark (Concurrent)...")
    rest_concurrent_latencies, rest_concurrent_errors = benchmark_rest_concurrent()
    rest_concurrent_stats = calculate_stats(rest_concurrent_latencies)
    print_results("REST API - Concurrent Requests", rest_concurrent_stats, rest_concurrent_errors, NUM_REQUESTS)
    
    print("Running gRPC benchmark (Concurrent)...")
    grpc_concurrent_latencies, grpc_concurrent_errors = benchmark_grpc_concurrent()
    grpc_concurrent_stats = calculate_stats(grpc_concurrent_latencies)
    print_results("gRPC - Concurrent Requests", grpc_concurrent_stats, grpc_concurrent_errors, NUM_REQUESTS)
    
    print_comparison(rest_concurrent_stats, grpc_concurrent_stats)
    
    # Final Summary
    print_header("SUMMARY")
    print("Key Observations:")
    print("1. Latency: Compare mean and median latencies")
    print("2. Consistency: Check standard deviation and percentiles")
    print("3. Concurrency: Evaluate performance under concurrent load")
    print("4. Reliability: Review success rates and error counts")
    print(f"\n{Colors.OKGREEN}Benchmark completed!{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Benchmark interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        sys.exit(1)