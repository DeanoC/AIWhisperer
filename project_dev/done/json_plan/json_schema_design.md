# JSON Schema Design

## Introduction

This document outlines the proposed JSON schema design to replace the current YAML structure in the AI Whisperer project. The goal is to create a more structured and predictable format that addresses the issues with the current YAML implementation.

## Current YAML Structure

The current YAML structure for task plans looks like this:

```yaml
natural_language_goal: Enhance the `--list-models` command to provide detailed model information and optionally export it to a CSV file.
overall_context: |
  The goal is to improve the user experience when listing available models using the `ai-whisperer` CLI by providing richer information and an export option.
plan:
  - step_id: plan_implementation
    description: Analyze the requirements and plan the necessary code modifications in main.py and the OpenRouter API module.
    depends_on: []
    agent_spec:
      type: planning
      input_artifacts:
        - main.py
        - ai_whisperer/openrouter_api.py
      output_artifacts:
        - docs/list_models_enhancement_plan.md
      instructions: |
        Analyze the feature request for enhancing the `--list-models` command.
        Identify the specific changes needed in `main.py` to handle the new `--output-csv` argument and integrate with the enhanced API call.
      validation_criteria:
        - docs/list_models_enhancement_plan.md exists.
        - docs/list_models_enhancement_plan.md outlines changes to main.py for argument parsing.
```

And for subtasks:

```yaml
subtask_id: 123e4567-e89b-12d3-a456-426614174000
step_id: plan_implementation
agent_spec:
  type: planning
  input_artifacts:
    - main.py
    - ai_whisperer/openrouter_api.py
  output_artifacts:
    - docs/list_models_enhancement_plan.md
  instructions: |
    Analyze the feature request for enhancing the `--list-models` command.
    Identify the specific changes needed in `main.py` to handle the new `--output-csv` argument.
  validation_criteria:
    - docs/list_models_enhancement_plan.md exists.
    - docs/list_models_enhancement_plan.md outlines changes to main.py for argument parsing.
```

## Proposed JSON Structure

The proposed JSON structure for task plans:

```json
{
  "natural_language_goal": "Enhance the `--list-models` command to provide detailed model information and optionally export it to a CSV file.",
  "overall_context": "The goal is to improve the user experience when listing available models using the `ai-whisperer` CLI by providing richer information and an export option.",
  "plan": [
    {
      "step_id": "plan_implementation",
      "description": "Analyze the requirements and plan the necessary code modifications in main.py and the OpenRouter API module.",
      "depends_on": [],
      "agent_spec": {
        "type": "planning",
        "input_artifacts": [
          "main.py",
          "ai_whisperer/openrouter_api.py"
        ],
        "output_artifacts": [
          "docs/list_models_enhancement_plan.md"
        ],
        "instructions": "Analyze the feature request for enhancing the `--list-models` command.\nIdentify the specific changes needed in `main.py` to handle the new `--output-csv` argument and integrate with the enhanced API call.",
        "validation_criteria": [
          "docs/list_models_enhancement_plan.md exists.",
          "docs/list_models_enhancement_plan.md outlines changes to main.py for argument parsing."
        ]
      }
    }
  ],
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "input_hashes": {
    "requirements_md": "abc123",
    "config_yaml": "def456",
    "prompt_file": "ghi789"
  }
}
```

And for subtasks:

```json
{
  "subtask_id": "123e4567-e89b-12d3-a456-426614174000",
  "step_id": "plan_implementation",
  "agent_spec": {
    "type": "planning",
    "input_artifacts": [
      "main.py",
      "ai_whisperer/openrouter_api.py"
    ],
    "output_artifacts": [
      "docs/list_models_enhancement_plan.md"
    ],
    "instructions": "Analyze the feature request for enhancing the `--list-models` command.\nIdentify the specific changes needed in `main.py` to handle the new `--output-csv` argument.",
    "validation_criteria": [
      "docs/list_models_enhancement_plan.md exists.",
      "docs/list_models_enhancement_plan.md outlines changes to main.py for argument parsing."
    ]
  }
}
```

