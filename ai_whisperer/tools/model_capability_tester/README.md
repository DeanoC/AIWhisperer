# Model Capability Tester 🔍

A standalone tool for automatically testing OpenRouter models to detect their capabilities and quirks.

**Location**: `ai_whisperer/tools/model_capability_tester/`

## Features

- Tests basic functionality, tool calling, structured output, and model-specific quirks
- Detects capabilities like:
  - Single and multi-tool calling
  - Parallel tool execution
  - Structured JSON output support
  - Reasoning token support (for models that advertise it)
- Identifies quirks like:
  - `no_tools_with_structured_output`: Models that can't use tools and structured output together (e.g., Gemini)
- Outputs results in JSON format compatible with `model_capabilities.py`

## Usage

### Run as a Python module (recommended)
```bash
python -m ai_whisperer.tools.model_capability_tester
```

### Test top models (default)
```bash
python -m ai_whisperer.tools.model_capability_tester
```
This tests the most popular models from OpenRouter rankings.

### Test a specific model
```bash
python -m ai_whisperer.tools.model_capability_tester --model google/gemini-2.5-flash-preview
```

### List available models
```bash
python -m ai_whisperer.tools.model_capability_tester --list
```

### Test ALL models (expensive!)
```bash
python -m ai_whisperer.tools.model_capability_tester --all
```
⚠️ **Warning**: This will test hundreds of models and can be very expensive!

### Custom output file
```bash
python -m ai_whisperer.tools.model_capability_tester --output my_results.json
```

### Direct script execution (alternative)
```bash
cd ai_whisperer/tools/model_capability_tester
python test_models.py --list
```

## Output Files

The script generates two files:

1. **Full test results** (`model_capabilities_tested.json`):
   - Complete test results including all test data
   - Error messages for failed tests
   - Timestamps and detailed responses

2. **Capability dictionary** (`model_capabilities_tested_capabilities.json`):
   - Clean dictionary format compatible with `model_capabilities.py`
   - Only includes successfully tested models
   - Ready to review and merge into the main configuration

## Test Suite

The tool runs the following tests on each model:

1. **Basic Functionality**: Can the model respond to simple prompts?
2. **Single Tool Calling**: Can the model call a single tool?
3. **Multiple Tool Calling**: Can the model call multiple tools in one response?
4. **Structured Output**: Does the model support JSON Schema validated responses?
5. **Tools + Structured Output**: Can the model use both features together? (quirk detection)
6. **Reasoning Tokens**: For models with "thinking" or "reasoning" in their name

## Example Output

```json
{
  "generated_at": "2024-06-04T10:30:00",
  "model_capabilities": {
    "google/gemini-2.5-flash-preview": {
      "multi_tool": true,
      "parallel_tools": true,
      "max_tools_per_turn": 10,
      "structured_output": true,
      "quirks": {
        "no_tools_with_structured_output": true
      }
    }
  }
}
```

## Rate Limiting

The tool includes a 2-second delay between model tests to avoid rate limiting. Intermediate results are saved after each test in case the process is interrupted.

## Cost Considerations

- Testing a single model typically costs < $0.01
- Testing top models (~20) costs approximately $0.10-0.20
- Testing all models (200+) can cost $2-5 depending on the models

## Integration

After running the tests:

1. Review the generated `*_capabilities.json` file
2. Compare with existing entries in `ai_whisperer/model_capabilities.py`
3. Manually merge new discoveries, being careful to preserve any manual overrides
4. Test the changes with actual AIWhisperer usage

## Adding New Tests

To add new capability or quirk tests, modify the `ModelCapabilityTester` class:

1. Add a new test method (e.g., `_test_new_feature()`)
2. Call it from `test_model()`
3. Update the capability dictionary generation
4. Document the new capability/quirk in both this README and `model_capabilities.py`