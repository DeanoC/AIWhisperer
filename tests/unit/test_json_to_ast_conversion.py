"""Unit tests for JSON to AST conversion - TDD RED phase tests."""

import pytest
import ast
import json
from typing import Dict, Any

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestJSONToASTBasicReconstruction:
    """Tests for basic AST reconstruction from JSON."""
    
    def test_reconstruct_simple_module(self):
        """Test reconstructing a simple module from JSON."""
        json_data = {
            "ast": {
                "node_type": "Module",
                "body": [
                    {
                        "node_type": "Assign",
                        "targets": [
                            {
                                "node_type": "Identifier",
                                "name": "x",
                                "ctx": "Store"
                            }
                        ],
                        "value": {
                            "node_type": "Constant",
                            "value": 42
                        }
                    }
                ],
                "type_ignores": []
            },
            "metadata": {
                "python_version": "3.12.0",
                "conversion_timestamp": "2024-01-01T00:00:00",
                "encoding": "utf-8"
            }
        }
        
        result = PythonASTJSONTool.json_to_ast(json_data)
        # When implemented, should verify:
        # - result is an ast.Module
        # - has one statement (Assign)
        # - target is Name with id='x'
        # - value is Constant with value=42
    
def test_reconstruct_function_def(self):
    """Test reconstructing a function definition from JSON."""
    json_data = {
        "node_type": "FunctionDef",
        "name": "greet",
        "args": {
            "posonlyargs": [],
            "args": [
                {
                    "node_type": "arg",
                    "arg": "name",
                    "annotation": {
                        "node_type": "Identifier",
                        "name": "str",
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
                    "node_type": "JoinedStr",
                    "values": [
                        {
                            "node_type": "Constant",
                            "value": "Hello, "
                        },
                        {
                            "node_type": "FormattedValue",
                            "value": {
                                "node_type": "Identifier",
                                "name": "name",
                                "ctx": "Load"
                            },
                            "conversion": -1,
                            "format_spec": None
                        }
                    ]
                }
            }
        ],
        "decorator_list": [],
        "returns": {
            "node_type": "Identifier",
            "name": "str",
            "ctx": "Load"
        }
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # Should create a FunctionDef node with proper structure
    
def test_reconstruct_class_def(self):
    """Test reconstructing a class definition from JSON."""
    json_data = {
        "node_type": "ClassDef",
        "name": "Person",
        "bases": [],
        "keywords": [],
        "body": [
            {
                "node_type": "FunctionDef",
                "name": "__init__",
                "args": {
                    "posonlyargs": [],
                    "args": [
                        {"node_type": "arg", "arg": "self", "annotation": None},
                        {"node_type": "arg", "arg": "name", "annotation": None}
                    ],
                    "vararg": None,
                    "kwonlyargs": [],
                    "kw_defaults": [],
                    "kwarg": None,
                    "defaults": []
                },
                "body": [
                    {
                        "node_type": "Assign",
                        "targets": [
                            {
                                "node_type": "Attribute",
                                "value": {
                                    "node_type": "Identifier",
                                    "name": "self",
                                    "ctx": "Load"
                                },
                                "attr": "name",
                                "ctx": "Store"
                            }
                        ],
                        "value": {
                            "node_type": "Identifier",
                            "name": "name",
                            "ctx": "Load"
                        }
                    }
                ],
                "decorator_list": [],
                "returns": None
            }
        ],
        "decorator_list": []
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_reconstruct_with_location_info(self):
    """Test that location information is preserved during reconstruction."""
    json_data = {
        "node_type": "Assign",
        "location": {
            "lineno": 5,
            "col_offset": 4,
            "end_lineno": 5,
            "end_col_offset": 10
        },
        "targets": [
            {
                "node_type": "Identifier",
                "name": "x",
                "ctx": "Store",
                "location": {"lineno": 5, "col_offset": 4}
            }
        ],
        "value": {
            "node_type": "Constant",
            "value": 42,
            "location": {"lineno": 5, "col_offset": 8}
        }
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # When implemented, should verify location info is preserved

class TestJSONToASTComplexStructures:
    """Tests for reconstructing complex AST structures from JSON."""
    
    def test_reconstruct_nested_expressions(self):
        """Test reconstructing nested expressions."""
        json_data = {
            "node_type": "BinOp",
            "left": {
                "node_type": "BinOp",
                "left": {"node_type": "Identifier", "name": "a", "ctx": "Load"},
                "op": "Add",
                "right": {"node_type": "Identifier", "name": "b", "ctx": "Load"}
            },
            "op": "Mult",
            "right": {
                "node_type": "BinOp",
                "left": {"node_type": "Identifier", "name": "c", "ctx": "Load"},
                "op": "Sub",
                "right": {"node_type": "Identifier", "name": "d", "ctx": "Load"}
            }
        }
        
        result = PythonASTJSONTool.json_to_ast(json_data)
        # Should create (a + b) * (c - d)
    
def test_reconstruct_comprehensions(self):
    """Test reconstructing various comprehensions."""
    # List comprehension
    list_comp_json = {
        "node_type": "ListComp",
        "elt": {
            "node_type": "BinOp",
            "left": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
            "op": "Mult",
            "right": {"node_type": "Constant", "value": 2}
        },
        "generators": [
            {
                "target": {"node_type": "Identifier", "name": "x", "ctx": "Store"},
                "iter": {
                    "node_type": "Call",
                    "func": {"node_type": "Identifier", "name": "range", "ctx": "Load"},
                    "args": [{"node_type": "Constant", "value": 10}],
                    "keywords": []
                },
                "ifs": [
                    {
                        "node_type": "Compare",
                        "left": {
                            "node_type": "BinOp",
                            "left": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
                            "op": "Mod",
                            "right": {"node_type": "Constant", "value": 2}
                        },
                        "ops": ["Eq"],
                        "comparators": [{"node_type": "Constant", "value": 0}]
                    }
                ],
                "is_async": False
            }
        ]
    }
        
    result = PythonASTJSONTool.json_to_ast(list_comp_json)
    
def test_reconstruct_control_flow(self):
    """Test reconstructing control flow structures."""
    if_json = {
        "node_type": "If",
        "test": {
            "node_type": "Compare",
            "left": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
            "ops": ["Gt"],
            "comparators": [{"node_type": "Constant", "value": 0}]
        },
        "body": [
            {
                "node_type": "Expr",
                "value": {
                    "node_type": "Call",
                    "func": {"node_type": "Identifier", "name": "print", "ctx": "Load"},
                    "args": [{"node_type": "Constant", "value": "positive"}],
                    "keywords": []
                }
            }
        ],
        "orelse": [
            {
                "node_type": "Expr",
                "value": {
                    "node_type": "Call",
                    "func": {"node_type": "Identifier", "name": "print", "ctx": "Load"},
                    "args": [{"node_type": "Constant", "value": "non-positive"}],
                    "keywords": []
                }
            }
        ]
    }
        
    result = PythonASTJSONTool.json_to_ast(if_json)
    
def test_reconstruct_match_statement(self):
    """Test reconstructing match statements (Python 3.10+)."""
    match_json = {
        "node_type": "Match",
        "subject": {"node_type": "Identifier", "name": "command", "ctx": "Load"},
        "cases": [
            {
                "pattern": {
                    "node_type": "MatchSequence",
                    "patterns": [
                        {"node_type": "MatchValue", "value": {"node_type": "Constant", "value": "move"}},
                        {"node_type": "MatchAs", "pattern": None, "name": "x"},
                        {"node_type": "MatchAs", "pattern": None, "name": "y"}
                    ]
                },
                "guard": None,
                "body": [
                    {
                        "node_type": "Expr",
                        "value": {
                            "node_type": "Call",
                            "func": {"node_type": "Identifier", "name": "move_to", "ctx": "Load"},
                            "args": [
                                {"node_type": "Identifier", "name": "x", "ctx": "Load"},
                                {"node_type": "Identifier", "name": "y", "ctx": "Load"}
                            ],
                            "keywords": []
                        }
                    }
                ]
            },
            {
                "pattern": {"node_type": "MatchAs", "pattern": None, "name": None},
                "guard": None,
                "body": [{"node_type": "Pass"}]
            }
        ]
    }
        
    result = PythonASTJSONTool.json_to_ast(match_json)
    
def test_reconstruct_async_constructs(self):
    """Test reconstructing async/await constructs."""
    async_func_json = {
        "node_type": "AsyncFunctionDef",
        "name": "fetch_data",
        "args": {
            "posonlyargs": [],
            "args": [],
            "vararg": None,
            "kwonlyargs": [],
            "kw_defaults": [],
            "kwarg": None,
            "defaults": []
        },
        "body": [
            {
                "node_type": "AsyncWith",
                "items": [
                    {
                        "context_expr": {
                            "node_type": "Call",
                            "func": {"node_type": "Identifier", "name": "session", "ctx": "Load"},
                            "args": [],
                            "keywords": []
                        },
                        "optional_vars": {"node_type": "Identifier", "name": "s", "ctx": "Store"}
                    }
                ],
                "body": [
                    {
                        "node_type": "Return",
                        "value": {
                            "node_type": "Await",
                            "value": {
                                "node_type": "Call",
                                "func": {
                                    "node_type": "Attribute",
                                    "value": {"node_type": "Identifier", "name": "s", "ctx": "Load"},
                                    "attr": "get",
                                    "ctx": "Load"
                                },
                                "args": [{"node_type": "Identifier", "name": "url", "ctx": "Load"}],
                                "keywords": []
                            }
                        }
                    }
                ]
            }
        ],
        "decorator_list": [],
        "returns": None
    }
        
    result = PythonASTJSONTool.json_to_ast(async_func_json)

class TestJSONValidation:
    """Tests for JSON validation before conversion."""
    
    def test_validate_missing_node_type(self):
        """Test validation fails when node_type is missing."""
        json_data = {
            "name": "x",
            "ctx": "Load"
            # Missing node_type
        }
        
        result = PythonASTJSONTool.json_to_ast(json_data)
        # Should raise validation error about missing node_type
    
def test_validate_invalid_node_type(self):
    """Test validation fails for invalid node types."""
    json_data = {
        "node_type": "InvalidNodeType",
        "value": 42
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # Should raise validation error about invalid node type
    
def test_validate_missing_required_fields(self):
    """Test validation fails when required fields are missing."""
    # FunctionDef missing required 'name' field
    json_data = {
        "node_type": "FunctionDef",
        # Missing 'name'
        "args": {"posonlyargs": [], "args": [], "vararg": None, 
                "kwonlyargs": [], "kw_defaults": [], "kwarg": None, "defaults": []},
        "body": [{"node_type": "Pass"}],
        "decorator_list": []
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_validate_incorrect_field_types(self):
    """Test validation fails for incorrect field types."""
    json_data = {
        "node_type": "Constant",
        "value": {"nested": "object"}  # Should be a simple value
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_validate_action_parameter(self):
    """Test validation through the execute method."""
    tool = PythonASTJSONTool()
        
    result = tool.execute(
            action="validate",
            json_data={"node_type": "Module", "body": []}
        )
    
def test_validate_with_schema(self):
    """Test validation against the full schema."""
    # Valid module structure
    valid_json = {
        "ast": {
            "node_type": "Module",
            "body": [],
            "type_ignores": []
        },
        "metadata": {
            "python_version": "3.12.0",
            "conversion_timestamp": "2024-01-01T00:00:00Z",
            "encoding": "utf-8"
        }
    }
        
    result = PythonASTJSONTool.validate_ast_json(valid_json)
        # Should return success
        
    # Invalid structure
    invalid_json = {
        "ast": {
            "node_type": "Module"
            # Missing required 'body' field
        }
    }
        
    result = PythonASTJSONTool.validate_ast_json(invalid_json)
        # Should return validation errors

class TestMalformedJSONHandling:
    """Tests for handling malformed JSON gracefully."""
    
    def test_handle_non_dict_input(self):
        """Test handling non-dictionary JSON input."""
        result = PythonASTJSONTool.json_to_ast("not a dict")
        # Should raise appropriate error
        
    result = PythonASTJSONTool.json_to_ast(42)
        # Should raise appropriate error
        
    result = PythonASTJSONTool.json_to_ast(["list", "input"])
        # Should raise appropriate error
    
def test_handle_circular_references(self):
    """Test handling JSON with circular references."""
    # Note: True circular references can't exist in JSON,
    # but we can test recursive structures
    json_data = {
        "node_type": "BinOp",
        "left": {"node_type": "Identifier", "name": "x", "ctx": "Load"},
        "op": "Add",
        "right": {
            "node_type": "BinOp",
            "left": {"node_type": "Identifier", "name": "y", "ctx": "Load"},
            "op": "Add",
            "right": {
                "node_type": "BinOp",
                # Very deep nesting...
                "left": {"node_type": "Identifier", "name": "z", "ctx": "Load"},
                "op": "Add",
                "right": {"node_type": "Constant", "value": 1}
            }
        }
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # Should handle deep nesting gracefully
    
def test_handle_null_values(self):
    """Test handling null/None values in JSON."""
    json_data = {
        "node_type": "FunctionDef",
        "name": "test",
        "args": {
            "posonlyargs": [],
            "args": [],
            "vararg": None,  # Explicit None
            "kwonlyargs": [],
            "kw_defaults": [],
            "kwarg": None,
            "defaults": []
        },
        "body": [{"node_type": "Pass"}],
        "decorator_list": [],
        "returns": None  # Explicit None
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_handle_empty_structures(self):
    """Test handling empty lists and objects."""
    json_data = {
        "node_type": "Module",
        "body": [],  # Empty body
        "type_ignores": []
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_handle_mixed_types_in_lists(self):
    """Test handling lists with mixed types."""
    json_data = {
        "node_type": "Module",
        "body": [
            {"node_type": "Pass"},
            None,  # Invalid: None in body list
            "string"  # Invalid: string in body list
        ]
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # Should raise validation error

class TestASTNodeTypeCorrectness:
    """Tests to verify correct AST node types are created."""
    
    def test_correct_expression_node_types(self):
        """Test that expression nodes are created with correct types."""
        test_cases = [
            ({"node_type": "Constant", "value": 42}, ast.Constant),
            ({"node_type": "Identifier", "name": "x", "ctx": "Load"}, ast.Name),
            ({"node_type": "List", "elts": [], "ctx": "Load"}, ast.List),
            ({"node_type": "Dict", "keys": [], "values": []}, ast.Dict),
            ({"node_type": "Set", "elts": []}, ast.Set),
            ({"node_type": "Tuple", "elts": [], "ctx": "Load"}, ast.Tuple),
        ]
        
        for json_data, expected_type in test_cases:
                        result = PythonASTJSONTool.json_to_ast(json_data)
            # When implemented, should verify isinstance(result, expected_type)
    
def test_correct_statement_node_types(self):
    """Test that statement nodes are created with correct types."""
    test_cases = [
        ({"node_type": "Pass"}, ast.Pass),
        ({"node_type": "Break"}, ast.Break),
        ({"node_type": "Continue"}, ast.Continue),
        ({"node_type": "Return", "value": None}, ast.Return),
        ({"node_type": "Global", "names": ["x"]}, ast.Global),
        ({"node_type": "Nonlocal", "names": ["x"]}, ast.Nonlocal),
    ]
        
    for json_data, expected_type in test_cases:
        result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_correct_operator_types(self):
    """Test that operators are converted correctly."""
    json_data = {
        "node_type": "BinOp",
        "left": {"node_type": "Constant", "value": 1},
        "op": "Add",
        "right": {"node_type": "Constant", "value": 2}
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # When implemented, should verify:
        # - isinstance(result.op, ast.Add)
    
def test_correct_context_types(self):
    """Test that contexts (Load, Store, Del) are handled correctly."""
    test_cases = [
        ("Load", ast.Load),
        ("Store", ast.Store),
        ("Del", ast.Del),
    ]
        
    for ctx_name, expected_type in test_cases:
        json_data = {
            "node_type": "Identifier",
            "name": "x",
            "ctx": ctx_name
        }
            
        result = PythonASTJSONTool.json_to_ast(json_data)
            # When implemented, should verify context type
    
def test_identifier_node_conversion(self):
    """Test that 'Identifier' nodes are converted to ast.Name."""
    json_data = {
        "node_type": "Identifier",
        "name": "variable",
        "ctx": "Load"
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # Should create ast.Name, not ast.Identifier

class TestJSONToASTEdgeCases:
    """Tests for edge cases in JSON to AST conversion."""
    
    def test_empty_function_body(self):
        """Test function with empty body (should add Pass)."""
        json_data = {
            "node_type": "FunctionDef",
            "name": "empty",
            "args": {
                "posonlyargs": [], "args": [], "vararg": None,
                "kwonlyargs": [], "kw_defaults": [], "kwarg": None, "defaults": []
            },
            "body": [],  # Empty body
            "decorator_list": [],
            "returns": None
        }
        
        result = PythonASTJSONTool.json_to_ast(json_data)
        # Should handle empty body appropriately
    
def test_special_string_values(self):
    """Test handling of special string values."""
    test_strings = [
        "",  # Empty string
        "\\n\\t\\r",  # Escape sequences
        "🐍",  # Unicode
        "\"quotes\"",  # Quotes
        "'single'",  # Single quotes
    ]
        
    for string_val in test_strings:
        json_data = {
            "node_type": "Constant",
            "value": string_val
        }
            
        result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_large_numbers(self):
    """Test handling of various number types."""
    test_numbers = [
        0,
        -1,
        1.5,
        -3.14,
        1e10,
        float('inf'),
        float('-inf'),
        # float('nan'),  # NaN might need special handling
    ]
        
    for num in test_numbers:
        json_data = {
            "node_type": "Constant",
            "value": num
        }
            
        result = PythonASTJSONTool.json_to_ast(json_data)
    
def test_docstring_handling(self):
    """Test that docstrings in JSON are handled correctly."""
    json_data = {
        "node_type": "FunctionDef",
        "name": "documented",
        "args": {"posonlyargs": [], "args": [], "vararg": None,
                "kwonlyargs": [], "kw_defaults": [], "kwarg": None, "defaults": []},
        "body": [{"node_type": "Pass"}],
        "decorator_list": [],
        "returns": None,
        "docstring": "This is a docstring"
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # Should handle docstring field appropriately
    
def test_type_comment_preservation(self):
    """Test that type comments are preserved."""
    json_data = {
        "node_type": "Assign",
        "targets": [{"node_type": "Identifier", "name": "x", "ctx": "Store"}],
        "value": {"node_type": "Constant", "value": 42},
        "type_comment": "int"
    }
        
    result = PythonASTJSONTool.json_to_ast(json_data)
        # Should preserve type_comment

class TestJSONToASTWithExecuteMethod:
    """Tests for JSON to AST conversion through execute method."""
    
    def test_execute_from_json_action(self):
        """Test the from_json action in execute method."""
        tool = PythonASTJSONTool()
        
        json_data = {
            "ast": {
                "node_type": "Module",
                "body": [
                    {
                        "node_type": "Expr",
                        "value": {
                            "node_type": "Constant",
                            "value": "Hello, World!"
                        }
                    }
                ]
            },
            "metadata": {
                "python_version": "3.12.0",
                "conversion_timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        result = tool.execute(
                action="from_json",
                json_data=json_data
            )
            # Should return Python code
    
    def test_execute_from_json_with_string_input(self):
        """Test from_json with JSON string instead of dict."""
        tool = PythonASTJSONTool()
        
        json_string = '{"node_type": "Module", "body": []}'
        
        result = tool.execute(
                action="from_json",
                json_data=json_string
            )
    
    def test_execute_from_json_with_file_path(self):
        """Test from_json with path to JSON file."""
        tool = PythonASTJSONTool()
        
        result = tool.execute(
                action="from_json",
                json_data="/path/to/ast.json"
            )
    
    def test_json_to_code_static_method(self):
        """Test the json_to_code static method."""
        json_data = {
            "ast": {
                "node_type": "Module",
                "body": [
                    {
                        "node_type": "Assign",
                        "targets": [{"node_type": "Identifier", "name": "x", "ctx": "Store"}],
                        "value": {"node_type": "Constant", "value": 42}
                    }
                ]
            }
        }
        
        result = PythonASTJSONTool.json_to_code(json_data)
            # Should return "x = 42"
    
    def test_validate_before_conversion(self):
        """Test that validation happens before conversion."""
        invalid_json = {
            "node_type": "InvalidType",
            "value": "test"
        }
        
        result = PythonASTJSONTool.json_to_ast(invalid_json)
            # Should fail validation before attempting conversion