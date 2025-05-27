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

## Next Steps

- Integrate metrics collection into automated test scripts.
- Add reporting step to CI pipeline or test runner.
- Periodically review and update performance targets as system evolves.
