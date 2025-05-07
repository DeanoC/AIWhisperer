import pytest
import json
from typing import Dict, Any, Tuple, List, Optional

# Import the function we'll be testing
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor


class TestAddItemsPostprocessor:
    """Test suite for the add_items_postprocessor function."""

    def test_add_top_level_items(self):
        """Test adding items at the top level of a JSON document."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document",
    "steps": [
        {
            "step1": "Do something"
        },
        {
            "step2": "Do something else"
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123",
                    "input_hashes": {"file1": "hash1", "file2": "hash2"}
                }
            }
        }

        # Expected output should have the new items at the top level
        expected_json_dict = {
            "title": "Test Document",
            "description": "A test document",
            "steps": [
                {
                    "step1": "Do something"
                },
                {
                    "step2": "Do something else"
                }
            ],
            "task_id": "abc-123",
            "input_hashes": {"file1": "hash1", "file2": "hash2"}
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]


    def test_add_step_level_items(self):
        """Test adding items to each step/subtask in a JSON document."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document",
    "plan": [
        {
            "step_id": "step1",
            "description": "First step"
        },
        {
            "step_id": "step2",
            "description": "Second step"
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "subtask_id": "xyz-789"
                }
            }
        }

        # Expected output should have the new items in each step
        expected_json_dict = {
            "title": "Test Document",
            "description": "A test document",
            "plan": [
                {
                    "step_id": "step1",
                    "description": "First step",
                    "subtask_id": "xyz-789"
                },
                {
                    "step_id": "step2",
                    "description": "Second step",
                    "subtask_id": "xyz-789"
                }
            ]
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]


    def test_add_both_top_and_step_level_items(self):
        """Test adding items at both top level and step level simultaneously."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document",
    "plan": [
        {
            "step_id": "step1",
            "description": "First step"
        },
        {
            "step_id": "step2",
            "description": "Second step"
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123",
                    "input_hashes": {"file1": "hash1", "file2": "hash2"}
                },
                "step_level": {
                    "subtask_id": "xyz-789"
                }
            }
        }

        # Expected output should have both top-level and step-level items
        expected_json_dict = {
            "title": "Test Document",
            "description": "A test document",
            "plan": [
                {
                    "step_id": "step1",
                    "description": "First step",
                    "subtask_id": "xyz-789"
                },
                {
                    "step_id": "step2",
                    "description": "Second step",
                    "subtask_id": "xyz-789"
                }
            ]
        }
        expected_json_dict["task_id"] = "abc-123"
        expected_json_dict["input_hashes"] = {"file1": "hash1", "file2": "hash2"}


        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]


    def test_empty_json_string(self):
        """Test handling of an empty JSON string."""
        # Arrange
        json_string = ""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)

        # Assert
        # Should succeed by treating empty string as empty object and adding items
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Input string is empty or whitespace-only, treating as empty object." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Using empty dictionary due to empty input string" in warning for warning in updated_result["steps"]["add_items_postprocessor"]["warnings"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        # Check the output content is a formatted JSON string with the added item
        assert json.loads(modified_json_string) == {"task_id": "abc-123"}


    def test_invalid_json_string(self):
        """Test handling of an invalid JSON string."""
        # Arrange
        json_string = '{"invalid": json: string}' # Invalid JSON syntax
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)

        # Assert
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is False # Should fail to parse invalid JSON
        assert "add_items_postprocessor" in updated_result["steps"]
        assert len(updated_result["steps"]["add_items_postprocessor"]["errors"]) > 0
        assert "Failed to parse content as JSON" in updated_result["steps"]["add_items_postprocessor"]["errors"][0]


    def test_no_items_to_add(self):
        """Test when no items are specified to add."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document"
}
"""
        result_data = {}  # No items_to_add key

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert - should return unchanged JSON
        assert modified_json_dict == {"title": "Test Document", "description": "A test document"}
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert "No items to add specified" in updated_result["steps"]["add_items_postprocessor"]["logs"][0]

    def test_empty_items_to_add(self):
        """Test when items_to_add is empty."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document"
}
"""
        result_data = {"items_to_add": {}}  # Empty items_to_add

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert - should return unchanged JSON
        assert modified_json_dict == {"title": "Test Document", "description": "A test document"}
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert "No items to add specified" in updated_result["steps"]["add_items_postprocessor"]["logs"][0]

    def test_add_items_with_existing_keys(self):
        """Test adding items that would overwrite existing keys."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document",
    "task_id": "existing-id"
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "new-id",
                    "input_hashes": {"file1": "hash1"}
                }
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert - should warn about conflict but still add non-conflicting items
        assert modified_json_dict["task_id"] == "new-id"  # Should be overwritten
        assert modified_json_dict["input_hashes"] == {"file1": "hash1"}  # New item added
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        # No warning expected for overwriting based on clarified behavior

    def test_add_items_to_nested_steps(self):
        """Test adding items to steps that are nested under a different key."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document",
    "subtasks": [
        {
            "step_id": "step1",
            "description": "First step"
        },
        {
            "step_id": "step2",
            "description": "Second step"
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "subtask_id": "xyz-789"
                },
                "step_container": "subtasks"  # Specify the container key
            }
        }

        # Expected output should have the new items in each step
        expected_json_dict = {
            "title": "Test Document",
            "description": "A test document",
            "subtasks": [
                {
                    "step_id": "step1",
                    "description": "First step",
                    "subtask_id": "xyz-789"
                },
                {
                    "step_id": "step2",
                    "description": "Second step",
                    "subtask_id": "xyz-789"
                }
            ]
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]


    def test_missing_step_container(self):
        """Test when the specified step container is missing from the JSON."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document"
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "subtask_id": "xyz-789"
                }
            },
            "step_container": "nonexistent_container"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string) # Should still be able to parse the original JSON

        # Assert - should warn about missing container but still succeed
        assert modified_json_dict == json.loads(json_string) # Original JSON structure should be preserved
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert len(updated_result["steps"]["add_items_postprocessor"]["warnings"]) > 0
        assert "Step container 'nonexistent_container' not found or not a list" in updated_result["steps"]["add_items_postprocessor"]["warnings"][0]

    def test_step_container_not_a_list(self):
        """Test when the specified step container exists but is not a list."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document",
    "plan": {"not": "a list"}
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "subtask_id": "xyz-789"
                }
            },
            "step_container": "plan"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string) # Should still be able to parse the original JSON

        # Assert - should warn about container not being a list but still succeed
        assert modified_json_dict == json.loads(json_string) # Original JSON structure should be preserved
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert len(updated_result["steps"]["add_items_postprocessor"]["warnings"]) > 0
        assert "Found key 'plan' but it is not a list (type: dict), cannot add step-level items here." in updated_result["steps"]["add_items_postprocessor"]["warnings"][0]

    def test_input_is_dictionary(self):
        """Test handling when input is already a dictionary."""
        # Arrange
        input_dict = {
            "title": "Test Document",
            "description": "A test document",
            "plan": [
                {
                    "step_id": "step1",
                    "description": "First step"
                }
            ]
        }
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                },
                "step_level": {
                    "subtask_id": "xyz-789"
                }
            }
        }

        # Expected output should be the modified dictionary
        expected_dict = {
            "title": "Test Document",
            "description": "A test document",
            "plan": [
                {
                    "step_id": "step1",
                    "description": "First step",
                    "subtask_id": "xyz-789"
                }
            ],
            "task_id": "abc-123"
        }

        # Act
        modified_content, updated_result = add_items_postprocessor(input_dict, result_data)

        # Assert
        assert modified_content == expected_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Input is a dict, processing directly." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        assert any("Added step-level item: subtask_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_input_is_list(self):
        """Test handling when input is already a list (should not add items if schema is for dict)."""
        # Arrange
        input_list = [
            {
                "step_id": "step1",
                "description": "First step"
            }
        ]
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_content, updated_result = add_items_postprocessor(input_list, result_data)

        # Assert - should return the original list and log that it's a list
        assert modified_content == input_list
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Input is a list, processing directly." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert not updated_result["steps"]["add_items_postprocessor"]["changes"] # No changes should be made

    def test_add_items_to_empty_dict_input(self):
        """Test adding items to an empty dictionary input."""
        # Arrange
        input_dict = {}
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }
        expected_dict = {"task_id": "abc-123"}

        # Act
        modified_content, updated_result = add_items_postprocessor(input_dict, result_data)

        # Assert
        assert modified_content == expected_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Input is a dict, processing directly." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_empty_list_input(self):
        """Test adding items to an empty list input (should not add top-level items)."""
        # Arrange
        input_list = []
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_content, updated_result = add_items_postprocessor(input_list, result_data)

        # Assert - should return the original empty list
        assert modified_content == input_list
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Input is a list, processing directly." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert not updated_result["steps"]["add_items_postprocessor"]["changes"] # No changes should be made

    def test_add_items_to_json_string_with_whitespace(self):
        """Test handling of a JSON string with only whitespace."""
        # Arrange
        json_string = "   \n  "
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }
        # Expected output should be a formatted JSON string with the added item
        expected_json_string = '{\n    "task_id": "abc-123"\n}'

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)

        # Assert
        assert json.loads(modified_json_string) == json.loads(expected_json_string)
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Input string is empty or whitespace-only, treating as empty object." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Using empty dictionary due to empty input string" in warning for warning in updated_result["steps"]["add_items_postprocessor"]["warnings"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_json_string_with_comments(self):
        """Test handling of a JSON string with comments (should be treated as invalid JSON)."""
        # Arrange
        json_string = """
{
    "key": "value"
}
// This is a comment
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)

        # Assert - should fail to parse due to comments
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is False
        assert "add_items_postprocessor" in updated_result["steps"]
        assert len(updated_result["steps"]["add_items_postprocessor"]["errors"]) > 0
        assert "Failed to parse content as JSON" in updated_result["steps"]["add_items_postprocessor"]["errors"][0]

    def test_add_items_to_json_string_with_backticks(self):
        """Test handling of a JSON string with backticks (should be treated as invalid JSON)."""
        # Arrange
        json_string = """
```json
{
    "key": "value"
}
```
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)

        # Assert - should fail to parse due to backticks
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is False
        assert "add_items_postprocessor" in updated_result["steps"]
        assert len(updated_result["steps"]["add_items_postprocessor"]["errors"]) > 0
        assert "Failed to parse content as JSON" in updated_result["steps"]["add_items_postprocessor"]["errors"][0]

    def test_add_items_to_json_string_with_extra_text(self):
        """Test handling of a JSON string with extra text before or after the JSON."""
        # Arrange
        json_string = """
