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

* `id`: The unique identifier of the model.
* `name`: The human-readable name of the model.
* `description`: A brief description of the model.
* `features`: A list of features supported by the model.
* `context_window`: The maximum context window size for the model.
* `input_cost`: The cost per token for prompt input.
* `output_cost`: The cost per token for completion output.

## Refining Requirement Documents

The `refine` command allows you to refine a requirement document using an AI model. This can help improve clarity, consistency, and completeness of your requirements.

```bash
ai_whisperer refine <input_file_path> --config <config_file_path> [--prompt-file <prompt_file_path>] [--iterations <number_of_iterations>]
```

**Purpose:**

* Refines an existing requirement document (e.g., a Markdown file) using an AI model.

**Arguments:**

* `<input_file_path>` (Required): The path to the requirement document you want to refine.
* `--config <config_file_path>` (Required): Path to the configuration YAML file. This file contains API keys and model preferences necessary for AI interaction.
* `--prompt-file <prompt_file_path>` (Optional): Path to a custom prompt file. If not provided, a default prompt will be used for the refinement process.
* `--iterations <number_of_iterations>` (Optional): The number of refinement iterations to perform. Defaults to 1.

**Output Behavior:**

When you run the `refine` command:

1. The original input file (e.g., `requirements.md`) is renamed to include both an "old_" prefix and an iteration number (e.g., `old_requirements_iteration1.md`).
2. The AI-refined content is then written back to the original filename (e.g., `requirements.md`).
3. If multiple iterations are specified, each iteration builds upon the previous refinement.

**Examples:**

1. **Basic Usage (refine a document with default prompt):**

   ```bash
   ai_whisperer refine my_project_requirements.md --config config.yaml
   ```

2. **Using a Custom Prompt:**

   ```bash
   ai_whisperer refine my_project_requirements.md --config config.yaml --prompt-file custom_refine_prompt.txt
   ```

3. **Specifying Number of Iterations:**

   ```bash
   ai_whisperer refine my_project_requirements.md --config config.yaml --iterations 3
   ```
