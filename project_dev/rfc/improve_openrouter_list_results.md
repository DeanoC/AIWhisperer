# Feature Request: Improve OpenRouter List Models Results

## Problem Statement

The current `--list-models` command only displays a simple list of model names to the console. This is useful for quick reference but does not provide detailed information about each model's capabilities, pricing, or other important characteristics that would help users select the most appropriate model for their needs.

## Proposed Solution

Enhance the `--list-models` command to:

1. Add an optional `--output-csv` parameter to save model details to a CSV file
2. Retrieve and include additional model metadata from OpenRouter API:
   - Model features/capabilities
   - Cost per input/output token
   - Context window size
   - Provider information
   - Any other relevant model attributes available from OpenRouter

## Implementation Details

1. Modify the `main.py` module to accept an additional optional argument `--output-csv` when used with `--list-models`
2. Enhance the `OpenRouterAPI.list_models()` method to fetch comprehensive model details instead of just names
3. Add functionality to format and export this data to CSV when requested

## Example Usage

```bash
# Current functionality: List models to console
ai-whisperer --list-models --config config.yaml

# New functionality: Export detailed model info to CSV
ai-whisperer --list-models --config config.yaml --output-csv models.csv
```

## Benefits

- Users can more easily compare and select models based on their specific requirements
- CSV format enables sorting, filtering, and analysis in spreadsheet applications
- Facilitates model selection based on pricing and performance characteristics
- Provides a reference document for model capabilities that can be shared or stored

## Acceptance Criteria

- [ ] Command line supports new optional `--output-csv` parameter
- [ ] OpenRouter API integration retrieves comprehensive model metadata
- [ ] CSV export properly formats all available model information
- [ ] Console output still works as before when `--output-csv` is not specified
- [ ] Documentation updated to reflect new functionality
