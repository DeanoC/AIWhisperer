# YAML Postprocessing Design

This document outlines the design for the YAML postprocessing module, which aims to enhance the reliability and format adherence of AI-generated YAML task files.

## Overview

The postprocessing pipeline consists of two sequential phases:

1. **Scripted Phase**: A deterministic series of steps that apply transformations to fix common YAML issues and enforce format conventions
2. **AI Improvements Phase**: An AI-based enhancement step that can make higher-level improvements to the YAML structure and content

## Detailed Design

### 1. Two-Phase Architecture

The postprocessing pipeline executes in the following order:

``` mermaid
[Input YAML] → [Scripted Phase] → [AI Improvements Phase] → [Final YAML Output]
```

#### Scripted Phase

This phase focuses on rule-based corrections that can be programmatically defined, such as:

- Format standardization
- Type conversion
- Schema validation
- Structural fixing
- Adding required items (new functionality)

#### AI Improvements Phase

This phase (initially implemented as a dummy transform) will eventually apply more nuanced improvements that require AI reasoning, such as:

- Content enhancement
- Field completion
- Logic validation
- Structure optimization

### 2. Scripted Phase Chaining Mechanism

The scripted phase implements a chain-of-responsibility pattern where:

1. Each step is a discrete function that performs a specific transformation
2. Steps are executed sequentially in a predefined order
3. The output of one step becomes the input to the next step
4. A processing status/result object is passed between steps to accumulate information

``` mermaid
[Step 1] → [Step 2] → [Step 3] → ... → [Step N]
```

#### Step Execution Flow

1. The pipeline starts with the input YAML and an empty result object
2. For each step in the chain:
   - Call the step function with the current YAML and result object
   - The step processes the YAML and updates the result object
   - The modified YAML and result object are returned
   - These become the inputs for the next step
3. After all scripted steps are processed, the final YAML and result object are passed to the AI improvements phase

### 3. Step Input/Output Structure

Each scripted step follows a consistent interface:

#### Input

- `yaml_data`: The YAML data object to be processed (dict or other parsed YAML structure)
- `result`: A dictionary containing processing status, logs, and other metadata

#### Output

- `yaml_data`: The processed YAML data object
- `result`: The updated result dictionary with additional information about this step

#### Result Object Structure

```python
{
    "success": bool,  # Overall success status
    "steps": {
        "step_name": {
            "success": bool,  # Step-specific success status
            "changes": list,  # List of changes made by the step
            "errors": list,   # List of errors encountered
            "warnings": list  # List of warnings
        }
    },
    "logs": list,  # General processing logs
    "items_to_add": {  # New field for the add_items_postprocessor
        "top_level": {  # Items to add at the top level of the YAML
            "task_id": "abc-123",
            "input_hashes": {"file1": "hash1", "file2": "hash2"}
        },
        "step_level": {  # Items to add to each step/subtask
            "subtask_id": "xyz-789"
        }
    }
}
```

### 4. AI Improvements Phase (Initial Implementation)

In the initial implementation, the AI improvements phase will be a dummy identity transform:

1. It will receive the YAML data and result object from the scripted phase
2. It will return them unchanged, effectively passing through the data
3. The implementation will maintain the interface required for future AI-based improvements

This placeholder structure allows for future integration of AI capabilities without disrupting the current pipeline.

### 5. Extensibility and Modularity

The design emphasizes modularity and extensibility:

#### Adding New Scripted Steps

1. Create a new Python module in `src/postprocessing/scripted_steps/`
2. Implement the standard step interface (accepting and returning `yaml_data` and `result`)
3. Add the step to the configuration or step list in the pipeline

#### Enabling the AI Improvements Phase

1. The dummy implementation will be replaced with an actual AI implementation
2. No changes will be required to the pipeline structure or interfaces

#### Configuration Options

1. Enable/disable individual scripted steps
2. Enable/disable the AI improvements phase
3. Configure parameters for specific steps
4. Define the order of scripted steps

## Implementation Considerations

1. **Error Handling**: Each step should handle exceptions gracefully and update the result object with error information
2. **Logging**: The pipeline should provide detailed logging of each transformation
3. **Testing**: Each scripted step should be independently testable
4. **Performance**: Consider the efficiency of YAML parsing/serialization between steps

## Initial Implementation Steps

1. Implement the basic pipeline structure with support for chaining scripted steps
2. Create a simple identity transform as the first scripted step
3. Implement the dummy AI improvements phase
4. Build tests to verify the pipeline correctness

## New Postprocessing Step: Add Items to AI Output

### `add_items_postprocessor` Function

We will implement a new scripted step function that can be added to the `PostprocessingPipeline`:

```python
def add_items_postprocessor(yaml_string: str, result_data: Dict) -> Tuple[str, Dict]:
    """
    Adds specified items to the YAML string at designated positions.
    
    Args:
        yaml_string: The YAML string to process
        result_data: Dictionary containing processing results and metadata
        
    Returns:
        Tuple containing:
        - The modified YAML string with items added
        - The updated result_data dictionary
    """
```

### Input Parameters

The function will receive items to add through a configuration dictionary passed in the `result_data` parameter:

```python
result_data = {
    # ... existing fields ...
    'items_to_add': {
        'top_level': {  # Items to add at the top level of the YAML
            'task_id': 'abc-123',
            'input_hashes': {'file1': 'hash1', 'file2': 'hash2'}
        },
        'step_level': {  # Items to add to each step/subtask
            'subtask_id': 'xyz-789'
        }
    }
}
```

### Insertion Logic

The postprocessor will:

1. Parse the input YAML string into a Python dictionary
2. Add the specified items at their designated locations:
   - Top-level items will be added to the root of the YAML structure
   - Step-level items will be added to each step/subtask in the YAML
3. Convert the modified dictionary back to a YAML string
4. Return the modified string and updated result_data

### Error Handling

The postprocessor will handle the following error cases:

1. Invalid YAML input (cannot be parsed)
2. Missing expected structure in the YAML (e.g., no 'plan' section for step-level items)
3. Conflicts between existing keys and items to add

Errors will be logged and added to the `result_data['logs']` list, following the pattern of existing postprocessors.

### Integration with Pipeline

The new postprocessor will be added to the `PostprocessingPipeline` as a scripted step:

```python
pipeline = PostprocessingPipeline(
    scripted_steps=[
        clean_backtick_wrapper,
        add_items_postprocessor,
        # other steps...
    ]
)
```

### Configuration

The items to add will be configured by the calling code (Orchestrator or SubtaskGenerator) before invoking the pipeline:

```python
# Example in Orchestrator
result_data = {
    'items_to_add': {
        'top_level': {
            'task_id': task_id,
            'input_hashes': input_hashes
        }
    }
}
yaml_string, result = pipeline.process(yaml_string, result_data)

# Example in SubtaskGenerator
result_data = {
    'items_to_add': {
        'top_level': {
            'subtask_id': subtask_id
        }
    }
}
yaml_string, result = pipeline.process(yaml_string, result_data)
```
