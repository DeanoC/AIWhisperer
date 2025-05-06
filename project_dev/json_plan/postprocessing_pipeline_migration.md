# Postprocessing Pipeline Migration Plan

## Introduction

This document outlines the changes needed to migrate the postprocessing pipeline and its scripted steps from YAML to JSON. The postprocessing pipeline is responsible for processing the output from the AI model, fixing common issues, and ensuring the output meets the required structure and validation criteria.

## Current Implementation

The postprocessing pipeline currently:

1. Processes YAML through a series of scripted steps
2. Handles YAML in both string and dictionary formats
3. Includes steps for fixing YAML structure, normalizing indentation, validating syntax, etc.
4. Has an AI improvements phase (currently a dummy identity transform)

Key components:

- `PostprocessingPipeline` class in `src/postprocessing/pipeline.py`
- Scripted steps in `src/postprocessing/scripted_steps/`:
  - `clean_backtick_wrapper.py`
  - `escape_text_fields.py`
  - `fix_yaml_structure.py`
  - `normalize_indentation.py`
  - `validate_syntax.py`
  - `handle_required_fields.py`
  - `add_items_postprocessor.py`
  - `identity_transform.py`

## Required Changes

### 1. Update the PostprocessingPipeline Class

The `PostprocessingPipeline` class needs to be updated to handle JSON instead of YAML:

```python
class PostprocessingPipeline:
    """
    A pipeline for processing JSON data through a series of scripted steps
    followed by an AI improvements phase.

    The pipeline takes a list of scripted step functions and executes them in order,
    passing the output of one step as the input to the next. After all scripted steps
    are complete, a dummy AI improvements phase is executed.

    Each scripted step function signature MUST be:
    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_json_content must be in the same format as the input (str | dict).
        tuple: (processed_json_content (str | dict), updated_result (dict))
    """
    # ... rest of the class implementation ...
```

The methods `_execute_scripted_phase`, `_execute_ai_phase`, and `process` need to be updated to handle JSON instead of YAML, but the changes are minimal since these methods already handle both string and dictionary formats.

### 2. Remove or Replace YAML-Specific Steps

Some steps are YAML-specific and need to be removed or replaced with JSON equivalents:

#### Remove:
- `fix_yaml_structure.py`: This step fixes YAML indentation and structure issues, which are not relevant for JSON.
- `normalize_indentation.py`: This step normalizes YAML indentation, which is not relevant for JSON.

#### Replace with JSON equivalents:
- `validate_syntax.py`: Update to validate JSON syntax instead of YAML syntax.

#### Update:
- `clean_backtick_wrapper.py`: Update to handle JSON code blocks.
- `escape_text_fields.py`: Update to handle JSON string escaping.
- `handle_required_fields.py`: Update to check for required fields in JSON.
- `add_items_postprocessor.py`: Update to add items to JSON.
- `identity_transform.py`: No changes needed as it's format-agnostic.

### 3. Create New JSON-Specific Steps

Create new steps for JSON-specific processing:

#### `format_json.py`:
```python
"""
Format JSON for Postprocessing

This module provides a function to format JSON data, ensuring it's properly
structured and indented.
"""

import json
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def format_json(json_content: str | dict, data: dict = None) -> Tuple[str | dict, Dict]:
    """
    Formats JSON data, ensuring it's properly structured and indented.

    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        tuple: A tuple containing:
            - processed_json_content (str | dict): The JSON content with proper formatting.
              Must be in the same format as the input.
            - updated_data (dict): The updated data dictionary with processing logs.
    """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # If json_content is a dictionary, format it by converting to string and back
    if isinstance(json_content, dict):
        try:
            json_string = json.dumps(json_content, indent=2)
            json_content = json.loads(json_string)
            data["logs"].append("Formatted JSON dictionary.")
        except Exception as e:
            data["logs"].append(f"Error formatting JSON dictionary: {e}")
        return json_content, data

    if not json_content.strip():
        data["logs"].append("No content to format.")
        return json_content, data

    # Log the original content for debugging
    logger.debug(f"Input to format_json:\n{json_content}")
    if "logs" in data:
        data["logs"].append(f"Original content starts with: {json_content[:50]}")

    # Format the JSON string
    try:
        # Parse the JSON string
        parsed_json = json.loads(json_content)

        # Format the JSON with proper indentation
        formatted_json = json.dumps(parsed_json, indent=2)

        data["logs"].append("Successfully formatted JSON.")
        return formatted_json, data
    except json.JSONDecodeError as e:
        data["logs"].append(f"JSON parsing error: {e}. Returning original content.")
        return json_content, data
    except Exception as e:
        data["logs"].append(f"Unexpected error: {e}. Returning original content.")
        return json_content, data
```

