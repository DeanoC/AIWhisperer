"""
JSON to AST conversion functions
"""

import ast
import json
from typing import Dict, Any, Optional, Union, List


    def _json_to_python(self, **kwargs) -> Dict[str, Any]:
        """Convert AST JSON representation back to Python code."""
        json_data = kwargs.get("json_data")
        reconstruction_mode = kwargs.get("reconstruction_mode", "docstrings")
        
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
            
            # Fix missing locations for unparsing
            ast_node = self._fix_missing_locations(ast_node)
            
            # Convert AST to Python code
            try:
                code = ast.unparse(ast_node)
                
                # Apply reconstruction mode enhancements
                if reconstruction_mode != "minimal" and isinstance(json_data, dict):
                    code = self._apply_reconstruction_mode(
                        code, json_data, reconstruction_mode
                    )
                
                return {
                    "code": code,
                    "success": True,
                    "mode_applied": reconstruction_mode
                }
            except AttributeError as e:
                # Check if it's really because ast.unparse is not available
                if not hasattr(ast, 'unparse'):
                    return {
                        "error": "Python code generation requires Python 3.9 or later",
                        "ast": ast_node  # Return AST object as fallback
                    }
                else:
                    # Re-raise if it's a different AttributeError
                    raise
                
        except ValueError as e:
            return {"error": f"Validation error: {str(e)}"}
        except Exception as e:
            return {"error": f"Conversion error: {str(e)}"}
    


    def json_to_ast(json_data: Dict[str, Any]) -> ast.AST:
        """Convert JSON representation back to an AST node.
        
        Args:
            json_data: The JSON representation of the AST
            
        Returns:
            The reconstructed AST node
        """
        # Handle full JSON structure with metadata
        if isinstance(json_data, dict) and "ast" in json_data:
            # Extract just the AST portion
            json_data = json_data["ast"]
        
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
    

