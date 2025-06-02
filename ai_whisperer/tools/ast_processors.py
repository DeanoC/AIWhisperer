"""
AST processing functions extracted from python_ast_json_tool.py
These are complex processing functions that can be imported on demand.
"""

import ast
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import time
def process_batch_files(files: List[str], action: str, options: Dict[str, Any], 
                       progress_callback=None) -> Dict[str, Any]:
    """Process multiple files in batch with progress tracking."""
    result = {
        'processed': 0,
        'failed': 0,
        'results': {},
        'errors': [],
        'summary': {
            'total_processing_time': 0,
            'average_processing_time': 0,
            'memory_usage': {}
        }
    }
    
    start_time = time.time()
    
    for i, file_path in enumerate(files):
        file_start = time.time()
        
        try:
            # Process individual file
            if action == 'to_json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                # Process the source
                # This is simplified - actual implementation would call the tool's method
                file_result = {'status': 'success', 'ast': ast.parse(source)}
            else:
                file_result = {'status': 'error', 'error': 'Unsupported batch action'}
            
            result['results'][file_path] = file_result
            result['processed'] += 1
            
        except Exception as e:
            result['errors'].append({
                'file': file_path,
                'error': str(e),
                'error_type': type(e).__name__
            })
            result['failed'] += 1
        
        # Progress callback
        if progress_callback:
            progress_callback(i + 1, len(files), file_path)
        
        # Update timing
        file_time = time.time() - file_start
        result['summary']['total_processing_time'] += file_time
    
    # Calculate summary statistics
    total_time = time.time() - start_time
    result['summary']['total_processing_time'] = total_time
    if result['processed'] > 0:
        result['summary']['average_processing_time'] = total_time / result['processed']
    
    return result

def generate_ast_statistics(tree: ast.AST) -> Dict[str, Any]:
    """Generate comprehensive statistics about an AST."""
    stats = {
        'node_counts': defaultdict(int),
        'depth': 0,
        'complexity': 0,
        'function_count': 0,
        'class_count': 0,
        'import_count': 0,
        'line_count': 0,
        'docstring_count': 0
    }
    
    # Count node types
    for node in ast.walk(tree):
        node_type = type(node).__name__
        stats['node_counts'][node_type] += 1
        
        # Special counters
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stats['function_count'] += 1
        elif isinstance(node, ast.ClassDef):
            stats['class_count'] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            stats['import_count'] += 1
        
        # Track line numbers
        if hasattr(node, 'lineno'):
            stats['line_count'] = max(stats['line_count'], node.lineno)
    
    # Calculate depth
    stats['depth'] = calculate_ast_depth(tree)
    
    # Calculate complexity
    stats['complexity'] = calculate_complexity_score(tree)
    
    # Convert defaultdict to regular dict
    stats['node_counts'] = dict(stats['node_counts'])
    
    return stats

def calculate_ast_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Calculate the maximum depth of an AST."""
    max_depth = current_depth
    
    for child in ast.iter_child_nodes(node):
        child_depth = calculate_ast_depth(child, current_depth + 1)
        max_depth = max(max_depth, child_depth)
    
    return max_depth

def calculate_complexity_score(tree: ast.AST) -> int:
    """Calculate a complexity score for an AST."""
    complexity = 0
    
    for node in ast.walk(tree):
        # Control flow adds complexity
        if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
            complexity += 2
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            complexity += 3
        elif isinstance(node, ast.Lambda):
            complexity += 1
        # Comprehensions add complexity
        elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            complexity += 2
        # Boolean operators
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    
    return complexity

def optimize_ast_for_size(tree: ast.AST) -> ast.AST:
    """Optimize AST for smaller JSON output."""
    class Optimizer(ast.NodeTransformer):
        def visit(self, node):
            # Remove optional fields that are None
            for field in list(node._fields):
                if hasattr(node, field) and getattr(node, field) is None:
                    delattr(node, field)
            
            # Remove empty lists
            for field in node._fields:
                if hasattr(node, field):
                    value = getattr(node, field)
                    if isinstance(value, list) and len(value) == 0:
                        delattr(node, field)
            
            return self.generic_visit(node)
    
    return Optimizer().visit(tree)

def validate_ast_structure(tree: ast.AST) -> List[Dict[str, Any]]:
    """Validate AST structure and return any issues found."""
    issues = []
    
    class Validator(ast.NodeVisitor):
        def __init__(self):
            self.issues = []
            self.context_stack = []
        
        def visit(self, node):
            self.context_stack.append(type(node).__name__)
            
            # Check for common issues
            if isinstance(node, ast.FunctionDef):
                # Check for missing return in non-void functions
                if node.returns and not self._has_return(node):
                    self.issues.append({
                        'type': 'missing_return',
                        'node': 'FunctionDef',
                        'name': node.name,
                        'line': getattr(node, 'lineno', None)
                    })
            
            elif isinstance(node, ast.Import):
                # Check for wildcard imports
                for alias in node.names:
                    if alias.name == '*':
                        self.issues.append({
                            'type': 'wildcard_import',
                            'line': getattr(node, 'lineno', None)
                        })
            
            self.generic_visit(node)
            self.context_stack.pop()
        
        def _has_return(self, func_node):
            for node in ast.walk(func_node):
                if isinstance(node, ast.Return) and node.value is not None:
                    return True
            return False
    
    validator = Validator()
    validator.visit(tree)
    
    return validator.issues

def extract_code_patterns(tree: ast.AST) -> Dict[str, List[Any]]:
    """Extract common code patterns from AST."""
    patterns = {
        'decorators': [],
        'context_managers': [],
        'comprehensions': [],
        'lambda_functions': [],
        'exception_handlers': [],
        'assertions': [],
        'type_annotations': []
    }
    
    for node in ast.walk(tree):
        # Decorators
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.decorator_list:
            for dec in node.decorator_list:
                patterns['decorators'].append({
                    'type': type(node).__name__,
                    'name': node.name,
                    'decorator': ast.unparse(dec) if hasattr(ast, 'unparse') else '<decorator>',
                    'line': getattr(node, 'lineno', None)
                })
        
        # Context managers
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            patterns['context_managers'].append({
                'type': type(node).__name__,
                'line': getattr(node, 'lineno', None)
            })
        
        # Comprehensions
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            patterns['comprehensions'].append({
                'type': type(node).__name__,
                'line': getattr(node, 'lineno', None)
            })
        
        # Lambda functions
        elif isinstance(node, ast.Lambda):
            patterns['lambda_functions'].append({
                'line': getattr(node, 'lineno', None)
            })
        
        # Exception handlers
        elif isinstance(node, ast.ExceptHandler):
            patterns['exception_handlers'].append({
                'type': node.type.id if node.type and hasattr(node.type, 'id') else 'bare',
                'line': getattr(node, 'lineno', None)
            })
        
        # Assertions
        elif isinstance(node, ast.Assert):
            patterns['assertions'].append({
                'line': getattr(node, 'lineno', None)
            })
        
        # Type annotations
        elif isinstance(node, ast.AnnAssign):
            patterns['type_annotations'].append({
                'target': ast.unparse(node.target) if hasattr(ast, 'unparse') else '<target>',
                'annotation': ast.unparse(node.annotation) if hasattr(ast, 'unparse') else '<type>',
                'line': getattr(node, 'lineno', None)
            })
    
    return patterns
