# Alice Prompt A/B Testing Process

## Complete Testing Workflow

### 1. Initial Setup

First, ensure the prompt metrics tool is properly integrated:

```bash
cd /home/deano/projects/AIWhisperer
python scripts/alice_prompt_testing/setup_metrics_integration.py
```

This will:
- ✅ Create metrics directory
- ✅ Verify prompt_metrics_tool is in the correct location
- ✅ Create a template revised prompt if needed
- ✅ Set up initial metrics files

### 2. Create Your Revised Prompt

Edit the revised Alice prompt with your improvements:

```bash
# Edit the revised prompt
nano prompts/agents/alice_assistant_revised.prompt.md
```

Key improvements to consider:
- **Response Channels**: Ensure ALWAYS using [ANALYSIS], [COMMENTARY], [FINAL]
- **Conciseness**: Add "Skip preambles" and "Get straight to the point"
- **Autonomy**: Emphasize "Use tools immediately without asking permission"
- **Task Completion**: Add "Complete all steps before responding"

### 3. Run A/B Tests

Run the test suite with multiple iterations:

```bash
# Quick test (1 iteration)
python scripts/alice_prompt_testing/run_ab_tests.py --iterations 1

# Standard test (3 iterations) 
python scripts/alice_prompt_testing/run_ab_tests.py --iterations 3

# Comprehensive test (5 iterations)
python scripts/alice_prompt_testing/run_ab_tests.py --iterations 5
```

Test results will be saved to:
- `scripts/alice_prompt_testing/results/ab_test_results_[timestamp].json`
- `scripts/alice_prompt_testing/results/ab_test_summary_[timestamp].json`

### 4. Evaluate with Debbie

Use Debbie to provide detailed evaluation of the responses:

```bash
# Find your latest results file
ls -la scripts/alice_prompt_testing/results/

# Run Debbie's evaluation
python scripts/alice_prompt_testing/evaluate_with_debbie.py \
  scripts/alice_prompt_testing/results/ab_test_results_[timestamp].json
```

This creates:
- `results/evaluations/debbie_evaluations_[timestamp].json`
- `results/evaluations/evaluation_summary_[timestamp].json`

### 5. Analyze Results

Review the evaluation summary to see:
- Average scores by version (current vs revised)
- Improvements across all criteria
- Per-scenario performance differences

Key metrics to examine:
- **Channel Compliance**: Should be 100% for revised prompt
- **Conciseness Score**: Higher is better (max 100)
- **Autonomy Score**: Higher indicates less permission-seeking
- **Tool Usage**: Should increase with revised prompt
- **Overall Score**: Weighted combination of all metrics

### 6. Iterate and Improve

Based on results:
1. Identify weak areas in the revised prompt
2. Update `alice_assistant_revised.prompt.md`
3. Re-run tests to verify improvements
4. Repeat until satisfactory results

## Test Scenarios Explained

### 1. test_workspace_status.txt
- **Purpose**: Tests if Alice proactively uses tools to check workspace
- **Good response**: Uses `workspace_stats` or similar tools immediately
- **Poor response**: Just describes what could be done

### 2. test_agent_listing.txt  
- **Purpose**: Tests comprehensive agent information delivery
- **Good response**: Lists all agents with clear descriptions
- **Poor response**: Vague or incomplete agent list

### 3. test_mailbox_question.txt
- **Purpose**: Tests mailbox system understanding and tool usage
- **Good response**: Explains system AND checks for messages
- **Poor response**: Only explains without checking

### 4. test_high_level_code.txt
- **Purpose**: Tests code architecture understanding
- **Good response**: Uses tools to explore and explain architecture
- **Poor response**: Generic explanation without exploring

### 5. test_low_level_code.txt
- **Purpose**: Tests specific code detail retrieval
- **Good response**: Finds and shows actual tool code
- **Poor response**: Describes without showing code

## Success Criteria

A successful revised prompt should show:

✅ **100% Channel Compliance** - All responses use proper channels
✅ **Improved Conciseness** - Fewer words, no preambles
✅ **Higher Autonomy** - No permission-seeking phrases
✅ **More Tool Usage** - Proactive tool use for all requests
✅ **Better Task Completion** - Fully addresses user requests

## Example Good vs Bad Responses

### Bad (Current Prompt):
```
I'll help you check the workspace status. Let me look into that for you.

To check the workspace status, I can use the workspace_stats tool. Would you like me to run it?
```

### Good (Revised Prompt):
```
[ANALYSIS]
User wants workspace status. Using workspace_stats tool immediately.
[/ANALYSIS]

[COMMENTARY]
Running workspace_stats to get current metrics...
[/COMMENTARY]

[FINAL]
Workspace contains 1,247 Python files, 89 test files, and 15,823 lines of code. 
Last modified: 2 minutes ago. All tests passing.
[/FINAL]
```

## Troubleshooting

### "Tool not found" errors
- Run `setup_metrics_integration.py` again
- Check that prompt_metrics_tool.py exists in ai_whisperer/tools/

### "Connection refused" errors
- Ensure no other servers running: `lsof -i :8000`
- Check config file has valid OpenRouter API key

### Low scores across the board
- Review the revised prompt for clarity
- Ensure instructions are explicit and unambiguous
- Add specific examples in the prompt

### Debbie evaluation fails
- Check JSON parsing in responses
- Ensure Debbie is using structured evaluation format
- Review raw evaluation responses for errors