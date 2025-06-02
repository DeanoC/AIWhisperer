"""
Constants and data structures for Python AST JSON tool.
Extracted to reduce main module size and improve import time.
"""

# Error type mappings
ERROR_TYPE_MAPPINGS = {
    FileNotFoundError: 'file_not_found',
    PermissionError: 'permission_denied',
    IsADirectoryError: 'is_directory',
    NotADirectoryError: 'not_directory',
    OSError: 'os_error',
    IOError: 'io_error',
    UnicodeDecodeError: 'encoding_error',
    UnicodeError: 'unicode_error',
    SyntaxError: 'syntax_error',
    IndentationError: 'indentation_error',
    TabError: 'tab_error',
    ValueError: 'value_error',
    TypeError: 'type_error',
    AttributeError: 'attribute_error',
    KeyError: 'key_error',
    MemoryError: 'memory_exhaustion',
    RecursionError: 'recursion_limit_exceeded',
    TimeoutError: 'network_timeout',
    Exception: 'unknown_error'
}

# AST node type mappings
AST_NODE_TYPES = {
    'Module': 'module',
    'FunctionDef': 'function',
    'AsyncFunctionDef': 'async_function',
    'ClassDef': 'class',
    'Return': 'return',
    'Delete': 'delete',
    'Assign': 'assign',
    'AugAssign': 'aug_assign',
    'AnnAssign': 'ann_assign',
    'For': 'for',
    'AsyncFor': 'async_for',
    'While': 'while',
    'If': 'if',
    'With': 'with',
    'AsyncWith': 'async_with',
    'Raise': 'raise',
    'Try': 'try',
    'Assert': 'assert',
    'Import': 'import',
    'ImportFrom': 'import_from',
    'Global': 'global',
    'Nonlocal': 'nonlocal',
    'Expr': 'expr',
    'Pass': 'pass',
    'Break': 'break',
    'Continue': 'continue',
}

# Built-in types that need special handling
BUILTIN_TYPES = {
    'int', 'float', 'str', 'bool', 'list', 'dict', 'tuple', 'set',
    'frozenset', 'bytes', 'bytearray', 'complex', 'range', 'slice',
    'NoneType', 'type', 'function', 'method', 'module', 'generator',
    'iterator', 'property', 'staticmethod', 'classmethod'
}

# Python operators
OPERATORS = {
    'Add': '+',
    'Sub': '-',
    'Mult': '*',
    'Div': '/',
    'Mod': '%',
    'Pow': '**',
    'LShift': '<<',
    'RShift': '>>',
    'BitOr': '|',
    'BitXor': '^',
    'BitAnd': '&',
    'FloorDiv': '//',
    'MatMult': '@'
}

# Comparison operators
COMPARE_OPS = {
    'Eq': '==',
    'NotEq': '!=',
    'Lt': '<',
    'LtE': '<=',
    'Gt': '>',
    'GtE': '>=',
    'Is': 'is',
    'IsNot': 'is not',
    'In': 'in',
    'NotIn': 'not in'
}

# Default processing limits
DEFAULT_LIMITS = {
    'max_depth': 1000,
    'max_nodes': 50000,
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'timeout_seconds': 60,
    'max_batch_files': 1000,
    'checkpoint_interval': 100
}

# Reconstruction modes
RECONSTRUCTION_MODES = {
    'minimal': {
        'include_docstrings': False,
        'include_comments': False,
        'include_type_comments': False,
        'preserve_formatting': False
    },
    'docstrings': {
        'include_docstrings': True,
        'include_comments': False,
        'include_type_comments': False,
        'preserve_formatting': False
    },
    'comments': {
        'include_docstrings': True,
        'include_comments': True,
        'include_type_comments': True,
        'preserve_formatting': False
    },
    'formatted': {
        'include_docstrings': True,
        'include_comments': True,
        'include_type_comments': True,
        'preserve_formatting': True
    },
    'complete': {
        'include_docstrings': True,
        'include_comments': True,
        'include_type_comments': True,
        'preserve_formatting': True,
        'include_metadata': True
    }
}