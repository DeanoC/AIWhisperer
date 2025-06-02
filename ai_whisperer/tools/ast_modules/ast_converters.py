"""
AST to JSON conversion functions
"""

import ast
import json
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timezone


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
            
            # Extract metadata if requested
            comments = []
            formatting = {}
            if include_metadata:
                # Get source code
                if source_type == "code":
                    source_code = source
                else:
                    source_code = code_content
                    
                # Extract comments and formatting
                comments = extract_comments_from_source(source_code)
                formatting = calculate_formatting_metrics(source_code)
            
            # Convert AST to JSON with metadata
            json_result = self.ast_to_json(
                tree, 
                include_metadata=include_metadata,
                source_code=source_code if include_metadata else None,
                comments=comments,
                formatting=formatting
            )
            
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
    


    def ast_to_json(node: ast.AST, 
                   include_metadata: bool = True,
                   source_code: Optional[str] = None,
                   comments: Optional[List[Dict[str, Any]]] = None,
                   formatting: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert an AST node to JSON representation.
        
        Args:
            node: The AST node to convert
            include_metadata: Whether to include source location metadata
            source_code: Optional source code for extracting additional metadata
            comments: Optional pre-extracted comments
            formatting: Optional pre-extracted formatting metrics
            
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
            result = {
                "ast": ast_json,
                "metadata": {
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "conversion_timestamp": datetime.now(timezone.utc).isoformat(),
                    "encoding": "utf-8",
                    "line_count": len(source_code.split('\n')) if source_code else None,
                    "source_hash": hash(source_code) if source_code else None
                }
            }
            
            # Add comments if provided
            if comments is not None:
                result["comments"] = comments
                
            # Add formatting if provided
            if formatting is not None:
                result["formatting"] = formatting
                
            return result
        else:
            # For other node types, just return the converted node
            return convert_node(node)
    


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
    

