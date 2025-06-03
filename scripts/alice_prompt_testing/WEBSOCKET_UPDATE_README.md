# WebSocket Protocol Update for A/B Testing Scripts

## Summary of Changes

The A/B testing scripts have been updated to use the proper WebSocket JSON-RPC protocol based on the working implementation in `test_simple_fixed.py`. The key changes include:

### 1. Proper WebSocket Connection Flow

Both scripts now follow the correct protocol:
1. Connect to WebSocket server
2. Set up notification handlers to capture channel messages
3. Start a session using `startSession` method
4. Send messages using `sendUserMessage` method
5. Capture responses via notification handlers

### 2. Response Capture via Notifications

Instead of expecting direct responses from WebSocket calls, the scripts now:
- Set up notification handlers that listen for `ChannelMessageNotification` events
- Collect all channel messages (ANALYSIS, COMMENTARY, FINAL) 
- Combine them into full responses for analysis

### 3. Enhanced Metrics Collection

The `run_ab_tests.py` script now collects more detailed metrics:
- Channel usage (has_channels, has_analysis, has_commentary, has_final)
- Preamble detection (checking for phrases like "I'll help you", "Let me")
- Permission-seeking detection (checking for "Would you like me to", "Should I")
- Response and FINAL section lengths
- Channel count per response

### 4. Improved Debbie Evaluation

The `evaluate_with_debbie.py` script:
- Properly switches to Debbie using the WebSocket protocol
- Captures Debbie's evaluation responses via notifications
- Includes better JSON extraction from Debbie's responses
- Adds color-coded output for improvements (green for positive, red for negative)

## Usage Examples

### Running A/B Tests

```bash
# Run full A/B test with 3 iterations (tests both current and revised prompts)
python scripts/alice_prompt_testing/run_ab_tests.py

# Run with custom iterations
python scripts/alice_prompt_testing/run_ab_tests.py --iterations 5

# Test a single scenario
python scripts/alice_prompt_testing/run_ab_tests.py --single test_workspace_status.txt --version current

# Test revised prompt only
python scripts/alice_prompt_testing/run_ab_tests.py --single test_workspace_status.txt --version revised
```

### Evaluating Results with Debbie

```bash
# Evaluate the most recent test results
python scripts/alice_prompt_testing/evaluate_with_debbie.py results/ab_test_results_20250603_HHMMSS.json

# With custom config
python scripts/alice_prompt_testing/evaluate_with_debbie.py results/ab_test_results_20250603_HHMMSS.json --config config/main.yaml
```

## Output Files

### A/B Test Results

Results are saved in `scripts/alice_prompt_testing/results/`:
- `ab_test_results_TIMESTAMP.json` - Full test results with all responses
- `ab_test_summary_TIMESTAMP.json` - Summary statistics

### Debbie Evaluations

Evaluations are saved in `scripts/alice_prompt_testing/results/evaluations/`:
- `debbie_evaluations_TIMESTAMP.json` - Full evaluation details
- `evaluation_summary_TIMESTAMP.json` - Summary of scores and improvements

## Key Improvements in Metrics

The updated scripts now properly measure:
1. **Channel Compliance** - Whether Alice uses the required channel structure
2. **Conciseness** - Avoidance of unnecessary preambles
3. **Autonomy** - Not seeking permission, taking initiative
4. **Task Completion** - Fully addressing user requests
5. **Tool Usage** - Proactive and appropriate tool selection

## Troubleshooting

If you encounter issues:
1. Ensure the server starts properly (3-second delay is built in)
2. Check that the WebSocket connection is established
3. Verify that notification handlers are receiving messages
4. Look for error messages in the results JSON files

The scripts now properly handle the asynchronous nature of WebSocket communications and should reliably capture all responses from Alice for comparison.