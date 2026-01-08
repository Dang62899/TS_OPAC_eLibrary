#!/usr/bin/env python
"""
Load Testing Script - Tests system under concurrent load
Tests typical user scenarios: browsing, searching, viewing analytics
"""

import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

BASE_URL = "http://localhost"
TIMEOUT = 10
RESULTS = {
    'homepage': [],
    'search': [],
    'analytics': [],
    'admin': [],
    'api': [],
    'errors': []
}

def test_homepage(thread_id):
    """Test homepage load"""
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        duration = (time.time() - start) * 1000
        RESULTS['homepage'].append({
            'status': response.status_code,
            'time': duration,
            'thread': thread_id
        })
        return response.status_code == 200
    except Exception as e:
        RESULTS['errors'].append(f"Homepage error: {str(e)}")
        return False

def test_search(thread_id):
    """Test search functionality"""
    try:
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/search/?q=fiction",
            timeout=TIMEOUT
        )
        duration = (time.time() - start) * 1000
        RESULTS['search'].append({
            'status': response.status_code,
            'time': duration,
            'thread': thread_id
        })
        return response.status_code == 200
    except Exception as e:
        RESULTS['errors'].append(f"Search error: {str(e)}")
        return False

def test_analytics(thread_id):
    """Test browse functionality"""
    try:
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/browse/type/1/",
            timeout=TIMEOUT
        )
        duration = (time.time() - start) * 1000
        RESULTS['analytics'].append({
            'status': response.status_code,
            'time': duration,
            'thread': thread_id
        })
        return response.status_code == 200
    except Exception as e:
        RESULTS['errors'].append(f"Browse error: {str(e)}")
        return False

def test_health_check(thread_id):
    """Test health check endpoint"""
    try:
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/health/",
            timeout=TIMEOUT
        )
        duration = (time.time() - start) * 1000
        RESULTS['api'].append({
            'status': response.status_code,
            'time': duration,
            'thread': thread_id
        })
        return response.status_code == 200
    except Exception as e:
        RESULTS['errors'].append(f"Health check error: {str(e)}")
        return False

def run_load_test(num_concurrent_users=10, requests_per_user=5):
    """Run load test with concurrent users"""
    print(f"\n📊 LOAD TEST: {num_concurrent_users} concurrent users × {requests_per_user} requests")
    print("─" * 60)
    
    total_requests = num_concurrent_users * requests_per_user
    completed = 0
    
    with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
        futures = []
        
        for user_id in range(num_concurrent_users):
            for req in range(requests_per_user):
                if req % 4 == 0:
                    futures.append(executor.submit(test_homepage, user_id))
                elif req % 4 == 1:
                    futures.append(executor.submit(test_search, user_id))
                elif req % 4 == 2:
                    futures.append(executor.submit(test_analytics, user_id))
                else:
                    futures.append(executor.submit(test_health_check, user_id))
        
        for future in as_completed(futures):
            completed += 1
            if completed % 5 == 0:
                print(f"  Progress: {completed}/{total_requests} requests completed...")
            try:
                future.result()
            except Exception as e:
                RESULTS['errors'].append(str(e))
    
    print(f"\n✅ Completed: {completed}/{total_requests} requests\n")

def print_results():
    """Print detailed load test results"""
    print("\n" + "="*60)
    print("LOAD TEST RESULTS")
    print("="*60)
    
    endpoints = ['homepage', 'search', 'analytics', 'api']
    
    for endpoint in endpoints:
        data = RESULTS[endpoint]
        if data:
            statuses = [r['status'] for r in data]
            times = [r['time'] for r in data]
            
            success_rate = (statuses.count(200) / len(statuses)) * 100
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            stdev = statistics.stdev(times) if len(times) > 1 else 0
            
            print(f"\n{endpoint.upper()}:")
            print(f"  Requests: {len(data)}")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Response Times:")
            print(f"    - Average: {avg_time:.2f}ms")
            print(f"    - Min: {min_time:.2f}ms")
            print(f"    - Max: {max_time:.2f}ms")
            print(f"    - StdDev: {stdev:.2f}ms")
    
    if RESULTS['errors']:
        print(f"\n⚠️  ERRORS ({len(RESULTS['errors'])}):")
        for error in RESULTS['errors'][:5]:
            print(f"  - {error}")
        if len(RESULTS['errors']) > 5:
            print(f"  ... and {len(RESULTS['errors']) - 5} more")
    
    # Performance assessment
    total_reqs = sum(len(RESULTS[e]) for e in endpoints)
    total_success = sum(1 for r in (RESULTS['homepage'] + RESULTS['search'] + 
                                    RESULTS['analytics'] + RESULTS['api']) 
                        if r['status'] == 200)
    
    print(f"\n{'─'*60}")
    print(f"TOTAL REQUESTS: {total_reqs}")
    print(f"SUCCESS RATE: {(total_success/total_reqs*100):.1f}%")
    
    # Performance assessment
    if RESULTS['homepage']:
        avg_home = statistics.mean([r['time'] for r in RESULTS['homepage']])
        if avg_home < 500:
            print(f"PERFORMANCE: ✅ EXCELLENT (Avg {avg_home:.0f}ms)")
        elif avg_home < 1000:
            print(f"PERFORMANCE: ⚠️  GOOD (Avg {avg_home:.0f}ms)")
        else:
            print(f"PERFORMANCE: ❌ POOR (Avg {avg_home:.0f}ms)")

if __name__ == "__main__":
    try:
        print("\n🚀 Starting Load Tests...")
        print("   Scenario 1: Light load (5 users)")
        run_load_test(num_concurrent_users=5, requests_per_user=3)
        
        print("\n   Scenario 2: Medium load (10 users)")
        run_load_test(num_concurrent_users=10, requests_per_user=5)
        
        print("\n   Scenario 3: Heavy load (20 users)")
        run_load_test(num_concurrent_users=20, requests_per_user=3)
        
        print_results()
        
        print("\n✅ Load testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Load test failed: {str(e)}")
