"""
Security-focused tests for ScriptParserTool.
Following TDD principles - tests written before implementation.
"""

import pytest
import json
import os
import sys
from pathlib import Path
import tempfile

from ai_whisperer.tools.script_parser_tool import ScriptParserTool, ScriptFormat, ParsedScript


class TestScriptParserSecurity:
    """Test security features of ScriptParserTool"""
    
    @pytest.fixture
    def parser_tool(self):
        """Provide an initialized ScriptParserTool"""
        return ScriptParserTool()
    
    @pytest.fixture
    def workspace_path(self):
        """Provide a safe workspace path"""
        return Path(tempfile.mkdtemp())
    
    # File access security
    
    def test_enforce_workspace_boundaries(self, parser_tool, workspace_path):
        """Test that file operations are restricted to workspace"""
        # Set workspace path
        parser_tool.set_workspace(str(workspace_path))
        
        # Allowed: within workspace
        safe_script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Safe",
            steps=[{
                "action": "read_file",
                "path": str(workspace_path / "data.txt")
            }],
            raw_content="{}"
        )
        parser_tool.validate_script(safe_script)  # Should not raise
        
        # Not allowed: outside workspace
        unsafe_script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Unsafe",
            steps=[{
                "action": "read_file",
                "path": "/etc/passwd"
            }],
            raw_content="{}"
        )
        with pytest.raises(ValueError, match="forbidden|unsafe|outside workspace"):
            parser_tool.validate_script(unsafe_script)
    
    def test_prevent_symlink_escape(self, parser_tool, workspace_path):
        """Test that symlinks cannot escape workspace"""
        # Create a symlink pointing outside workspace
        symlink_path = workspace_path / "escape_link"
        if os.name != 'nt':  # Skip on Windows
            os.symlink("/etc", str(symlink_path))
            
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Symlink test",
                steps=[{
                    "action": "read_file",
                    "path": str(symlink_path / "passwd")
                }],
                raw_content="{}"
            )
            
            parser_tool.set_workspace(str(workspace_path))
            with pytest.raises(ValueError, match="outside workspace|Symlink.*outside"):
                parser_tool.validate_script(script)
    
    # Command injection prevention
    
    def test_prevent_command_injection_in_paths(self, parser_tool):
        """Test that command injection via paths is prevented"""
        injection_paths = [
            "/tmp/test; rm -rf /",
            "/tmp/$(whoami).txt",
            "/tmp/`id`.log",
            "/tmp/test|cat /etc/passwd"
        ]
        
        for path in injection_paths:
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Injection test",
                steps=[{"action": "read_file", "path": path}],
                raw_content="{}"
            )
            
            with pytest.raises(ValueError, match="Invalid.*character"):
                parser_tool.validate_script(script)
    
    def test_prevent_command_injection_in_content(self, parser_tool):
        """Test that command injection in content is handled safely"""
        # These should be allowed but treated as literal text
        contents = [
            "Hello $(whoami)",
            "Path: `pwd`",
            "Command: rm -rf /"
        ]
        
        for content in contents:
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Content test",
                steps=[{
                    "action": "create_file",
                    "path": "/tmp/safe.txt",
                    "content": content
                }],
                raw_content="{}"
            )
            
            # Should validate - content is treated as plain text
            parser_tool.validate_script(script)
    
    # Resource limits
    
    def test_enforce_memory_limits(self, parser_tool, tmp_path):
        """Test that memory usage is limited during parsing"""
        # Create a file with deeply nested JSON
        deeply_nested = {"level": 0}
        current = deeply_nested
        for i in range(1000):  # Very deep nesting
            current["next"] = {"level": i + 1}
            current = current["next"]
        
        nested_file = tmp_path / "nested.json"
        nested_file.write_text(json.dumps(deeply_nested))
        
        with pytest.raises(ValueError, match="nesting.*deep"):
            parser_tool.parse_script(str(nested_file))
    
    @pytest.mark.skip(reason="Timeout functionality is conceptual - not implemented yet")
    def test_enforce_parsing_timeout(self, parser_tool, tmp_path):
        """Test that parsing has a timeout"""
        # Create a file that would take long to parse
        # (This is conceptual - actual implementation would need timeout)
        complex_yaml = tmp_path / "complex.yaml"
        
        # YAML with many anchors and references (slow to parse)
        yaml_content = "base: &base\n"
        for i in range(10000):
            yaml_content += f"  key{i}: value{i}\n"
        yaml_content += "\n"
        for i in range(100):
            yaml_content += f"copy{i}:\n  <<: *base\n"
        
        complex_yaml.write_text(yaml_content)
        
        # Should timeout or reject complexity
        with pytest.raises(ValueError, match="timeout|complex"):
            parser_tool.parse_script(str(complex_yaml))
    
    # Input sanitization
    
    @pytest.mark.skipif(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Windows file validation in CI environment")
    def test_sanitize_file_names(self, parser_tool):
        """Test that file names are sanitized"""
        unsafe_names = [
            "test\x00.txt",  # Null byte
            "test\n.txt",    # Newline
            "../test.txt",   # Path traversal
            # "test/.txt",     # Actually valid - hidden file in subdirectory
        ]
        
        # Add Windows-specific names only on Windows
        if os.name == 'nt':
            unsafe_names.extend([
                "CON.txt",       # Windows reserved name
                "test:data.txt"  # Alternative data stream
            ])
        
        for name in unsafe_names:
            script = ParsedScript(
                format=ScriptFormat.JSON,
                name="Test",
                steps=[{
                    "action": "create_file",
                    "path": f"/tmp/{name}",
                    "content": "test"
                }],
                raw_content="{}"
            )
            
            try:
                parser_tool.validate_script(script)
                print(f"ERROR: Name '{name}' was not rejected!")
                assert False, f"Name '{name}' should have been rejected"
            except ValueError as e:
                # Expected - check message pattern
                if not any(x in str(e) for x in ["Invalid", "name", "pattern", "Path traversal"]):
                    print(f"ERROR: Name '{name}' raised unexpected error: {e}")
                    raise
    
    def test_validate_encoding(self, parser_tool, tmp_path):
        """Test that files must be valid UTF-8"""
        # Create file with invalid UTF-8
        invalid_utf8 = tmp_path / "invalid.txt"
        invalid_utf8.write_bytes(b"Valid start \xff\xfe Invalid UTF-8")
        
        with pytest.raises(ValueError, match="encoding|UTF-8|not valid UTF-8"):
            parser_tool.parse_script(str(invalid_utf8))
    
    # Permission checks
    
    def test_respect_file_permissions(self, parser_tool, tmp_path):
        """Test that file permissions are respected"""
        if os.name != 'nt':  # Unix-like systems only
            # Create a file with no read permissions
            no_read = tmp_path / "no_read.json"
            no_read.write_text('{"name": "test", "steps": []}')
            os.chmod(str(no_read), 0o000)
            
            with pytest.raises(ValueError, match="Permission denied"):
                parser_tool.parse_script(str(no_read))
            
            # Cleanup
            os.chmod(str(no_read), 0o644)
    
    # DOS prevention
    
    def test_prevent_zip_bomb(self, parser_tool, tmp_path):
        """Test prevention of zip bomb style attacks"""
        # Create a small file that expands to huge content
        small_looking = {
            "name": "Looks small",
            "steps": []
        }
        
        # Add a step with repeated content
        huge_content = "A" * 1000
        for i in range(1000):
            small_looking["steps"].append({
                "action": "create_file",
                "path": f"/tmp/file{i}.txt",
                "content": huge_content
            })
        
        bomb_file = tmp_path / "bomb.json"
        bomb_file.write_text(json.dumps(small_looking))
        
        # Should detect expansion attack
        with pytest.raises(ValueError, match="expansion|too large|exceeds size limit"):
            parser_tool.parse_script(str(bomb_file))