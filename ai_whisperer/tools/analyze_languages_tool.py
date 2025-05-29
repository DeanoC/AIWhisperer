"""
Analyze Languages Tool - Detects programming languages used in the project
"""
import os
import logging
import json
from typing import Dict, Any, Optional, List, Set
from pathlib import Path
from collections import defaultdict

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class AnalyzeLanguagesTool(AITool):
    """Tool for analyzing programming languages used in the project."""
    
    # Common language extensions
    LANGUAGE_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript (React)',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript (React)',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.R': 'R',
        '.m': 'MATLAB/Objective-C',
        '.lua': 'Lua',
        '.pl': 'Perl',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.ps1': 'PowerShell',
        '.bat': 'Batch',
        '.cmd': 'Batch',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.xml': 'XML',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.cfg': 'Config',
        '.conf': 'Config',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX',
        '.vue': 'Vue.js',
        '.svelte': 'Svelte',
        '.elm': 'Elm',
        '.clj': 'Clojure',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.erl': 'Erlang',
        '.hrl': 'Erlang',
        '.ml': 'OCaml',
        '.mli': 'OCaml',
        '.fs': 'F#',
        '.fsx': 'F#',
        '.vb': 'Visual Basic',
        '.dart': 'Dart',
        '.zig': 'Zig',
        '.nim': 'Nim',
        '.jl': 'Julia',
        '.sol': 'Solidity',
    }
    
    # Package files that indicate frameworks/languages
    PACKAGE_FILES = {
        'package.json': 'Node.js/JavaScript',
        'package-lock.json': 'Node.js/JavaScript',
        'yarn.lock': 'Node.js/JavaScript',
        'requirements.txt': 'Python',
        'setup.py': 'Python',
        'pyproject.toml': 'Python',
        'Pipfile': 'Python',
        'poetry.lock': 'Python',
        'Gemfile': 'Ruby',
        'Gemfile.lock': 'Ruby',
        'pom.xml': 'Java/Maven',
        'build.gradle': 'Java/Gradle',
        'build.gradle.kts': 'Kotlin/Gradle',
        'Cargo.toml': 'Rust',
        'Cargo.lock': 'Rust',
        'go.mod': 'Go',
        'go.sum': 'Go',
        'composer.json': 'PHP',
        'composer.lock': 'PHP',
        'CMakeLists.txt': 'C/C++/CMake',
        'Makefile': 'Make/C/C++',
        'tsconfig.json': 'TypeScript',
        'webpack.config.js': 'JavaScript/Webpack',
        'vite.config.js': 'JavaScript/Vite',
        '.eslintrc.js': 'JavaScript',
        '.prettierrc': 'JavaScript',
        'jest.config.js': 'JavaScript/Jest',
        'pytest.ini': 'Python/pytest',
        'tox.ini': 'Python/tox',
        '.flake8': 'Python',
        '.rubocop.yml': 'Ruby',
        'Dockerfile': 'Docker',
        'docker-compose.yml': 'Docker',
        '.gitignore': 'Git',
        '.github/workflows': 'GitHub Actions',
        '.gitlab-ci.yml': 'GitLab CI',
        'Jenkinsfile': 'Jenkins',
        '.travis.yml': 'Travis CI',
    }
    
    @property
    def name(self) -> str:
        return "analyze_languages"
    
    @property
    def description(self) -> str:
        return "Analyze programming languages and frameworks used in the project."
    
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
                "include_config": {
                    "type": "boolean",
                    "description": "Include configuration and markup languages",
                    "default": True
                },
                "min_files": {
                    "type": "integer",
                    "description": "Minimum files of a language to include in results",
                    "default": 2
                }
            }
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Code Analysis"
    
    @property
    def tags(self) -> List[str]:
        return ["analysis", "codebase", "languages", "project_structure"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'analyze_languages' tool to understand what programming languages and frameworks are used in the project.
        Parameters:
        - path (string, optional): Path to analyze (defaults to workspace root)
        - include_config (boolean, optional): Include config/markup languages (default: true)
        - min_files (integer, optional): Minimum files to include language (default: 2)
        
        This tool helps understand the project's technology stack.
        Example usage:
        <tool_code>
        analyze_languages()
        analyze_languages(path="src", include_config=False)
        analyze_languages(min_files=5)  # Only show languages with 5+ files
        </tool_code>
        """
    
    def _detect_frameworks(self, package_files: Dict[str, Path]) -> Dict[str, List[str]]:
        """Detect frameworks based on package file contents."""
        frameworks = defaultdict(list)
        
        # Check package.json for JS frameworks
        if 'package.json' in package_files:
            try:
                with open(package_files['package.json'], 'r') as f:
                    package_data = json.load(f)
                    
                deps = {}
                deps.update(package_data.get('dependencies', {}))
                deps.update(package_data.get('devDependencies', {}))
                
                # React
                if 'react' in deps:
                    frameworks['JavaScript'].append('React')
                # Vue
                if 'vue' in deps:
                    frameworks['JavaScript'].append('Vue.js')
                # Angular
                if '@angular/core' in deps:
                    frameworks['JavaScript'].append('Angular')
                # Express
                if 'express' in deps:
                    frameworks['JavaScript'].append('Express.js')
                # Next.js
                if 'next' in deps:
                    frameworks['JavaScript'].append('Next.js')
                # Jest
                if 'jest' in deps:
                    frameworks['JavaScript'].append('Jest (Testing)')
            except:
                pass
        
        # Check requirements.txt for Python frameworks
        if 'requirements.txt' in package_files:
            try:
                with open(package_files['requirements.txt'], 'r') as f:
                    requirements = f.read().lower()
                    
                if 'django' in requirements:
                    frameworks['Python'].append('Django')
                if 'flask' in requirements:
                    frameworks['Python'].append('Flask')
                if 'fastapi' in requirements:
                    frameworks['Python'].append('FastAPI')
                if 'pytest' in requirements:
                    frameworks['Python'].append('pytest (Testing)')
                if 'numpy' in requirements:
                    frameworks['Python'].append('NumPy')
                if 'pandas' in requirements:
                    frameworks['Python'].append('Pandas')
                if 'torch' in requirements or 'pytorch' in requirements:
                    frameworks['Python'].append('PyTorch')
                if 'tensorflow' in requirements:
                    frameworks['Python'].append('TensorFlow')
            except:
                pass
        
        return dict(frameworks)
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute language analysis."""
        path = arguments.get('path', '.')
        include_config = arguments.get('include_config', True)
        min_files = arguments.get('min_files', 2)
        
        try:
            path_manager = PathManager.get_instance()
            
            # Resolve path
            if path == '.':
                root_path = Path(path_manager.workspace_path)
            else:
                root_path = Path(path_manager.resolve_path(path))
            
            if not root_path.exists():
                return f"Error: Path '{path}' does not exist."
            
            # Statistics
            language_stats = defaultdict(lambda: {'count': 0, 'size': 0, 'files': []})
            package_files_found = {}
            total_files = 0
            ignored_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                          'env', 'build', 'dist', 'target', '.idea', '.vscode',
                          'coverage', '.pytest_cache', '.mypy_cache', '.tox'}
            
            # Walk directory tree
            for file_path in root_path.rglob('*'):
                # Skip ignored directories
                if any(part in ignored_dirs for part in file_path.parts):
                    continue
                
                if file_path.is_file():
                    total_files += 1
                    
                    # Check for package files
                    if file_path.name in self.PACKAGE_FILES:
                        package_files_found[file_path.name] = file_path
                    
                    # Analyze by extension
                    ext = file_path.suffix.lower()
                    if ext in self.LANGUAGE_EXTENSIONS:
                        lang = self.LANGUAGE_EXTENSIONS[ext]
                        
                        # Skip config languages if requested
                        if not include_config and lang in ['JSON', 'YAML', 'XML', 'INI', 
                                                          'Config', 'Markdown', 'HTML', 'CSS']:
                            continue
                        
                        try:
                            size = file_path.stat().st_size
                            language_stats[lang]['count'] += 1
                            language_stats[lang]['size'] += size
                            
                            # Track a few example files
                            rel_path = file_path.relative_to(root_path)
                            if len(language_stats[lang]['files']) < 5:
                                language_stats[lang]['files'].append(str(rel_path))
                        except:
                            pass
            
            # Filter by minimum files
            filtered_stats = {
                lang: stats for lang, stats in language_stats.items() 
                if stats['count'] >= min_files
            }
            
            # Sort by file count
            sorted_languages = sorted(
                filtered_stats.items(), 
                key=lambda x: x[1]['count'], 
                reverse=True
            )
            
            # Detect frameworks
            frameworks = self._detect_frameworks(package_files_found)
            
            # Build response
            response = f"**Language Analysis for: {path}**\n"
            response += f"Total files analyzed: {total_files}\n\n"
            
            if sorted_languages:
                response += "## Programming Languages\n\n"
                for lang, stats in sorted_languages:
                    response += f"### {lang}\n"
                    response += f"- Files: {stats['count']}\n"
                    response += f"- Total size: {self._format_size(stats['size'])}\n"
                    
                    # Add framework info if available
                    if lang in frameworks:
                        response += f"- Frameworks: {', '.join(frameworks[lang])}\n"
                    
                    if stats['files']:
                        response += f"- Examples:\n"
                        for example in stats['files'][:3]:
                            response += f"  - {example}\n"
                    response += "\n"
            else:
                response += "No programming language files found.\n"
            
            # Package files section
            if package_files_found:
                response += "## Package/Configuration Files\n\n"
                for pkg_file, pkg_path in sorted(package_files_found.items()):
                    rel_path = pkg_path.relative_to(root_path)
                    indicator = self.PACKAGE_FILES.get(pkg_file, 'Unknown')
                    response += f"- **{pkg_file}**: {indicator} (at {rel_path})\n"
                response += "\n"
            
            # Summary
            response += "## Summary\n\n"
            if sorted_languages:
                primary_lang = sorted_languages[0][0]
                response += f"- **Primary language**: {primary_lang} "
                response += f"({sorted_languages[0][1]['count']} files)\n"
                
                if len(sorted_languages) > 1:
                    response += f"- **Other languages**: "
                    response += ", ".join([lang for lang, _ in sorted_languages[1:4]])
                    if len(sorted_languages) > 4:
                        response += f" and {len(sorted_languages) - 4} more"
                    response += "\n"
            
            # Project type inference
            project_type = self._infer_project_type(sorted_languages, package_files_found, frameworks)
            if project_type:
                response += f"- **Project type**: {project_type}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing languages: {e}")
            return f"Error analyzing languages: {str(e)}"
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{size}{unit}"
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"
    
    def _infer_project_type(self, languages: List[tuple], package_files: Dict[str, Path], 
                           frameworks: Dict[str, List[str]]) -> str:
        """Infer the project type based on languages and frameworks."""
        if not languages:
            return ""
        
        primary_lang, primary_stats = languages[0]
        
        # Web frontend
        if primary_lang in ['JavaScript', 'TypeScript', 'JavaScript (React)', 'TypeScript (React)']:
            if 'React' in frameworks.get('JavaScript', []):
                return "React Web Application"
            elif 'Vue.js' in frameworks.get('JavaScript', []):
                return "Vue.js Web Application"
            elif 'Angular' in frameworks.get('JavaScript', []):
                return "Angular Web Application"
            elif 'package.json' in package_files:
                return "Node.js/JavaScript Project"
        
        # Python projects
        elif primary_lang == 'Python':
            if 'Django' in frameworks.get('Python', []):
                return "Django Web Application"
            elif 'Flask' in frameworks.get('Python', []):
                return "Flask Web Application"
            elif 'FastAPI' in frameworks.get('Python', []):
                return "FastAPI Web Service"
            elif any(ml in frameworks.get('Python', []) 
                    for ml in ['PyTorch', 'TensorFlow', 'NumPy', 'Pandas']):
                return "Python Data Science/ML Project"
            elif 'setup.py' in package_files or 'pyproject.toml' in package_files:
                return "Python Package/Library"
            else:
                return "Python Application"
        
        # Other languages
        elif primary_lang == 'Java':
            if 'pom.xml' in package_files:
                return "Java Maven Project"
            elif 'build.gradle' in package_files:
                return "Java Gradle Project"
        elif primary_lang == 'Go':
            return "Go Application"
        elif primary_lang == 'Rust':
            return "Rust Application"
        elif primary_lang == 'Ruby':
            if 'Gemfile' in package_files:
                return "Ruby/Rails Application"
        elif primary_lang in ['C', 'C++']:
            return "C/C++ Application"
        elif primary_lang == 'C#':
            return ".NET Application"
        
        return f"{primary_lang} Project"