"""Advanced unit tests for JSON to AST conversion - TDD RED phase tests."""

import pytest
import ast
import json
from typing import Dict, Any
import tempfile
import os

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestJSONToASTModernPythonFeatures:
    """Tests for modern Python features in JSON to AST conversion."""
    
    def test_walrus_operator_reconstruction(self):
        """Test reconstructing walrus operator (named expressions)."""
        json_data = {
            "node_type": "NamedExpr",
            "target": {
                "node_type": "Identifier",
                "name": "n",
                "ctx": "Store"
            },
            "value": {
                "node_type": "Call",
                "func": {"node_type": "Identifier", "name": "len", "ctx": "Load"},
                "args": [{"node_type": "Identifier", "name": "data", "ctx": "Load"}],
                "keywords": []
            }
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create ast.NamedExpr for n := len(data)
    
    def test_positional_only_args_reconstruction(self):
        """Test reconstructing positional-only arguments (Python 3.8+)."""
        json_data = {
            "node_type": "FunctionDef",
            "name": "func",
            "args": {
                "posonlyargs": [
                    {"node_type": "arg", "arg": "a", "annotation": None},
                    {"node_type": "arg", "arg": "b", "annotation": None}
                ],
                "args": [
                    {"node_type": "arg", "arg": "c", "annotation": None}
                ],
                "vararg": None,
                "kwonlyargs": [],
                "kw_defaults": [],
                "kwarg": None,
                "defaults": []
            },
            "body": [{"node_type": "Pass"}],
            "decorator_list": [],
            "returns": None
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create function with a, b, /, c signature
    
    def test_type_params_reconstruction(self):
        """Test reconstructing generic type parameters (Python 3.12+)."""
        json_data = {
            "node_type": "FunctionDef",
            "name": "first",
            "args": {
                "posonlyargs": [],
                "args": [
                    {
                        "node_type": "arg",
                        "arg": "items",
                        "annotation": {
                            "node_type": "Subscript",
                            "value": {"node_type": "Identifier", "name": "list", "ctx": "Load"},
                            "slice": {"node_type": "Identifier", "name": "T", "ctx": "Load"},
                            "ctx": "Load"
                        }
                    }
                ],
                "vararg": None,
                "kwonlyargs": [],
                "kw_defaults": [],
                "kwarg": None,
                "defaults": []
            },
            "body": [
                {
                    "node_type": "Return",
                    "value": {
                        "node_type": "Subscript",
                        "value": {"node_type": "Identifier", "name": "items", "ctx": "Load"},
                        "slice": {"node_type": "Constant", "value": 0},
                        "ctx": "Load"
                    }
                }
            ],
            "decorator_list": [],
            "returns": {"node_type": "Identifier", "name": "T", "ctx": "Load"},
            "type_params": []  # Would contain TypeVar info in real implementation
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
    
    def test_pattern_matching_reconstruction(self):
        """Test reconstructing complex pattern matching."""
        json_data = {
            "node_type": "Match",
            "subject": {"node_type": "Identifier", "name": "point", "ctx": "Load"},
            "cases": [
                {
                    "pattern": {
                        "node_type": "MatchClass",
                        "cls": {"node_type": "Identifier", "name": "Point", "ctx": "Load"},
                        "patterns": [],
                        "kwd_attrs": ["x", "y"],
                        "kwd_patterns": [
                            {"node_type": "MatchAs", "pattern": None, "name": "x"},
                            {"node_type": "MatchAs", "pattern": None, "name": "y"}
                        ]
                    },
                    "guard": {
                        "node_type": "Compare",
                        "left": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
                        "ops": ["Eq"],
                        "comparators": [{"node_type": "Identifier", "name": "y", "ctx": "Load"}]
                    },
                    "body": [
                        {
                            "node_type": "Return",
                            "value": {"node_type": "Constant", "value": "diagonal"}
                        }
                    ]
                }
            ]
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)


class TestJSONToASTErrorRecovery:
    """Tests for error recovery and graceful degradation."""
    
    def test_unknown_fields_ignored(self):
        """Test that unknown fields in JSON are ignored."""
        json_data = {
            "node_type": "Constant",
            "value": 42,
            "unknown_field": "should be ignored",
            "another_unknown": {"nested": "data"}
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create Constant node, ignoring unknown fields
    
    def test_partial_reconstruction(self):
        """Test partial reconstruction when some nodes fail."""
        json_data = {
            "node_type": "Module",
            "body": [
                {"node_type": "Pass"},  # Valid
                {"node_type": "InvalidNode", "data": "bad"},  # Invalid
                {"node_type": "Break"}  # Valid
            ]
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should handle partial failure gracefully
    
    def test_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        json_data = {
            "node_type": "FunctionDef",
            "name": "minimal",
            "args": {
                "posonlyargs": [],
                "args": [],
                "vararg": None,
                "kwonlyargs": [],
                "kw_defaults": [],
                "kwarg": None,
                "defaults": []
            },
            "body": [{"node_type": "Pass"}],
            # Missing optional fields: decorator_list, returns, type_comment
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should use defaults for missing optional fields
    
    def test_version_compatibility(self):
        """Test handling of version-specific features."""
        # Match statement (requires Python 3.10+)
        match_json = {
            "node_type": "Match",
            "subject": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
            "cases": []
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(match_json)
            # Should handle version compatibility


class TestJSONToASTComplexExpressions:
    """Tests for complex expression reconstruction."""
    
    def test_nested_comprehensions(self):
        """Test reconstructing nested comprehensions."""
        json_data = {
            "node_type": "ListComp",
            "elt": {
                "node_type": "ListComp",
                "elt": {
                    "node_type": "BinOp",
                    "left": {"node_type": "Identifier", "name": "i", "ctx": "Load"},
                    "op": "Mult",
                    "right": {"node_type": "Identifier", "name": "j", "ctx": "Load"}
                },
                "generators": [
                    {
                        "target": {"node_type": "Identifier", "name": "j", "ctx": "Store"},
                        "iter": {
                            "node_type": "Call",
                            "func": {"node_type": "Identifier", "name": "range", "ctx": "Load"},
                            "args": [{"node_type": "Constant", "value": 3}],
                            "keywords": []
                        },
                        "ifs": [],
                        "is_async": False
                    }
                ]
            },
            "generators": [
                {
                    "target": {"node_type": "Identifier", "name": "i", "ctx": "Store"},
                    "iter": {
                        "node_type": "Call",
                        "func": {"node_type": "Identifier", "name": "range", "ctx": "Load"},
                        "args": [{"node_type": "Constant", "value": 3}],
                        "keywords": []
                    },
                    "ifs": [],
                    "is_async": False
                }
            ]
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create [[i*j for j in range(3)] for i in range(3)]
    
    def test_lambda_with_complex_body(self):
        """Test reconstructing lambda with complex expressions."""
        json_data = {
            "node_type": "Lambda",
            "args": {
                "posonlyargs": [],
                "args": [
                    {"node_type": "arg", "arg": "x", "annotation": None},
                    {"node_type": "arg", "arg": "y", "annotation": None}
                ],
                "vararg": None,
                "kwonlyargs": [],
                "kw_defaults": [],
                "kwarg": None,
                "defaults": [{"node_type": "Constant", "value": 0}]
            },
            "body": {
                "node_type": "IfExp",
                "test": {
                    "node_type": "Compare",
                    "left": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
                    "ops": ["Gt"],
                    "comparators": [{"node_type": "Identifier", "name": "y", "ctx": "Load"}]
                },
                "body": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
                "orelse": {"node_type": "Identifier", "name": "y", "ctx": "Load"}
            }
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create lambda x, y=0: x if x > y else y
    
    def test_chained_comparisons(self):
        """Test reconstructing chained comparisons."""
        json_data = {
            "node_type": "Compare",
            "left": {"node_type": "Identifier", "name": "a", "ctx": "Load"},
            "ops": ["Lt", "Le", "Lt"],
            "comparators": [
                {"node_type": "Identifier", "name": "b", "ctx": "Load"},
                {"node_type": "Identifier", "name": "c", "ctx": "Load"},
                {"node_type": "Identifier", "name": "d", "ctx": "Load"}
            ]
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create a < b <= c < d
    
    def test_starred_expressions(self):
        """Test reconstructing starred expressions."""
        json_data = {
            "node_type": "List",
            "elts": [
                {"node_type": "Constant", "value": 1},
                {
                    "node_type": "Starred",
                    "value": {"node_type": "Identifier", "name": "rest", "ctx": "Load"},
                    "ctx": "Load"
                },
                {"node_type": "Constant", "value": 2}
            ],
            "ctx": "Load"
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create [1, *rest, 2]


class TestJSONToASTSpecialCases:
    """Tests for special cases and corner cases."""
    
    def test_empty_module(self):
        """Test reconstructing empty module."""
        json_data = {
            "node_type": "Module",
            "body": [],
            "type_ignores": []
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create empty module
    
    def test_single_expression_mode(self):
        """Test reconstructing single expression (eval mode)."""
        json_data = {
            "node_type": "Expression",
            "body": {
                "node_type": "BinOp",
                "left": {"node_type": "Constant", "value": 2},
                "op": "Add",
                "right": {"node_type": "Constant", "value": 2}
            }
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create Expression node for eval mode
    
    def test_interactive_mode(self):
        """Test reconstructing interactive mode AST."""
        json_data = {
            "node_type": "Interactive",
            "body": [
                {
                    "node_type": "Expr",
                    "value": {"node_type": "Constant", "value": 42}
                }
            ]
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create Interactive node
    
    def test_ellipsis_literal(self):
        """Test reconstructing ellipsis literal."""
        json_data = {
            "node_type": "Constant",
            "value": "..."  # Ellipsis might be represented as string
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should handle ellipsis correctly
    
    def test_bytes_literal(self):
        """Test reconstructing bytes literals."""
        json_data = {
            "node_type": "Constant",
            "value": "hello",
            "kind": "b"  # bytes literal
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create bytes constant
    
    def test_formatted_strings(self):
        """Test reconstructing f-strings."""
        json_data = {
            "node_type": "JoinedStr",
            "values": [
                {"node_type": "Constant", "value": "Hello, "},
                {
                    "node_type": "FormattedValue",
                    "value": {"node_type": "Identifier", "name": "name", "ctx": "Load"},
                    "conversion": -1,
                    "format_spec": None
                },
                {"node_type": "Constant", "value": "!"}
            ]
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should create f"Hello, {name}!"


class TestJSONToASTIntegration:
    """Integration tests for JSON to AST conversion."""
    
    def test_full_module_reconstruction(self):
        """Test reconstructing a complete module."""
        json_data = {
            "ast": {
                "node_type": "Module",
                "body": [
                    {
                        "node_type": "Import",
                        "names": [{"name": "sys", "asname": None}]
                    },
                    {
                        "node_type": "FunctionDef",
                        "name": "main",
                        "args": {"posonlyargs": [], "args": [], "vararg": None,
                                "kwonlyargs": [], "kw_defaults": [], "kwarg": None, "defaults": []},
                        "body": [
                            {
                                "node_type": "Expr",
                                "value": {
                                    "node_type": "Call",
                                    "func": {"node_type": "Identifier", "name": "print", "ctx": "Load"},
                                    "args": [{"node_type": "Constant", "value": "Hello"}],
                                    "keywords": []
                                }
                            }
                        ],
                        "decorator_list": [],
                        "returns": None
                    },
                    {
                        "node_type": "If",
                        "test": {
                            "node_type": "Compare",
                            "left": {"node_type": "Identifier", "name": "__name__", "ctx": "Load"},
                            "ops": ["Eq"],
                            "comparators": [{"node_type": "Constant", "value": "__main__"}]
                        },
                        "body": [
                            {
                                "node_type": "Expr",
                                "value": {
                                    "node_type": "Call",
                                    "func": {"node_type": "Identifier", "name": "main", "ctx": "Load"},
                                    "args": [],
                                    "keywords": []
                                }
                            }
                        ],
                        "orelse": []
                    }
                ],
                "type_ignores": []
            },
            "metadata": {
                "python_version": "3.12.0",
                "conversion_timestamp": "2024-01-01T00:00:00Z",
                "encoding": "utf-8"
            }
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_data)
            # Should reconstruct complete module
    
    def test_json_file_input(self, tmp_path):
        """Test loading JSON from file."""
        json_data = {
            "ast": {
                "node_type": "Module",
                "body": [{"node_type": "Pass"}]
            }
        }
        
        # Write JSON to file
        json_file = tmp_path / "ast.json"
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        
        with pytest.raises(NotImplementedError):
            # Test with file path
            result = PythonASTJSONTool.json_to_ast(str(json_file))
    
    def test_json_string_input(self):
        """Test parsing JSON from string."""
        json_string = '{"node_type": "Constant", "value": 42}'
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(json_string)
    
    def test_execute_method_integration(self):
        """Test integration with execute method."""
        tool = PythonASTJSONTool()
        
        # Test validation action
        with pytest.raises(NotImplementedError):
            validation_result = tool.execute(
                action="validate",
                json_data={"node_type": "Module", "body": []}
            )
        
        # Test from_json action
        with pytest.raises(NotImplementedError):
            conversion_result = tool.execute(
                action="from_json",
                json_data={"ast": {"node_type": "Module", "body": []}}
            )
    
    def test_error_reporting(self):
        """Test that errors include helpful information."""
        invalid_json = {
            "node_type": "FunctionDef"
            # Missing required fields
        }
        
        with pytest.raises(NotImplementedError):
            result = PythonASTJSONTool.json_to_ast(invalid_json)
            # Error should indicate what's missing