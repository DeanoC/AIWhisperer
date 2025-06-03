# Alice Prompt A/B Testing Framework

This directory contains a comprehensive testing framework for evaluating improvements to Alice's prompt.

## Overview

The framework allows you to:
1. Run automated A/B tests comparing current vs revised Alice prompts
2. Collect detailed metrics on response quality
3. Use Debbie (the debugger agent) to evaluate responses
4. Generate reports comparing prompt effectiveness

## Test Scenarios

The framework includes 5 key test scenarios:

1. **test_workspace_status.txt** - Tests Alice's ability to proactively check workspace status
2. **test_agent_listing.txt** - Tests comprehensive agent information delivery  
3. **test_mailbox_question.txt** - Tests mailbox system explanation and checking
4. **test_high_level_code.txt** - Tests high-level code architecture understanding
5. **test_low_level_code.txt** - Tests specific code detail retrieval

## Setup

1. First, run the setup script to ensure everything is configured:
   ```bash
   python scripts/alice_prompt_testing/setup_metrics_integration.py
   ```

2. Create your revised Alice prompt at:
   ```
   prompts/agents/alice_assistant_revised.prompt.md
   ```

## Running A/B Tests

### Full Test Suite
Run all test scenarios with both prompt versions (3 iterations by default):
```bash
python scripts/alice_prompt_testing/run_ab_tests.py --config config/main.yaml
```

### Custom Iterations
Run with a specific number of iterations:
```bash
python scripts/alice_prompt_testing/run_ab_tests.py --iterations 5
```

### Single Test
Run a specific test scenario:
```bash
python scripts/alice_prompt_testing/run_ab_tests.py --single test_workspace_status.txt --version revised
```

## Evaluating Results

After running tests, use Debbie to evaluate the responses:
```bash
python scripts/alice_prompt_testing/evaluate_with_debbie.py results/ab_test_results_[timestamp].json
```

This will:
- Have Debbie analyze each response based on 5 criteria
- Generate scores for channel compliance, conciseness, autonomy, task completion, and tool usage
- Create a summary comparing current vs revised prompt performance

## Results Structure

### Test Results (`results/ab_test_results_*.json`)
Contains raw test data including:
- Test scenario name
- Prompt version used
- Session ID
- Full conversation transcript
- Basic metrics

### Evaluation Results (`results/evaluations/debbie_evaluations_*.json`)
Contains Debbie's analysis including:
- Scores for each evaluation criterion (0-10)
- Strengths and weaknesses identified
- Specific improvement suggestions

### Summary Reports
Both test runner and evaluator generate summary JSON files with:
- Success rates by version
- Average scores across criteria
- Improvement metrics (revised vs current)
- Per-scenario breakdowns

## Prompt Metrics Tool

The framework integrates with `prompt_metrics_tool` which tracks:
- Channel compliance (use of [ANALYSIS], [COMMENTARY], [FINAL])
- Response conciseness (word count, forbidden patterns)
- Autonomy indicators (permission-seeking patterns)
- Tool usage patterns
- Overall effectiveness scores

## Creating Test Scenarios

To add new test scenarios:

1. Create a new `.txt` file in this directory
2. Add comments starting with `#` to describe the test
3. Write the user message(s) as plain text
4. Add the filename to the `test_scenarios` list in `run_ab_tests.py`

Example:
```text
# Test Alice's ability to find specific functions
# This tests code search and analysis capabilities

Can you find all functions that handle WebSocket connections in this codebase?
```

## Interpreting Results

### Key Metrics to Watch

1. **Channel Compliance Rate**: Should be 100% for revised prompt
2. **Conciseness Score**: Higher is better (max 100)
3. **Autonomy Score**: Higher indicates less permission-seeking
4. **Tool Usage Count**: Should increase with revised prompt
5. **Task Completion Rate**: Should be near 100%

### Success Indicators

A successful revised prompt should show:
- ✅ Consistent use of response channels
- ✅ More concise responses (fewer preambles)
- ✅ Proactive tool usage without asking permission
- ✅ Complete task execution before responding
- ✅ Higher overall scores from Debbie's evaluation

## Troubleshooting

### Common Issues

1. **"No revised prompt found"**
   - Create `prompts/agents/alice_assistant_revised.prompt.md`

2. **"Tool not registered"**
   - Run `setup_metrics_integration.py` to register tools

3. **"Connection refused"**
   - Ensure no other servers are running on the same port
   - Check that config file has valid OpenRouter API key

4. **"Evaluation parsing failed"**
   - Check Debbie's response format in the raw evaluation
   - Ensure Debbie is using JSON code blocks for scores

## Best Practices

1. **Run multiple iterations** - At least 3 to account for variability
2. **Test both versions** - Always compare against baseline
3. **Review raw responses** - Don't just rely on scores
4. **Iterate on prompts** - Use evaluation feedback to improve
5. **Document changes** - Keep track of what prompt changes you make

## Example Workflow

1. Create revised prompt with improvements
2. Run A/B tests: `python run_ab_tests.py`
3. Evaluate with Debbie: `python evaluate_with_debbie.py results/latest.json`
4. Review summary reports
5. Iterate on prompt based on feedback
6. Repeat until metrics improve significantly