# Using the AI Whisperer CLI

This document provides examples and explanations for using the AI Whisperer command-line interface.

## Listing Available Models

The `--list-models` command allows you to view a list of available models from configured providers, such as OpenRouter.

```bash
ai_whisperer --list-models
```

### Outputting Model List to CSV

You can output the detailed list of models to a CSV file using the optional `--output-csv` parameter. This is useful for further analysis or processing of the model data.

```bash
ai_whisperer --list-models --output-csv path/to/models_output.csv
```

The CSV file will contain the following columns:

*   `id`: The unique identifier of the model.
*   `name`: The human-readable name of the model.
*   `description`: A brief description of the model.
*   `features`: A list of features supported by the model.
*   `context_window`: The maximum context window size for the model.
*   `input_cost`: The cost per token for prompt input.
*   `output_cost`: The cost per token for completion output.
