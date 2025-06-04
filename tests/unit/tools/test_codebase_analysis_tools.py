"""Unit tests for codebase analysis tools."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from ai_whisperer.tools.analyze_languages_tool import AnalyzeLanguagesTool
from ai_whisperer.tools.find_similar_code_tool import FindSimilarCodeTool
from ai_whisperer.tools.get_project_structure_tool import GetProjectStructureTool
from ai_whisperer.utils.path import PathManager


class TestAnalyzeLanguagesTool:
    """Test AnalyzeLanguagesTool functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create Python files
            (project_path / "src").mkdir()
            (project_path / "src" / "main.py").write_text("def main():\n    print('Hello')")
            (project_path / "src" / "utils.py").write_text("def helper():\n    pass")
            
            # Create JavaScript files
            (project_path / "frontend").mkdir()
            (project_path / "frontend" / "app.js").write_text("console.log('App');")
            (project_path / "frontend" / "index.js").write_text("import './app';")
            
            # Create test files
            (project_path / "tests").mkdir()
            (project_path / "tests" / "test_main.py").write_text("def test_main():\n    assert True")
            
            # Create config files
            (project_path / "requirements.txt").write_text("pytest==7.4.0\nflask==2.3.0\n")
            (project_path / "package.json").write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "react": "^18.0.0",
                    "express": "^4.18.0"
                }
            }))
            
            # Create some other files
            (project_path / "README.md").write_text("# Test Project")
            (project_path / ".gitignore").write_text("*.pyc\nnode_modules/")
            
            yield tmpdir
    
    @pytest.fixture
    def analyze_tool(self, temp_project):
        """Create tool instance with mocked PathManager."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_project
            mock_instance.resolve_path = lambda x: str(Path(temp_project) / x) if x != '.' else temp_project
            mock_pm.return_value = mock_instance
            
            tool = AnalyzeLanguagesTool()
            yield tool
    
    def test_tool_properties(self, analyze_tool):
        """Test tool properties."""
        assert analyze_tool.name == "analyze_languages"
        assert "Analyze programming languages" in analyze_tool.description
        assert analyze_tool.category == "Code Analysis"
        assert "analysis" in analyze_tool.tags
        assert "codebase" in analyze_tool.tags
    
    def test_analyze_languages_basic(self, analyze_tool):
        """Test basic language analysis."""
        result = analyze_tool.execute({})
        
        assert isinstance(result, dict)
        assert 'languages' in result
        
        # Check that languages were detected
        language_names = [lang['language'] for lang in result['languages']]
        assert 'Python' in language_names
        assert 'JavaScript' in language_names
        
        # Check file counts
        python_lang = next((l for l in result['languages'] if l['language'] == 'Python'), None)
        js_lang = next((l for l in result['languages'] if l['language'] == 'JavaScript'), None)
        assert python_lang['file_count'] == 3  # 3 Python files
        assert js_lang['file_count'] == 2  # 2 JS files
        
        # Check package files detected
        assert 'package_files' in result
        package_file_names = [pf['file'] for pf in result['package_files']]
        assert 'requirements.txt' in package_file_names
        assert 'package.json' in package_file_names
    
    def test_framework_detection(self, analyze_tool):
        """Test framework detection from package files."""
        result = analyze_tool.execute({})
        
        assert isinstance(result, dict)
        assert 'frameworks' in result
        
        frameworks = result['frameworks']
        
        # Check Python frameworks
        if 'Python' in frameworks:
            python_frameworks = frameworks['Python']
            assert any('Flask' in fw or 'flask' in fw for fw in python_frameworks)
            assert any('pytest' in fw for fw in python_frameworks)
        
        # Check JavaScript frameworks
        if 'JavaScript' in frameworks:
            js_frameworks = frameworks['JavaScript']
            assert any('React' in fw or 'react' in fw for fw in js_frameworks)
            assert any('Express' in fw or 'express' in fw for fw in js_frameworks)
    
    def test_exclude_config_files(self, analyze_tool):
        """Test excluding configuration files."""
        result = analyze_tool.execute({"include_config": False})
        
        assert isinstance(result, dict)
        assert 'languages' in result
        
        language_names = [lang['language'] for lang in result['languages']]
        
        # Should still have Python and JS
        assert 'Python' in language_names
        assert 'JavaScript' in language_names
        
        # Should not include Markdown when config is False
        assert 'Markdown' not in language_names
    
    def test_min_files_filter(self, analyze_tool):
        """Test minimum files filter."""
        # Set threshold to 4 to ensure JavaScript is filtered out
        result = analyze_tool.execute({"min_files": 4})
        
        assert isinstance(result, dict)
        
        # No language should meet this threshold in our test setup  
        # Python has 3 files, JS has 2, both less than 4
        assert len(result['languages']) == 0
    
    def test_project_type_inference(self, analyze_tool):
        """Test project type inference."""
        result = analyze_tool.execute({})
        
        assert isinstance(result, dict)
        assert 'project_type' in result
        
        # Should detect as a web app due to React and Flask
        project_type = result['project_type']
        assert "Application" in project_type or "Web" in project_type or "Project" in project_type


class TestFindSimilarCodeTool:
    """Test FindSimilarCodeTool functionality."""
    
    @pytest.fixture
    def temp_codebase(self):
        """Create a temporary codebase with various patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create files with caching patterns
            (project_path / "cache_manager.py").write_text("""
import functools

class CacheManager:
    def __init__(self):
        self._cache = {}
    
    @functools.lru_cache(maxsize=128)
    def get_from_cache(self, key):
        return self._cache.get(key)
    
    def set_cache(self, key, value):
        self._cache[key] = value
""")
            
            # Create files with authentication patterns
            (project_path / "auth.py").write_text("""
def authenticate(username, password):
    # Check login credentials
    token = generate_jwt_token(username)
    return token

def logout(session):
    session.clear()
""")
            
            # Create files with file operations
            (project_path / "file_handler.py").write_text("""
from pathlib import Path

def read_file(file_path):
    path = Path(file_path)
    if path.exists() and path.is_file():
        with open(path, 'r') as f:
            return f.read()
""")
            
            # Create test file
            (project_path / "test_cache.py").write_text("""
def test_cache_functionality():
    cache = CacheManager()
    assert cache.get_from_cache('key') is None
""")
            
            yield tmpdir
    
    @pytest.fixture
    def similar_code_tool(self, temp_codebase):
        """Create tool instance."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_codebase
            mock_pm.return_value = mock_instance
            
            tool = FindSimilarCodeTool()
            yield tool
    
    def test_find_caching_patterns(self, similar_code_tool):
        """Test finding caching-related code."""
        result = similar_code_tool.execute({"feature": "caching"})
        
        assert isinstance(result, dict)
        assert 'results' in result
        assert result['feature'] == 'caching'
        
        # Check file paths in results
        file_paths = [r['path'] for r in result['results']]
        assert any('cache_manager.py' in path for path in file_paths)
        assert any('test_cache.py' in path for path in file_paths)
        
        # Check content matches in contexts
        all_contexts = [ctx['context'] for r in result['results'] for ctx in r.get('contexts', [])]
        content_str = ' '.join(all_contexts)
        assert 'CacheManager' in content_str or 'cache' in content_str.lower()
        assert 'lru_cache' in content_str or '_cache' in content_str
    
    def test_find_authentication_patterns(self, similar_code_tool):
        """Test finding authentication code."""
        result = similar_code_tool.execute({"feature": "authentication"})
        
        assert isinstance(result, dict)
        assert 'results' in result
        
        # Check file paths
        file_paths = [r['path'] for r in result['results']]
        assert any('auth.py' in path for path in file_paths)
        
        # Check content matches in contexts
        all_contexts = [ctx['context'] for r in result['results'] for ctx in r.get('contexts', [])]
        content_str = ' '.join(all_contexts)
        assert 'authenticate' in content_str
        assert 'jwt' in content_str.lower() or 'token' in content_str.lower()
        assert 'logout' in content_str
    
    def test_custom_patterns(self, similar_code_tool):
        """Test custom pattern search."""
        result = similar_code_tool.execute({
            "feature": "custom",
            "custom_patterns": [r"Path\(", r"\.exists\(\)"]
        })
        
        assert isinstance(result, dict)
        assert 'results' in result
        assert result['custom_patterns'] == [r"Path\(", r"\.exists\(\)"]
        
        # Check file paths
        file_paths = [r['path'] for r in result['results']]
        assert any('file_handler.py' in path for path in file_paths)
        
        # Check content matches in contexts
        all_contexts = [ctx['context'] for r in result['results'] for ctx in r.get('contexts', [])]
        content_str = ' '.join(all_contexts)
        assert 'Path(' in content_str
        assert '.exists()' in content_str
    
    def test_file_type_filter(self, similar_code_tool):
        """Test filtering by file type."""
        result = similar_code_tool.execute({
            "feature": "testing",
            "file_types": [".py"]
        })
        
        assert isinstance(result, dict)
        assert 'results' in result
        
        # Check that we found test files
        file_paths = [r['path'] for r in result['results']]
        assert any('test_cache.py' in path for path in file_paths)
        
        # All results should be Python files
        for result_item in result['results']:
            assert result_item['path'].endswith('.py')
    
    def test_no_matches(self, similar_code_tool):
        """Test when no similar code is found."""
        result = similar_code_tool.execute({"feature": "blockchain"})
        
        assert isinstance(result, dict)
        assert 'results' in result
        assert len(result['results']) == 0
        assert result['result_count'] == 0
    
    def test_context_extraction(self, similar_code_tool):
        """Test context line extraction."""
        result = similar_code_tool.execute({
            "feature": "caching",
            "context_lines": 1
        })
        
        assert isinstance(result, dict)
        assert result['context_lines'] == 1
        assert 'results' in result
        
        # Should have contexts with line numbers
        if result['results']:
            first_result = result['results'][0]
            assert 'contexts' in first_result
            if first_result['contexts']:
                assert 'line' in first_result['contexts'][0]


class TestGetProjectStructureTool:
    """Test GetProjectStructureTool functionality."""
    
    @pytest.fixture
    def temp_project_structure(self):
        """Create a complex project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create source directories
            (project_path / "src" / "models").mkdir(parents=True)
            (project_path / "src" / "controllers").mkdir(parents=True)
            (project_path / "src" / "utils").mkdir(parents=True)
            
            # Create test directories
            (project_path / "tests" / "unit").mkdir(parents=True)
            (project_path / "tests" / "integration").mkdir(parents=True)
            
            # Create config directory
            (project_path / "config").mkdir()
            
            # Create docs
            (project_path / "docs").mkdir()
            
            # Create some files
            (project_path / "src" / "main.py").write_text("# Main entry")
            (project_path / "src" / "models" / "user.py").write_text("class User: pass")
            (project_path / "tests" / "unit" / "test_user.py").write_text("def test_user(): pass")
            (project_path / "config" / "settings.yaml").write_text("debug: true")
            (project_path / "README.md").write_text("# Project")
            (project_path / "requirements.txt").write_text("flask")
            (project_path / "Makefile").write_text("test:\n\tpytest")
            
            # Add some ignored directories
            (project_path / ".git").mkdir()
            (project_path / "__pycache__").mkdir()
            
            yield tmpdir
    
    @pytest.fixture
    def structure_tool(self, temp_project_structure):
        """Create tool instance."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_project_structure
            mock_instance.resolve_path = lambda x: str(Path(temp_project_structure) / x) if x != '.' else temp_project_structure
            mock_pm.return_value = mock_instance
            
            tool = GetProjectStructureTool()
            yield tool
    
    def test_basic_structure_analysis(self, structure_tool):
        """Test basic project structure analysis."""
        result = structure_tool.execute({})
        
        assert isinstance(result, dict)
        assert 'statistics' in result
        assert 'key_directories' in result
        
        # Check statistics
        stats = result['statistics']
        assert 'total_directories' in stats
        assert 'total_files' in stats
        assert stats['total_directories'] > 0
        assert stats['total_files'] > 0
        
        # Check key directories identified
        key_dirs = result['key_directories']
        dir_names = [d['name'] for d in key_dirs]
        assert 'src' in dir_names
        assert 'tests' in dir_names
        assert 'config' in dir_names
        
        # Check purposes are identified
        src_dir = next((d for d in key_dirs if d['name'] == 'src'), None)
        assert src_dir is not None
        assert 'source' in src_dir['purpose'].lower() or 'code' in src_dir['purpose'].lower()
    
    def test_important_files_detection(self, structure_tool):
        """Test detection of important files."""
        result = structure_tool.execute({"include_files": True})
        
        assert isinstance(result, dict)
        assert 'important_files' in result
        
        # Check important files
        important_files = result['important_files']
        file_names = [f['name'] for f in important_files]
        assert 'README.md' in file_names
        assert 'requirements.txt' in file_names
        assert 'Makefile' in file_names
        
        # Check purposes
        req_file = next((f for f in important_files if f['name'] == 'requirements.txt'), None)
        assert req_file is not None
        assert 'python' in req_file['purpose'].lower() or 'dependencies' in req_file['purpose'].lower()
    
    def test_project_components(self, structure_tool):
        """Test project component identification."""
        result = structure_tool.execute({})
        
        assert isinstance(result, dict)
        assert 'components' in result
        
        components = result['components']
        assert 'source_roots' in components
        assert 'test_roots' in components
        assert 'entry_points' in components
        
        # Check specific components
        assert any('src' in root for root in components['source_roots'])
        assert any('tests' in root for root in components['test_roots'])
        assert any('main.py' in ep for ep in components['entry_points'])
    
    def test_directory_tree(self, structure_tool):
        """Test ASCII tree generation."""
        result = structure_tool.execute({"show_tree": True})
        
        assert isinstance(result, dict)
        assert 'tree_visualization' in result
        
        tree = result['tree_visualization']
        assert "├──" in tree or "└──" in tree
        assert "src" in tree
        assert "models" in tree
    
    def test_ignored_directories(self, structure_tool):
        """Test that ignored directories are excluded."""
        result = structure_tool.execute({})
        
        assert isinstance(result, dict)
        
        # Check in various places where directories might appear
        all_text = str(result)
        assert ".git" not in all_text
        assert "__pycache__" not in all_text
        
        # Also check specifically in key directories
        if 'key_directories' in result:
            dir_names = [d['name'] for d in result['key_directories']]
            assert '.git' not in dir_names
            assert '__pycache__' not in dir_names
    
    def test_max_depth_limit(self, structure_tool):
        """Test depth limiting."""
        result = structure_tool.execute({"max_depth": 1, "show_tree": True})
        
        assert isinstance(result, dict)
        assert 'tree_visualization' in result
        
        # Check tree visualization with limited depth
        tree = result['tree_visualization']
        assert tree is not None
        assert "src" in tree
        assert "tests" in tree
        # With max_depth=1, subdirectories may not show their contents
    
    def test_file_type_distribution(self, structure_tool):
        """Test file type statistics."""
        result = structure_tool.execute({})
        
        assert isinstance(result, dict)
        assert 'file_types' in result
        
        file_types = result['file_types']
        extensions = [ft['extension'] for ft in file_types]
        assert '.py' in extensions
        assert '.yaml' in extensions or '.yml' in extensions
        
        # Check counts
        py_type = next((ft for ft in file_types if ft['extension'] == '.py'), None)
        assert py_type is not None
        assert py_type['count'] > 0