### 4. Update `validate_syntax.py`

Update the `validate_syntax.py` file to validate JSON syntax instead of YAML syntax:

```python
"""
Validate JSON Syntax for Postprocessing

This module provides a function to validate the syntax of JSON data,
ensuring it can be parsed correctly.
"""

import json
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def validate_syntax(json_content: str | dict, data: dict = None) -> Tuple[str | dict, Dict]:
    """
    Validates the syntax of JSON data, ensuring it can be parsed correctly.

    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        tuple: A tuple containing:
            - processed_json_content (str | dict): The JSON content with validated syntax.
              Must be in the same format as the input.
            - updated_data (dict): The updated data dictionary with processing logs.
    """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # If json_content is a dictionary, it's already parsed JSON, so return it as is
    if isinstance(json_content, dict):
        data["logs"].append("Input is a dictionary, no syntax validation needed.")
        return json_content, data

    if not json_content.strip():
        data["logs"].append("No content to validate syntax for.")
        return json_content, data

    # Log the original content for debugging
    logger.debug(f"Input to validate_syntax:\n{json_content}")
    if "logs" in data:
        data["logs"].append(f"Original content starts with: {json_content[:50]}")

    # Validate the JSON syntax
    try:
        # Parse the JSON string
        parsed_json = json.loads(json_content)

        # Convert back to string with proper formatting
        validated_json = json.dumps(parsed_json, indent=2)

        data["logs"].append("JSON syntax is valid.")
        return validated_json, data
    except json.JSONDecodeError as e:
        data["logs"].append(f"JSON syntax error: {e}. Returning original content.")
        return json_content, data
    except Exception as e:
        data["logs"].append(f"Unexpected error: {e}. Returning original content.")
        return json_content, data
```

### 5. Update `clean_backtick_wrapper.py`

Update the `clean_backtick_wrapper.py` file to handle JSON code blocks:

```python
"""
Clean Backtick Wrapper for Postprocessing

This module provides a function to clean JSON content that might be wrapped
in markdown code blocks with backticks.
"""

import re
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def clean_backtick_wrapper(json_content: str | dict, data: dict = None) -> Tuple[str | dict, Dict]:
    """
    Cleans JSON content that might be wrapped in markdown code blocks with backticks.

    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        tuple: A tuple containing:
            - processed_json_content (str | dict): The JSON content with backtick wrappers removed.
              Must be in the same format as the input.
            - updated_data (dict): The updated data dictionary with processing logs.
    """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # If json_content is a dictionary, it's already parsed JSON, so return it as is
    if isinstance(json_content, dict):
        data["logs"].append("Input is a dictionary, no backtick cleaning needed.")
        return json_content, data

    if not json_content.strip():
        data["logs"].append("No content to clean backticks for.")
        return json_content, data

    # Log the original content for debugging
    logger.debug(f"Input to clean_backtick_wrapper:\n{json_content}")
    if "logs" in data:
        data["logs"].append(f"Original content starts with: {json_content[:50]}")

    # Clean the backtick wrappers
    cleaned_content = json_content

    # Remove markdown code block markers for JSON
    if cleaned_content.startswith("```json"):
        cleaned_content = cleaned_content.replace("```json", "", 1)
        data["logs"].append("Removed starting ```json marker.")
    elif cleaned_content.startswith("```"):
        cleaned_content = cleaned_content.replace("```", "", 1)
        data["logs"].append("Removed starting ``` marker.")

    if cleaned_content.endswith("```"):
        cleaned_content = cleaned_content.rsplit("```", 1)[0]
        data["logs"].append("Removed ending ``` marker.")

    # Trim whitespace
    cleaned_content = cleaned_content.strip()

    # Log the changes
    logger.debug(f"Output from clean_backtick_wrapper:\n{cleaned_content}")
    if "logs" in data:
        data["logs"].append(f"Cleaned content starts with: {cleaned_content[:50]}")

    return cleaned_content, data
```

### 6. Update `escape_text_fields.py`

Update the `escape_text_fields.py` file to handle JSON string escaping:

```python
"""
Escape Text Fields for Postprocessing

This module provides a function to ensure text fields in JSON data
are properly escaped.
"""

