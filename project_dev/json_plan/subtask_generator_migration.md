# Subtask Generator Migration Plan

## Introduction

This document outlines the changes needed to migrate the `subtask_generator.py` file from YAML to JSON. The SubtaskGenerator class is responsible for generating detailed subtask definitions from high-level steps, making it a key component in the migration process.

## Current Implementation

The SubtaskGenerator class currently:

1. Generates detailed subtask YAML definitions from input steps
2. Uses both standard `yaml` and `ruamel.yaml` libraries
3. Has a method for sanitizing YAML content
4. Uses the same postprocessing pipeline as the Orchestrator

Key methods that handle YAML:

- `generate_subtask`: Generates a detailed subtask YAML definition
- `_sanitize_yaml_content`: Sanitizes YAML content before parsing
- `_prepare_prompt`: Prepares the prompt for the AI model, including converting input step to YAML

## Required Changes

### 1. Rename Methods and Variables

Update method and variable names to reflect the switch from YAML to JSON:

- `_sanitize_yaml_content` → `_sanitize_json_content`
- Update variable names like `yaml_content` → `json_content`, `yaml_string` → `json_string`, etc.

### 2. Update Import Statements

Replace YAML imports with JSON imports:

```python
# Remove or comment out
import yaml  # Keep for compatibility
from ruamel.yaml import YAML

# Keep or add
import json
```

### 3. Modify `_prepare_prompt` Method

Update the method to convert the input step to JSON instead of YAML:

```python
def _prepare_prompt(self, input_step: Dict[str, Any]) -> str:
    """Prepares the prompt for the AI model using all context placeholders."""
    try:
        # Convert the input step dictionary to a JSON string
        json_str = json.dumps(input_step, indent=2)

        # Replace all placeholders in the template
        prompt = self.subtask_prompt_template
        prompt = prompt.replace("{subtask_json}", json_str)  # Update placeholder name
        # Use stored context
        prompt = prompt.replace("{overall_context}", self.overall_context)
        prompt = prompt.replace("{workspace_context}", self.workspace_context)

        return prompt
    except Exception as e:
        # Catch potential errors during JSON dumping or string replacement
        raise SubtaskGenerationError(f"Failed to prepare prompt: {e}") from e
```

### 4. Modify `_sanitize_yaml_content` Method

Replace with a JSON-specific sanitization method:

```python
def _sanitize_json_content(self, json_string: str) -> str:
    """
    Sanitize JSON content before parsing to handle common issues.

    Args:
        json_string: The raw JSON string to sanitize

    Returns:
        The sanitized JSON string
    """
    # For JSON, we mainly need to ensure it's properly formatted
    # Most of the YAML-specific sanitization isn't needed for JSON

    # Remove any markdown code block markers if present
    if json_string.startswith("```json"):
        json_string = json_string.replace("```json", "", 1)
    if json_string.endswith("```"):
        json_string = json_string.rsplit("```", 1)[0]

    json_string = json_string.strip()

    # Try to parse and re-serialize to ensure valid JSON
    try:
        parsed_json = json.loads(json_string)
        return json.dumps(parsed_json)
    except json.JSONDecodeError:
        # If parsing fails, return the original string for further processing
        return json_string
