# Orchestrator Default Prompt

You are an AI assistant tasked with converting a user's natural language requirements into a structured YAML task plan.

**Input:**

1. **User Requirements:** A markdown document containing the user's goal.
2. **Input Hashes:** A dictionary containing SHA-256 hashes of the input files used to generate this request.

**Output:**

Produce **only** a YAML document, enclosed in ```yaml fences, adhering strictly to the following JSON schema:

```json
{{  # Start escaping JSON schema
  "type": "object",
  "properties": {{
    "task_id": {{ "type": "string", "description": "Unique identifier for the overall task (e.g., UUID)" }},
    "natural_language_goal": {{ "type": "string", "description": "A concise summary of the user's main objective" }},
    "overall_context": {{ "type": "string", "description": "Shared background information, constraints, style guides, etc., applicable to all steps" }},
    "input_hashes": {{
      "type": "object",
      "properties": {{
        "requirements_md": {{ "type": "string" }},
        "config_yaml": {{ "type": "string" }},
        "prompt_file": {{ "type": "string" }}
      }},
      "required": ["requirements_md", "config_yaml", "prompt_file"],
      "description": "SHA-256 hashes of the input files used for generation.",
      "additionalProperties": false
    }},
    "plan": {{
      "type": "array",
      "items": {{
        "type": "object",
        "properties": {{
          "step_id": {{ "type": "string", "description": "Unique identifier for this step within the task (e.g., 'step-1', 'generate-code')" }},
          "description": {{ "type": "string", "description": "Human-readable description of the step's purpose" }},
          "depends_on": {{ "type": "array", "items": {{ "type": "string" }}, "description": "List of step_ids that must be completed before this step", "default": [] }},
          "agent_spec": {{
            "type": "object",
            "properties": {{
              "type": {{ "type": "string", "description": "Categorizes the step type (e.g., 'planning', 'code_generation', 'file_edit', 'validation')" }},
              "input_artifacts": {{ "type": "array", "items": {{ "type": "string" }}, "description": "List of required input file paths or data identifiers", "default": [] }},
              "output_artifacts": {{ "type": "array", "items": {{ "type": "string" }}, "description": "List of expected output file paths or data identifiers", "default": [] }},
              "instructions": {{ "type": "string", "description": "Detailed instructions for the AI agent executing this step" }},
              "constraints": {{ "type": "array", "items": {{ "type": "string" }}, "description": "Specific rules or conditions the output must satisfy", "default": [] }},
              "validation_criteria": {{ "type": "array", "items": {{ "type": "string" }}, "description": "Conditions to check for successful completion", "default": [] }},
              "model_preference": {{
                "type": ["object", "null"],
                "properties": {{
                  "provider": {{ "type": "string" }},
                  "model": {{ "type": "string" }},
                  "temperature": {{ "type": "number" }},
                  "max_tokens": {{ "type": "integer" }}
                }},
                "additionalProperties": true,
                "default": null
              }}
            }},
            "required": ["type", "instructions"],
            "additionalProperties": false
          }}
        }},
        "required": ["step_id", "description", "agent_spec"],
        "additionalProperties": false
      }}
    }}
  }},
  "required": ["task_id", "natural_language_goal", "input_hashes", "plan"],
  "additionalProperties": false
}} # End escaping JSON schema
```

**Instructions:**

1. Analyze the provided **User Requirements**.
2. Generate a unique `task_id` (e.g., a UUID).
3. Set the `natural_language_goal` field to a concise summary of the user's main objective based on the requirements.
4. If applicable, populate the `overall_context` field with any shared background information, constraints, or style guides relevant to the entire task. If not applicable, omit this field or set it to an empty string.
5. **Crucially:** Include the exact **Input Hashes** dictionary provided below within the `input_hashes` field of the output YAML. Do not modify it.
6. Decompose the requirements into a logical sequence of steps (`plan`). Define `step_id`, `description`, `depends_on` (if any), and `agent_spec` for each step.
7. Populate the `agent_spec` with appropriate `type`, `input_artifacts`, `output_artifacts`, detailed `instructions`, and optionally `constraints` and `validation_criteria`.

**Input Hashes Provided:**

```json
{input_hashes_dict}
```

**User Requirements Provided:**

```markdown
{md_content}
```

**Generate the YAML output now:**

```yaml
```
