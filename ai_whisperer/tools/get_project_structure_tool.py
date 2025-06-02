"""
Module: ai_whisperer/tools/get_project_structure_tool.py
Purpose: AI tool implementation for get project structure

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- GetProjectStructureTool: Tool for analyzing and understanding project structure and organization.

Usage:
    tool = GetProjectStructureTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- collections

Related:
- See PHASE_CONSOLIDATED_SUMMARY.md

"""

from typing import Any, Dict, List, Optional, Type

import logging
from pathlib import Path
from collections import defaultdict

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

class GetProjectStructureTool(AITool):
    """Tool for analyzing and understanding project structure and organization."""
    
    # Common directory patterns and their purposes
    DIRECTORY_PATTERNS = {
        'src': 'Source code',
        'lib': 'Library code',
        'app': 'Application code',
        'core': 'Core functionality',
        'api': 'API endpoints/interfaces',
        'models': 'Data models/schemas',
        'views': 'View/UI components',
        'controllers': 'Controller logic',
        'services': 'Service layer',
        'utils': 'Utility functions',
        'helpers': 'Helper functions',
        'common': 'Common/shared code',
        'shared': 'Shared resources',
        'components': 'UI components',
        'pages': 'Page components',
        'routes': 'Routing logic',
        'middleware': 'Middleware functions',
        'handlers': 'Request handlers',
        'repositories': 'Data repositories',
        'database': 'Database related',
        'db': 'Database files/migrations',
        'migrations': 'Database migrations',
        'schemas': 'Data schemas',
        'tests': 'Test files',
        'test': 'Test files',
        'spec': 'Test specifications',
        '__tests__': 'Jest tests',
        'e2e': 'End-to-end tests',
        'unit': 'Unit tests',
        'integration': 'Integration tests',
        'fixtures': 'Test fixtures',
        'mocks': 'Mock data/objects',
        'docs': 'Documentation',
        'documentation': 'Documentation',
        'examples': 'Example code',
        'samples': 'Sample code',
        'demo': 'Demo code',
        'scripts': 'Utility scripts',
        'bin': 'Executable scripts',
        'tools': 'Development tools',
        'config': 'Configuration files',
        'configs': 'Configuration files',
        'settings': 'Settings files',
        'public': 'Public assets',
        'static': 'Static files',
        'assets': 'Asset files',
        'images': 'Image files',
        'styles': 'Style files',
        'css': 'CSS files',
        'scss': 'SCSS files',
        'templates': 'Template files',
        'layouts': 'Layout templates',
        'vendor': 'Third-party code',
        'node_modules': 'Node.js dependencies',
        'packages': 'Package definitions',
        'modules': 'Code modules',
        'plugins': 'Plugin code',
        'extensions': 'Extensions',
        'build': 'Build output',
        'dist': 'Distribution files',
        'out': 'Output files',
        'target': 'Build target',
        'logs': 'Log files',
        'temp': 'Temporary files',
        'tmp': 'Temporary files',
        'cache': 'Cache files',
        '.git': 'Git repository',
        '.github': 'GitHub configuration',
        '.vscode': 'VS Code settings',
        '.idea': 'IntelliJ IDEA settings'
    }
    
    # Important files to identify
    IMPORTANT_FILES = {
        # Documentation
        'README.md': 'Project documentation',
        'README.rst': 'Project documentation',
        'README.txt': 'Project documentation',
        'CONTRIBUTING.md': 'Contribution guidelines',
        'CODE_OF_CONDUCT.md': 'Code of conduct',
        'LICENSE': 'License file',
        'CHANGELOG.md': 'Change log',
        'TODO.md': 'TODO list',
        
        # Configuration
        'package.json': 'Node.js project config',
        'requirements.txt': 'Python dependencies',
        'setup.py': 'Python package setup',
        'pyproject.toml': 'Python project config',
        'Pipfile': 'Pipenv config',
        'Cargo.toml': 'Rust project config',
        'go.mod': 'Go module config',
        'pom.xml': 'Maven project config',
        'build.gradle': 'Gradle build config',
        'composer.json': 'PHP project config',
        'Gemfile': 'Ruby dependencies',
        
        # Build/CI
        'Makefile': 'Make build config',
        'Dockerfile': 'Docker container config',
        'docker-compose.yml': 'Docker compose config',
        '.dockerignore': 'Docker ignore patterns',
        '.gitignore': 'Git ignore patterns',
        'Jenkinsfile': 'Jenkins CI config',
        '.travis.yml': 'Travis CI config',
        '.gitlab-ci.yml': 'GitLab CI config',
        '.github/workflows': 'GitHub Actions',
        
        # Entry points
        'main.py': 'Python entry point',
        'app.py': 'Python app entry',
        'index.js': 'JavaScript entry point',
        'index.ts': 'TypeScript entry point',
        'main.js': 'JavaScript main',
        'main.go': 'Go entry point',
        'main.rs': 'Rust entry point',
        'Main.java': 'Java entry point',
        'index.html': 'Web entry point',
        'index.php': 'PHP entry point',
        
        # Config files
        'config.yaml': 'Configuration',
        'config.yml': 'Configuration',
        'config.json': 'Configuration',
        'settings.py': 'Python settings',
        'tsconfig.json': 'TypeScript config',
        'webpack.config.js': 'Webpack config',
        'jest.config.js': 'Jest test config',
        'pytest.ini': 'Pytest config',
        '.eslintrc.js': 'ESLint config',
        '.prettierrc': 'Prettier config'
    }
    
    @property
    def name(self) -> str:
        return "get_project_structure"
    
    @property
    def description(self) -> str:
        return "Analyze and understand the project's directory structure and organization."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to analyze (defaults to workspace root)",
                    "nullable": True
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum directory depth to analyze",
                    "default": 4
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Include important files in the analysis",
                    "default": True
                },
                "show_tree": {
                    "type": "boolean",
                    "description": "Show ASCII directory tree",
                    "default": False
                }
            }
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Code Analysis"
    
    @property
    def tags(self) -> List[str]:
        return ["analysis", "codebase", "project_structure", "organization"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'get_project_structure' tool to understand project organization.
        Parameters:
        - path (string, optional): Path to analyze (defaults to workspace root)
        - max_depth (integer, optional): Max directory depth (default: 4)
        - include_files (boolean, optional): Include important files (default: true)
        - show_tree (boolean, optional): Show ASCII tree (default: false)
        
        This tool helps understand how the project is organized.
        Example usage:
        <tool_code>
        get_project_structure()
        get_project_structure(show_tree=True, max_depth=3)
        get_project_structure(path="src")
        </tool_code>
        """
    
    def _analyze_directory(self, path: Path, base_path: Path, depth: int, 
                          max_depth: int, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively analyze directory structure."""
        if depth > max_depth:
            return None
        
        dir_info = {
            'name': path.name,
            'type': 'directory',
            'relative_path': str(path.relative_to(base_path)),
            'purpose': self._identify_purpose(path.name),
            'children': [],
            'file_count': 0,
            'subdir_count': 0
        }
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                if item.is_dir():
                    # Skip common ignored directories
                    if item.name in {'.git', '__pycache__', 'node_modules', '.venv', 
                                   'venv', 'env', '.pytest_cache', '.mypy_cache'}:
                        continue
                    
                    subdir = self._analyze_directory(item, base_path, depth + 1, max_depth, stats)
                    if subdir:
                        dir_info['children'].append(subdir)
                        dir_info['subdir_count'] += 1
                        stats['total_dirs'] += 1
                elif item.is_file():
                    dir_info['file_count'] += 1
                    stats['total_files'] += 1
                    
                    # Track important files
                    if item.name in self.IMPORTANT_FILES:
                        stats['important_files'].append({
                            'name': item.name,
                            'path': str(item.relative_to(base_path)),
                            'purpose': self.IMPORTANT_FILES[item.name]
                        })
                    
                    # Track file types
                    ext = item.suffix.lower()
                    if ext:
                        stats['extensions'][ext] += 1
        except PermissionError:
            pass
        
        return dir_info
    
    def _identify_purpose(self, dir_name: str) -> str:
        """Identify the purpose of a directory based on its name."""
        dir_lower = dir_name.lower()
        
        # Check exact matches first
        if dir_lower in self.DIRECTORY_PATTERNS:
            return self.DIRECTORY_PATTERNS[dir_lower]
        
        # Check partial matches
        for pattern, purpose in self.DIRECTORY_PATTERNS.items():
            if pattern in dir_lower or dir_lower in pattern:
                return purpose
        
        # Check common suffixes
        if dir_lower.endswith('s') and dir_lower[:-1] in self.DIRECTORY_PATTERNS:
            return self.DIRECTORY_PATTERNS[dir_lower[:-1]] + " (plural)"
        
        return "Custom directory"
    
    def _build_tree(self, structure: Dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
        """Build ASCII tree representation."""
        tree = ""
        
        # Current item
        connector = "└── " if is_last else "├── "
        tree += prefix + connector + structure['name']
        
        if structure['type'] == 'directory':
            purpose = structure.get('purpose', '')
            if purpose and purpose != "Custom directory":
                tree += f" ({purpose})"
            if structure['file_count'] > 0:
                tree += f" [{structure['file_count']} files]"
        
        tree += "\n"
        
        # Children
        if 'children' in structure:
            extension = "    " if is_last else "│   "
            for i, child in enumerate(structure['children']):
                is_last_child = i == len(structure['children']) - 1
                tree += self._build_tree(child, prefix + extension, is_last_child)
        
        return tree
    
    def _identify_project_components(self, structure: Dict[str, Any], 
                                   important_files: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """Identify key project components from structure."""
        components = defaultdict(list)
        
        def traverse(node: Dict[str, Any], path: str = ""):
            current_path = f"{path}/{node['name']}" if path else node['name']
            
            # Categorize based on directory purpose
            purpose = node.get('purpose', '').lower()
            
            if 'source' in purpose or 'src' in node['name'].lower():
                components['source_roots'].append(current_path)
            elif 'test' in purpose:
                components['test_roots'].append(current_path)
            elif 'doc' in purpose:
                components['doc_roots'].append(current_path)
            elif 'api' in purpose or 'endpoint' in purpose:
                components['api_dirs'].append(current_path)
            elif 'model' in purpose or 'schema' in purpose:
                components['model_dirs'].append(current_path)
            elif 'config' in purpose or 'setting' in purpose:
                components['config_dirs'].append(current_path)
            elif 'script' in purpose or 'tool' in purpose:
                components['script_dirs'].append(current_path)
            elif 'component' in purpose or 'view' in purpose or 'page' in purpose:
                components['ui_dirs'].append(current_path)
            
            # Traverse children
            for child in node.get('children', []):
                traverse(child, current_path)
        
        traverse(structure)
        
        # Identify entry points from important files
        for file_info in important_files:
            if 'entry point' in file_info['purpose'].lower():
                components['entry_points'].append(file_info['path'])
            elif 'config' in file_info['purpose'].lower():
                components['config_files'].append(file_info['path'])
            elif 'documentation' in file_info['purpose'].lower():
                components['docs'].append(file_info['path'])
        
        return dict(components)
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute project structure analysis."""
        path = arguments.get('path', '.')
        max_depth = arguments.get('max_depth', 4)
        include_files = arguments.get('include_files', True)
        show_tree = arguments.get('show_tree', False)
        
        try:
            path_manager = PathManager.get_instance()
            
            # Resolve path
            if path == '.':
                root_path = Path(path_manager.workspace_path)
            else:
                root_path = Path(path_manager.resolve_path(path))
            
            if not root_path.exists():
                return f"Error: Path '{path}' does not exist."
            
            # Initialize statistics
            stats = {
                'total_dirs': 1,  # Include root
                'total_files': 0,
                'extensions': defaultdict(int),
                'important_files': []
            }
            
            # Analyze structure
            structure = self._analyze_directory(root_path, root_path, 0, max_depth, stats)
            
            # Build response
            response = f"**Project Structure Analysis: {root_path.name}**\n\n"
            
            # Overview statistics
            response += "## Overview\n"
            response += f"- Total directories: {stats['total_dirs']}\n"
            response += f"- Total files: {stats['total_files']}\n"
            response += f"- Directory depth analyzed: {max_depth}\n\n"
            
            # Important files
            if include_files and stats['important_files']:
                response += "## Key Files\n"
                for file_info in stats['important_files']:
                    response += f"- **{file_info['name']}**: {file_info['purpose']} "
                    response += f"(at {file_info['path']})\n"
                response += "\n"
            
            # Project components
            components = self._identify_project_components(structure, stats['important_files'])
            if components:
                response += "## Project Components\n"
                
                if components.get('source_roots'):
                    response += f"- **Source roots**: {', '.join(components['source_roots'])}\n"
                if components.get('test_roots'):
                    response += f"- **Test directories**: {', '.join(components['test_roots'])}\n"
                if components.get('api_dirs'):
                    response += f"- **API/Endpoints**: {', '.join(components['api_dirs'])}\n"
                if components.get('model_dirs'):
                    response += f"- **Models/Schemas**: {', '.join(components['model_dirs'])}\n"
                if components.get('ui_dirs'):
                    response += f"- **UI Components**: {', '.join(components['ui_dirs'])}\n"
                if components.get('config_dirs'):
                    response += f"- **Configuration**: {', '.join(components['config_dirs'])}\n"
                if components.get('entry_points'):
                    response += f"- **Entry points**: {', '.join(components['entry_points'])}\n"
                
                response += "\n"
            
            # File type distribution
            if stats['extensions']:
                response += "## File Types\n"
                sorted_exts = sorted(stats['extensions'].items(), 
                                   key=lambda x: x[1], reverse=True)[:10]
                for ext, count in sorted_exts:
                    response += f"- {ext}: {count} files\n"
                if len(stats['extensions']) > 10:
                    response += f"- ... and {len(stats['extensions']) - 10} more types\n"
                response += "\n"
            
            # Directory tree
            if show_tree:
                response += "## Directory Tree\n```\n"
                response += structure['name'] + "/\n"
                for i, child in enumerate(structure['children']):
                    is_last = i == len(structure['children']) - 1
                    response += self._build_tree(child, "", is_last)
                response += "```\n\n"
            
            # Key directories with purposes
            response += "## Key Directories\n"
            
            def list_key_dirs(node: Dict[str, Any], indent: int = 0):
                result = ""
                if node.get('purpose') and node.get('purpose') != "Custom directory":
                    prefix = "  " * indent + "- "
                    result += f"{prefix}**{node['name']}**: {node['purpose']}\n"
                    
                    # Show selected important subdirectories
                    important_children = [
                        child for child in node.get('children', [])
                        if child.get('purpose') and child.get('purpose') != "Custom directory"
                    ][:3]  # Limit to 3 subdirs
                    
                    for child in important_children:
                        result += list_key_dirs(child, indent + 1)
                
                return result
            
            dirs_text = ""
            for child in structure['children']:
                dirs_text += list_key_dirs(child)
            
            if dirs_text:
                response += dirs_text
            else:
                response += "No standard directories detected.\n"
            
            response += "\n"
            
            # Project type inference
            response += "## Project Type Analysis\n"
            
            # Determine project type based on files and structure
            project_types = []
            
            # Check for web frameworks
            if any(f['name'] == 'package.json' for f in stats['important_files']):
                if components.get('ui_dirs'):
                    project_types.append("JavaScript/TypeScript Web Application")
                else:
                    project_types.append("Node.js Application")
            
            if any(f['name'] in ['requirements.txt', 'setup.py', 'pyproject.toml'] 
                  for f in stats['important_files']):
                project_types.append("Python Project")
            
            if any(f['name'] in ['Cargo.toml'] for f in stats['important_files']):
                project_types.append("Rust Project")
            
            if any(f['name'] in ['go.mod'] for f in stats['important_files']):
                project_types.append("Go Project")
            
            if components.get('api_dirs'):
                project_types.append("API/Backend Service")
            
            if components.get('test_roots'):
                project_types.append("Has Test Suite")
            
            if project_types:
                response += "This appears to be: " + ", ".join(project_types)
            else:
                response += "Project type could not be determined from structure."
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing project structure: {e}")
            return f"Error analyzing project structure: {str(e)}"
