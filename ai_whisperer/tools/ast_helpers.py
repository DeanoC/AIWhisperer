"""
Helper functions for Python AST JSON tool.
Extracted to reduce main module size.
"""

import ast
import tokenize
import io
from typing import List, Dict, Any, Optional

def extract_comments_from_source(source: str) -> List[Dict[str, Any]]:
    """Extract comments from Python source code."""
    comments = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                comments.append({
                    'line': token.start[0],
                    'column': token.start[1],
                    'text': token.string
                })
    except tokenize.TokenError:
        pass  # Invalid source code, ignore comments
    return comments

def calculate_formatting_metrics(source: str) -> Dict[str, Any]:
    """Calculate formatting metrics for source code."""
    lines = source.splitlines()
    
    # Basic metrics
    total_lines = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    
    # Indentation analysis
    indent_levels = []
    for line in lines:
        if line.strip():  # Non-empty line
            indent = len(line) - len(line.lstrip())
            indent_levels.append(indent)
    
    # Calculate average indentation
    avg_indent = sum(indent_levels) / len(indent_levels) if indent_levels else 0
    
    # Line length analysis
    line_lengths = [len(line) for line in lines if line.strip()]
    max_line_length = max(line_lengths) if line_lengths else 0
    avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0
    
    return {
        'total_lines': total_lines,
        'blank_lines': blank_lines,
        'comment_lines': comment_lines,
        'code_lines': total_lines - blank_lines - comment_lines,
        'average_indentation': round(avg_indent, 2),
        'max_line_length': max_line_length,
        'average_line_length': round(avg_line_length, 2)
    }

def extract_docstring_info(node: ast.AST) -> Optional[Dict[str, Any]]:
    """Extract docstring information from an AST node."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        return None
    
    # Get the first statement in the body
    if node.body and isinstance(node.body[0], ast.Expr):
        expr = node.body[0]
        if isinstance(expr.value, ast.Constant) and isinstance(expr.value.value, str):
            docstring = expr.value.value
            return {
                'docstring': docstring,
                'line': expr.lineno,
                'type': 'single_line' if '\n' not in docstring else 'multi_line',
                'length': len(docstring)
            }
    
    return None

def safe_ast_parse(source: str, filename: str = '<unknown>') -> Optional[ast.AST]:
    """Safely parse Python source code into AST."""
    try:
        return ast.parse(source, filename=filename)
    except SyntaxError as e:
        # Try to parse with different Python versions' syntax
        try:
            # Try parsing with type comments
            return ast.parse(source, filename=filename, type_comments=True)
        except:
            # Return partial AST if possible
            return None
    except Exception:
        return None

def get_node_type_name(node: ast.AST) -> str:
    """Get human-readable name for AST node type."""
    node_type = type(node).__name__
    
    # Special cases for better readability
    special_names = {
        'FunctionDef': 'Function',
        'AsyncFunctionDef': 'Async Function',
        'ClassDef': 'Class',
        'Module': 'Module',
        'Assign': 'Assignment',
        'AugAssign': 'Augmented Assignment',
        'AnnAssign': 'Annotated Assignment',
        'If': 'If Statement',
        'For': 'For Loop',
        'While': 'While Loop',
        'With': 'With Statement',
        'Try': 'Try-Except Block',
        'Import': 'Import Statement',
        'ImportFrom': 'Import From Statement'
    }
    
    return special_names.get(node_type, node_type)

def estimate_node_complexity(node: ast.AST) -> int:
    """Estimate complexity score for an AST node."""
    complexity = 1  # Base complexity
    
    # Add complexity for control flow
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
            complexity += 2
        elif isinstance(child, (ast.FunctionDef, ast.ClassDef)):
            complexity += 3
        elif isinstance(child, ast.Lambda):
            complexity += 1
        elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            complexity += 2
    
    return complexity

def count_ast_nodes(tree: ast.AST) -> int:
    """Count total number of nodes in an AST."""
    return sum(1 for _ in ast.walk(tree))

def get_ast_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Calculate maximum depth of an AST."""
    max_depth = current_depth
    
    for child in ast.iter_child_nodes(node):
        child_depth = get_ast_depth(child, current_depth + 1)
        max_depth = max(max_depth, child_depth)
    
    return max_depth