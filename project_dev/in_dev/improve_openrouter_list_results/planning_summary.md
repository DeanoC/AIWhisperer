# Planning Summary: Improve OpenRouter List Results

This document outlines the plan to enhance the OpenRouter list models command in the AI Whisperer CLI. The goal is to include detailed metadata for each model and add an option to output the data in CSV format.

## 1. API Data Fetching: Changes to [`src/ai_whisperer/openrouter_api.py`](src/ai_whisperer/openrouter_api.py:1)

*   No changes are required in this file. The `list_models()` function already retrieves all the necessary metadata from the OpenRouter API.

## 2. CLI and CSV Output: Changes to [`src/ai_whisperer/main.py`](src/ai_whisperer/main.py:1)

*   **Console Output:**
    *   Modify the `list-models` command to display detailed metadata for each model in the console output. This should include fields such as:
        *   `id`
        *   `name`
        *   `description`
        *   `supported_parameters`
        *   `context_length`
        *   `input_cost`
        *   `output_cost`
        *   `อื่นๆ` (any other relevant metadata)
    *   Consider using a formatted table or a similar approach to display the metadata in a readable way.
*   **CSV Output:**
    *   Ensure that the `--output-csv` option includes all the relevant metadata fields in the CSV output.
    *   Update the `fieldnames` variable in the `list-models` command to include the following fields:
        *   `id`
        *   `name`
        *   `description`
        *   `supported_parameters`
        *   `context_length`
        *   `input_cost`
        *   `output_cost`
        *   `อื่นๆ` (any other relevant metadata)

## 3. Documentation: Changes to [`docs/usage.md`](docs/usage.md:1)

*   **Update the description of the `list-models` command:**
    *   Mention that the command now displays detailed metadata for each model.
*   **Update the example output:**
    *   Provide an example of the detailed metadata output in the console.
*   **Update the description of the CSV output:**
    *   List all the columns that are included in the CSV file. The list should include:
        *   `id`
        *   `name`
        *   `description`
        *   `supported_parameters`
        *   `context_length`
        *   `input_cost`
        *   `output_cost`