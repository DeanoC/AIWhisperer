# Performance Metrics for AILoop Interactive Integration

## Key Metrics

- **Session Latency:**
  - Time from user message sent to first AI chunk received.
  - Time from user message sent to final response.
- **Throughput:**
  - Number of user messages processed per second (across all sessions).
- **Concurrent Sessions:**
  - Maximum number of stable, active WebSocket sessions.
- **Memory Usage:**
  - Peak and average memory usage during load tests.
- **Error Rate:**
  - Number and type of errors per 1000 requests (timeouts, disconnects, AI errors).
- **Session Duration:**
  - Average and maximum session lifetime under load.
- **AI Service Timeout Handling:**
  - Time to detect and report AI service timeouts.

## Measurement Approach

- Use automated pytest scripts to:
  - Record timestamps for sent/received messages.
  - Log memory usage (via `tracemalloc` or `psutil`).
  - Count errors and timeouts.
  - Track session open/close events.
- Aggregate results into a summary report after each test run.


## Reporting

- Store raw metrics in CSV or JSON for analysis.
- Summarize key metrics in markdown or HTML for documentation.
- Compare results to baseline and performance targets.

---

# 📊 Current Performance Metrics Summary (auto-generated)

See also: `performance_metrics_report.md`

## memory_usage_metrics.csv

- Samples: 243
- Mean latency: 32,455,837.30 ms
- Median latency: 65.21 ms
- Min: 17.77 ms, Max: 2,633,826,000.00 ms
- 95th percentile: 97.92 ms
- Stddev: 290,893,379.59 ms

## long_running_session_metrics.csv

- Samples: 93
- Mean latency: 0.73 ms
- Median latency: 0.62 ms
- Min: 0.16 ms, Max: 2.85 ms
- 95th percentile: 2.17 ms
- Stddev: 0.52 ms

## ai_service_timeout_metrics.csv

- Samples: 10
- Mean latency: 5,006.56 ms
- Median latency: 5,004.72 ms
- Min: 2.00 ms, Max: 10,015.69 ms
- Stddev: 5,274.72 ms

---

## Next Steps

- Integrate metrics collection into automated test scripts (done)
- Add reporting step to CI pipeline or test runner (see `summarize_performance_metrics.py`)
- Periodically review and update performance targets as system evolves.
