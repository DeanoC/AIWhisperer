"""
Unit tests for ScriptParserTool validation and security features.
Following TDD principles - tests written before implementation.
"""

import pytest
import json
import yaml
from pathlib import Path
from typing import Dict, Any

from ai_whisperer.tools.script_parser_tool import ScriptParserTool, ScriptFormat, ParsedScript


class TestScriptParserValidation:
    """Test validation and security features of ScriptParserTool"""
    
    @pytest.fixture
    def parser_tool(self):
        """Provide an initialized ScriptParserTool"""
        return ScriptParserTool()
    
    # Action validation tests
    
    def test_validate_allowed_actions(self, parser_tool):
        """Test that only allowed actions are accepted"""
        # Define what actions should be allowed
        allowed_actions = [
            "list_files", "read_file", "create_file", "write_file",
            "switch_agent", "list_rfcs", "create_rfc", "execute_command",
            "search_files", "analyze_code"
        ]
        
        for action in allowed_actions:
            # Add minimal required parameters for each action
            step = {"action": action}
            if action in ["read_file", "write_file", "create_file"]:
                step["path"] = "/tmp/test.txt"
            
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Test",
                steps=[step],
                raw_content="{}"
            )
            assert parser_tool.validate_script(script) == True
    
    def test_reject_dangerous_actions(self, parser_tool):
        """Test that dangerous actions are rejected"""
        dangerous_actions = [
            "delete_file", "remove_directory", "format_disk",
            "execute_shell", "eval", "exec"
        ]
        
        for action in dangerous_actions:
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Test",
                steps=[{"action": action}],
                raw_content="{}"
            )
            with pytest.raises(ValueError, match="not allowed|dangerous"):
                parser_tool.validate_script(script)
    
    # Parameter validation tests
    
    def test_validate_required_parameters(self, parser_tool):
        """Test that required parameters are validated"""
        # Action with missing required parameter
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test",
            steps=[{"action": "read_file"}],  # Missing 'path' parameter
            raw_content="{}"
        )
        
        with pytest.raises(ValueError, match="Missing required parameter"):
            parser_tool.validate_script(script)
    
    def test_validate_parameter_types(self, parser_tool):
        """Test that parameter types are validated"""
        # Invalid parameter type
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test",
            steps=[{
                "action": "create_file",
                "path": 123,  # Should be string
                "content": "test"
            }],
            raw_content="{}"
        )
        
        with pytest.raises(ValueError, match="Invalid parameter type"):
            parser_tool.validate_script(script)
    
    # Path validation tests
    
    def test_validate_safe_paths(self, parser_tool):
        """Test that safe paths are allowed"""
        safe_paths = [
            "/tmp/test.txt",
            "./data/file.json",
            "workspace/project/src/main.py",
            "output/report.md"
        ]
        
        for path in safe_paths:
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Test",
                steps=[{"action": "read_file", "path": path}],
                raw_content="{}"
            )
            # Should not raise
            parser_tool.validate_script(script)
    
    def test_reject_unsafe_paths(self, parser_tool):
        """Test that unsafe paths are rejected"""
        unsafe_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "~/.ssh/id_rsa",
            "/root/.bashrc",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for path in unsafe_paths:
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Test",
                steps=[{"action": "read_file", "path": path}],
                raw_content="{}"
            )
            with pytest.raises(ValueError, match="forbidden|unsafe|Path traversal"):
                parser_tool.validate_script(script)
    
    # Content validation tests
    
    def test_validate_content_size(self, parser_tool):
        """Test that content size is limited"""
        # Very large content
        large_content = "x" * (1024 * 1024 + 1)  # 1MB + 1 byte
        
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test",
            steps=[{
                "action": "create_file",
                "path": "/tmp/large.txt",
                "content": large_content
            }],
            raw_content="{}"
        )
        
        with pytest.raises(ValueError, match="Content too large"):
            parser_tool.validate_script(script)
    
    def test_validate_no_script_injection(self, parser_tool):
        """Test that script injection is prevented"""
        injection_attempts = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "${EVIL_COMMAND}",
            "$(rm -rf /)"
        ]
        
        for injection in injection_attempts:
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Test",
                steps=[{
                    "action": "create_file",
                    "path": "/tmp/test.txt",
                    "content": injection
                }],
                raw_content="{}"
            )
            # Should validate but content should be treated as plain text
            parser_tool.validate_script(script)
    
    # Step limit tests
    
    def test_validate_step_count_limit(self, parser_tool):
        """Test that scripts have reasonable step limits"""
        # Too many steps
        many_steps = [{"action": "list_files", "path": "/tmp"}] * 1001
        
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test",
            steps=many_steps,
            raw_content="{}"
        )
        
        with pytest.raises(ValueError, match="Too many steps"):
            parser_tool.validate_script(script)
    
    # Nested action validation
    
    def test_validate_no_recursive_scripts(self, parser_tool):
        """Test that scripts cannot call other scripts recursively"""
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test",
            steps=[{
                "action": "run_script",
                "script": "another_script.json"
            }],
            raw_content="{}"
        )
        
        with pytest.raises(ValueError, match="not allowed"):
            parser_tool.validate_script(script)
    
    # Format-specific validation
    
    def test_validate_json_specific_rules(self, parser_tool):
        """Test JSON-specific validation rules"""
        # JSON should have proper structure
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name=None,  # Missing name
            steps=[{"action": "test"}],
            raw_content="{}"
        )
        
        with pytest.raises(ValueError, match="JSON scripts must have a name"):
            parser_tool.validate_script(script)
    
    def test_validate_yaml_specific_rules(self, parser_tool):
        """Test YAML-specific validation rules"""
        # YAML should not have dangerous tags
        script = ParsedScript(
            format=ScriptFormat.YAML,
            name="Test",
            steps=[{"action": "test"}],
            raw_content="!!python/object/apply:os.system ['ls']"  # Dangerous YAML
        )
        
        with pytest.raises(ValueError, match="Unsafe YAML"):
            parser_tool.validate_script(script)
    
    def test_validate_text_specific_rules(self, parser_tool):
        """Test text format specific rules"""
        # Text commands should be simple
        script = ParsedScript(
            format=ScriptFormat.TEXT,
            name="Text Script",
            steps=[{"command": "rm -rf / --no-preserve-root"}],  # Dangerous
            raw_content="rm -rf /"
        )
        
        with pytest.raises(ValueError, match="Dangerous command"):
            parser_tool.validate_script(script)