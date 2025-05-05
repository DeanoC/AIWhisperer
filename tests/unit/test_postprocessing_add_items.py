import pytest
import yaml
from typing import Dict, Any, Tuple

# Import the function we'll be testing (this will exist later)
# This import will fail until we implement the function, which is expected in TDD
from src.postprocessing.add_items_postprocessor import add_items_postprocessor


class TestAddItemsPostprocessor:
    """Test suite for the add_items_postprocessor function."""

    def test_add_top_level_items(self):
        """Test adding items at the top level of a YAML document."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
steps:
  - step1: Do something
  - step2: Do something else
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
        expected_yaml_dict = {
            "title": "Test Document",
            "description": "A test document",
            "steps": [
                {"step1": "Do something"},
                {"step2": "Do something else"}
            ],
            "task_id": "abc-123",
            "input_hashes": {"file1": "hash1", "file2": "hash2"}
        }

        # Act
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        modified_yaml_dict = yaml.safe_load(modified_yaml_string)

        # Assert
        assert modified_yaml_dict == expected_yaml_dict
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True

    def test_add_step_level_items(self):
        """Test adding items to each step/subtask in a YAML document."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
plan:
  - step_id: step1
    description: First step
  - step_id: step2
    description: Second step
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "subtask_id": "xyz-789"
                }
            }
        }

        # Expected output should have the new items in each step
        expected_yaml_dict = {
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
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        modified_yaml_dict = yaml.safe_load(modified_yaml_string)

        # Assert
        assert modified_yaml_dict == expected_yaml_dict
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True

    def test_add_both_top_and_step_level_items(self):
        """Test adding items at both top level and step level simultaneously."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
plan:
  - step_id: step1
    description: First step
  - step_id: step2
    description: Second step
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
        expected_yaml_dict = {
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
            ],
            "task_id": "abc-123",
            "input_hashes": {"file1": "hash1", "file2": "hash2"}
        }

        # Act
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        modified_yaml_dict = yaml.safe_load(modified_yaml_string)

        # Assert
        assert modified_yaml_dict == expected_yaml_dict
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True

    def test_empty_yaml_string(self):
        """Test handling of an empty YAML string."""
        # Arrange
        yaml_string = ""
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        
        # Assert
        assert updated_result["success"] is False
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is False
        assert len(updated_result["steps"]["add_items_postprocessor"]["errors"]) > 0

    def test_invalid_yaml_string(self):
        """Test handling of an invalid YAML string."""
        # Arrange
        yaml_string = "invalid: yaml: string: with: too: many: colons"
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "abc-123"
                }
            }
        }

        # Act
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        
        # Assert
        assert updated_result["success"] is False
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is False
        assert len(updated_result["steps"]["add_items_postprocessor"]["errors"]) > 0

    def test_no_items_to_add(self):
        """Test when no items are specified to add."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
"""
        result_data = {}  # No items_to_add key

        # Act
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        modified_yaml_dict = yaml.safe_load(modified_yaml_string)
        
        # Assert - should return unchanged YAML
        assert modified_yaml_dict == {"title": "Test Document", "description": "A test document"}
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "No items to add specified" in updated_result["steps"]["add_items_postprocessor"]["logs"][0]

    def test_empty_items_to_add(self):
        """Test when items_to_add is empty."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
"""
        result_data = {"items_to_add": {}}  # Empty items_to_add

        # Act
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        modified_yaml_dict = yaml.safe_load(modified_yaml_string)
        
        # Assert - should return unchanged YAML
        assert modified_yaml_dict == {"title": "Test Document", "description": "A test document"}
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert "No items to add specified" in updated_result["steps"]["add_items_postprocessor"]["logs"][0]

    def test_add_items_with_existing_keys(self):
        """Test adding items that would overwrite existing keys."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
task_id: existing-id
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
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        modified_yaml_dict = yaml.safe_load(modified_yaml_string)
        
        # Assert - should warn about conflict but still add non-conflicting items
        assert modified_yaml_dict["task_id"] == "existing-id"  # Original value preserved
        assert modified_yaml_dict["input_hashes"] == {"file1": "hash1"}  # New item added
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert len(updated_result["steps"]["add_items_postprocessor"]["warnings"]) > 0
        assert "task_id" in updated_result["steps"]["add_items_postprocessor"]["warnings"][0]

    def test_add_items_to_nested_steps(self):
        """Test adding items to steps that are nested under a different key."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
subtasks:
  - step_id: step1
    description: First step
  - step_id: step2
    description: Second step
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
        expected_yaml_dict = {
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
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        modified_yaml_dict = yaml.safe_load(modified_yaml_string)

        # Assert
        assert modified_yaml_dict == expected_yaml_dict
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True

    def test_missing_step_container(self):
        """Test when the specified step container is missing from the YAML."""
        # Arrange
        yaml_string = """
title: Test Document
description: A test document
"""
        result_data = {
            "items_to_add": {
                "step_level": {
                    "subtask_id": "xyz-789"
                },
                "step_container": "nonexistent_container"
            }
        }

        # Act
        modified_yaml_string, updated_result = add_items_postprocessor(yaml_string, result_data)
        
        # Assert - should warn about missing container but still succeed
        assert updated_result["success"] is True
        assert "add_items_postprocessor" in updated_result["steps"]
        assert updated_result["steps"]["add_items_postprocessor"]["success"] is True
        assert len(updated_result["steps"]["add_items_postprocessor"]["warnings"]) > 0
        assert "nonexistent_container" in updated_result["steps"]["add_items_postprocessor"]["warnings"][0]
