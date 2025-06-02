"""Tests for the WorkspaceStatsTool."""
import pytest
from pathlib import Path
import tempfile
import time
import os

from ai_whisperer.tools.workspace_stats_tool import WorkspaceStatsTool
from ai_whisperer.path_management import PathManager


class TestWorkspaceStatsTool:
    """Test the WorkspaceStatsTool class."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create test file structure
            files = {
                "src/main.py": "print('Hello')" * 100,  # ~1.4KB
                "src/utils.py": "def util():\n    pass\n" * 50,  # ~1KB
                "src/large.py": "x = 1\n" * 1000,  # ~6KB
                "tests/test_main.py": "import pytest\n" * 10,
                "tests/test_utils.py": "def test():\n    pass\n" * 20,
                "docs/README.md": "# Documentation\n" * 30,
                "docs/guide.md": "## Guide\n" * 40,
                "data/data.json": '{"key": "value"}\n' * 100,
                "data/config.yaml": "config: true\n" * 20,
                ".hidden/secret.txt": "secret data",
                "node_modules/package.json": '{"name": "test"}',
                "build/output.js": "compiled code",
                "empty.txt": "",
            }
            
            # Create files with different timestamps
            now = time.time()
            for file_path, content in files.items():
                full_path = tmpdir_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                
                # Set different modification times
                if "main.py" in file_path:
                    # Modified today
                    os.utime(full_path, (now, now))
                elif "utils" in file_path:
                    # Modified this week
                    os.utime(full_path, (now, now - 3 * 24 * 60 * 60))
                elif "README" in file_path:
                    # Modified this month
                    os.utime(full_path, (now, now - 15 * 24 * 60 * 60))
                elif "data.json" in file_path:
                    # Modified this year
                    os.utime(full_path, (now, now - 100 * 24 * 60 * 60))
                else:
                    # Older
                    os.utime(full_path, (now, now - 400 * 24 * 60 * 60))
                    
            yield tmpdir_path
            
    @pytest.fixture
    def stats_tool(self, temp_workspace):
        """Create WorkspaceStatsTool with temporary workspace."""
        path_manager = PathManager()
        path_manager.initialize(config_values={'workspace_path': str(temp_workspace)})
        return WorkspaceStatsTool(path_manager)
        
    def test_basic_statistics(self, stats_tool):
        """Test basic workspace statistics."""
        result = stats_tool.execute()
        
        assert "total_files" in result
        assert "total_directories" in result
        assert "total_size" in result
        assert result["total_files"] > 0
        assert result["total_directories"] > 0
        assert result["total_size"] > 0
        
    def test_file_extension_statistics(self, stats_tool):
        """Test file counting by extension."""
        result = stats_tool.execute()
        
        assert "files_by_extension" in result
        assert ".py" in result["files_by_extension"]
        assert ".md" in result["files_by_extension"]
        assert ".json" in result["files_by_extension"]
        
        # Check counts
        assert result["files_by_extension"][".py"] >= 4
        assert result["files_by_extension"][".md"] >= 2
        
    def test_size_by_extension(self, stats_tool):
        """Test size tracking by extension."""
        result = stats_tool.execute()
        
        assert "size_by_extension" in result
        assert ".py" in result["size_by_extension"]
        
        # Python files should have significant size
        assert result["size_by_extension"][".py"] > 1000
        
    def test_largest_files(self, stats_tool):
        """Test largest files tracking."""
        result = stats_tool.execute()
        
        assert "largest_files" in result
        assert len(result["largest_files"]) > 0
        
        # Check structure
        for file_info in result["largest_files"]:
            assert "path" in file_info
            assert "size" in file_info
            assert "human_size" in file_info
            assert "extension" in file_info
            
        # Should be sorted by size
        sizes = [f["size"] for f in result["largest_files"]]
        assert sizes == sorted(sizes, reverse=True)
        
        # large.py should be near the top
        paths = [f["path"] for f in result["largest_files"]]
        assert any("large.py" in p for p in paths[:3])
        
    def test_directory_sizes(self, stats_tool):
        """Test directory size analysis."""
        result = stats_tool.execute()
        
        assert "directory_sizes" in result
        assert len(result["directory_sizes"]) > 0
        
        # src directory should be one of the largest
        assert any("src" in d for d in result["directory_sizes"])
        
    def test_recent_changes(self, stats_tool):
        """Test recent file changes tracking."""
        result = stats_tool.execute(recent_days=30)
        
        assert "recent_changes" in result
        recent = result["recent_changes"]
        
        assert "modified_files" in recent
        assert "total_modified" in recent
        assert recent["total_modified"] > 0
        
        # Check modified files structure
        for file_info in recent["modified_files"]:
            assert "path" in file_info
            assert "modified_time" in file_info
            assert "modified_date" in file_info
            assert "size" in file_info
            
    def test_file_age_distribution(self, stats_tool):
        """Test file age distribution statistics."""
        result = stats_tool.execute()
        
        assert "file_age_distribution" in result
        age_dist = result["file_age_distribution"]
        
        assert "today" in age_dist
        assert "this_week" in age_dist
        assert "this_month" in age_dist
        assert "this_year" in age_dist
        assert "older" in age_dist
        
        # Based on our test setup
        assert age_dist["today"] >= 1  # main.py
        assert age_dist["this_week"] >= 1  # utils files
        assert age_dist["this_month"] >= 1  # README
        assert age_dist["this_year"] >= 1  # data.json
        
    def test_exclude_directories(self, stats_tool):
        """Test directory exclusion."""
        result = stats_tool.execute(exclude_dirs=["node_modules", "build"])
        
        # Should not include files from excluded directories
        for file_info in result["largest_files"]:
            assert "node_modules" not in file_info["path"]
            assert "build" not in file_info["path"]
            
    def test_include_hidden_files(self, stats_tool):
        """Test hidden file inclusion."""
        # Without hidden files
        result_no_hidden = stats_tool.execute(include_hidden=False)
        
        # With hidden files
        result_with_hidden = stats_tool.execute(include_hidden=True)
        
        # Should have more files when including hidden
        assert result_with_hidden["total_files"] > result_no_hidden["total_files"]
        
        # Check that .hidden directory is included
        hidden_found = any(
            ".hidden" in f["path"] 
            for f in result_with_hidden["largest_files"]
        )
        assert hidden_found
        
    def test_max_depth_limiting(self, stats_tool):
        """Test maximum depth limiting."""
        # Very shallow scan
        result_shallow = stats_tool.execute(max_depth=1)
        
        # Deeper scan  
        result_deep = stats_tool.execute(max_depth=10)
        
        # Deep scan should find more files
        assert result_deep["total_files"] >= result_shallow["total_files"]
        
    def test_summary_information(self, stats_tool):
        """Test summary information."""
        result = stats_tool.execute()
        
        assert "summary" in result
        summary = result["summary"]
        
        assert "path" in summary
        assert "total_items" in summary
        assert "human_readable_size" in summary
        assert "average_file_size" in summary
        assert "unique_extensions" in summary
        assert "analysis_time" in summary
        
        # Check formatting
        assert "KB" in summary["human_readable_size"] or "MB" in summary["human_readable_size"]
        
    def test_empty_directory(self, stats_tool, temp_workspace):
        """Test statistics on empty directory."""
        empty_dir = temp_workspace / "empty_dir"
        empty_dir.mkdir()
        
        result = stats_tool.execute(path="empty_dir")
        
        assert result["total_files"] == 0
        assert result["total_directories"] == 0
        assert result["total_size"] == 0
        
    def test_single_file_path(self, stats_tool):
        """Test error handling for single file path."""
        result = stats_tool.execute(path="src/main.py")
        
        assert "error" in result
        assert "Not a directory" in result["error"]
        
    def test_nonexistent_path(self, stats_tool):
        """Test error handling for nonexistent path."""
        result = stats_tool.execute(path="nonexistent/path")
        
        assert "error" in result
        assert "Path not found" in result["error"]
        
    def test_size_formatting(self, stats_tool):
        """Test human-readable size formatting."""
        tool = stats_tool
        
        assert tool._format_size(100) == "100.0 B"
        assert tool._format_size(1024) == "1.0 KB"
        assert tool._format_size(1024 * 1024) == "1.0 MB"
        assert tool._format_size(1024 * 1024 * 1024) == "1.0 GB"