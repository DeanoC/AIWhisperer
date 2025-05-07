# Orchestrator Migration Plan

## Introduction

This document outlines the changes needed to migrate the `orchestrator.py` file from YAML to JSON. The Orchestrator class is responsible for generating the initial task plan and coordinating the generation of subtasks, making it a critical component in the migration process.

## Current Implementation

The Orchestrator class currently:

1. Generates initial YAML task plans from requirements
2. Uses both standard `yaml` and `ruamel.yaml` libraries
3. Has methods for sanitizing YAML text fields
4. Saves YAML content to files
5. Uses a complex postprocessing pipeline for YAML content

Key methods that handle YAML:

- `generate_initial_yaml`: Generates the initial task plan YAML
- `save_yaml`: Saves YAML content to a file
- `_sanitize_yaml_text_fields`: Sanitizes string fields in YAML data
- `generate_full_project_plan`: Generates a complete project plan including initial task YAML and all subtasks

## Required Changes

### 1. Rename Methods and Variables

Update method and variable names to reflect the switch from YAML to JSON:

- `generate_initial_yaml` → `generate_initial_json`
- `save_yaml` → `save_json`
- `_sanitize_yaml_text_fields` → `_sanitize_json_text_fields`
- Update variable names like `yaml_content` → `json_content`, `yaml_string` → `json_string`, etc.

### 2. Update Import Statements

Replace YAML imports with JSON imports:

```python
# Remove or comment out
import yaml
from ruamel.yaml import YAML

# Keep or add
import json
```

### 3. Modify `_sanitize_yaml_text_fields` Method

The current method sanitizes YAML text fields that might contain special YAML characters. For JSON, we need to ensure proper escaping of special characters, particularly newlines in multi-line strings:

```python
def _sanitize_json_text_fields(self, json_data):
    """
    Sanitizes string fields in JSON data that might contain special characters.
    Focuses on specific text fields that commonly contain natural language.

    Args:
        json_data: The parsed JSON dictionary.

    Returns:
        The sanitized JSON dictionary.
    """
    if not isinstance(json_data, dict):
        return json_data

    # Fields that commonly contain natural language
    text_fields = ["natural_language_goal", "overall_context"]

    for field in text_fields:
        if field in json_data and isinstance(json_data[field], str):
            # No special handling needed for JSON strings, they're already properly escaped
            pass

    # Process any nested dictionaries in the plan
    if "plan" in json_data and isinstance(json_data["plan"], list):
        for step in json_data["plan"]:
            if isinstance(step, dict):
                # Handle instructions field
                if "agent_spec" in step and isinstance(step["agent_spec"], dict):
                    agent_spec = step["agent_spec"]
                    if "instructions" in agent_spec and isinstance(agent_spec["instructions"], str):
                        # No special handling needed for JSON strings
                        pass

    return json_data
```

### 4. Update `save_yaml` Method

Replace the YAML saving logic with JSON saving:

```python
def save_json(self, json_content, output_filename):
    """
    Saves the JSON content to a file in the specified output directory.

    Args:
        json_content: The JSON content to save.
        output_filename: The name of the output file.

    Returns:
        The path to the saved file.
    """
    # Ensure the output directory exists
    os.makedirs(self.output_dir, exist_ok=True)

    # Construct the file path using self.output_dir
    output_path = os.path.join(self.output_dir, output_filename)

    # Save the file using json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully saved initial orchestrator JSON to {output_path}")
    return output_path
```

### 5. Update `generate_initial_yaml` Method

Rename to `generate_initial_json` and update the YAML-specific code:

```python
def generate_initial_json(self, requirements_md_path_str: str, config_path_str: str) -> Path:
    """
    Generates the initial task plan JSON file based on input requirements markdown.

    This method orchestrates the end-to-end process:
    1. Loads the prompt template
    2. Calculates SHA-256 hashes of input files
    3. Reads the requirements markdown content
    4. Constructs a prompt with markdown content and input hashes
    5. Calls the OpenRouter API
    6. Parses and validates the JSON response (checks hashes and schema)
    7. Saves the validated JSON to the output directory

    Args:
        requirements_md_path_str: Path string to the input requirements markdown file.
        config_path_str: Path string to the configuration file used.

    Returns:
        The Path object of the generated JSON file.

    Raises:
        Various exceptions for different error conditions.
    """
    # ... [existing code for loading prompt, calculating hashes, etc.] ...

    # Update the API response handling
    try:
        # Extract JSON content from potential markdown code blocks
        json_string = api_response_content

        # Create result_data with items to add
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": str(uuid.uuid4()),  # Generate a unique task ID
                    "input_hashes": input_hashes,
                }
            },
            "success": True,
            "steps": {},
            "logs": [],
        }

        # Save JSON string to temp file for debugging
        logger.debug("Saving JSON string to temporary file for debugging")
        try:
            with open("./temp.txt", "w", encoding="utf-8") as f:
                f.write(json_string)
            logger.debug("Successfully saved JSON string to ./temp.txt")
        except IOError as e:
            logger.warning(f"Failed to save debug JSON file: {e}")

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
        json_string, postprocessing_result = pipeline.process(
            json_string, result_data
        )

        print(f"JSON string after postprocessing:\n{json_string}")

        # Parse the JSON content
        json_data = json.loads(json_string)

        if not isinstance(json_data, dict):
            logger.error(
                f"Parsed JSON is not a dictionary. Type: {type(json_data).__name__}"
            )
            raise OrchestratorError(
                f"API response did not yield a valid JSON dictionary. Content: {api_response_content[:200]}..."
            )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(
            f"Response content that failed parsing:\n{api_response_content}"
        )
        raise OrchestratorError(f"Invalid JSON received from API: {e}") from e
    except Exception as e:
        logger.error(f"An error occurred during JSON postprocessing: {e}")
        raise OrchestratorError(f"JSON postprocessing failed: {e}") from e

    # Create output filename based on the input requirements file
    config_stem = config_path.stem
    output_filename = f"{requirements_md_path.stem}_{config_stem}.json"  # Change extension to .json

    # Save the JSON
    try:
        output_path = self.save_json(json_data, output_filename)
        return output_path
    except IOError as e:
        logger.error(f"Error writing output JSON file {output_filename}: {e}")
        raise ProcessingError(
            f"Error writing output JSON file {output_filename}: {e}"
        ) from e
```

