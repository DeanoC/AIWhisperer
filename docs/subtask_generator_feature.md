# Subtask Generator Feature

## Overview

The Subtask Generator is a component of the AIWhisperer system that refines high-level task steps into detailed, executable subtask YAML definitions using AI. This feature allows for automated refinement of tasks broken down by the Orchestrator, providing more detailed instructions, context, and validation criteria for each step.

## How It Works

1. **Input**: A high-level step definition YAML file containing basic information such as `step_id`, `description`, and optional `context` information.
2. **Processing**:
   - Loads configuration settings including the AI model to use
   - Gathers additional context from relevant files if specified in the input step
   - Constructs a prompt using the input step data, context, and template
   - Sends the prompt to the AI model via OpenRouter API
   - Parses and validates the AI-generated YAML response
3. **Output**: A detailed subtask YAML file saved to the `output` directory with a filename derived from the `step_id`.

## Usage

### Command Line

```bash
# Basic usage
python -m src.ai_whisperer.main --generate-subtask --config config.yaml --step step_definition.yaml

# Example with actual file paths
python -m src.ai_whisperer.main --generate-subtask --config ./config.yaml --step ./steps/step_1.yaml
```

### Configuration

The Subtask Generator uses the following configuration settings in your `config.yaml`:

```yaml
# OpenRouter API settings for AI interaction
openrouter:
  api_key: "sk-or-v1-..." # Or use OPENROUTER_API_KEY environment variable
  model: "mistralai/mistral-7b-instruct" # Or another compatible model
  params:
    temperature: 0.7
    max_tokens: 2048

# Prompt template settings
prompts:
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md" # Path to the prompt template

# Output directory
output_dir: "./output/"
```

## Input Format

The input step YAML file should include at least:

```yaml
step_id: unique_step_identifier
description: "A clear description of what this step should accomplish"
depends_on: [] # Optional: IDs of steps this step depends on

# Optional context information
context:
  relevant_files:
    - src/feature_x.py
    - tests/test_feature_x.py
```

## Output Format

The generated subtask YAML includes:

```yaml
task_id: unique_step_identifier # Derived from the input step_id
natural_language_goal: "Detailed description of the task objective"
overall_context: "Context information and background"
input_hashes: # Hashes of input files for verification
  step_yaml: "sha256-hash-of-input-step"
  # Additional files used for context
plan:
  - step_id: "implementation-step-1"
    description: "Detailed step description"
    # Additional execution details
  - step_id: "implementation-step-2"
    # ...
validation_criteria:
  - "Criteria for verifying successful completion"
  # ...
```

The output file is saved as `output/{task_id}_subtask.yaml`.

## Prompt Template

The prompt template (`prompts/subtask_generator_default.md`) guides the AI in generating detailed, well-structured subtask definitions. You can customize this template to suit your project's specific needs.

## Schema Validation

Generated subtasks are validated against a JSON schema (`src/ai_whisperer/schemas/task_schema.json`) to ensure consistency and correctness.

## Error Handling

The Subtask Generator handles various error scenarios:
- Missing or invalid configuration
- File access issues
- AI model response errors
- Schema validation failures

Errors are logged and displayed to the user with appropriate context.

## Customization

You can customize the Subtask Generator's behavior by:
- Modifying the prompt template in `prompts/subtask_generator_default.md`
- Adjusting the AI model parameters in `config.yaml`
- Enhancing the context gathering logic for more specialized information retrieval

## Testing

The Subtask Generator includes comprehensive tests:

- Unit tests in `tests/test_subtask_generator.py` (with mocked AI responses)
- Integration tests in `tests/test_subtask_integration.py` (testing CLI arguments and flows)

Run the tests using:

```bash
pytest tests/test_subtask_generator.py tests/test_subtask_integration.py -v
```

## Future Enhancements

Planned enhancements for the Subtask Generator include:
- Enhanced context gathering from version control history
- Better integration with external documentation sources
- Support for multi-step dependency analysis
- Interactive refinement workflow
