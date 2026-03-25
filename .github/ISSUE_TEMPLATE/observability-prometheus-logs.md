---
    title: "📊 Observability: Add Prometheus metrics & structured logging"
    labels: "enhancement, monitoring, devops"
    ---

    ## Problem Statement

    Agent Zero currently has **no observability** - operators cannot:

    - Monitor system health (uptime, errors, latency)
    - Track resource usage (memory, CPU, network)
    - Debug issues (no structured logs, logs buried in HTML)
    - Set up alerts for failures
    - Understand usage patterns (no metrics)

    ## Current Limitations

    1. **Logs**
       - Logs stored in `log.py` as plain text
       - Saved to `logs/` as HTML files (human-readable only)
       - No log levels (just types: 'info', 'warning', 'error')
       - No JSON output for log aggregation
       - No correlation IDs for tracing requests

    2. **Metrics**
       - Zero built-in metrics
       - No counters, gauges, histograms
       - Can't measure:
         - Requests per second
         - Agent response latency
         - Tool execution times
         - Memory search performance
         - LLM API call costs
         - Error rates

    3. **Tracing**
       - No distributed tracing
       - Can't track request flow across agents/subordinates
       - No W3C Trace Context propagation

    4. **Alerting**
       - No built-in alerting on failures
       - No integration with PagerDuty, Slack, etc.

    ## Proposed Solution

    ### 1. Prometheus Metrics Endpoint

    Add `/metrics` endpoint exposing:

    ```python
    # prometheus-metrics-example
    from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest

    # Counters
    AGENT_REQUESTS_TOTAL = Counter('agent_requests_total', 'Total agent requests', ['agent_id', 'profile'])
    AGENT_ERRORS_TOTAL = Counter('agent_errors_total', 'Total agent errors', ['agent_id', 'error_type'])
    TOOL_CALLS_TOTAL = Counter('tool_calls_total', 'Total tool invocations', ['tool_name', 'agent_id'])
    LLM_CALLS_TOTAL = Counter('llm_calls_total', 'Total LLM API calls', ['provider', 'model'])

    # Histograms (latency distributions)
    AGENT_RESPONSE_DURATION = Histogram('agent_response_duration_seconds', 'Agent response time', ['agent_id'])
    TOOL_EXECUTION_DURATION = Histogram('tool_execution_duration_seconds', 'Tool execution time', ['tool_name'])
    LLM_TOKEN_GENERATION = Histogram('llm_tokens_generated', 'Tokens generated per LLM call', ['model'])

    # Gauges (current state)
    ACTIVE_AGENTS = Gauge('active_agents', 'Currently active agent contexts')
    MEMORY_ENTRIES_TOTAL = Gauge('memory_entries_total', 'Total entries in vector DB', ['memory_area'])
    MEMORY_SEARCH_DURATION = Histogram('memory_search_duration_seconds', 'Vector search latency')

    # Summaries (percentiles can be calculated)
    TOOL_SUCCESS_RATE = Summary('tool_success_rate', 'Tool success/failure ratio', ['tool_name'])

    @app.get('/metrics')
    def metrics():
        return generate_latest()
    ```

    ### 2. Structured JSON Logging

    Replace current log.py with JSON logger:

    ```python
    import json_log_formatter
    import logging

    handler = logging.StreamHandler()
    handler.setFormatter(json_log_formatter.JSONFormatter())
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Output:
    # {
    #   "timestamp": "2024-01-15T10:30:00.123Z",
    #   "level": "INFO",
    #   "logger": "agent-zero",
    #   "message": "Agent response generated",
    #   "agent_id": "abc123",
    #   "trace_id": "xyz789",
    #   "duration_ms": 1250,
    #   "tool_name": "code_execution_tool"
    # }
    ```

    ### 3. Request Tracing with W3C Trace Context

    ```python
    # Add trace_id to all logs
    import uuid
    from w3c.trace_context import TraceContext

    trace_id = os.environ.get('TRACE_ID', str(uuid.uuid4()))

    def log_with_trace(msg, **kwargs):
        logger.info(msg, extra={'trace_id': trace_id, **kwargs})

    # Propagate via HTTP headers for external API calls
    headers = {
        'traceparent': f'00-{trace_id}-{span_id}-01'
    }
    ```

    ### 4. Alerting (via webhook)

    ```python
    # alerts.py
    async def check_system_health():
        metrics = scrape_metrics()
    
        if metrics['agent_errors_total']['rate_5m'] > 0.1:
            await send_alert('high_error_rate', metrics)
    
        if metrics['agent_response_duration_seconds']['p95'] > 30:
            await send_alert('slow_responses', metrics)
    
        if metrics['active_agents'] > MAX_CONCURRENT_AGENTS:
            await send_alert('overload', metrics)

    # Run every minute
    ```

    ## Implementation Plan

    ### Phase 1: Metrics Instrumentation (Week 1-2)
    1. Add `prometheus-client` to requirements.txt
    2. Create `python/helpers/metrics.py` with all metric definitions
    3. Instrument key functions:
       - `Agent.monologue()` - response duration, iteration count
       - `Tool.execute()` - execution time, success/failure
       - `call_chat_model()` - LLM latency, token counts
       - `Memory.search()` - search latency, result count
    4. Add `/metrics` endpoint to FastAPI app in `run_ui.py`
    5. Verify metrics with `curl http://localhost:8000/metrics`

    ### Phase 2: Structured Logging (Week 3)
    1. Add `python-json-logger` dependency
    2. Modify `python/helpers/log.py` to output JSON when `LOG_FORMAT=json`
    3. Add trace ID propagation:
       - Generate trace_id on agent context creation
       - Include in all log entries
       - Pass to LLM API calls (traceparent header)
    4. Update Docker logging driver to `json-file` (default)
    5. Add log rotation configuration

    ### Phase 3: Grafana Dashboards (Week 4)
    Create dashboards for:

    1. **System Overview**
       - Active agents, requests/sec, error rate
       - Response time p50/p95/p99
       - Memory usage, CPU usage

    2. **LLM Costs**
       - Calls per provider/model
       - Token usage (input/output) per model
       - Estimated costs (if pricing configured)

    3. **Tool Performance**
       - Slowest tools (bar chart)
       - Tool success rates
       - Most frequently used tools

    4. **Memory Operations**
       - Search latency
       - Insert/update rates
       - Memory size growth

    Provide dashboard JSON exports and README.

    ### Phase 4: Alerting Rules (Week 5)
    Add Prometheus alert rules:

    ```yaml
    # alerts.yml
    groups:
      - name: agent_zero
        rules:
          - alert: HighErrorRate
            expr: rate(agent_errors_total[5m]) / rate(agent_requests_total[5m]) > 0.1
            for: 2m
            labels:
              severity: critical
            annotations:
              summary: "High error rate detected"
          
          - alert: SlowResponses
            expr: histogram_quantile(0.95, rate(agent_response_duration_seconds_bucket[5m])) > 30
            for: 5m
            labels:
              severity: warning
    ```

    ## File Changes

    - `requirements.txt` (+2 packages)
    - `python/helpers/metrics.py` (NEW - 150 lines)
    - `python/helpers/log.py` (MODIFIED - JSON format support)
    - `run_ui.py` (+ `/metrics` endpoint)
    - `docker-compose.yml` (add Prometheus service if self-hosted)
    - `monitoring/` directory (NEW):
      - `grafana/dashboards/agent-zero.json`
      - `prometheus/alerts.yml`
      - `README.md` (how to monitor)

    ## Testing

    - [ ] Metrics endpoint returns valid Prometheus format
    - [ ] Metrics increment correctly on operations
    - [ ] Histograms record buckets properly
    - [ ] Logs are valid JSON when JSON format enabled
    - [ ] Trace IDs appear in all log entries
    - [ ] Log rotation works (max size, retention)
    - [ ] Prometheus can scrape metrics successfully
    - [ ] Grafana dashboard displays data correctly

    ## Benefits

    - **Operations:** See what's happening in real-time
    - **Debugging:** Correlate logs with traces
    - **Capacity Planning:** Know when to scale
    - **Cost Control:** Track LLM spending by model
    - **Reliability:** Alert on failures before users notice

    ## Dependencies

    - `prometheus-client` (pure Python, lightweight)
    - `python-json-logger` (pure Python)
    - Optional: `grafana`, `prometheus`, `loki` for full stack

    ## Deployment

    1. Add metrics endpoint (no breaking changes)
    2. Deploy with `PROMETHEUS_MULTIPROC_DIR` if using multi-process
    3. Configure Prometheus scrape job:
    ```yaml
    scrape_configs:
      - job_name: 'agent-zero'
        static_configs:
          - targets: ['localhost:8000']
    ```

    4. Import Grafana dashboard
    5. Set up alertmanager for notifications

    ---
    *Observability is essential for production AI systems.*
    