### 6. Update `generate_full_project_plan` Method

Update to use the new JSON methods and handle JSON files:

```python
def generate_full_project_plan(self, requirements_md_path_str: str, config_path_str: str) -> Dict[str, Any]:
    """
    Generates a complete project plan including initial task JSON and all subtasks.

    This method:
    1. First generates the initial task plan JSON
    2. For each step in the task plan, generates a detailed subtask JSON
    3. Returns paths to all generated files

    Args:
        requirements_md_path_str: Path string to the input requirements markdown file.
        config_path_str: Path string to the configuration file used.

    Returns:
        Dict with task_plan (Path) and subtasks (list of Paths)

    Raises:
        Various exceptions for different error conditions.
    """
    logger.info("Starting full project plan generation")

    # First generate the initial task plan
    task_plan_path = self.generate_initial_json(
        requirements_md_path_str, config_path_str
    )
    logger.info(f"Initial task plan generated: {task_plan_path}")

    # Load the generated task plan to extract steps
    try:
        with open(task_plan_path, "r", encoding="utf-8") as f:
            task_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read generated task plan: {e}")
        raise OrchestratorError(f"Failed to read generated task plan: {e}") from e

    # Initialize subtask generator
    from .subtask_generator import SubtaskGenerator

    # Extract overall_context from the loaded task data
    overall_context = task_data.get(
        "overall_context", ""
    )
    workspace_context = ""  # Placeholder for now
    subtask_generator = SubtaskGenerator(
        config_path=config_path_str,
        overall_context=overall_context,
        workspace_context=workspace_context,
        output_dir=self.output_dir,
    )
    logger.info("Initialized subtask generator with overall context.")

    # Generate subtask for each step
    subtask_paths = []
    if "plan" in task_data and isinstance(
        task_data["plan"], list
    ):
        steps_count = len(task_data["plan"])
        logger.info(f"Generating subtasks for {steps_count} steps")

        for i, step in enumerate(task_data["plan"], 1):
            try:
                step_id = step.get("step_id", f"step_{i}")
                logger.info(f"Generating subtask {i}/{steps_count}: {step_id}")
                subtask_path = subtask_generator.generate_subtask(step)
                subtask_paths.append(subtask_path)
                logger.info(f"Generated subtask: {subtask_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to generate subtask for step {step.get('step_id', i)}: {e}"
                )
                # Continue with other steps instead of failing completely
    else:
        logger.warning("No steps found in task plan, no subtasks will be generated")

    result = {"task_plan": task_plan_path, "subtasks": subtask_paths}

    logger.info(
        f"Full project plan generation completed with {len(subtask_paths)} subtasks"
    )
    return result
```

### 7. Update Exception Types

Update any YAML-specific exception types to JSON-specific ones:

- `YAMLValidationError` → `JSONValidationError`

### 8. Update Prompt Templates

Ensure that the prompt templates instruct the AI to generate JSON instead of YAML. This will require updating the prompt files referenced by the Orchestrator.

## Testing Strategy

1. Create unit tests for the new JSON methods
2. Update existing tests to use JSON instead of YAML
3. Create integration tests to verify the end-to-end process with JSON

## Breaking Changes

Since we're taking a direct approach without backward compatibility, the following breaking changes will occur:

1. All output files will be in JSON format with `.json` extension instead of YAML with `.yaml` extension
2. Code that expects YAML output will need to be updated to handle JSON
3. The `generate_initial_yaml` method will be replaced with `generate_initial_json`
4. The `save_yaml` method will be replaced with `save_json`
5. The postprocessing pipeline will only handle JSON format

## Conclusion

Migrating the Orchestrator from YAML to JSON will require significant changes to several methods, but the overall structure and logic will remain largely the same. By taking a direct approach without backward compatibility, we can implement these changes quickly and efficiently. The main challenges will be handling multi-line strings and ensuring proper JSON validation, but the simplified codebase without dual format support will be easier to maintain. The benefits of this migration include improved reliability, better error handling, and a more structured output format, which will significantly outweigh the short-term costs of the breaking changes.
