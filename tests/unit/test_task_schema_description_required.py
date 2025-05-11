from jsonschema import validate, ValidationError
import json
import pytest

def test_schema_validation():
    schema_path = "src/ai_whisperer/schemas/task_schema.json"
    with open(schema_path, "r") as f:
        schema = json.load(f)
    
    print("Loaded schema:", json.dumps(schema, indent=2))

    invalid_data = {
        "task_id": "task-123",
        "natural_language_goal": "Test goal",
        "input_hashes": {
            "requirements_md": "hash1",
            "config_yaml": "hash2",
            "prompt_file": "hash3"
        },
        "plan": [
            {
                "subtask_id": "subtask-001",
                # Missing 'description' field
                "agent_spec": {
                    "type": "code_generation",
                    "instructions": ["Do something."]
                }
            }
        ]
    }

    with pytest.raises(ValidationError) as excinfo:
        validate(instance=invalid_data, schema=schema)
    assert "'description' is a required property" in str(excinfo.value)

    try:
      validate(instance=invalid_data, schema=schema)
      assert False, "Validation should have failed"
    except ValidationError as e:
      print(f"Validation failed: {e.message}")
      assert "'description' is a required property" in e.message