import json
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def escape_text_fields(json_content: str | dict, data: dict = None) -> Tuple[str | dict, Dict]:
    """
    Ensures text fields in JSON data are properly escaped.

    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        tuple: A tuple containing:
            - processed_json_content (str | dict): The JSON content with properly escaped text fields.
              Must be in the same format as the input.
            - updated_data (dict): The updated data dictionary with processing logs.
    """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # If json_content is a dictionary, process it directly
    if isinstance(json_content, dict):
        # Process the dictionary recursively
        try:
            # Convert to JSON string and back to ensure proper escaping
            json_string = json.dumps(json_content)
            processed_dict = json.loads(json_string)
            data["logs"].append("Processed dictionary to ensure proper escaping.")
            return processed_dict, data
        except Exception as e:
            data["logs"].append(f"Error processing dictionary: {e}")
            return json_content, data

    if not json_content.strip():
        data["logs"].append("No content to escape text fields for.")
        return json_content, data

    # Log the original content for debugging
    logger.debug(f"Input to escape_text_fields:\n{json_content}")
    if "logs" in data:
        data["logs"].append(f"Original content starts with: {json_content[:50]}")

    # Escape the text fields
    try:
        # Parse the JSON string
        parsed_json = json.loads(json_content)

        # Convert back to string with proper escaping
        escaped_json = json.dumps(parsed_json, ensure_ascii=False)

        data["logs"].append("Text fields properly escaped.")
        return escaped_json, data
    except json.JSONDecodeError as e:
        data["logs"].append(f"JSON parsing error: {e}. Returning original content.")
        return json_content, data
    except Exception as e:
        data["logs"].append(f"Unexpected error: {e}. Returning original content.")
        return json_content, data
```

### 7. Update `handle_required_fields.py`

Update the `handle_required_fields.py` file to check for required fields in JSON:

```python
"""
Handle Required Fields for Postprocessing

This module provides a function to ensure required fields are present in JSON data.
"""

import json
from typing import Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

def handle_required_fields(json_content: str | dict, data: dict = None) -> Tuple[str | dict, Dict]:
    """
    Ensures required fields are present in JSON data.

    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        tuple: A tuple containing:
            - processed_json_content (str | dict): The JSON content with required fields added if missing.
              Must be in the same format as the input.
            - updated_data (dict): The updated data dictionary with processing logs.
    """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # Define required fields for different types of JSON
    task_required_fields = ["natural_language_goal", "plan"]
    step_required_fields = ["step_id", "description", "agent_spec"]
    agent_spec_required_fields = ["type", "input_artifacts", "output_artifacts", "instructions"]
    subtask_required_fields = ["subtask_id", "step_id", "agent_spec"]

    # Process dictionary directly if json_content is a dictionary
    if isinstance(json_content, dict):
        json_dict = json_content
    else:
        # Parse the JSON string
        try:
            json_dict = json.loads(json_content)
        except json.JSONDecodeError as e:
            data["logs"].append(f"JSON parsing error: {e}. Returning original content.")
            return json_content, data

    # Check and add required fields
    modified = False

    # Check if this is a task JSON
    if "natural_language_goal" in json_dict or "plan" in json_dict:
        for field in task_required_fields:
            if field not in json_dict:
                json_dict[field] = get_default_value(field)
                data["logs"].append(f"Added missing required field: {field}")
                modified = True

        # Check plan steps
        if "plan" in json_dict and isinstance(json_dict["plan"], list):
            for i, step in enumerate(json_dict["plan"]):
                if isinstance(step, dict):
                    for field in step_required_fields:
                        if field not in step:
                            step[field] = get_default_value(field)
                            data["logs"].append(f"Added missing required field in step {i}: {field}")
                            modified = True

                    # Check agent_spec
                    if "agent_spec" in step and isinstance(step["agent_spec"], dict):
                        agent_spec = step["agent_spec"]
                        for field in agent_spec_required_fields:
                            if field not in agent_spec:
                                agent_spec[field] = get_default_value(field)
                                data["logs"].append(f"Added missing required field in step {i} agent_spec: {field}")
                                modified = True

    # Check if this is a subtask JSON
    elif "subtask_id" in json_dict or "step_id" in json_dict:
        for field in subtask_required_fields:
            if field not in json_dict:
                json_dict[field] = get_default_value(field)
                data["logs"].append(f"Added missing required field: {field}")
                modified = True

        # Check agent_spec
        if "agent_spec" in json_dict and isinstance(json_dict["agent_spec"], dict):
            agent_spec = json_dict["agent_spec"]
            for field in agent_spec_required_fields:
                if field not in agent_spec:
                    agent_spec[field] = get_default_value(field)
                    data["logs"].append(f"Added missing required field in agent_spec: {field}")
                    modified = True

    # Return the result in the same format as the input
    if isinstance(json_content, dict):
        return json_dict, data
    else:
        return json.dumps(json_dict, indent=2), data

