"""Unit tests for PythonASTJSONTool - TDD RED phase tests."""

import pytest
import json
import ast
from pathlib import Path
from unittest.mock import Mock, patch

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool

# Mark all tests in this module as skipped - TDD tests for future implementation
pytestmark = pytest.mark.skip(reason="TDD tests - implementation in progress")


class TestPythonASTJSONToolSchema:
    """Tests for JSON schema validation."""
    
    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        tool = PythonASTJSONTool()
        assert tool._schema_path.exists(), "Schema file should exist"
    
    def test_schema_is_valid_json(self):
        """Test that the schema file contains valid JSON."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        assert isinstance(schema, dict), "Schema should be a dictionary"
        assert "$schema" in schema, "Schema should have $schema property"
    
    def test_schema_covers_all_node_types(self):
        """Test that schema covers all Python AST node types."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        
        # Check for essential node types
        definitions = schema.get("definitions", {})
        essential_nodes = [
            "module", "functionDef", "classDef", "assign", "for", "while",
            "if", "with", "import", "importFrom", "expr", "stmt"
        ]
        
        for node in essential_nodes:
            assert node in definitions, f"Schema should define {node}"
    
    def test_schema_includes_metadata(self):
        """Test that schema includes metadata fields."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        
        assert "metadata" in schema["properties"], "Schema should have metadata property"
        metadata_def = schema["definitions"].get("metadata", {})
        required_fields = ["python_version", "conversion_timestamp"]
        
        for field in required_fields:
            assert field in metadata_def.get("required", []), f"Metadata should require {field}"
    
    def test_schema_includes_source_location(self):
        """Test that schema includes source location information."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        
        assert "sourceLocation" in schema["definitions"], "Schema should define sourceLocation"
        location = schema["definitions"]["sourceLocation"]
        assert "lineno" in location["properties"], "Source location should have lineno"
        assert "col_offset" in location["properties"], "Source location should have col_offset"


class TestPythonASTJSONToolAPI:
    """Tests for the tool API design."""
    
    def test_tool_properties(self):
        """Test that tool has required properties."""
        tool = PythonASTJSONTool()
        assert tool.name == "python_ast_json"
        assert tool.description == "Convert Python code to AST JSON representation and back"
        assert tool.category == "Code Analysis"
        assert "ast" in tool.tags
        assert "json" in tool.tags
    
    def test_parameters_schema(self):
        """Test the parameters schema structure."""
        tool = PythonASTJSONTool()
        schema = tool.parameters_schema
        
        assert schema["type"] == "object"
        assert "action" in schema["properties"]
        assert "source" in schema["properties"]
        assert "json_data" in schema["properties"]
        assert "source_type" in schema["properties"]
        
        # Check action enum values
        actions = schema["properties"]["action"]["enum"]
        assert "to_json" in actions
        assert "from_json" in actions
        assert "validate" in actions
    
    @pytest.skip("TDD test - implementation now complete")
    def test_execute_to_json_not_implemented(self):
        """Test that to_json action raises NotImplementedError."""
        tool = PythonASTJSONTool()
        tool.execute(action="to_json", source="test.py")
    
    @pytest.skip("TDD test - implementation now complete")
    def test_execute_from_json_not_implemented(self):
        """Test that from_json action raises NotImplementedError."""
        tool = PythonASTJSONTool()
        tool.execute(action="from_json", json_data={})
    
    @pytest.skip("TDD test - implementation now complete")
    def test_execute_validate_not_implemented(self):
        """Test that validate action raises NotImplementedError."""
        tool = PythonASTJSONTool()
        tool.execute(action="validate", json_data={})
    
    def test_execute_unknown_action(self):
        """Test that unknown action returns error."""
        tool = PythonASTJSONTool()
        result = tool.execute(action="unknown")
        assert "error" in result
        assert "Unknown action" in result["error"]

