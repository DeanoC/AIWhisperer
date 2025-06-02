"""
Code formatting and style utilities
"""

import re
from typing import Dict, Any, List


def calculate_formatting_metrics(source: str) -> Dict[str, Any]:
    """Calculate formatting metrics for source code."""
    lines = source.split('\n')
    
    # Detect indentation style
    indentation_counts = defaultdict(int)
    for line in lines:
        if line.strip() and line[0] in ' \t':
            indent = ''
            for char in line:
                if char in ' \t':
                    indent += char
                else:
                    break
            if indent:
                indentation_counts[indent] += 1
    
    # Determine predominant indentation
    indentation_style = 'none'
    indentation_size = 0
    if indentation_counts:
        # Find most common indentation pattern
        common_indent = max(indentation_counts.items(), key=lambda x: x[1])[0]
        if '\t' in common_indent:
            indentation_style = 'tabs'
        else:
            indentation_style = 'spaces'
            indentation_size = len(common_indent)
    
    # Detect quote preferences
    single_quotes = source.count("'")
    double_quotes = source.count('"')
    quote_style = 'single' if single_quotes > double_quotes else 'double'
    
    # Line length statistics
    line_lengths = [len(line) for line in lines if line.strip()]
    max_line_length = max(line_lengths) if line_lengths else 0
    avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0
    
    # Blank line patterns
    blank_lines = sum(1 for line in lines if not line.strip())
    
    return {
        'indentation': {
            'style': indentation_style,
            'size': indentation_size
        },
        'quote_style': quote_style,
        'line_endings': '\n',  # Default to Unix style
        'line_length': {
            'max': max_line_length,
            'average': avg_line_length
        },
        'blank_lines': blank_lines,
        'total_lines': len(lines)
    }