def get_default_value(field: str) -> Any:
    """
    Returns a default value for a given field.

    Args:
        field: The name of the field.

    Returns:
        A default value appropriate for the field.
    """
    if field == "natural_language_goal":
        return "Default goal"
    elif field == "plan":
        return []
    elif field == "step_id":
        return f"step_{hash(field) % 1000}"
    elif field == "description":
        return "Default description"
    elif field == "agent_spec":
        return {
            "type": "default",
            "input_artifacts": [],
            "output_artifacts": [],
            "instructions": "Default instructions"
        }
    elif field == "type":
        return "default"
    elif field == "input_artifacts":
        return []
    elif field == "output_artifacts":
        return []
    elif field == "instructions":
        return "Default instructions"
    elif field == "subtask_id":
        return f"subtask_{hash(field) % 1000}"
    else:
        return None
```

### 8. Update `add_items_postprocessor.py`

Update the `add_items_postprocessor.py` file to add items to JSON:

```python
"""
Add Items Postprocessor for JSON

This module provides a function to add items to JSON data based on the
items_to_add field in the data dictionary.
"""

import json
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def add_items_postprocessor(json_content: str | dict, data: dict = None) -> Tuple[str | dict, Dict]:
    """
    Adds items to JSON data based on the items_to_add field in the data dictionary.

    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        tuple: A tuple containing:
            - processed_json_content (str | dict): The JSON content with items added.
              Must be in the same format as the input.
            - updated_data (dict): The updated data dictionary with processing logs.
    """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # Check if there are items to add
    if "items_to_add" not in data:
        data["logs"].append("No items_to_add field in data dictionary.")
        return json_content, data

    # Process dictionary directly if json_content is a dictionary
    if isinstance(json_content, dict):
        json_dict = json_content
    else:
        # Parse the JSON string
        try:
            json_dict = json.loads(json_content)
        except json.JSONDecodeError as e:
            data["logs"].append(f"JSON parsing error: {e}. Returning original content.")
            return json_content, data

    # Add top-level items
    if "top_level" in data["items_to_add"]:
        for key, value in data["items_to_add"]["top_level"].items():
            json_dict[key] = value
            data["logs"].append(f"Added top-level item: {key}")

    # Add step-level items
    if "step_level" in data["items_to_add"] and "plan" in json_dict and isinstance(json_dict["plan"], list):
        for step in json_dict["plan"]:
            if isinstance(step, dict) and "step_id" in step:
                step_id = step["step_id"]
                if step_id in data["items_to_add"]["step_level"]:
                    for key, value in data["items_to_add"]["step_level"][step_id].items():
                        step[key] = value
                        data["logs"].append(f"Added step-level item to step {step_id}: {key}")

    # Return the result in the same format as the input
    if isinstance(json_content, dict):
        return json_dict, data
    else:
        return json.dumps(json_dict, indent=2), data
```

### 9. Update the Pipeline Configuration

Update the pipeline configuration in the Orchestrator and SubtaskGenerator to use the new JSON-specific steps:

```python
# In orchestrator.py and subtask_generator.py
pipeline = PostprocessingPipeline(
    scripted_steps=[
        clean_backtick_wrapper,
        escape_text_fields,
        format_json,  # New step
        validate_syntax,
        handle_required_fields,
        add_items_postprocessor
    ]
)
```

## Testing Strategy

1. Create unit tests for the new JSON-specific steps
2. Update existing tests to use JSON instead of YAML
3. Create integration tests to verify the end-to-end process with JSON

## Breaking Changes

Since we're taking a direct approach without backward compatibility, the following breaking changes will occur:

1. YAML-specific steps (`fix_yaml_structure.py` and `normalize_indentation.py`) will be removed
2. All steps will be updated to handle JSON only
3. A new `format_json.py` step will be added to the pipeline
4. The pipeline configuration will be updated to use JSON-specific steps only
5. Code that expects YAML output from the pipeline will need to be updated

## Conclusion

Migrating the postprocessing pipeline from YAML to JSON will require significant changes to several steps, but the overall structure and logic will remain largely the same. By taking a direct approach without backward compatibility, we can implement these changes quickly and efficiently. The main challenges will be handling JSON-specific formatting and validation, but the simplified codebase without dual format support will be easier to maintain. The benefits of this migration include improved reliability, better error handling, and a more structured output format, which will significantly outweigh the short-term costs of the breaking changes.