## Key Differences and Advantages

1. **Strict Structure**: JSON enforces a stricter structure than YAML, making it less prone to indentation and parsing errors.

2. **Multi-line Strings**: In JSON, multi-line strings are represented with newline characters (`\n`) rather than YAML's block scalar styles (`|` or `>`), which are often a source of parsing issues.

3. **No Indentation Sensitivity**: JSON doesn't rely on indentation for structure, eliminating a major source of errors in YAML.

4. **Better Library Support**: JSON parsing is more standardized across programming languages and has robust library support.

5. **Easier Validation**: JSON Schema validation is more widely supported and easier to implement than YAML validation.

6. **Consistent Quoting**: JSON has consistent rules for quoting strings, avoiding the confusion with YAML's various quoting styles.

## JSON Schema Definition

Here's a proposed JSON Schema for the task plan structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["natural_language_goal", "plan", "task_id"],
  "properties": {
    "natural_language_goal": {
      "type": "string",
      "description": "A natural language description of the goal of the task"
    },
    "overall_context": {
      "type": "string",
      "description": "Additional context for the task"
    },
    "plan": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["step_id", "description", "agent_spec"],
        "properties": {
          "step_id": {
            "type": "string",
            "description": "A unique identifier for the step"
          },
          "description": {
            "type": "string",
            "description": "A description of the step"
          },
          "depends_on": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "A list of step_ids that this step depends on"
          },
          "agent_spec": {
            "type": "object",
            "required": ["type", "input_artifacts", "output_artifacts", "instructions"],
            "properties": {
              "type": {
                "type": "string",
                "description": "The type of agent to use for this step"
              },
              "input_artifacts": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "A list of input artifacts for this step"
              },
              "output_artifacts": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "A list of output artifacts for this step"
              },
              "instructions": {
                "type": "string",
                "description": "Instructions for the agent"
              },
              "validation_criteria": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "A list of validation criteria for this step"
              }
            }
          }
        }
      }
    },
    "task_id": {
      "type": "string",
      "description": "A unique identifier for the task"
    },
    "input_hashes": {
      "type": "object",
      "description": "Hashes of input files"
    }
  }
}
```

And for subtasks:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["subtask_id", "step_id", "agent_spec"],
  "properties": {
    "subtask_id": {
      "type": "string",
      "description": "A unique identifier for the subtask"
    },
    "step_id": {
      "type": "string",
      "description": "The step_id this subtask is associated with"
    },
    "agent_spec": {
      "type": "object",
      "required": ["type", "input_artifacts", "output_artifacts", "instructions"],
      "properties": {
        "type": {
          "type": "string",
          "description": "The type of agent to use for this subtask"
        },
        "input_artifacts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "A list of input artifacts for this subtask"
        },
        "output_artifacts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "A list of output artifacts for this subtask"
        },
        "instructions": {
          "type": "string",
          "description": "Instructions for the agent"
        },
        "validation_criteria": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "A list of validation criteria for this subtask"
        }
      }
    }
  }
}
```

## Handling Multi-line Strings

One of the challenges in migrating from YAML to JSON is handling multi-line strings. In YAML, multi-line strings are often represented using block scalar styles (`|` or `>`), which preserve line breaks. In JSON, multi-line strings must use escape sequences (`\n`) for line breaks.

To handle this, we'll need to:

1. Modify the AI prompts to generate properly escaped JSON strings
2. Update the postprocessing pipeline to handle JSON string escaping
3. Ensure that any code that reads the JSON properly handles the escaped newlines

## Conclusion

The proposed JSON schema provides a more structured and predictable format for the AI Whisperer project. It addresses the issues with the current YAML implementation while maintaining the same semantic structure. The migration to JSON will require changes to several components of the project, but the benefits in terms of reliability and maintainability will be significant.