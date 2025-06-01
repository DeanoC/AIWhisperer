"""Python AST to JSON converter tool.

This tool provides functionality to convert Python Abstract Syntax Trees (AST)
to JSON representation and back, supporting both file paths and module names.
"""

import ast
import json
import sys
import os
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timezone

from .base_tool import AITool


class PythonASTJSONTool(AITool):
    """Tool for converting Python code to AST JSON representation and back."""
    
    def __init__(self):
        super().__init__()
        self._schema_path = Path(__file__).parent.parent.parent / "schemas" / "python_ast_schema.json"
        
    @property
    def name(self) -> str:
        return "python_ast_json"
    
    @property
    def description(self) -> str:
        return "Convert Python code to AST JSON representation and back"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["to_json", "from_json", "validate"],
                    "description": "The conversion action to perform"
                },
                "source": {
                    "type": "string",
                    "description": "File path, module name, or Python code (for to_json)"
                },
                "json_data": {
                    "type": ["string", "object"],
                    "description": "JSON data or path to JSON file (for from_json)"
                },
                "source_type": {
                    "type": "string",
                    "enum": ["file", "module", "code"],
                    "default": "file",
                    "description": "Type of source input"
                },
                "include_metadata": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include metadata in the output"
                },
                "format_output": {
                    "type": "boolean", 
                    "default": True,
                    "description": "Whether to format the output JSON"
                }
            },
            "required": ["action"],
            "allOf": [
                {
                    "if": {"properties": {"action": {"const": "to_json"}}},
                    "then": {"required": ["source"]}
                },
                {
                    "if": {"properties": {"action": {"const": "from_json"}}},
                    "then": {"required": ["json_data"]}
                },
                {
                    "if": {"properties": {"action": {"const": "validate"}}},
                    "then": {"required": ["json_data"]}
                }
            ]
        }
    
    @property
    def category(self) -> str:
        return "Code Analysis"
    
    @property
    def tags(self) -> List[str]:
        return ["analysis", "python", "ast", "json", "code_structure", "parser"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """Use this tool to:
1. Convert Python code to AST JSON representation
2. Convert AST JSON back to Python code
3. Validate AST JSON against the schema

The tool supports:
- File paths (relative or absolute)
- Module names (e.g., 'os.path', 'json')
- Direct Python code strings
- Bidirectional conversion with metadata preservation
- Schema validation

Example uses:
- Analyze code structure: action="to_json", source="path/to/file.py"
- Convert module: action="to_json", source="json", source_type="module"
- Reconstruct code: action="from_json", json_data=<ast_json>
- Validate structure: action="validate", json_data=<ast_json>
"""
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the AST to JSON conversion based on the action."""
        action = kwargs.get("action")
        
        if action == "to_json":
            return self._python_to_json(**kwargs)
        elif action == "from_json":
            return self._json_to_python(**kwargs)
        elif action == "validate":
            return self._validate_json(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _python_to_json(self, **kwargs) -> Dict[str, Any]:
        """Convert Python code/file/module to AST JSON representation."""
        source = kwargs.get("source")
        source_type = kwargs.get("source_type", "file")
        include_metadata = kwargs.get("include_metadata", True)
        format_output = kwargs.get("format_output", True)
        
        try:
            # Parse based on source type
            if source_type == "file":
                # For file paths, convert to Path object
                file_path = Path(source)
                
                # If it's not absolute, make it relative to current directory
                if not file_path.is_absolute():
                    file_path = Path.cwd() / file_path
                
                resolved_path = file_path
                
                if not resolved_path.exists():
                    return {"error": f"File not found: {source}"}
                
                # Read file content
                try:
                    with open(resolved_path, 'r', encoding='utf-8') as f:
                        code_content = f.read()
                    source_file = str(resolved_path)
                except UnicodeDecodeError:
                    # Try with different encodings
                    for encoding in ['latin-1', 'cp1252']:
                        try:
                            with open(resolved_path, 'r', encoding=encoding) as f:
                                code_content = f.read()
                            break
                        except:
                            continue
                    else:
                        return {"error": f"Unable to decode file: {source}"}
                
                # Parse the code
                try:
                    tree = ast.parse(code_content, filename=source_file)
                except SyntaxError as e:
                    return {
                        "error": "Syntax error in Python code",
                        "details": {
                            "message": str(e),
                            "filename": e.filename,
                            "line": e.lineno,
                            "offset": e.offset,
                            "text": e.text
                        }
                    }
                
            elif source_type == "module":
                # Find and load the module
                try:
                    spec = importlib.util.find_spec(source)
                    if spec is None:
                        return {"error": f"Module not found: {source}"}
                    
                    # Get the source file
                    source_file = spec.origin
                    if source_file is None or source_file == 'built-in' or source_file == 'frozen':
                        # For built-in modules, we can't get the source
                        return {"error": f"Cannot get source for built-in module: {source}"}
                    elif not os.path.exists(source_file):
                        return {"error": f"Module source file not found: {source_file}"}
                    else:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            code_content = f.read()
                    
                    # Parse the code
                    tree = ast.parse(code_content, filename=source_file or source)
                    
                except Exception as e:
                    return {"error": f"Error loading module {source}: {str(e)}"}
                    
            elif source_type == "code":
                # Parse code directly
                try:
                    tree = ast.parse(source)
                    source_file = None
                except SyntaxError as e:
                    return {
                        "error": "Syntax error in Python code",
                        "details": {
                            "message": str(e),
                            "line": e.lineno,
                            "offset": e.offset,
                            "text": e.text
                        }
                    }
            else:
                return {"error": f"Unknown source type: {source_type}"}
            
            # Convert AST to JSON
            json_result = self.ast_to_json(tree, include_metadata=include_metadata)
            
            # Add source-specific metadata
            if include_metadata and "metadata" in json_result:
                if source_type == "file":
                    json_result["metadata"]["source_file"] = source_file
                elif source_type == "module":
                    json_result["metadata"]["module_name"] = source
            
            # Format output if requested
            if format_output:
                # The result is already a dictionary, formatting would be done during serialization
                pass
            
            return json_result
            
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _json_to_python(self, **kwargs) -> Dict[str, Any]:
        """Convert AST JSON representation back to Python code."""
        json_data = kwargs.get("json_data")
        
        try:
            # Handle string input (file path or JSON string)
            if isinstance(json_data, str):
                # Check if it's a file path
                if os.path.exists(json_data):
                    with open(json_data, 'r') as f:
                        json_data = json.load(f)
                else:
                    # Try to parse as JSON string
                    try:
                        json_data = json.loads(json_data)
                    except json.JSONDecodeError:
                        return {"error": f"Invalid JSON data or file not found: {json_data}"}
            
            # Convert JSON to AST
            ast_node = self.json_to_ast(json_data)
            
            # Convert AST to Python code
            try:
                code = ast.unparse(ast_node)
                return {
                    "code": code,
                    "success": True
                }
            except AttributeError:
                # ast.unparse not available in Python < 3.9
                # Use a fallback or return error
                return {
                    "error": "Python code generation requires Python 3.9 or later",
                    "ast": ast_node  # Return AST object as fallback
                }
                
        except ValueError as e:
            return {"error": f"Validation error: {str(e)}"}
        except Exception as e:
            return {"error": f"Conversion error: {str(e)}"}
    
    def _validate_json(self, **kwargs) -> Dict[str, Any]:
        """Validate AST JSON against the schema."""
        json_data = kwargs.get("json_data")
        
        try:
            # Handle string input (file path or JSON string)
            if isinstance(json_data, str):
                # Check if it's a file path
                if os.path.exists(json_data):
                    with open(json_data, 'r') as f:
                        json_data = json.load(f)
                else:
                    # Try to parse as JSON string
                    try:
                        json_data = json.loads(json_data)
                    except json.JSONDecodeError:
                        return {"error": f"Invalid JSON data or file not found: {json_data}"}
            
            # Perform validation
            validation_result = self.validate_ast_json(json_data, self._schema_path)
            
            return validation_result
            
        except Exception as e:
            return {"error": f"Validation error: {str(e)}"}
    
    # Public API functions for direct use
    
    @staticmethod
    def ast_to_json(node: ast.AST, include_metadata: bool = True) -> Dict[str, Any]:
        """Convert an AST node to JSON representation.
        
        Args:
            node: The AST node to convert
            include_metadata: Whether to include source location metadata
            
        Returns:
            Dictionary representing the AST in JSON format
        """
        def get_location(node: ast.AST) -> Optional[Dict[str, Any]]:
            """Extract location information from a node."""
            if not include_metadata or not hasattr(node, 'lineno'):
                return None
                
            location = {}
            if hasattr(node, 'lineno'):
                location['lineno'] = node.lineno
            if hasattr(node, 'col_offset'):
                location['col_offset'] = node.col_offset
            if hasattr(node, 'end_lineno'):
                location['end_lineno'] = node.end_lineno
            if hasattr(node, 'end_col_offset'):
                location['end_col_offset'] = node.end_col_offset
                
            return location if location else None
        
        def get_docstring(node: ast.AST) -> Optional[str]:
            """Extract docstring from a function or class node."""
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    return node.body[0].value.value
            return None
        
        def convert_node(node: Any) -> Any:
            """Convert an AST node to JSON representation."""
            if node is None:
                return None
                
            # Handle non-AST types
            if isinstance(node, (str, int, float, bool, type(None))):
                return node
            
            if isinstance(node, list):
                return [convert_node(item) for item in node]
                
            if not isinstance(node, ast.AST):
                return str(node)
            
            # Start building the JSON representation
            result = {"node_type": node.__class__.__name__}
            
            # Add location if available
            location = get_location(node)
            if location:
                result["location"] = location
            
            # Handle specific node types
            node_type = node.__class__.__name__
            
            # Module
            if isinstance(node, ast.Module):
                result["body"] = [convert_node(stmt) for stmt in node.body]
                if hasattr(node, 'type_ignores'):
                    result["type_ignores"] = []
            
            # Expressions
            elif isinstance(node, ast.Expression):
                result["body"] = convert_node(node.body)
            
            # Interactive
            elif isinstance(node, ast.Interactive):
                result["body"] = [convert_node(stmt) for stmt in node.body]
            
            # Function definitions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result["name"] = node.name
                result["args"] = convert_arguments(node.args)
                result["body"] = [convert_node(stmt) for stmt in node.body]
                result["decorator_list"] = [convert_node(dec) for dec in node.decorator_list]
                result["returns"] = convert_node(node.returns) if node.returns else None
                if hasattr(node, 'type_comment') and node.type_comment:
                    result["type_comment"] = node.type_comment
                if hasattr(node, 'type_params'):
                    result["type_params"] = []
                docstring = get_docstring(node)
                if docstring:
                    result["docstring"] = docstring
            
            # Class definition
            elif isinstance(node, ast.ClassDef):
                result["name"] = node.name
                result["bases"] = [convert_node(base) for base in node.bases]
                result["keywords"] = []  # Simplified for now
                result["body"] = [convert_node(stmt) for stmt in node.body]
                result["decorator_list"] = [convert_node(dec) for dec in node.decorator_list]
                if hasattr(node, 'type_params'):
                    result["type_params"] = []
                docstring = get_docstring(node)
                if docstring:
                    result["docstring"] = docstring
            
            # Assignments
            elif isinstance(node, ast.Assign):
                result["targets"] = [convert_node(target) for target in node.targets]
                result["value"] = convert_node(node.value)
                if hasattr(node, 'type_comment') and node.type_comment:
                    result["type_comment"] = node.type_comment
                    
            elif isinstance(node, ast.AugAssign):
                result["target"] = convert_node(node.target)
                result["op"] = node.op.__class__.__name__
                result["value"] = convert_node(node.value)
                
            elif isinstance(node, ast.AnnAssign):
                result["target"] = convert_node(node.target)
                result["annotation"] = convert_node(node.annotation)
                result["value"] = convert_node(node.value) if node.value else None
                result["simple"] = node.simple
            
            # Control flow
            elif isinstance(node, ast.If):
                result["test"] = convert_node(node.test)
                result["body"] = [convert_node(stmt) for stmt in node.body]
                result["orelse"] = [convert_node(stmt) for stmt in node.orelse]
                
            elif isinstance(node, ast.For):
                result["target"] = convert_node(node.target)
                result["iter"] = convert_node(node.iter)
                result["body"] = [convert_node(stmt) for stmt in node.body]
                result["orelse"] = [convert_node(stmt) for stmt in node.orelse]
                if hasattr(node, 'type_comment') and node.type_comment:
                    result["type_comment"] = node.type_comment
                    
            elif isinstance(node, ast.AsyncFor):
                result["node_type"] = "AsyncFor"
                result["target"] = convert_node(node.target)
                result["iter"] = convert_node(node.iter)
                result["body"] = [convert_node(stmt) for stmt in node.body]
                result["orelse"] = [convert_node(stmt) for stmt in node.orelse]
                    
            elif isinstance(node, ast.While):
                result["test"] = convert_node(node.test)
                result["body"] = [convert_node(stmt) for stmt in node.body]
                result["orelse"] = [convert_node(stmt) for stmt in node.orelse]
                
            elif isinstance(node, ast.With):
                result["items"] = [convert_withitem(item) for item in node.items]
                result["body"] = [convert_node(stmt) for stmt in node.body]
                if hasattr(node, 'type_comment') and node.type_comment:
                    result["type_comment"] = node.type_comment
                    
            elif isinstance(node, ast.AsyncWith):
                result["node_type"] = "AsyncWith"
                result["items"] = [convert_withitem(item) for item in node.items]
                result["body"] = [convert_node(stmt) for stmt in node.body]
            
            # Exception handling
            elif isinstance(node, ast.Try):
                result["body"] = [convert_node(stmt) for stmt in node.body]
                result["handlers"] = [convert_excepthandler(h) for h in node.handlers]
                result["orelse"] = [convert_node(stmt) for stmt in node.orelse]
                result["finalbody"] = [convert_node(stmt) for stmt in node.finalbody]
            
            # Import statements
            elif isinstance(node, ast.Import):
                result["names"] = [{"name": alias.name, "asname": alias.asname} 
                                  for alias in node.names]
                                  
            elif isinstance(node, ast.ImportFrom):
                result["module"] = node.module
                result["names"] = [{"name": alias.name, "asname": alias.asname} 
                                  for alias in node.names]
                result["level"] = node.level
            
            # Other statements
            elif isinstance(node, ast.Global):
                result["names"] = node.names
                
            elif isinstance(node, ast.Nonlocal):
                result["names"] = node.names
                
            elif isinstance(node, ast.Pass):
                pass  # Just node_type is enough
                
            elif isinstance(node, ast.Break):
                pass  # Just node_type is enough
                
            elif isinstance(node, ast.Continue):
                pass  # Just node_type is enough
                
            elif isinstance(node, ast.Return):
                result["value"] = convert_node(node.value) if node.value else None
                
            elif isinstance(node, ast.Delete):
                result["targets"] = [convert_node(target) for target in node.targets]
                
            elif isinstance(node, ast.Raise):
                result["exc"] = convert_node(node.exc) if node.exc else None
                result["cause"] = convert_node(node.cause) if node.cause else None
                
            elif isinstance(node, ast.Assert):
                result["test"] = convert_node(node.test)
                result["msg"] = convert_node(node.msg) if node.msg else None
                
            elif isinstance(node, ast.Expr):
                result["value"] = convert_node(node.value)
            
            # Match statement (Python 3.10+)
            elif node_type == "Match":
                result["subject"] = convert_node(node.subject)
                result["cases"] = [convert_match_case(case) for case in node.cases]
            
            # Expressions
            elif isinstance(node, ast.BinOp):
                result["left"] = convert_node(node.left)
                result["op"] = node.op.__class__.__name__
                result["right"] = convert_node(node.right)
                
            elif isinstance(node, ast.UnaryOp):
                result["op"] = node.op.__class__.__name__
                result["operand"] = convert_node(node.operand)
                
            elif isinstance(node, ast.BoolOp):
                result["op"] = node.op.__class__.__name__
                result["values"] = [convert_node(v) for v in node.values]
                
            elif isinstance(node, ast.Compare):
                result["left"] = convert_node(node.left)
                result["ops"] = [op.__class__.__name__ for op in node.ops]
                result["comparators"] = [convert_node(c) for c in node.comparators]
            
            elif isinstance(node, ast.Call):
                result["func"] = convert_node(node.func)
                result["args"] = [convert_node(arg) for arg in node.args]
                result["keywords"] = [convert_keyword(kw) for kw in node.keywords]
                
            elif isinstance(node, ast.Attribute):
                result["value"] = convert_node(node.value)
                result["attr"] = node.attr
                result["ctx"] = node.ctx.__class__.__name__
                
            elif isinstance(node, ast.Subscript):
                result["value"] = convert_node(node.value)
                result["slice"] = convert_node(node.slice)
                result["ctx"] = node.ctx.__class__.__name__
                
            elif isinstance(node, ast.Slice):
                result["lower"] = convert_node(node.lower) if node.lower else None
                result["upper"] = convert_node(node.upper) if node.upper else None
                result["step"] = convert_node(node.step) if node.step else None
                
            elif isinstance(node, ast.Name):
                result["node_type"] = "Identifier"
                result["name"] = node.id
                result["ctx"] = node.ctx.__class__.__name__
                
            elif isinstance(node, ast.Constant):
                result["value"] = node.value
                if hasattr(node, 'kind') and node.kind:
                    result["kind"] = node.kind
                    
            elif isinstance(node, ast.JoinedStr):  # f-strings
                result["node_type"] = "JoinedStr"
                result["values"] = [convert_node(v) for v in node.values]
                
            elif isinstance(node, ast.FormattedValue):
                result["node_type"] = "FormattedValue"
                result["value"] = convert_node(node.value)
                result["conversion"] = node.conversion
                result["format_spec"] = convert_node(node.format_spec) if node.format_spec else None
            
            # Collections
            elif isinstance(node, ast.List):
                result["elts"] = [convert_node(elt) for elt in node.elts]
                result["ctx"] = node.ctx.__class__.__name__
                
            elif isinstance(node, ast.Tuple):
                result["elts"] = [convert_node(elt) for elt in node.elts]
                result["ctx"] = node.ctx.__class__.__name__
                
            elif isinstance(node, ast.Set):
                result["elts"] = [convert_node(elt) for elt in node.elts]
                
            elif isinstance(node, ast.Dict):
                result["keys"] = [convert_node(k) for k in node.keys]
                result["values"] = [convert_node(v) for v in node.values]
            
            # Comprehensions
            elif isinstance(node, ast.ListComp):
                result["elt"] = convert_node(node.elt)
                result["generators"] = [convert_comprehension(gen) for gen in node.generators]
                
            elif isinstance(node, ast.SetComp):
                result["elt"] = convert_node(node.elt)
                result["generators"] = [convert_comprehension(gen) for gen in node.generators]
                
            elif isinstance(node, ast.DictComp):
                result["key"] = convert_node(node.key)
                result["value"] = convert_node(node.value)
                result["generators"] = [convert_comprehension(gen) for gen in node.generators]
                
            elif isinstance(node, ast.GeneratorExp):
                result["elt"] = convert_node(node.elt)
                result["generators"] = [convert_comprehension(gen) for gen in node.generators]
            
            # Other expressions
            elif isinstance(node, ast.Lambda):
                result["args"] = convert_arguments(node.args)
                result["body"] = convert_node(node.body)
                
            elif isinstance(node, ast.IfExp):
                result["test"] = convert_node(node.test)
                result["body"] = convert_node(node.body)
                result["orelse"] = convert_node(node.orelse)
                
            elif isinstance(node, ast.Yield):
                result["value"] = convert_node(node.value) if node.value else None
                
            elif isinstance(node, ast.YieldFrom):
                result["value"] = convert_node(node.value)
                
            elif isinstance(node, ast.Await):
                result["value"] = convert_node(node.value)
                
            elif isinstance(node, ast.Starred):
                result["value"] = convert_node(node.value)
                result["ctx"] = node.ctx.__class__.__name__
                
            elif isinstance(node, ast.NamedExpr):  # Walrus operator
                result["target"] = convert_node(node.target)
                result["value"] = convert_node(node.value)
            
            else:
                # Fallback for any unhandled node types
                for field, value in ast.iter_fields(node):
                    if field not in result:
                        result[field] = convert_node(value)
            
            return result
        
        def convert_arguments(args: ast.arguments) -> Dict[str, Any]:
            """Convert function arguments to JSON."""
            result = {}
            
            if hasattr(args, 'posonlyargs') and args.posonlyargs:
                result["posonlyargs"] = [convert_node(arg) for arg in args.posonlyargs]
            else:
                result["posonlyargs"] = []
                
            result["args"] = [convert_node(arg) for arg in args.args]
            result["vararg"] = convert_node(args.vararg) if args.vararg else None
            result["kwonlyargs"] = [convert_node(arg) for arg in args.kwonlyargs]
            result["kw_defaults"] = [convert_node(d) if d else None for d in args.kw_defaults]
            result["kwarg"] = convert_node(args.kwarg) if args.kwarg else None
            result["defaults"] = [convert_node(d) for d in args.defaults]
            
            return result
        
        def convert_comprehension(comp: ast.comprehension) -> Dict[str, Any]:
            """Convert comprehension to JSON."""
            return {
                "target": convert_node(comp.target),
                "iter": convert_node(comp.iter),
                "ifs": [convert_node(if_) for if_ in comp.ifs],
                "is_async": comp.is_async
            }
        
        def convert_excepthandler(handler: ast.ExceptHandler) -> Dict[str, Any]:
            """Convert exception handler to JSON."""
            result = {"node_type": "ExceptHandler"}
            location = get_location(handler)
            if location:
                result["location"] = location
            result["type"] = convert_node(handler.type) if handler.type else None
            result["name"] = handler.name
            result["body"] = [convert_node(stmt) for stmt in handler.body]
            return result
        
        def convert_withitem(item: ast.withitem) -> Dict[str, Any]:
            """Convert with item to JSON."""
            return {
                "context_expr": convert_node(item.context_expr),
                "optional_vars": convert_node(item.optional_vars) if item.optional_vars else None
            }
        
        def convert_keyword(kw: ast.keyword) -> Dict[str, Any]:
            """Convert keyword argument to JSON."""
            return {
                "arg": kw.arg,
                "value": convert_node(kw.value)
            }
        
        def convert_match_case(case) -> Dict[str, Any]:
            """Convert match case to JSON."""
            return {
                "pattern": convert_node(case.pattern),
                "guard": convert_node(case.guard) if case.guard else None,
                "body": [convert_node(stmt) for stmt in case.body]
            }
        
        # Convert AST arg nodes
        if isinstance(node, ast.arg):
            result = {
                "node_type": "arg",
                "arg": node.arg,
                "annotation": convert_node(node.annotation) if node.annotation else None
            }
            location = get_location(node)
            if location:
                result["location"] = location
            return result
        
        # Main conversion
        if isinstance(node, ast.Module):
            # Return the expected structure for module
            ast_json = convert_node(node)
            return {
                "ast": ast_json,
                "metadata": {
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "conversion_timestamp": datetime.now(timezone.utc).isoformat(),
                    "encoding": "utf-8"
                }
            }
        else:
            # For other node types, just return the converted node
            return convert_node(node)
    
    @staticmethod
    def json_to_ast(json_data: Dict[str, Any]) -> ast.AST:
        """Convert JSON representation back to an AST node.
        
        Args:
            json_data: The JSON representation of the AST
            
        Returns:
            The reconstructed AST node
        """
        def get_operator(op_name: str):
            """Convert operator name to AST operator class."""
            operators = {
                # Binary operators
                'Add': ast.Add,
                'Sub': ast.Sub,
                'Mult': ast.Mult,
                'MatMult': ast.MatMult,
                'Div': ast.Div,
                'Mod': ast.Mod,
                'Pow': ast.Pow,
                'LShift': ast.LShift,
                'RShift': ast.RShift,
                'BitOr': ast.BitOr,
                'BitXor': ast.BitXor,
                'BitAnd': ast.BitAnd,
                'FloorDiv': ast.FloorDiv,
                # Boolean operators
                'And': ast.And,
                'Or': ast.Or,
                # Comparison operators
                'Eq': ast.Eq,
                'NotEq': ast.NotEq,
                'Lt': ast.Lt,
                'LtE': ast.LtE,
                'Gt': ast.Gt,
                'GtE': ast.GtE,
                'Is': ast.Is,
                'IsNot': ast.IsNot,
                'In': ast.In,
                'NotIn': ast.NotIn,
                # Unary operators
                'Invert': ast.Invert,
                'Not': ast.Not,
                'UAdd': ast.UAdd,
                'USub': ast.USub,
            }
            return operators.get(op_name, ast.Add)()
        
        def get_context(ctx_name: str):
            """Convert context name to AST context class."""
            contexts = {
                'Load': ast.Load,
                'Store': ast.Store,
                'Del': ast.Del,
            }
            return contexts.get(ctx_name, ast.Load)()
        
        def reconstruct_node(data: Any) -> Any:
            """Reconstruct an AST node from JSON data."""
            if data is None:
                return None
            
            # Handle primitive types
            if isinstance(data, (str, int, float, bool)):
                return data
            
            # Handle lists
            if isinstance(data, list):
                return [reconstruct_node(item) for item in data]
            
            # Handle dictionaries that aren't nodes
            if not isinstance(data, dict) or 'node_type' not in data:
                return data
            
            node_type = data['node_type']
            
            # Special case: Identifier nodes become Name nodes
            if node_type == 'Identifier':
                node = ast.Name(
                    id=data['name'],
                    ctx=get_context(data.get('ctx', 'Load'))
                )
            
            # Module
            elif node_type == 'Module':
                node = ast.Module(
                    body=reconstruct_node(data.get('body', [])),
                    type_ignores=[]
                )
            
            # Expression (for eval mode)
            elif node_type == 'Expression':
                node = ast.Expression(
                    body=reconstruct_node(data['body'])
                )
            
            # Interactive
            elif node_type == 'Interactive':
                node = ast.Interactive(
                    body=reconstruct_node(data.get('body', []))
                )
            
            # Function definitions
            elif node_type in ('FunctionDef', 'AsyncFunctionDef'):
                cls = ast.AsyncFunctionDef if node_type == 'AsyncFunctionDef' else ast.FunctionDef
                node = cls(
                    name=data['name'],
                    args=reconstruct_arguments(data['args']),
                    body=reconstruct_node(data.get('body', [])) or [ast.Pass()],
                    decorator_list=reconstruct_node(data.get('decorator_list', [])),
                    returns=reconstruct_node(data.get('returns')),
                    type_comment=data.get('type_comment')
                )
            
            # Class definition
            elif node_type == 'ClassDef':
                node = ast.ClassDef(
                    name=data['name'],
                    bases=reconstruct_node(data.get('bases', [])),
                    keywords=[],  # TODO: Handle keywords properly
                    body=reconstruct_node(data.get('body', [])) or [ast.Pass()],
                    decorator_list=reconstruct_node(data.get('decorator_list', []))
                )
            
            # Assignments
            elif node_type == 'Assign':
                node = ast.Assign(
                    targets=reconstruct_node(data['targets']),
                    value=reconstruct_node(data['value']),
                    type_comment=data.get('type_comment')
                )
            
            elif node_type == 'AugAssign':
                node = ast.AugAssign(
                    target=reconstruct_node(data['target']),
                    op=get_operator(data['op']),
                    value=reconstruct_node(data['value'])
                )
            
            elif node_type == 'AnnAssign':
                node = ast.AnnAssign(
                    target=reconstruct_node(data['target']),
                    annotation=reconstruct_node(data['annotation']),
                    value=reconstruct_node(data.get('value')),
                    simple=data.get('simple', 1)
                )
            
            # Control flow
            elif node_type == 'If':
                node = ast.If(
                    test=reconstruct_node(data['test']),
                    body=reconstruct_node(data['body']),
                    orelse=reconstruct_node(data.get('orelse', []))
                )
            
            elif node_type == 'For':
                node = ast.For(
                    target=reconstruct_node(data['target']),
                    iter=reconstruct_node(data['iter']),
                    body=reconstruct_node(data['body']),
                    orelse=reconstruct_node(data.get('orelse', [])),
                    type_comment=data.get('type_comment')
                )
            
            elif node_type == 'AsyncFor':
                node = ast.AsyncFor(
                    target=reconstruct_node(data['target']),
                    iter=reconstruct_node(data['iter']),
                    body=reconstruct_node(data['body']),
                    orelse=reconstruct_node(data.get('orelse', []))
                )
            
            elif node_type == 'While':
                node = ast.While(
                    test=reconstruct_node(data['test']),
                    body=reconstruct_node(data['body']),
                    orelse=reconstruct_node(data.get('orelse', []))
                )
            
            elif node_type == 'With':
                node = ast.With(
                    items=[reconstruct_withitem(item) for item in data.get('items', [])],
                    body=reconstruct_node(data['body']),
                    type_comment=data.get('type_comment')
                )
            
            elif node_type == 'AsyncWith':
                node = ast.AsyncWith(
                    items=[reconstruct_withitem(item) for item in data.get('items', [])],
                    body=reconstruct_node(data['body'])
                )
            
            # Exception handling
            elif node_type == 'Try':
                node = ast.Try(
                    body=reconstruct_node(data['body']),
                    handlers=[reconstruct_excepthandler(h) for h in data.get('handlers', [])],
                    orelse=reconstruct_node(data.get('orelse', [])),
                    finalbody=reconstruct_node(data.get('finalbody', []))
                )
            
            # Imports
            elif node_type == 'Import':
                node = ast.Import(
                    names=[ast.alias(name=n['name'], asname=n.get('asname')) 
                          for n in data['names']]
                )
            
            elif node_type == 'ImportFrom':
                node = ast.ImportFrom(
                    module=data.get('module'),
                    names=[ast.alias(name=n['name'], asname=n.get('asname')) 
                          for n in data['names']],
                    level=data.get('level', 0)
                )
            
            # Other statements
            elif node_type == 'Return':
                node = ast.Return(value=reconstruct_node(data.get('value')))
            
            elif node_type == 'Delete':
                node = ast.Delete(targets=reconstruct_node(data['targets']))
            
            elif node_type == 'Global':
                node = ast.Global(names=data['names'])
            
            elif node_type == 'Nonlocal':
                node = ast.Nonlocal(names=data['names'])
            
            elif node_type == 'Pass':
                node = ast.Pass()
            
            elif node_type == 'Break':
                node = ast.Break()
            
            elif node_type == 'Continue':
                node = ast.Continue()
            
            elif node_type == 'Raise':
                node = ast.Raise(
                    exc=reconstruct_node(data.get('exc')),
                    cause=reconstruct_node(data.get('cause'))
                )
            
            elif node_type == 'Assert':
                node = ast.Assert(
                    test=reconstruct_node(data['test']),
                    msg=reconstruct_node(data.get('msg'))
                )
            
            elif node_type == 'Expr':
                node = ast.Expr(value=reconstruct_node(data['value']))
            
            # Match statement (Python 3.10+)
            elif node_type == 'Match':
                if hasattr(ast, 'Match'):
                    node = ast.Match(
                        subject=reconstruct_node(data['subject']),
                        cases=[reconstruct_match_case(c) for c in data['cases']]
                    )
                else:
                    # Fallback for older Python versions
                    node = ast.Pass()
            
            # Expressions
            elif node_type == 'BinOp':
                node = ast.BinOp(
                    left=reconstruct_node(data['left']),
                    op=get_operator(data['op']),
                    right=reconstruct_node(data['right'])
                )
            
            elif node_type == 'UnaryOp':
                node = ast.UnaryOp(
                    op=get_operator(data['op']),
                    operand=reconstruct_node(data['operand'])
                )
            
            elif node_type == 'BoolOp':
                node = ast.BoolOp(
                    op=get_operator(data['op']),
                    values=reconstruct_node(data['values'])
                )
            
            elif node_type == 'Compare':
                node = ast.Compare(
                    left=reconstruct_node(data['left']),
                    ops=[get_operator(op) for op in data['ops']],
                    comparators=reconstruct_node(data['comparators'])
                )
            
            elif node_type == 'Call':
                node = ast.Call(
                    func=reconstruct_node(data['func']),
                    args=reconstruct_node(data.get('args', [])),
                    keywords=[reconstruct_keyword(kw) for kw in data.get('keywords', [])]
                )
            
            elif node_type == 'Attribute':
                node = ast.Attribute(
                    value=reconstruct_node(data['value']),
                    attr=data['attr'],
                    ctx=get_context(data.get('ctx', 'Load'))
                )
            
            elif node_type == 'Subscript':
                node = ast.Subscript(
                    value=reconstruct_node(data['value']),
                    slice=reconstruct_node(data['slice']),
                    ctx=get_context(data.get('ctx', 'Load'))
                )
            
            elif node_type == 'Slice':
                node = ast.Slice(
                    lower=reconstruct_node(data.get('lower')),
                    upper=reconstruct_node(data.get('upper')),
                    step=reconstruct_node(data.get('step'))
                )
            
            elif node_type == 'Constant':
                value = data['value']
                # Handle special string constants
                if data.get('kind') == 'b' and isinstance(value, str):
                    value = value.encode()
                node = ast.Constant(value=value)
            
            # Collections
            elif node_type == 'List':
                node = ast.List(
                    elts=reconstruct_node(data['elts']),
                    ctx=get_context(data.get('ctx', 'Load'))
                )
            
            elif node_type == 'Tuple':
                node = ast.Tuple(
                    elts=reconstruct_node(data['elts']),
                    ctx=get_context(data.get('ctx', 'Load'))
                )
            
            elif node_type == 'Set':
                node = ast.Set(elts=reconstruct_node(data['elts']))
            
            elif node_type == 'Dict':
                node = ast.Dict(
                    keys=reconstruct_node(data['keys']),
                    values=reconstruct_node(data['values'])
                )
            
            # Comprehensions
            elif node_type == 'ListComp':
                node = ast.ListComp(
                    elt=reconstruct_node(data['elt']),
                    generators=[reconstruct_comprehension(g) for g in data['generators']]
                )
            
            elif node_type == 'SetComp':
                node = ast.SetComp(
                    elt=reconstruct_node(data['elt']),
                    generators=[reconstruct_comprehension(g) for g in data['generators']]
                )
            
            elif node_type == 'DictComp':
                node = ast.DictComp(
                    key=reconstruct_node(data['key']),
                    value=reconstruct_node(data['value']),
                    generators=[reconstruct_comprehension(g) for g in data['generators']]
                )
            
            elif node_type == 'GeneratorExp':
                node = ast.GeneratorExp(
                    elt=reconstruct_node(data['elt']),
                    generators=[reconstruct_comprehension(g) for g in data['generators']]
                )
            
            # Other expressions
            elif node_type == 'Lambda':
                node = ast.Lambda(
                    args=reconstruct_arguments(data['args']),
                    body=reconstruct_node(data['body'])
                )
            
            elif node_type == 'IfExp':
                node = ast.IfExp(
                    test=reconstruct_node(data['test']),
                    body=reconstruct_node(data['body']),
                    orelse=reconstruct_node(data['orelse'])
                )
            
            elif node_type == 'Yield':
                node = ast.Yield(value=reconstruct_node(data.get('value')))
            
            elif node_type == 'YieldFrom':
                node = ast.YieldFrom(value=reconstruct_node(data['value']))
            
            elif node_type == 'Await':
                node = ast.Await(value=reconstruct_node(data['value']))
            
            elif node_type == 'Starred':
                node = ast.Starred(
                    value=reconstruct_node(data['value']),
                    ctx=get_context(data.get('ctx', 'Load'))
                )
            
            elif node_type == 'NamedExpr':
                if hasattr(ast, 'NamedExpr'):
                    node = ast.NamedExpr(
                        target=reconstruct_node(data['target']),
                        value=reconstruct_node(data['value'])
                    )
                else:
                    # Fallback for older Python
                    node = reconstruct_node(data['value'])
            
            # F-strings
            elif node_type == 'JoinedStr':
                if hasattr(ast, 'JoinedStr'):
                    node = ast.JoinedStr(values=reconstruct_node(data['values']))
                else:
                    # Fallback
                    node = ast.Constant(value='')
            
            elif node_type == 'FormattedValue':
                if hasattr(ast, 'FormattedValue'):
                    node = ast.FormattedValue(
                        value=reconstruct_node(data['value']),
                        conversion=data.get('conversion', -1),
                        format_spec=reconstruct_node(data.get('format_spec'))
                    )
                else:
                    node = reconstruct_node(data['value'])
            
            # arg nodes
            elif node_type == 'arg':
                node = ast.arg(
                    arg=data['arg'],
                    annotation=reconstruct_node(data.get('annotation'))
                )
            
            # ExceptHandler
            elif node_type == 'ExceptHandler':
                node = ast.ExceptHandler(
                    type=reconstruct_node(data.get('type')),
                    name=data.get('name'),
                    body=reconstruct_node(data.get('body', []))
                )
            
            else:
                # Unknown node type - return as-is or raise error
                raise ValueError(f"Unknown node type: {node_type}")
            
            # Set location info if available
            if 'location' in data and hasattr(node, 'lineno'):
                loc = data['location']
                if 'lineno' in loc:
                    node.lineno = loc['lineno']
                if 'col_offset' in loc:
                    node.col_offset = loc['col_offset']
                if 'end_lineno' in loc:
                    node.end_lineno = loc.get('end_lineno')
                if 'end_col_offset' in loc:
                    node.end_col_offset = loc.get('end_col_offset')
            
            return node
        
        def reconstruct_arguments(args_data: Dict[str, Any]) -> ast.arguments:
            """Reconstruct function arguments."""
            return ast.arguments(
                posonlyargs=reconstruct_node(args_data.get('posonlyargs', [])),
                args=reconstruct_node(args_data.get('args', [])),
                vararg=reconstruct_node(args_data.get('vararg')),
                kwonlyargs=reconstruct_node(args_data.get('kwonlyargs', [])),
                kw_defaults=reconstruct_node(args_data.get('kw_defaults', [])),
                kwarg=reconstruct_node(args_data.get('kwarg')),
                defaults=reconstruct_node(args_data.get('defaults', []))
            )
        
        def reconstruct_comprehension(comp_data: Dict[str, Any]) -> ast.comprehension:
            """Reconstruct comprehension."""
            return ast.comprehension(
                target=reconstruct_node(comp_data['target']),
                iter=reconstruct_node(comp_data['iter']),
                ifs=reconstruct_node(comp_data.get('ifs', [])),
                is_async=comp_data.get('is_async', 0)
            )
        
        def reconstruct_withitem(item_data: Dict[str, Any]) -> ast.withitem:
            """Reconstruct with item."""
            return ast.withitem(
                context_expr=reconstruct_node(item_data['context_expr']),
                optional_vars=reconstruct_node(item_data.get('optional_vars'))
            )
        
        def reconstruct_keyword(kw_data: Dict[str, Any]) -> ast.keyword:
            """Reconstruct keyword argument."""
            return ast.keyword(
                arg=kw_data.get('arg'),
                value=reconstruct_node(kw_data['value'])
            )
        
        def reconstruct_excepthandler(handler_data: Dict[str, Any]) -> ast.ExceptHandler:
            """Reconstruct exception handler."""
            handler = ast.ExceptHandler(
                type=reconstruct_node(handler_data.get('type')),
                name=handler_data.get('name'),
                body=reconstruct_node(handler_data.get('body', []))
            )
            # Set location if available
            if 'location' in handler_data:
                loc = handler_data['location']
                if 'lineno' in loc:
                    handler.lineno = loc['lineno']
                if 'col_offset' in loc:
                    handler.col_offset = loc['col_offset']
            return handler
        
        def reconstruct_match_case(case_data: Dict[str, Any]):
            """Reconstruct match case."""
            if hasattr(ast, 'match_case'):
                return ast.match_case(
                    pattern=reconstruct_pattern(case_data['pattern']),
                    guard=reconstruct_node(case_data.get('guard')),
                    body=reconstruct_node(case_data['body'])
                )
            return None
        
        def reconstruct_pattern(pattern_data: Dict[str, Any]):
            """Reconstruct match pattern."""
            if not hasattr(ast, 'MatchAs'):
                return None
                
            pattern_type = pattern_data.get('node_type')
            
            if pattern_type == 'MatchAs':
                return ast.MatchAs(
                    pattern=reconstruct_pattern(pattern_data.get('pattern')) if pattern_data.get('pattern') else None,
                    name=pattern_data.get('name')
                )
            elif pattern_type == 'MatchValue':
                return ast.MatchValue(value=reconstruct_node(pattern_data['value']))
            elif pattern_type == 'MatchSequence':
                return ast.MatchSequence(patterns=[reconstruct_pattern(p) for p in pattern_data['patterns']])
            elif pattern_type == 'MatchClass':
                return ast.MatchClass(
                    cls=reconstruct_node(pattern_data['cls']),
                    patterns=[reconstruct_pattern(p) for p in pattern_data.get('patterns', [])],
                    kwd_attrs=pattern_data.get('kwd_attrs', []),
                    kwd_patterns=[reconstruct_pattern(p) for p in pattern_data.get('kwd_patterns', [])]
                )
            
            return None
        
        # Handle different input formats
        if isinstance(json_data, str):
            # Parse JSON string
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e}")
        
        if not isinstance(json_data, dict):
            raise ValueError(f"Expected dict, got {type(json_data).__name__}")
        
        # Check if it's wrapped with ast/metadata structure
        if 'ast' in json_data:
            # Full structure with metadata
            return reconstruct_node(json_data['ast'])
        else:
            # Direct node representation
            return reconstruct_node(json_data)
    
    @staticmethod
    def file_to_json(file_path: str, include_metadata: bool = True) -> Dict[str, Any]:
        """Convert a Python file to AST JSON representation.
        
        Args:
            file_path: Path to the Python file
            include_metadata: Whether to include metadata
            
        Returns:
            Dictionary with AST and metadata
        """
        tool = PythonASTJSONTool()
        return tool._python_to_json(
            source=file_path,
            source_type="file",
            include_metadata=include_metadata
        )
    
    @staticmethod
    def module_to_json(module_name: str, include_metadata: bool = True) -> Dict[str, Any]:
        """Convert a Python module to AST JSON representation.
        
        Args:
            module_name: Name of the module (e.g., 'os.path')
            include_metadata: Whether to include metadata
            
        Returns:
            Dictionary with AST and metadata
        """
        tool = PythonASTJSONTool()
        return tool._python_to_json(
            source=module_name,
            source_type="module",
            include_metadata=include_metadata
        )
    
    @staticmethod
    def json_to_code(json_data: Dict[str, Any]) -> str:
        """Convert AST JSON representation to Python source code.
        
        Args:
            json_data: The JSON representation of the AST
            
        Returns:
            The reconstructed Python source code
        """
        # Convert JSON to AST
        ast_node = PythonASTJSONTool.json_to_ast(json_data)
        
        # Convert AST to Python code
        try:
            # ast.unparse available in Python 3.9+
            code = ast.unparse(ast_node)
            return code
        except AttributeError:
            # ast.unparse not available in Python < 3.9
            # Try using astor or similar library as fallback
            try:
                import astor
                return astor.to_source(ast_node)
            except ImportError:
                # If no fallback available, raise informative error
                raise RuntimeError(
                    "Python code generation requires Python 3.9+ or the 'astor' library. "
                    "Install astor with: pip install astor"
                )
    
    @staticmethod
    def validate_ast_json(json_data: Dict[str, Any], schema_path: Optional[str] = None) -> Dict[str, Any]:
        """Validate AST JSON against the schema.
        
        Args:
            json_data: The JSON data to validate
            schema_path: Optional path to schema file
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Import jsonschema for validation
            try:
                import jsonschema
            except ImportError:
                return {
                    "valid": False,
                    "error": "jsonschema library not installed. Install with: pip install jsonschema"
                }
            
            # Load schema
            if schema_path is None:
                schema_path = Path(__file__).parent.parent.parent / "schemas" / "python_ast_schema.json"
            else:
                schema_path = Path(schema_path)
            
            if not schema_path.exists():
                return {
                    "valid": False,
                    "error": f"Schema file not found: {schema_path}"
                }
            
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Validate against schema
            jsonschema.validate(instance=json_data, schema=schema)
            
            # Additional semantic validation
            semantic_errors = []
            
            # Check if it's a valid AST structure by trying to convert it
            try:
                ast_node = PythonASTJSONTool.json_to_ast(json_data)
                
                # Verify it's a valid AST by compiling it
                if isinstance(ast_node, ast.Module):
                    compile(ast_node, '<string>', 'exec')
                elif isinstance(ast_node, ast.Expression):
                    compile(ast_node, '<string>', 'eval')
                elif isinstance(ast_node, ast.Interactive):
                    compile(ast_node, '<string>', 'single')
                
            except SyntaxError as e:
                semantic_errors.append(f"Invalid Python syntax: {str(e)}")
            except ValueError as e:
                semantic_errors.append(f"Invalid AST structure: {str(e)}")
            except Exception as e:
                semantic_errors.append(f"AST validation error: {str(e)}")
            
            if semantic_errors:
                return {
                    "valid": False,
                    "schema_valid": True,
                    "semantic_errors": semantic_errors
                }
            
            return {
                "valid": True,
                "message": "AST JSON is valid"
            }
            
        except jsonschema.ValidationError as e:
            return {
                "valid": False,
                "schema_valid": False,
                "error": str(e),
                "path": list(e.absolute_path) if e.absolute_path else []
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Unexpected validation error: {str(e)}"
            }