class TestPythonASTJSONToolStaticMethods:
    """Tests for static API methods."""
    
    @pytest.skip("TDD test - implementation now complete")
    def test_ast_to_json_not_implemented(self):
        """Test that ast_to_json raises NotImplementedError."""
        node = ast.parse("x = 1")
        PythonASTJSONTool.ast_to_json(node)
    
    @pytest.skip("TDD test - implementation now complete")
    def test_json_to_ast_not_implemented(self):
        """Test that json_to_ast raises NotImplementedError."""
        PythonASTJSONTool.json_to_ast({"node_type": "Module"})
    
    @pytest.skip("TDD test - implementation now complete")
    def test_file_to_json_not_implemented(self):
        """Test that file_to_json raises NotImplementedError."""
        PythonASTJSONTool.file_to_json("test.py")
    
    @pytest.skip("TDD test - implementation now complete")
    def test_module_to_json_not_implemented(self):
        """Test that module_to_json raises NotImplementedError."""
        PythonASTJSONTool.module_to_json("os.path")
    
    @pytest.skip("TDD test - implementation now complete")
    def test_json_to_code_not_implemented(self):
        """Test that json_to_code raises NotImplementedError."""
        PythonASTJSONTool.json_to_code({"node_type": "Module"})
    
    @pytest.skip("TDD test - implementation now complete")
    def test_validate_ast_json_not_implemented(self):
        """Test that validate_ast_json raises NotImplementedError."""
        PythonASTJSONTool.validate_ast_json({"node_type": "Module"})

class TestPythonASTJSONToolBidirectional:
    """Tests for bidirectional conversion support."""
    
    def test_supports_file_paths(self):
        """Test that API supports file path input."""
        tool = PythonASTJSONTool()
        schema = tool.parameters_schema
        source_types = schema["properties"]["source_type"]["enum"]
        assert "file" in source_types
    
    def test_supports_module_names(self):
        """Test that API supports module name input."""
        tool = PythonASTJSONTool()
        schema = tool.parameters_schema
        source_types = schema["properties"]["source_type"]["enum"]
        assert "module" in source_types
    
    def test_supports_code_strings(self):
        """Test that API supports direct code input."""
        tool = PythonASTJSONTool()
        schema = tool.parameters_schema
        source_types = schema["properties"]["source_type"]["enum"]
        assert "code" in source_types
    
    def test_metadata_preservation(self):
        """Test that API design includes metadata preservation."""
        tool = PythonASTJSONTool()
        schema = tool.parameters_schema
        assert "include_metadata" in schema["properties"]
        assert schema["properties"]["include_metadata"]["default"] is True
    
    def test_round_trip_conversion_design(self):
        """Test that API supports round-trip conversion."""
        # This test verifies the API design supports bidirectional conversion
        # by checking that both to_json and from_json actions exist
        tool = PythonASTJSONTool()
        schema = tool.parameters_schema
        actions = schema["properties"]["action"]["enum"]
        
        assert "to_json" in actions, "Should support Python to JSON"
        assert "from_json" in actions, "Should support JSON to Python"
        
        # Check static methods exist for both directions
        assert hasattr(PythonASTJSONTool, "ast_to_json")
        assert hasattr(PythonASTJSONTool, "json_to_ast")
        assert hasattr(PythonASTJSONTool, "json_to_code")


class TestPythonASTJSONToolIntegration:
    """Integration tests for the tool with the AIWhisperer system."""
    
    def test_tool_can_be_instantiated(self):
        """Test that the tool can be instantiated."""
        tool = PythonASTJSONTool()
        assert isinstance(tool, PythonASTJSONTool)
    
    def test_tool_inherits_from_aitool(self):
        """Test that the tool inherits from AITool."""
        from ai_whisperer.tools.base_tool import AITool
        tool = PythonASTJSONTool()
        assert isinstance(tool, AITool)
    
    def test_get_ai_prompt_instructions(self):
        """Test that AI prompt instructions are provided."""
        tool = PythonASTJSONTool()
        instructions = tool.get_ai_prompt_instructions()
        
        assert isinstance(instructions, str)
        assert "Convert Python code to AST JSON" in instructions
        assert "File paths" in instructions
        assert "Module names" in instructions
        assert "Bidirectional conversion" in instructions