---
description: Run load tests to measure performance under stress
argument-hint: <url> [--users <count>] [--duration <seconds>] [--rps <target>]
model: claude-haiku-4-20250514
allowed-tools: Bash, Write
---

Load test: **${ARGUMENTS}**

## Load Testing

**Simulates**:

- Concurrent users
- Sustained load
- Traffic spikes
- Stress testing

```bash
URL="${URL}"
USERS="${USERS:-100}"
DURATION="${DURATION:-60}"
RPS_TARGET="${RPS:-100}"

echo "🚀 Starting load test..."
echo "======================================"
echo "Target: $URL"
echo "Virtual users: $USERS"
echo "Duration: $DURATION seconds"
echo "Target RPS: $RPS_TARGET"
echo "======================================"

# Check if artillery is installed
if ! command -v artillery &> /dev/null; then
  echo "Installing artillery..."
  npm install -g artillery
fi

# Create test scenario
cat > /tmp/load-test.yml <<EOF
config:
  target: "$URL"
  phases:
    - duration: 60
      arrivalRate: $RPS_TARGET
      name: "Sustained load"
  processor: "./test-processor.js"
scenarios:
  - name: "API Load Test"
    flow:
      - get:
          url: "/api/health"
      - think: 1
      - get:
          url: "/api/data"
EOF

# Run load test
artillery run /tmp/load-test.yml

# Alternative: Use Apache Bench for simple tests
# ab -n $((USERS * 10)) -c $USERS $URL

echo "======================================"
echo "✅ Load test complete"
echo "Review results above"
```

## Metrics Tracked

- **Throughput**: Requests per second
- **Latency**: p50, p95, p99 response times
- **Errors**: Error rate and types
- **Concurrency**: Max concurrent requests handled

## Success Criteria

- ✓ RPS > target
- ✓ p95 latency < 500ms
- ✓ Error rate < 1%
- ✓ No service crashes

---
**Model**: Haiku (fast)
**Output**: Load test results
**Next**: `/performance/profile` (analyze bottlenecks)
