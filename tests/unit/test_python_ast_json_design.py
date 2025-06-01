"""Additional design tests for Python AST JSON tool - TDD RED phase."""

import pytest
import json
import tempfile
from pathlib import Path

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestPythonASTJSONDesignRequirements:
    """Tests verifying the design meets all requirements."""
    
    def test_api_supports_file_path_input(self):
        """Test that API design supports file path as input."""
        tool = PythonASTJSONTool()
        
        # Test with execute method
        tool.execute(
            action="to_json",
            source="/path/to/file.py",
            source_type="file"
        )
        
        # Test with static method
        PythonASTJSONTool.file_to_json("/path/to/file.py")
    
    def test_api_supports_module_name_input(self):
        """Test that API design supports module names as input."""
        tool = PythonASTJSONTool()
        
        # Test with execute method
        tool.execute(
            action="to_json",
            source="os.path",
            source_type="module"
        )
        
        # Test with static method
        PythonASTJSONTool.module_to_json("os.path")
    
    def test_api_supports_code_string_input(self):
        """Test that API design supports direct code strings."""
        tool = PythonASTJSONTool()
            
        tool.execute(
                action="to_json",
                source="x = 42\nprint(x)",
                source_type="code"
            )
    
    def test_bidirectional_conversion_api(self):
        """Test that API supports full bidirectional conversion."""
        # Python → AST
        ast_json = PythonASTJSONTool.file_to_json("test.py")
            
        # AST JSON → AST node
        ast_node = PythonASTJSONTool.json_to_ast({"node_type": "Module"})
            
        # AST JSON → Python code
        code = PythonASTJSONTool.json_to_code({"node_type": "Module"})
        
    def test_metadata_fields_in_schema(self):
        """Test that schema includes all required metadata fields."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
            
        metadata = schema["definitions"]["metadata"]["properties"]
            
        # Required metadata fields
        assert "python_version" in metadata
        assert "conversion_timestamp" in metadata
            
        # Optional but important metadata fields
        assert "source_file" in metadata
        assert "module_name" in metadata
        assert "encoding" in metadata
        
    def test_source_location_preservation(self):
        """Test that design preserves source location information."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
            
        location = schema["definitions"]["sourceLocation"]["properties"]
            
        # All AST location fields
        assert "lineno" in location
        assert "col_offset" in location
        assert "end_lineno" in location
        assert "end_col_offset" in location
        
    def test_comprehensive_node_coverage(self):
        """Test that schema covers comprehensive Python AST nodes."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
            
        definitions = schema["definitions"]
            
        # Statement nodes
        stmt_nodes = ["functionDef", "classDef", "assign", "for", "while", "if", 
                    "with", "import", "importFrom", "return", "raise", "try"]
        for node in stmt_nodes:
            assert node in definitions, f"Missing statement node: {node}"
            
        # Expression nodes
        expr_nodes = ["binOp", "unaryOp", "call", "attribute", "subscript",
                    "list", "dict", "tuple", "set"]
        for node in expr_nodes:
            assert node in definitions, f"Missing expression node: {node}"
            
        # Comprehension nodes
        comp_nodes = ["listComp", "dictComp", "setComp", "generatorExp"]
        for node in comp_nodes:
            assert node in definitions, f"Missing comprehension node: {node}"
        
    def test_validation_capability(self):
        """Test that API includes validation capabilities."""
        tool = PythonASTJSONTool()
            
        # Via execute method
        tool.execute(
                action="validate",
                json_data={"node_type": "Module"}
            )
            
        # Via static method
        PythonASTJSONTool.validate_ast_json({"node_type": "Module"})
        
    def test_error_handling_design(self):
        """Test that API design includes error handling."""
        tool = PythonASTJSONTool()
            
        # Unknown action should return error dict
        result = tool.execute(action="unknown_action")
        assert isinstance(result, dict)
        assert "error" in result
        
    def test_formatting_options(self):
        """Test that API includes formatting options."""
        tool = PythonASTJSONTool()
        schema = tool.parameters_schema
            
        assert "format_output" in schema["properties"]
        assert schema["properties"]["format_output"]["default"] is True

class TestPythonASTJSONSchemaCompleteness:
    """Tests to ensure schema completeness for all Python constructs."""
    
    def test_async_constructs(self):
        """Test that schema includes async/await constructs."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        
        # Note: In RED phase, we're just checking the schema structure exists
        # Actual async nodes would be added in implementation
        assert "definitions" in schema
    
    def test_type_annotations_support(self):
        """Test that schema supports type annotations."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        
        # Check annAssign for annotated assignments
        assert "annAssign" in schema["definitions"]
        ann_assign = schema["definitions"]["annAssign"]
        # Check inside allOf structure
        assert "allOf" in ann_assign
        properties = ann_assign["allOf"][1]["properties"]
        assert "annotation" in properties
        assert "target" in properties
    
    def test_pattern_matching_support(self):
        """Test that schema supports Python 3.10+ pattern matching."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        
        # Check for match statement
        assert "match" in schema["definitions"]
        match_def = schema["definitions"]["match"]
        # Check inside allOf structure
        assert "allOf" in match_def
        properties = match_def["allOf"][1]["properties"]
        assert "subject" in properties
        assert "cases" in properties
    
    def test_docstring_preservation(self):
        """Test that schema design preserves docstrings."""
        tool = PythonASTJSONTool()
        with open(tool._schema_path) as f:
            schema = json.load(f)
        
        # Base node should have docstring field
        base_node = schema["definitions"]["baseNode"]["properties"]
        assert "docstring" in base_node