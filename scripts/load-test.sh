#!/bin/bash

# Load testing script with comprehensive analysis
set -euo pipefail

SERVICE_URL=${1:-"http://localhost:8000"}
NUM_REQUESTS=${2:-100}
CONCURRENT_REQUESTS=${3:-10}

echo "Starting load test against $SERVICE_URL"
echo "Requests: $NUM_REQUESTS, Concurrency: $CONCURRENT_REQUESTS"

# Test payload
PAYLOAD='{
  "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "text": "This is a comprehensive load test for the SRE microservice assessment. We are testing the performance and reliability of the service under various load conditions."
}'

# Create results directory
mkdir -p test-results

# Function to send single request
send_request() {
    local id=$1
    local start_time=$(date +%s.%N)
    
    response=$(curl -s -w "\n%{http_code}\n%{time_total}" \
        -H "Content-Type: application/json" \
        -X POST \
        -d "$PAYLOAD" \
        "$SERVICE_URL/payload" 2>/dev/null)
    
    local end_time=$(date +%s.%N)
    local http_code=$(echo "$response" | tail -n 2 | head -n 1)
    local time_total=$(echo "$response" | tail -n 1)
    
    echo "$id,$http_code,$time_total,$start_time,$end_time" >> test-results/requests.csv
}

# Initialize results file
echo "request_id,http_code,response_time,start_time,end_time" > test-results/requests.csv

# Test health endpoints first
echo "Testing health endpoints..."
curl -f "$SERVICE_URL/health" > /dev/null || { echo "Health check failed!"; exit 1; }
curl -f "$SERVICE_URL/ready" > /dev/null || { echo "Ready check failed!"; exit 1; }

# Start load test
echo "Starting load test..."
start_test_time=$(date +%s.%N)

# Send requests concurrently
for ((i=1; i<=NUM_REQUESTS; i++)); do
    if (( i % CONCURRENT_REQUESTS == 0 )); then
        wait  # Wait for previous batch to complete
    fi
    send_request $i &
done
wait  # Wait for all remaining requests

end_test_time=$(date +%s.%N)

echo "Load test completed!"

# Analyze results
python3 << 'PYTHON_SCRIPT'
import csv
import statistics
import sys

def analyze_results():
    requests = []
    with open('test-results/requests.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            requests.append({
                'id': int(row['request_id']),
                'status': int(row['http_code']),
                'response_time': float(row['response_time']),
                'start_time': float(row['start_time']),
                'end_time': float(row['end_time'])
            })
    
    if not requests:
        print("No requests found!")
        return
    
    # Calculate metrics
    response_times = [r['response_time'] for r in requests]
    success_count = len([r for r in requests if r['status'] == 200])
    error_count = len([r for r in requests if r['status'] != 200])
    
    total_time = max([r['end_time'] for r in requests]) - min([r['start_time'] for r in requests])
    throughput = len(requests) / total_time if total_time > 0 else 0
    
    # Generate report
    report = f"""
    ========================================
    LOAD TEST PERFORMANCE REPORT
    ========================================
    
    Test Configuration:
    - Total Requests: {len(requests)}
    - Successful Requests: {success_count}
    - Failed Requests: {error_count}
    - Success Rate: {(success_count/len(requests)*100):.2f}%
    
    Response Time Analysis:
    - Minimum: {min(response_times):.3f}s
    - Maximum: {max(response_times):.3f}s
    - Mean: {statistics.mean(response_times):.3f}s
    - Median: {statistics.median(response_times):.3f}s
    - 95th Percentile: {sorted(response_times)[int(len(response_times)*0.95)]:.3f}s
    - 99th Percentile: {sorted(response_times)[int(len(response_times)*0.99)]:.3f}s
    - Standard Deviation: {statistics.stdev(response_times):.3f}s
    
    Throughput Analysis:
    - Total Test Duration: {total_time:.3f}s
    - Requests per Second: {throughput:.2f}
    
    Error Analysis:
    """
    
    error_codes = {}
    for r in requests:
        if r['status'] != 200:
            code = r['status']
            error_codes[code] = error_codes.get(code, 0) + 1
    
    if error_codes:
        for code, count in error_codes.items():
            report += f"    - HTTP {code}: {count} requests\n"
    else:
        report += "    - No errors detected\n"
    
    report += f"""
    Performance Assessment:
    """
    
    if statistics.mean(response_times) < 0.1:
        report += "    - Response time: EXCELLENT (< 100ms average)\n"
    elif statistics.mean(response_times) < 0.5:
        report += "    - Response time: GOOD (< 500ms average)\n"
    elif statistics.mean(response_times) < 1.0:
        report += "    - Response time: ACCEPTABLE (< 1s average)\n"
    else:
        report += "    - Response time: NEEDS IMPROVEMENT (> 1s average)\n"
    
    if success_count / len(requests) >= 0.99:
        report += "    - Reliability: EXCELLENT (99%+ success rate)\n"
    elif success_count / len(requests) >= 0.95:
        report += "    - Reliability: GOOD (95%+ success rate)\n"
    else:
        report += "    - Reliability: NEEDS IMPROVEMENT (< 95% success rate)\n"
    
    if throughput >= 100:
        report += "    - Throughput: EXCELLENT (100+ RPS)\n"
    elif throughput >= 50:
        report += "    - Throughput: GOOD (50+ RPS)\n"
    else:
        report += "    - Throughput: NEEDS IMPROVEMENT (< 50 RPS)\n"
    
    report += "\n    ========================================\n"
    
    print(report)
    
    # Save report
    with open('test-results/load-test-report.txt', 'w') as f:
        f.write(report)

analyze_results()
PYTHON_SCRIPT

# Collect metrics from service
echo "Collecting service metrics..."
curl -s "$SERVICE_URL/metrics" > test-results/service-metrics.txt

echo "Load test analysis complete! Check test-results/ directory for detailed reports."