```

### 5. Update `generate_subtask` Method

Update to handle JSON instead of YAML:

```python
def generate_subtask(self, input_step: Dict[str, Any]) -> str:
    """
    Generates a detailed subtask JSON definition for the given input step.

    Args:
        input_step: A dictionary representing the high-level step from the orchestrator.

    Returns:
        The absolute path to the generated JSON file.

    Raises:
        SubtaskGenerationError: If any step in the generation process fails.
        SchemaValidationError: If the generated JSON fails schema validation.
    """
    if not isinstance(input_step, dict) or 'step_id' not in input_step or 'description' not in input_step:
         raise SubtaskGenerationError("Invalid input_step format. Must be a dict with 'step_id' and 'description'.")

    step_id = input_step['step_id']

    try:
        # 1. Prepare Prompt (now uses stored context via self)
        prompt_content = self._prepare_prompt(input_step)

        # 2. Call AI Model
        ai_response_json = self.openrouter_client.call_chat_completion(
            prompt_text=prompt_content,
            model=self.openrouter_client.model,
            params=self.openrouter_client.params
        )

        if not ai_response_json:
            raise SubtaskGenerationError("Received empty response from AI.")

        # 3. Parse AI Response JSON
        try:
            # Extract JSON content from potential markdown code blocks
            json_string = ai_response_json

            # Create result_data with items to add
            result_data = {
                "items_to_add": {
                    "top_level": {
                        "subtask_id": str(uuid.uuid4()),  # Generate a unique subtask ID
                        "step_id": step_id  # Preserve the original step_id
                    },
                    "step_level": {}  # No step-level items for subtasks
                },
                "success": True,
                "steps": {},
                "logs": []
            }

            # Use the postprocessing pipeline (which will need to be updated for JSON)
            pipeline = PostprocessingPipeline(
                scripted_steps=[
                    clean_backtick_wrapper,  # These steps will need to be updated for JSON
                    escape_text_fields,
                    # Remove YAML-specific steps
                    # fix_yaml_structure,
                    # normalize_indentation,
                    validate_syntax,  # Update for JSON validation
                    handle_required_fields,
                    add_items_postprocessor
                ]
            )

            # Pass the JSON data through the postprocessing pipeline
            json_string, postprocessing_result = pipeline.process(json_string, result_data)

            # Log the postprocessing results
            logger.info("Postprocessing completed successfully.")
            logger.debug(f"Postprocessing result logs: {postprocessing_result.get('logs', [])}")

            # Parse the JSON content
            generated_data = json.loads(json_string)

            if not isinstance(generated_data, dict):
                 raise ValueError("Parsed JSON is not a dictionary.")

        except (json.JSONDecodeError, ValueError) as e:
            raise SubtaskGenerationError(f"Failed to parse AI response as JSON: {e}\nResponse:\n{ai_response_json}") from e

        # 4. Validate Schema
        try:
            # Define the schema path relative to the project root
            schema_path = Path("src/ai_whisperer/schemas/subtask_schema.json")
            validate_against_schema(generated_data, schema_path)
        except SchemaValidationError as e:
            # Re-raise schema validation errors specifically
            raise e
        except Exception as e:
            # Catch other potential validation errors
            raise SubtaskGenerationError(f"Error during schema validation: {e}") from e

        # 5. Save Output JSON
        output_dir_path = Path(self.output_dir)
        output_filename = f"subtask_{step_id}.json"  # Change extension to .json
        output_path = output_dir_path / output_filename

        try:
            # Ensure output directory exists
            output_dir_path.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                # Save using json
                json.dump(generated_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise SubtaskGenerationError(f"Failed to write output file {output_path}: {e}") from e

        logger.info(f"Generated subtask JSON at: {output_path}")
        return output_path.resolve()

    except OpenRouterAPIError as e:
        raise SubtaskGenerationError(f"AI interaction failed: {e}") from e
    except ConfigError as e:
         # Config errors during generation (e.g., missing keys accessed later)
         raise SubtaskGenerationError(f"Configuration error during generation: {e}") from e
    except SubtaskGenerationError as e:
         # Re-raise specific generation errors
         raise e
    except SchemaValidationError as e:
         # Re-raise specific schema errors
         raise e
    except Exception as e:
        # Catch any other unexpected errors during generation
        raise SubtaskGenerationError(f"An unexpected error occurred during subtask generation: {e}") from e
```

### 6. Update Exception Types

Update any YAML-specific exception types to JSON-specific ones:

- `YAMLValidationError` → `JSONValidationError` (if used)

### 7. Update Prompt Templates

Ensure that the subtask prompt template instructs the AI to generate JSON instead of YAML. This will require updating the prompt content in the configuration.

## Testing Strategy

1. Create unit tests for the new JSON methods
2. Update existing tests to use JSON instead of YAML
3. Create integration tests to verify the end-to-end process with JSON

## Breaking Changes

Since we're taking a direct approach without backward compatibility, the following breaking changes will occur:

1. All output files will be in JSON format with `.json` extension instead of YAML with `.yaml` extension
2. The `_sanitize_yaml_content` method will be replaced with `_sanitize_json_content`
3. The `_prepare_prompt` method will be updated to use JSON instead of YAML
4. The prompt templates will need to be updated to instruct the AI to generate JSON
5. The postprocessing pipeline will only handle JSON format

## Conclusion

Migrating the SubtaskGenerator from YAML to JSON will require significant changes to several methods, but the overall structure and logic will remain largely the same. By taking a direct approach without backward compatibility, we can implement these changes quickly and efficiently. The main challenges will be handling multi-line strings and ensuring proper JSON validation, but the simplified codebase without dual format support will be easier to maintain. The benefits of this migration include improved reliability, better error handling, and a more structured output format, which will significantly outweigh the short-term costs of the breaking changes.
