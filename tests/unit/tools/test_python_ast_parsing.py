"""Unit tests for Python AST parsing functionality."""

import pytest
import ast
import tempfile
import os
import sys
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestASTParsingFilePaths:
    """Tests for parsing Python files via file paths."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Get the path to test fixtures directory."""
        return Path(__file__).parent.parent.parent / "fixtures" / "python_ast_test_files"
    
    def test_parse_simple_python_file(self, fixtures_dir, tmp_path):
        """Test parsing a simple Python file."""
        # Copy test file to tmp_path
        source_file = fixtures_dir / "simple.py"
        test_file = tmp_path / "simple.py"
        shutil.copy(source_file, test_file)
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        
        # Verify basic structure
        assert result["status"] == "success"
        assert "data" in result
        assert result["data"]["type"] == "Module"
    
    def test_parse_file_with_functions(self, fixtures_dir, tmp_path):
        """Test parsing a file with function definitions."""
        # Copy test file to tmp_path
        source_file = fixtures_dir / "functions.py"
        test_file = tmp_path / "functions.py"
        shutil.copy(source_file, test_file)
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        
        # Verify functions are parsed
        assert result["status"] == "success"
        assert "body" in result["data"]
        assert len(result["data"]["body"]) == 2  # Two functions
        assert all(node["type"] == "FunctionDef" for node in result["data"]["body"])
    
    def test_parse_file_with_classes(self, fixtures_dir, tmp_path):
        """Test parsing a file with class definitions."""
        # Copy test file to tmp_path
        source_file = fixtures_dir / "classes.py"
        test_file = tmp_path / "classes.py"
        shutil.copy(source_file, test_file)
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        
        # Verify class is parsed
        assert result["status"] == "success"
        assert "body" in result["data"]
        assert len(result["data"]["body"]) == 1  # One class
        assert result["data"]["body"][0]["type"] == "ClassDef"
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="/nonexistent/file.py",
            source_type="file"
        )
        
        # Should return error status
        assert result["status"] == "error"
        assert "error" in result
    
    def test_parse_file_with_encoding(self, fixtures_dir, tmp_path):
        """Test parsing a file with specific encoding."""
        # Copy test file to tmp_path
        source_file = fixtures_dir / "encoded.py"
        test_file = tmp_path / "encoded.py"
        shutil.copy(source_file, test_file)
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        
        # Should handle UTF-8 encoding
        assert result["status"] == "success"
    
    def test_parse_relative_file_path(self, fixtures_dir, tmp_path):
        """Test parsing with relative file path."""
        # Copy test file to tmp_path
        source_file = fixtures_dir / "simple.py"
        test_file = tmp_path / "simple.py"
        shutil.copy(source_file, test_file)
        
        # Change to tmp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            tool = PythonASTJSONTool()
            result = tool.execute(
                action="to_json",
                source="simple.py",  # Relative path
                source_type="file"
            )
            
            assert result["status"] == "success"
        finally:
            os.chdir(original_cwd)


class TestASTParsingModules:
    """Tests for parsing Python modules via import paths."""
    
    def test_parse_module_with_submodule(self):
        """Test parsing a module with submodule."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="os.path",
            source_type="module"
        )
        
        # Should successfully parse os.path module
        assert result["status"] == "success"
        assert result["data"]["type"] == "Module"
    
    def test_parse_third_party_module(self):
        """Test parsing a third-party module."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="pytest",
            source_type="module"
        )
        
        # Should parse pytest module
        assert result["status"] == "success"
    
    def test_parse_nonexistent_module(self):
        """Test parsing a module that doesn't exist."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="nonexistent_module_xyz",
            source_type="module"
        )
        
        # Should return error
        assert result["status"] == "error"
    
    def test_parse_package_init(self):
        """Test parsing a package __init__.py file."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="json",
            source_type="module"
        )
        
        # Should parse json module
        assert result["status"] == "success"
    
    @staticmethod
    def test_module_to_json_static_method():
        """Test using module_to_json static method directly."""
        # This is a static method test
        from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool
        
        result = PythonASTJSONTool.module_to_json("os")
        assert result["status"] == "success"
        assert result["data"]["type"] == "Module"


class TestASTParsingCodeStrings:
    """Tests for parsing Python code strings."""
    
    def test_parse_multiline_code_string(self):
        """Test parsing multiline code string."""
        code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(result)
'''
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        
        assert result["status"] == "success"
        assert len(result["data"]["body"]) == 3  # function def, assignment, print
    
    def test_parse_empty_code_string(self):
        """Test parsing empty code string."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="",
            source_type="code"
        )
        
        # Empty code should still parse successfully
        assert result["status"] == "success"
        assert result["data"]["body"] == []


class TestASTNodeStructure:
    """Tests for verifying AST node structure."""
    
    def test_verify_class_node_structure(self):
        """Test that class nodes have expected structure."""
        code = '''
class MyClass:
    def method(self):
        pass
'''
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        
        class_node = result["data"]["body"][0]
        assert class_node["type"] == "ClassDef"
        assert "name" in class_node
        assert "body" in class_node
        assert "bases" in class_node
        assert "decorator_list" in class_node
    
    def test_verify_comprehension_node_structure(self):
        """Test list comprehension node structure."""
        code = "[x * 2 for x in range(10) if x % 2 == 0]"
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        
        # Should have ListComp in expression
        expr_node = result["data"]["body"][0]
        assert expr_node["type"] == "Expr"
        assert expr_node["value"]["type"] == "ListComp"


class TestASTParsingEdgeCases:
    """Tests for edge cases and complex scenarios."""
    
    def test_parse_deeply_nested_code(self):
        """Test parsing deeply nested code structures."""
        code = '''
def outer():
    def middle():
        def inner():
            for i in range(10):
                if i > 5:
                    while True:
                        try:
                            with open('file') as f:
                                return f.read()
                        except:
                            break
'''
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        
        # Should parse without errors
        assert result["status"] == "success"
    
    def test_parse_unicode_identifiers(self):
        """Test parsing unicode identifiers."""
        code = '''
λ = lambda x: x * 2
π = 3.14159
'''
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        
        # Should handle unicode identifiers
        assert result["status"] == "success"
        assert len(result["data"]["body"]) == 2
    
    def test_parse_complex_expressions(self):
        """Test parsing complex expressions."""
        code = '''
result = (lambda x: x ** 2)(5) + [i for i in range(10)][5] + {'a': 1}.get('a', 0)
'''
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        
        # Should parse complex expression
        assert result["status"] == "success"
    
    def test_parse_file_with_different_newlines(self, tmp_path):
        """Test parsing files with different newline styles."""
        # Create file with Windows-style newlines
        test_file = tmp_path / "windows_newlines.py"
        test_file.write_bytes(b"x = 1\r\ny = 2\r\nprint(x + y)\r\n")
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        
        # Should handle different newline styles
        assert result["status"] == "success"
        assert len(result["data"]["body"]) == 3