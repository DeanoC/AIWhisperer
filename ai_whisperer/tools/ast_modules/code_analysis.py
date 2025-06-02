"""
Code analysis and metrics extraction
"""

import ast
import tokenize
import io
from typing import Dict, Any, List
from collections import defaultdict


def extract_comments_from_source(source: str) -> List[Dict[str, Any]]:
    """Extract comments from Python source code."""
    comments = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comments.append({
                    'line': tok.start[0],
                    'column': tok.start[1],
                    'text': tok.string,
                    'end_line': tok.end[0],
                    'end_column': tok.end[1]
                })
    except tokenize.TokenError:
        # Handle incomplete source
        pass
    return comments


def extract_docstring_info(node: ast.AST) -> Optional[Dict[str, Any]]:
    """Extract docstring information from AST node."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        if hasattr(node, 'body') and node.body:
            first = node.body[0]
            if (isinstance(first, ast.Expr) and 
                isinstance(first.value, ast.Constant) and
                isinstance(first.value.value, str)):
                return {
                    'value': first.value.value,
                    'lineno': getattr(first, 'lineno', None),
                    'col_offset': getattr(first, 'col_offset', None),
                    'end_lineno': getattr(first, 'end_lineno', None),
                    'end_col_offset': getattr(first, 'end_col_offset', None)
                }
    return None


    def _extract_metadata(self, tree, source_code: str) -> Dict[str, Any]:
        """Extract metadata from AST and source code."""
        metadata = {
            'functions': [],
            'classes': [],
            'imports': [],
            'docstrings': {},
            'complexity_metrics': {}
        }
        
        # Walk the AST to extract metadata
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line_number': getattr(node, 'lineno', 0),
                    'parameters': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node)
                }
                metadata['functions'].append(func_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line_number': getattr(node, 'lineno', 0),
                    'base_classes': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                    'docstring': ast.get_docstring(node)
                }
                metadata['classes'].append(class_info)
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        metadata['imports'].append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'type': 'import'
                        })
                else:  # ImportFrom
                    for alias in node.names:
                        metadata['imports'].append({
                            'module': node.module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'type': 'from_import'
                        })
        
        # Extract module-level docstring
        if (isinstance(tree, ast.Module) and tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            metadata['docstrings']['module'] = tree.body[0].value.value
        
        return metadata
    


    def _extract_comments(self, source_code: str) -> List[Dict[str, Any]]:
        """Extract comments from source code."""
        comments = []
        lines = source_code.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Find comments (simple implementation)
            in_string = False
            quote_char = None
            i = 0
            
            while i < len(line):
                char = line[i]
                
                if not in_string and char == '#':
                    comment_text = line[i+1:].strip()
                    if comment_text:  # Don't include empty comments
                        comments.append({
                            'line_number': line_num,
                            'column': i,
                            'text': comment_text,
                            'type': 'inline' if line[:i].strip() else 'standalone'
                        })
                    break
                
                elif char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                
                i += 1
        
        return comments
    