Some introductory text.
{
    "key": "value"
}
Some concluding text.
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)

        # Assert - should fail to parse due to extra text
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is False
        assert "add_items_postprocessor" in updated_result["steps"]
        assert len(updated_result["steps"]["add_items_postprocessor"]["errors"]) > 0
        assert "Failed to parse content as JSON" in updated_result["steps"]["add_items_postprocessor"]["errors"][0]

    def test_add_items_to_json_string_with_unicode(self):
        """Test adding items to a JSON string containing unicode characters."""
        # Arrange
        json_string = """
{
    "name": "José",
    "city": "São Paulo"
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }
        expected_json_dict = {
            "name": "José",
            "city": "São Paulo",
            "task_id": "abc-123"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_json_string_with_null_values(self):
        """Test adding items to a JSON string containing null values."""
        # Arrange
        json_string = """
{
    "key1": "value1",
    "key2": null
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }
        expected_json_dict = {
            "key1": "value1",
            "key2": None,
            "task_id": "abc-123"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_json_string_with_boolean_values(self):
        """Test adding items to a JSON string containing boolean values."""
        # Arrange
        json_string = """
{
    "key1": true,
    "key2": false
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }
        expected_json_dict = {
            "key1": True,
            "key2": False,
            "task_id": "abc-123"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_json_string_with_number_values(self):
        """Test adding items to a JSON string containing number values."""
        # Arrange
        json_string = """
{
    "key1": 123,
    "key2": 45.67
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }
        expected_json_dict = {
            "key1": 123,
            "key2": 45.67,
            "task_id": "abc-123"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_json_string_with_nested_empty_objects_and_arrays(self):
        """Test adding items to a JSON string with nested empty objects and arrays."""
        # Arrange
        json_string = """
{
    "key1": {},
    "key2": []
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }
        expected_json_dict = {
            "key1": {},
            "key2": [],
            "task_id": "abc-123"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: task_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_json_string_with_complex_nested_structure(self):
        """Test adding items to a JSON string with a complex nested structure."""
        # Arrange
        json_string = """
{
    "project": {
        "name": "AI Whisperer",
        "version": "1.0",
        "config": {
            "model": "gpt-4"
        }
    },
    "tasks": [
        {
            "id": "task1",
            "description": "Implement feature A",
            "steps": [
                {"step_id": "step1.1", "action": "Code"},
                {"step_id": "step1.2", "action": "Test"}
            ]
        },
        {
            "id": "task2",
            "description": "Fix bug B",
            "steps": [
                {"step_id": "step2.1", "action": "Debug"}
            ]
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "status": "in_progress"
                },
                "step_level": {
                    "assigned_to": "Roo"
                },
                "step_container": "steps" # Specify the nested step container
            }
        }
        expected_json_dict = {
            "project": {
                "name": "AI Whisperer",
                "version": "1.0",
                "config": {
                    "model": "gpt-4"
                }
            },
            "tasks": [
                {
                    "id": "task1",
                    "description": "Implement feature A",
                    "steps": [
                        {"step_id": "step1.1", "action": "Code", "assigned_to": "Roo"},
                        {"step_id": "step1.2", "action": "Test", "assigned_to": "Roo"}
                    ]
                },
                {
                    "id": "task2",
                    "description": "Fix bug B",
                    "steps": [
                        {"step_id": "step2.1", "action": "Debug", "assigned_to": "Roo"}
                    ]
                }
            ],
            "status": "in_progress"
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added/Overwrote top-level item: status" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        assert any("Added step-level item: assigned_to" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        # Check that the change count is correct (3 steps modified)
        assert len(updated_result["steps"]["add_items_postprocessor"]["changes"]) == 4 # 1 top-level + 3 step-level

    def test_add_items_to_json_string_with_step_container_at_top_level(self):
        """Test adding step-level items when the step container is at the top level."""
        # Arrange
        json_string = """
{
    "title": "Test Document",
    "description": "A test document",
    "plan": [
        {
            "step_id": "step1",
            "description": "First step"
        },
        {
            "step_id": "step2",
            "description": "Second step"
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "subtask_id": "xyz-789"
                }
            },
            "step_container": "plan" # Specify the top-level step container
        }
        expected_json_dict = {
            "title": "Test Document",
            "description": "A test document",
            "plan": [
                {
                    "step_id": "step1",
                    "description": "First step",
                    "subtask_id": "xyz-789"
                },
                {
                    "step_id": "step2",
                    "description": "Second step",
                    "subtask_id": "xyz-789"
                }
            ]
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added step-level item: subtask_id" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])

    def test_add_items_to_json_string_with_multiple_nested_step_containers(self):
        """Test adding step-level items when there are multiple nested step containers with the same name."""
        # Arrange
        json_string = """
{
    "tasks": [
        {
            "id": "task1",
            "steps": [
                {"step_id": "step1.1"}
            ]
        },
        {
            "id": "task2",
            "steps": [
                {"step_id": "step2.1"}
            ]
        }
    ],
    "sub_processes": [
        {
            "id": "sub1",
            "steps": [
                {"step_id": "sub1.1"}
            ]
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "status": "completed"
                }
            },
            "step_container": "steps" # Specify the nested step container name
        }
        expected_json_dict = {
            "tasks": [
                {
                    "id": "task1",
                    "steps": [
                        {"step_id": "step1.1", "status": "completed"}
                    ]
                },
                {
                    "id": "task2",
                    "steps": [
                        {"step_id": "step2.1", "status": "completed"}
                    ]
                }
            ],
            "sub_processes": [
                {
                    "id": "sub1",
                    "steps": [
                        {"step_id": "sub1.1", "status": "completed"}
                    ]
                }
            ]
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added step-level item: status" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        # Check that the change count is correct (3 steps modified)
        assert len(updated_result["steps"]["add_items_postprocessor"]["changes"]) == 3

    def test_add_items_to_json_string_with_step_container_nested_under_list(self):
        """Test adding step-level items when the step container is nested under a list."""
        # Arrange
        json_string = """
{
    "processes": [
        {
            "id": "process1",
            "tasks": [
                {
                    "id": "task1",
                    "steps": [
                        {"step_id": "step1.1"}
                    ]
                }
            ]
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "status": "completed"
                }
            },
            "step_container": "steps" # Specify the nested step container name
        }
        expected_json_dict = {
            "processes": [
                {
                    "id": "process1",
                    "tasks": [
                        {
                            "id": "task1",
                            "steps": [
                                {"step_id": "step1.1", "status": "completed"}
                            ]
                        }
                    ]
                }
            ]
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added step-level item: status" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        # Check that the change count is correct (1 step modified)
        assert len(updated_result["steps"]["add_items_postprocessor"]["changes"]) == 1

    def test_add_items_to_json_string_with_step_container_nested_under_multiple_levels(self):
        """Test adding step-level items when the step container is nested under multiple levels."""
        # Arrange
        json_string = """
{
    "organization": {
        "departments": [
            {
                "id": "dept1",
                "projects": [
                    {
                        "id": "proj1",
                        "tasks": [
                            {
                                "id": "task1",
                                "steps": [
                                    {"step_id": "step1.1"}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "status": "completed"
                }
            },
            "step_container": "steps" # Specify the nested step container name
        }
        expected_json_dict = {
            "organization": {
                "departments": [
                    {
                        "id": "dept1",
                        "projects": [
                            {
                                "id": "proj1",
                                "tasks": [
                                    {
                                        "id": "task1",
                                        "steps": [
                                            {"step_id": "step1.1", "status": "completed"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added step-level item: status" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        # Check that the change count is correct (1 step modified)
        assert len(updated_result["steps"]["add_items_postprocessor"]["changes"]) == 1

    def test_add_items_to_json_string_with_step_container_not_found_at_any_level(self):
        """Test adding step-level items when the specified step container is not found at any level."""
        # Arrange
        json_string = """
{
    "project": {
        "name": "AI Whisperer"
    },
    "tasks": [
        {
            "id": "task1",
            "description": "Implement feature A"
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "status": "completed"
                }
            },
            "step_container": "nonexistent_steps" # Specify a nonexistent container name
        }
        expected_json_dict = json.loads(json_string) # Original JSON should be preserved

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Step container 'nonexistent_steps' not found or not a list" in warning for warning in updated_result["steps"]["add_items_postprocessor"]["warnings"])
        assert not updated_result["steps"]["add_items_postprocessor"]["changes"] # No changes should be made

    def test_add_items_to_json_string_with_step_container_not_a_list_at_any_level(self):
        """Test adding step-level items when the specified step container exists but is not a list at any level."""
        # Arrange
        json_string = """
{
    "project": {
        "name": "AI Whisperer",
        "steps": {"not": "a list"}
    },
    "tasks": [
        {
            "id": "task1",
            "description": "Implement feature A",
            "steps": "not a list either"
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "status": "completed"
                }
            },
            "step_container": "steps" # Specify the container name
        }
        expected_json_dict = json.loads(json_string) # Original JSON should be preserved

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        # Expect warnings for each instance of 'steps' that is not a list
        assert len(updated_result["steps"]["add_items_postprocessor"]["warnings"]) == 2
        assert any("Found key 'steps' but it is not a list (type: dict)" in warning for warning in updated_result["steps"]["add_items_postprocessor"]["warnings"])
        assert any("Found key 'steps' but it is not a list (type: str)" in warning for warning in updated_result["steps"]["add_items_postprocessor"]["warnings"])
        assert not updated_result["steps"]["add_items_postprocessor"]["changes"] # No changes should be made

    def test_add_items_to_json_string_with_step_container_nested_under_non_dict_items(self):
        """Test adding step-level items when the step container is nested under non-dictionary items in a list."""
        # Arrange
        json_string = """
{
    "processes": [
        "process1",
        {
            "id": "process2",
            "tasks": [
                {
                    "id": "task1",
                    "steps": [
                        {"step_id": "step1.1"}
                    ]
                }
            ]
        }
    ]
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "status": "completed"
                }
            },
            "step_container": "steps" # Specify the nested step container name
        }
        expected_json_dict = {
            "processes": [
                "process1", # This item is not a dictionary, should be skipped
                {
                    "id": "process2",
                    "tasks": [
                        {
                            "id": "task1",
                            "steps": [
                                {"step_id": "step1.1", "status": "completed"}
                            ]
                        }
                    ]
                }
            ]
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added step-level item: status" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        # Check that the change count is correct (1 step modified)
        assert len(updated_result["steps"]["add_items_postprocessor"]["changes"]) == 1
        # Check for a log indicating a non-dictionary item was skipped (optional, but good for debugging)
        # assert any("Skipping non-dictionary item in list" in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"]) # Add this log in the implementation if needed

    def test_add_items_to_json_string_with_step_container_nested_under_non_list_items(self):
        """Test adding step-level items when the step container is nested under non-list items in a dictionary."""
        # Arrange
        json_string = """
{
    "data": {
        "item1": "not a list",
        "item2": {
            "id": "item2",
            "steps": [
                {"step_id": "step1.1"}
            ]
        }
    }
}
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "status": "completed"
                }
            },
            "step_container": "steps" # Specify the nested step container name
        }
        expected_json_dict = {
            "data": {
                "item1": "not a list", # This item is not a dictionary, should be skipped
                "item2": {
                    "id": "item2",
                    "steps": [
                        {"step_id": "step1.1", "status": "completed"}
                    ]
                }
            }
        }

        # Act
        modified_json_string, updated_result = add_items_postprocessor(json_string, result_data)
        modified_json_dict = json.loads(modified_json_string)

        # Assert
        assert modified_json_dict == expected_json_dict
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert any("Successfully parsed content as JSON." in log for log in updated_result["steps"]["add_items_postprocessor"]["logs"])
        assert any("Added step-level item: status" in change for change in updated_result["steps"]["add_items_postprocessor"]["changes"])
        # Check that the change count is correct (1 step modified)
        assert len(updated_result["steps"]["add_items_postprocessor"]["changes"]) == 1
        #
