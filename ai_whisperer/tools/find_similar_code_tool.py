"""
Find Similar Code Tool - Searches for code similar to proposed features
"""
import os
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from collections import defaultdict

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class FindSimilarCodeTool(AITool):
    """Tool for finding code similar to proposed features or patterns."""
    
    # Common code patterns to search for
    FEATURE_PATTERNS = {
        'caching': [
            r'cache',
            r'Cache',
            r'lru_cache',
            r'memoize',
            r'redis',
            r'memcache',
            r'_cache\s*=',
            r'\.get_from_cache',
            r'\.set_cache'
        ],
        'authentication': [
            r'auth',
            r'Auth',
            r'login',
            r'logout',
            r'token',
            r'jwt',
            r'session',
            r'password',
            r'authenticate',
            r'authorization'
        ],
        'database': [
            r'database',
            r'Database',
            r'query',
            r'SELECT\s+',
            r'INSERT\s+',
            r'UPDATE\s+',
            r'DELETE\s+',
            r'\.execute\(',
            r'connection',
            r'cursor'
        ],
        'api': [
            r'api',
            r'API',
            r'endpoint',
            r'route',
            r'@app\.route',
            r'@router\.',
            r'request\.',
            r'response\.',
            r'REST',
            r'GraphQL'
        ],
        'file_operations': [
            r'open\(',
            r'\.read\(',
            r'\.write\(',
            r'file_path',
            r'filepath',
            r'os\.path',
            r'pathlib',
            r'Path\(',
            r'\.exists\(',
            r'\.is_file\('
        ],
        'testing': [
            r'test_',
            r'Test',
            r'assert',
            r'mock',
            r'Mock',
            r'pytest',
            r'unittest',
            r'\.test\(',
            r'describe\(',
            r'it\('
        ],
        'logging': [
            r'logger',
            r'Logger',
            r'logging',
            r'\.info\(',
            r'\.debug\(',
            r'\.error\(',
            r'\.warning\(',
            r'log_',
            r'console\.log'
        ],
        'configuration': [
            r'config',
            r'Config',
            r'settings',
            r'Settings',
            r'\.env',
            r'environment',
            r'yaml',
            r'json',
            r'\.load_config',
            r'parse_args'
        ],
        'validation': [
            r'validate',
            r'Validate',
            r'validator',
            r'is_valid',
            r'check_',
            r'verify',
            r'sanitize',
            r'schema',
            r'Schema',
            r'pydantic'
        ],
        'error_handling': [
            r'try:',
            r'except',
            r'catch',
            r'throw',
            r'raise',
            r'Error',
            r'Exception',
            r'finally:',
            r'\.catch\(',
            r'error_handler'
        ]
    }
    
    @property
    def name(self) -> str:
        return "find_similar_code"
    
    @property
    def description(self) -> str:
        return "Find code similar to proposed features or patterns in the codebase."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "feature": {
                    "type": "string",
                    "description": "Feature or concept to search for (e.g., 'caching', 'authentication')"
                },
                "custom_patterns": {
                    "type": "array",
                    "description": "Custom regex patterns to search for",
                    "items": {"type": "string"},
                    "nullable": True
                },
                "file_types": {
                    "type": "array",
                    "description": "File extensions to search (e.g., ['.py', '.js'])",
                    "items": {"type": "string"},
                    "nullable": True
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of files to return",
                    "default": 20
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines around matches",
                    "default": 2
                }
            },
            "required": ["feature"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Code Analysis"
    
    @property
    def tags(self) -> List[str]:
        return ["analysis", "codebase", "search", "pattern_matching", "similarity"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'find_similar_code' tool to find existing code similar to proposed features.
        Parameters:
        - feature (string, required): Feature to search for (e.g., 'caching', 'authentication')
        - custom_patterns (array, optional): Custom regex patterns
        - file_types (array, optional): File extensions to search
        - max_results (integer, optional): Max files to return (default: 20)
        - context_lines (integer, optional): Context lines around matches (default: 2)
        
        Predefined features: caching, authentication, database, api, file_operations,
        testing, logging, configuration, validation, error_handling
        
        Example usage:
        <tool_code>
        find_similar_code(feature="caching")
        find_similar_code(feature="api", file_types=[".py"])
        find_similar_code(feature="custom", custom_patterns=["async def", "await"])
        </tool_code>
        """
    
    def _get_patterns_for_feature(self, feature: str, custom_patterns: Optional[List[str]]) -> List[str]:
        """Get search patterns for a feature."""
        feature_lower = feature.lower()
        
        # Use predefined patterns if available
        if feature_lower in self.FEATURE_PATTERNS:
            patterns = self.FEATURE_PATTERNS[feature_lower]
        else:
            # Generate basic patterns from feature name
            patterns = [
                feature,
                feature.lower(),
                feature.upper(),
                feature.capitalize(),
                f"_{feature.lower()}",
                f"{feature.lower()}_",
                f"get_{feature.lower()}",
                f"set_{feature.lower()}",
                f"{feature.lower()}s?"  # Plural
            ]
        
        # Add custom patterns if provided
        if custom_patterns:
            patterns.extend(custom_patterns)
        
        return patterns
    
    def _calculate_relevance_score(self, content: str, patterns: List[str]) -> Tuple[int, Dict[str, int]]:
        """Calculate relevance score based on pattern matches."""
        score = 0
        pattern_counts = defaultdict(int)
        
        for pattern in patterns:
            try:
                matches = len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
                if matches > 0:
                    pattern_counts[pattern] = matches
                    # Higher weight for exact feature name matches
                    if pattern.lower() == patterns[0].lower():
                        score += matches * 3
                    else:
                        score += matches
            except re.error:
                # Skip invalid regex patterns
                pass
        
        return score, dict(pattern_counts)
    
    def _extract_context(self, content: str, pattern: str, context_lines: int) -> List[Dict[str, Any]]:
        """Extract context around pattern matches."""
        lines = content.split('\n')
        contexts = []
        
        try:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                # Find line number
                line_start = content.count('\n', 0, match.start()) + 1
                
                # Calculate context range
                start_line = max(1, line_start - context_lines)
                end_line = min(len(lines), line_start + context_lines)
                
                # Extract context
                context_lines_text = lines[start_line-1:end_line]
                
                contexts.append({
                    'line': line_start,
                    'match': match.group(),
                    'context': '\n'.join(context_lines_text),
                    'pattern': pattern
                })
        except:
            pass
        
        return contexts
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute similar code search."""
        feature = arguments.get('feature')
        custom_patterns = arguments.get('custom_patterns', [])
        file_types = arguments.get('file_types')
        max_results = arguments.get('max_results', 20)
        context_lines = arguments.get('context_lines', 2)
        
        if not feature:
            return "Error: 'feature' is required."
        
        try:
            path_manager = PathManager.get_instance()
            workspace_path = Path(path_manager.workspace_path)
            
            # Get search patterns
            patterns = self._get_patterns_for_feature(feature, custom_patterns)
            
            # Results storage
            results = []
            ignored_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                          'env', 'build', 'dist', 'target', '.idea', '.vscode'}
            
            # Search files
            for file_path in workspace_path.rglob('*'):
                # Skip ignored directories
                if any(part in ignored_dirs for part in file_path.parts):
                    continue
                
                if file_path.is_file():
                    # Check file type filter
                    if file_types and file_path.suffix not in file_types:
                        continue
                    
                    # Skip binary files
                    if file_path.suffix in ['.pyc', '.pyo', '.so', '.dll', '.exe', 
                                          '.zip', '.tar', '.gz', '.jpg', '.png', '.gif']:
                        continue
                    
                    try:
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Calculate relevance
                        score, pattern_counts = self._calculate_relevance_score(content, patterns)
                        
                        if score > 0:
                            # Get example contexts
                            all_contexts = []
                            for pattern, count in pattern_counts.items():
                                contexts = self._extract_context(content, pattern, context_lines)
                                all_contexts.extend(contexts[:2])  # Limit contexts per pattern
                            
                            results.append({
                                'path': file_path.relative_to(workspace_path),
                                'score': score,
                                'pattern_counts': pattern_counts,
                                'contexts': all_contexts[:5],  # Limit total contexts
                                'language': self._detect_language(file_path)
                            })
                    except:
                        # Skip files that can't be read
                        pass
            
            # Sort by relevance score
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:max_results]
            
            # Build response
            response = f"**Similar Code Search: '{feature}'**\n"
            response += f"Searched patterns: {', '.join(patterns[:5])}"
            if len(patterns) > 5:
                response += f" and {len(patterns) - 5} more"
            response += "\n\n"
            
            if results:
                response += f"Found {len(results)} relevant files:\n\n"
                
                for i, result in enumerate(results, 1):
                    response += f"## {i}. {result['path']} (Score: {result['score']})\n"
                    response += f"Language: {result['language']}\n"
                    
                    # Show pattern match summary
                    response += "Matches: "
                    match_summary = []
                    for pattern, count in sorted(result['pattern_counts'].items(), 
                                               key=lambda x: x[1], reverse=True)[:3]:
                        match_summary.append(f"`{pattern}` ({count})")
                    response += ", ".join(match_summary)
                    response += "\n\n"
                    
                    # Show example contexts
                    if result['contexts']:
                        response += "Example matches:\n"
                        for ctx in result['contexts'][:2]:
                            response += f"\n```{result['language'].lower()}\n"
                            response += f"# Line {ctx['line']} (matched: '{ctx['match']}')\n"
                            response += ctx['context']
                            response += "\n```\n"
                    
                    response += "\n"
            else:
                response += f"No code similar to '{feature}' found in the codebase.\n\n"
                response += "Suggestions:\n"
                response += "- Try broader search terms\n"
                response += "- Use custom patterns for specific code constructs\n"
                response += "- Check if the feature might be named differently\n"
            
            # Add summary
            if results:
                response += "## Summary\n\n"
                
                # Language distribution
                lang_counts = defaultdict(int)
                for r in results:
                    lang_counts[r['language']] += 1
                
                response += "**Languages**: "
                response += ", ".join([f"{lang} ({count})" for lang, count in 
                                     sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)])
                response += "\n\n"
                
                # Common patterns
                all_patterns = defaultdict(int)
                for r in results:
                    for pattern, count in r['pattern_counts'].items():
                        all_patterns[pattern] += count
                
                top_patterns = sorted(all_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
                if top_patterns:
                    response += "**Most common patterns**: "
                    response += ", ".join([f"`{p}` ({c})" for p, c in top_patterns])
                    response += "\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error finding similar code: {e}")
            return f"Error finding similar code: {str(e)}"
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext_to_lang = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.sh': 'Shell',
            '.sql': 'SQL',
            '.html': 'HTML',
            '.css': 'CSS',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.md': 'Markdown'
        }
        
        return ext_to_lang.get(file_path.suffix.lower(), 'Text')