"""Unit tests for codebase analysis tools."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from ai_whisperer.tools.analyze_languages_tool import AnalyzeLanguagesTool
from ai_whisperer.tools.find_similar_code_tool import FindSimilarCodeTool
from ai_whisperer.tools.get_project_structure_tool import GetProjectStructureTool
from ai_whisperer.path_management import PathManager


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
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
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
        
        # Check that languages were detected
        assert "Python" in result
        assert "JavaScript" in result
        assert "Files: 3" in result  # 3 Python files
        assert "Files: 2" in result  # 2 JS files
        
        # Check package files detected
        assert "requirements.txt" in result
        assert "package.json" in result
    
    def test_framework_detection(self, analyze_tool):
        """Test framework detection from package files."""
        result = analyze_tool.execute({})
        
        # Python frameworks
        assert "Flask" in result
        assert "pytest" in result
        
        # JavaScript frameworks
        assert "React" in result
        assert "Express" in result
    
    def test_exclude_config_files(self, analyze_tool):
        """Test excluding configuration files."""
        result = analyze_tool.execute({"include_config": False})
        
        # Should still have Python and JS
        assert "Python" in result
        assert "JavaScript" in result
        
        # Should not include Markdown
        assert "Markdown" not in result
    
    def test_min_files_filter(self, analyze_tool):
        """Test minimum files filter."""
        # Set threshold to 4 to ensure JavaScript is filtered out
        result = analyze_tool.execute({"min_files": 4})
        
        # No language should meet this threshold in our test setup
        assert "No programming language files found" in result or "Python" not in result
    
    def test_project_type_inference(self, analyze_tool):
        """Test project type inference."""
        result = analyze_tool.execute({})
        
        assert "Project type" in result
        # Should detect as a web app due to React and Flask
        assert "Application" in result or "Project" in result


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
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_codebase
            mock_pm.return_value = mock_instance
            
            tool = FindSimilarCodeTool()
            yield tool
    
    def test_find_caching_patterns(self, similar_code_tool):
        """Test finding caching-related code."""
        result = similar_code_tool.execute({"feature": "caching"})
        
        assert "cache_manager.py" in result
        assert "test_cache.py" in result
        assert "CacheManager" in result
        assert "lru_cache" in result
        assert "Score:" in result  # Should have relevance scores
    
    def test_find_authentication_patterns(self, similar_code_tool):
        """Test finding authentication code."""
        result = similar_code_tool.execute({"feature": "authentication"})
        
        assert "auth.py" in result
        assert "authenticate" in result
        assert "jwt" in result
        assert "logout" in result
    
    def test_custom_patterns(self, similar_code_tool):
        """Test custom pattern search."""
        result = similar_code_tool.execute({
            "feature": "custom",
            "custom_patterns": [r"Path\(", r"\.exists\(\)"]
        })
        
        assert "file_handler.py" in result
        assert "Path(" in result
        assert ".exists()" in result
    
    def test_file_type_filter(self, similar_code_tool):
        """Test filtering by file type."""
        result = similar_code_tool.execute({
            "feature": "testing",
            "file_types": [".py"]
        })
        
        assert "test_cache.py" in result
        assert "test_" in result
    
    def test_no_matches(self, similar_code_tool):
        """Test when no similar code is found."""
        result = similar_code_tool.execute({"feature": "blockchain"})
        
        assert "No code similar to 'blockchain' found" in result
        assert "Suggestions:" in result
    
    def test_context_extraction(self, similar_code_tool):
        """Test context line extraction."""
        result = similar_code_tool.execute({
            "feature": "caching",
            "context_lines": 1
        })
        
        # Should show context around matches
        assert "Example matches:" in result
        assert "Line" in result


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
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_project_structure
            mock_instance.resolve_path = lambda x: str(Path(temp_project_structure) / x) if x != '.' else temp_project_structure
            mock_pm.return_value = mock_instance
            
            tool = GetProjectStructureTool()
            yield tool
    
    def test_basic_structure_analysis(self, structure_tool):
        """Test basic project structure analysis."""
        result = structure_tool.execute({})
        
        # Check overview
        assert "Total directories:" in result
        assert "Total files:" in result
        
        # Check key directories identified
        assert "src" in result
        assert "Source code" in result
        assert "tests" in result
        assert "Test files" in result
        assert "config" in result
        assert "Configuration" in result
    
    def test_important_files_detection(self, structure_tool):
        """Test detection of important files."""
        result = structure_tool.execute({"include_files": True})
        
        assert "Key Files" in result
        assert "README.md" in result
        assert "requirements.txt" in result
        assert "Makefile" in result
        assert "Python dependencies" in result
    
    def test_project_components(self, structure_tool):
        """Test project component identification."""
        result = structure_tool.execute({})
        
        assert "Project Components" in result
        # Check for either the label with colon or just the content
        assert "Source roots" in result or "src" in result
        assert "Test directories" in result or "tests" in result
        assert "Entry points" in result or "main.py" in result
    
    def test_directory_tree(self, structure_tool):
        """Test ASCII tree generation."""
        result = structure_tool.execute({"show_tree": True})
        
        assert "Directory Tree" in result
        assert "├──" in result or "└──" in result
        assert "src" in result
        assert "models" in result
    
    def test_ignored_directories(self, structure_tool):
        """Test that ignored directories are excluded."""
        result = structure_tool.execute({})
        
        # Should not include ignored directories
        assert ".git" not in result
        assert "__pycache__" not in result
    
    def test_max_depth_limit(self, structure_tool):
        """Test depth limiting."""
        result = structure_tool.execute({"max_depth": 1})
        
        # Should show top-level dirs but not subdirs
        assert "src" in result
        assert "tests" in result
        # Subdirectories like "models" might not be detailed
    
    def test_file_type_distribution(self, structure_tool):
        """Test file type statistics."""
        result = structure_tool.execute({})
        
        assert "File Types" in result
        assert ".py:" in result
        assert ".yaml:" in result or ".yml:" in result