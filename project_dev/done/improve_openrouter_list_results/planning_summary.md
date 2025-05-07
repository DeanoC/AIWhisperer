# Planning Summary: Enhance OpenRouter List Models Command

## Overview

This document outlines the plan to enhance the `ai-whisperer` tool's `[`--list-models`](src/ai_whisperer/main.py)` command to include detailed metadata and an optional CSV output.

## 1. Analyze Existing Code

*   **[`src/ai_whisperer/main.py`](src/ai_whisperer/main.py):** The `[`--list-models`](src/ai_whisperer/main.py)` command is handled using `argparse`. When specified, the script loads the configuration, instantiates `OpenRouterAPI`, calls the `list_models()` method, and prints the models to the console.
*   **[`src/ai_whisperer/openrouter_api.py`](src/ai_whisperer/openrouter_api.py):** The `[`OpenRouterAPI.list_models()`](src/ai_whisperer/openrouter_api.py)` method retrieves a list of available model IDs from the OpenRouter API by sending a GET request to the `[`/models`](https://openrouter.ai/docs#models)` endpoint. It extracts model IDs from the JSON response and handles potential errors.

## 2. Add `[`--output-csv`](src/ai_whisperer/main.py)` Argument

*   Modify [`src/ai_whisperer/main.py`](src/ai_whisperer/main.py) to add a new argument `[`--output-csv`](src/ai_whisperer/main.py)` using `argparse`.
*   The argument should accept a file path as its value.
*   When `[`--output-csv`](src/ai_whisperer/main.py)` is specified, the script should call a function to format and write the model data to the specified CSV file.

## 3. Modify API Call to Get Detailed Model Info

*   The `[`/models`](https://openrouter.ai/docs#models)` endpoint already returns detailed model information.
*   Modify the `[`OpenRouterAPI.list_models()`](src/ai_whisperer/openrouter_api.py)` method in [`src/ai_whisperer/openrouter_api.py`](src/ai_whisperer/openrouter_api.py) to extract all relevant information from the model objects in the `data` array.

## 4. Plan Data Structure for Detailed Model Info

*   Define a Python dictionary or class to represent the structure of the detailed model data.
*   The data structure should include fields such as:
    *   `id`: Model ID (string)
    *   `name`: Model name (string)
    *   `pricing`: Pricing information (dictionary or class)
    *   `description`: Model description (string)
    *   `features`: Model features (list of strings)
    *   `context_window`: Context window size (integer)
    *   `input_cost`: Input cost (float)
    *   `output_cost`: Output cost (float)

## 5. Plan CSV Formatting Logic

*   Use the `csv` Python library to write the data to a CSV file.
*   Define the CSV header row with the field names from the data structure.
*   For each model, format the data into a CSV row and write it to the file.
*   Handle potential errors during CSV writing.

## 6. Required Code Changes

### [`src/ai_whisperer/main.py`](src/ai_whisperer/main.py)

*   Add `[`--output-csv`](src/ai_whisperer/main.py)` argument using `argparse`.
*   Modify the `if args.list_models:` block to:
    *   Call `OpenRouterAPI.list_models()` to get the detailed model data.
    *   If `[`--output-csv`](src/ai_whisperer/main.py)` is specified:
        *   Call a function to format and write the model data to the specified CSV file.
    *   Otherwise:
        *   Print the model IDs to the console as before.

### [`src/ai_whisperer/openrouter_api.py`](src/ai_whisperer/openrouter_api.py)

*   Modify the `[`OpenRouterAPI.list_models()`](src/ai_whisperer/openrouter_api.py)` method to:
    *   Extract all relevant information from the model objects in the `data` array.
    *   Return a list of dictionaries, where each dictionary represents a model and contains the detailed model information.