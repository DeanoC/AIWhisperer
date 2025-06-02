"""Advanced tests for Python AST parsing functionality."""

import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestAdvancedASTScenarios:
    """Tests for advanced AST parsing scenarios."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Get the path to test fixtures directory."""
        return Path(__file__).parent.parent.parent / "fixtures" / "python_ast_test_files"
    
    def test_parse_circular_import_handling(self, fixtures_dir, tmp_path):
        """Test handling of circular imports."""
        # Copy test file to tmp_path
        source_file = fixtures_dir / "circular_import.py"
        test_file = tmp_path / "circular_import.py"
        shutil.copy(source_file, test_file)
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        
        # Should parse without errors
        assert result["status"] == "success"
        assert "body" in result["data"]
    
    def test_parse_malformed_unicode(self):
        """Test handling of malformed unicode in code."""
        # Create code with unicode that might cause issues
        code = '''
# Test unicode handling
text = "Hello \\u0041\\u0042\\u0043"  # ABC
emoji = "😀🎉🐍"
'''
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        
        # Should handle unicode properly
        assert result["status"] == "success"
    
    def test_parse_highly_nested_data_structures(self, fixtures_dir, tmp_path):
        """Test parsing of very deeply nested data structures."""
        # Copy test file to tmp_path
        source_file = fixtures_dir / "nested_data.py"
        test_file = tmp_path / "nested_data.py"
        shutil.copy(source_file, test_file)
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        
        # Should handle deep nesting
        assert result["status"] == "success"
        # The AST should contain the deeply nested dictionary
        assert result["data"]["body"][0]["type"] == "Assign"