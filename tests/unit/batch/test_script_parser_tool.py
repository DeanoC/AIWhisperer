"""
Unit tests for ScriptParserTool.
Following TDD principles - tests written before implementation.
"""

import pytest
import json
import yaml
from pathlib import Path
from typing import Dict, Any

# We expect these imports to work after implementation
from ai_whisperer.tools.script_parser_tool import ScriptParserTool, ScriptFormat, ParsedScript


class TestScriptParserTool:
    """Test ScriptParserTool functionality"""
    
    @pytest.fixture
    def parser_tool(self):
        """Provide an initialized ScriptParserTool"""
        return ScriptParserTool()
    
    @pytest.fixture
    def sample_json_script(self, tmp_path):
        """Create a sample JSON script file"""
        script_content = {
            "name": "Test Script",
            "description": "A test batch script",
            "steps": [
                {"action": "list_files", "path": "/tmp"},
                {"action": "create_file", "name": "test.txt", "content": "Hello"},
                {"action": "read_file", "path": "/tmp/test.txt"}
            ]
        }
        script_file = tmp_path / "test_script.json"
        script_file.write_text(json.dumps(script_content, indent=2))
        return script_file
    
    @pytest.fixture
    def sample_yaml_script(self, tmp_path):
        """Create a sample YAML script file"""
        script_content = """
name: Test YAML Script
description: A test batch script in YAML
steps:
  - action: switch_agent
    agent: p
  - action: list_rfcs
  - action: create_rfc
    params:
      title: New Feature
      description: Feature description
"""
        script_file = tmp_path / "test_script.yaml"
        script_file.write_text(script_content)
        return script_file
    
    @pytest.fixture
    def sample_text_script(self, tmp_path):
        """Create a sample plain text script file"""
        script_content = """# Test text script
# This is a comment
list files in /tmp
create file test.txt with content "Hello World"
read file /tmp/test.txt
# Another comment
switch to agent p
list rfcs
"""
        script_file = tmp_path / "test_script.txt"
        script_file.write_text(script_content)
        return script_file
    
    # Basic functionality tests
    
    def test_script_parser_tool_creation(self, parser_tool):
        """Test that ScriptParserTool can be created"""
        assert parser_tool is not None
        assert hasattr(parser_tool, 'name')
        assert parser_tool.name == 'script_parser'
        assert hasattr(parser_tool, 'description')
    
    def test_script_parser_tool_has_required_methods(self, parser_tool):
        """Test that ScriptParserTool has required methods"""
        assert hasattr(parser_tool, 'execute')
        assert hasattr(parser_tool, 'parse_script')
        assert hasattr(parser_tool, 'validate_script')
        assert hasattr(parser_tool, 'detect_format')
    
    # Format detection tests
    
    def test_detect_json_format(self, parser_tool, sample_json_script):
        """Test detection of JSON format"""
        detected_format = parser_tool.detect_format(str(sample_json_script))
        assert detected_format == ScriptFormat.JSON
    
    def test_detect_yaml_format(self, parser_tool, sample_yaml_script):
        """Test detection of YAML format"""
        detected_format = parser_tool.detect_format(str(sample_yaml_script))
        assert detected_format == ScriptFormat.YAML
    
    def test_detect_text_format(self, parser_tool, sample_text_script):
        """Test detection of plain text format"""
        detected_format = parser_tool.detect_format(str(sample_text_script))
        assert detected_format == ScriptFormat.TEXT
    
    # JSON parsing tests
    
    def test_parse_valid_json_script(self, parser_tool, sample_json_script):
        """Test parsing a valid JSON script"""
        result = parser_tool.parse_script(str(sample_json_script))
        
        assert isinstance(result, ParsedScript)
        assert result.format == ScriptFormat.JSON
        assert result.name == "Test Script"
        assert result.description == "A test batch script"
        assert len(result.steps) == 3
        assert result.steps[0]["action"] == "list_files"
    
    def test_parse_malformed_json(self, parser_tool, tmp_path):
        """Test parsing malformed JSON"""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text('{"name": "Bad JSON", "steps": [}')  # Invalid JSON
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            parser_tool.parse_script(str(bad_json))
    
    # YAML parsing tests
    
    def test_parse_valid_yaml_script(self, parser_tool, sample_yaml_script):
        """Test parsing a valid YAML script"""
        result = parser_tool.parse_script(str(sample_yaml_script))
        
        assert isinstance(result, ParsedScript)
        assert result.format == ScriptFormat.YAML
        assert result.name == "Test YAML Script"
        assert len(result.steps) == 3
        assert result.steps[0]["action"] == "switch_agent"
    
    def test_parse_malformed_yaml(self, parser_tool, tmp_path):
        """Test parsing malformed YAML"""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("name: Bad YAML\nsteps:\n  - action: test\n  bad indent")
        
        with pytest.raises(ValueError, match="Invalid YAML"):
            parser_tool.parse_script(str(bad_yaml))
    
    # Text parsing tests
    
    def test_parse_valid_text_script(self, parser_tool, sample_text_script):
        """Test parsing a valid text script"""
        result = parser_tool.parse_script(str(sample_text_script))
        
        assert isinstance(result, ParsedScript)
        assert result.format == ScriptFormat.TEXT
        assert len(result.steps) == 5  # Should skip comments and empty lines
        assert result.steps[0]["command"] == "list files in /tmp"
    
    def test_text_parser_skips_comments_and_empty_lines(self, parser_tool, tmp_path):
        """Test that text parser correctly handles comments and empty lines"""
        script = tmp_path / "comments.txt"
        script.write_text("""
# Comment line
command 1

# Another comment
command 2
  
command 3
""")
        result = parser_tool.parse_script(str(script))
        assert len(result.steps) == 3
        assert all(step["command"].startswith("command") for step in result.steps)
    
    # Validation tests
    
    def test_validate_script_structure(self, parser_tool):
        """Test script validation"""
        # Valid script
        valid_script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Valid Script",
            steps=[{"action": "test"}],
            raw_content="{}"
        )
        assert parser_tool.validate_script(valid_script) == True
        
        # Invalid script - no steps
        invalid_script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Invalid Script",
            steps=[],
            raw_content="{}"
        )
        with pytest.raises(ValueError, match="No steps found"):
            parser_tool.validate_script(invalid_script)
    
    # Security tests
    
    def test_prevent_path_traversal(self, parser_tool, tmp_path):
        """Test that parser prevents path traversal attempts"""
        malicious_script = tmp_path / "malicious.json"
        malicious_script.write_text(json.dumps({
            "name": "Malicious",
            "steps": [{"action": "read_file", "path": "../../../etc/passwd"}]
        }))
        
        with pytest.raises(ValueError, match="Path traversal"):
            parser_tool.parse_script(str(malicious_script))
    
    def test_file_size_limit(self, parser_tool, tmp_path):
        """Test that parser enforces file size limits"""
        large_script = tmp_path / "large.json"
        # Create a script larger than 1MB limit
        large_content = {"steps": [{"action": "test"}] * 100000}
        large_script.write_text(json.dumps(large_content))
        
        with pytest.raises(ValueError, match="exceeds size limit"):
            parser_tool.parse_script(str(large_script))
    
    def test_validate_file_extension(self, parser_tool, tmp_path):
        """Test that parser validates file extensions"""
        bad_extension = tmp_path / "script.exe"
        bad_extension.write_text("malicious content")
        
        with pytest.raises(ValueError, match="Unsupported file extension"):
            parser_tool.parse_script(str(bad_extension))
    
    # Tool interface tests
    
    def test_execute_method_with_file_path(self, parser_tool, sample_json_script):
        """Test the execute method with file path"""
        result = parser_tool.execute(file_path=str(sample_json_script))
        
        assert result["success"] == True
        assert "parsed_script" in result
        assert result["parsed_script"]["format"] == "json"
        assert result["parsed_script"]["step_count"] == 3
    
    def test_execute_method_with_missing_file(self, parser_tool):
        """Test execute method with non-existent file"""
        result = parser_tool.execute(file_path="/tmp/non_existent_script.json")
        
        assert result["success"] == False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_execute_method_validation_errors(self, parser_tool, tmp_path):
        """Test execute method handles validation errors properly"""
        empty_script = tmp_path / "empty.json"
        empty_script.write_text('{"name": "Empty", "steps": []}')
        
        result = parser_tool.execute(file_path=str(empty_script))
        
        assert result["success"] == False
        assert "error" in result
        assert "No steps" in result["error"]