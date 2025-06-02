"""
Tests specifically for RFC move tool extension handling
"""
import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
from ai_whisperer.utils.path import PathManager


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace with RFC directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create RFC directories
        rfc_base = Path(tmpdir) / ".WHISPER" / "rfc"
        (rfc_base / "in_progress").mkdir(parents=True, exist_ok=True)
        (rfc_base / "archived").mkdir(parents=True, exist_ok=True)
        
        # Mock PathManager to use temp directory
        with patch.object(PathManager, 'get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = tmpdir
            mock_pm.return_value = mock_instance
            yield tmpdir


class TestMoveRFCExtensions:
    """Test move RFC tool extension handling to prevent regression."""
    
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in Windows CI with file operations")
    def test_move_with_md_extension_input(self, temp_workspace):
        """Test moving RFC when input includes .md extension."""
        # Create an RFC
        create_tool = CreateRFCTool()
        create_tool.execute({
            'title': 'Test Move',
            'summary': 'Testing move with extension',
            'short_name': 'test-move'
        })
        
        # Get the created file
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        md_files = list(rfc_path.glob("test-move-*.md"))
        assert len(md_files) == 1
        original_filename = md_files[0].name
        
        # Move using filename WITH .md extension
        move_tool = MoveRFCTool()
        result = move_tool.execute({
            'rfc_id': original_filename,  # Includes .md
            'target_status': 'archived'
        })
        
        assert "moved successfully" in result.lower()
        
        # Check archived folder
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        
        # Should have exactly one .md file
        archived_md_files = list(archived_path.glob("*.md"))
        assert len(archived_md_files) == 1
        assert archived_md_files[0].name == original_filename
        
        # Should NOT have .md.md
        assert not any(f.name.endswith('.md.md') for f in archived_path.iterdir())
        
        # Check JSON file
        json_filename = original_filename.replace('.md', '.json')
        assert (archived_path / json_filename).exists()
        assert not (archived_path / f"{original_filename}.json").exists()  # No .md.json
    
    def test_move_without_md_extension_input(self, temp_workspace):
        """Test moving RFC when input excludes .md extension."""
        # Create an RFC
        create_tool = CreateRFCTool()
        create_tool.execute({
            'title': 'Test Move No Ext',
            'summary': 'Testing move without extension',
            'short_name': 'test-no-ext'
        })
        
        # Get the created file
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        md_files = list(rfc_path.glob("test-no-ext-*.md"))
        assert len(md_files) == 1
        original_filename = md_files[0].name
        filename_without_ext = original_filename[:-3]  # Remove .md
        
        # Move using filename WITHOUT .md extension
        move_tool = MoveRFCTool()
        result = move_tool.execute({
            'rfc_id': filename_without_ext,  # No .md
            'target_status': 'archived'
        })
        
        assert "moved successfully" in result.lower()
        
        # Check archived folder
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        
        # Should have correct files
        assert (archived_path / original_filename).exists()
        assert (archived_path / f"{filename_without_ext}.json").exists()
        
        # Should NOT have double extensions
        assert not any(f.name.endswith('.md.md') for f in archived_path.iterdir())
        assert not any(f.name.endswith('.md.json') for f in archived_path.iterdir())
    
    def test_move_back_and_forth(self, temp_workspace):
        """Test moving RFC back and forth doesn't accumulate extensions."""
        # Create an RFC
        create_tool = CreateRFCTool()
        create_tool.execute({
            'title': 'Ping Pong RFC',
            'summary': 'Testing multiple moves',
            'short_name': 'ping-pong'
        })
        
        # Get the created file
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        md_files = list(rfc_path.glob("ping-pong-*.md"))
        assert len(md_files) == 1
        original_filename = md_files[0].name
        
        move_tool = MoveRFCTool()
        
        # Move to archived
        move_tool.execute({
            'rfc_id': original_filename,
            'target_status': 'archived'
        })
        
        # Move back to in_progress
        move_tool.execute({
            'rfc_id': original_filename,
            'target_status': 'in_progress'
        })
        
        # Move to archived again
        move_tool.execute({
            'rfc_id': original_filename,
            'target_status': 'archived'
        })
        
        # Check final state
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        final_files = list(archived_path.iterdir())
        
        # Should still have original filename
        assert any(f.name == original_filename for f in final_files)
        
        # No accumulated extensions
        for f in final_files:
            assert f.name.count('.md') <= 1
            assert not f.name.endswith('.md.md')
            assert not f.name.endswith('.md.json')
    
    def test_move_updates_metadata_correctly(self, temp_workspace):
        """Test that move updates metadata without corrupting filenames."""
        # Create an RFC
        create_tool = CreateRFCTool()
        create_tool.execute({
            'title': 'Metadata Test',
            'summary': 'Testing metadata updates',
            'short_name': 'meta-test'
        })
        
        # Get the created files
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        md_files = list(rfc_path.glob("meta-test-*.md"))
        json_files = list(rfc_path.glob("meta-test-*.json"))
        assert len(md_files) == 1 and len(json_files) == 1
        
        original_md = md_files[0].name
        original_json = json_files[0].name
        
        # Read original metadata
        with open(rfc_path / original_json, 'r') as f:
            original_metadata = json.load(f)
        
        # Move to archived
        move_tool = MoveRFCTool()
        move_tool.execute({
            'rfc_id': original_md,
            'target_status': 'archived'
        })
        
        # Check archived files
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        
        # Files should have same names
        assert (archived_path / original_md).exists()
        assert (archived_path / original_json).exists()
        
        # Metadata should be updated but filename field preserved
        with open(archived_path / original_json, 'r') as f:
            updated_metadata = json.load(f)
        
        assert updated_metadata['status'] == 'archived'
        assert updated_metadata['filename'] == original_md
        assert updated_metadata['rfc_id'] == original_metadata['rfc_id']
    
    def test_move_edge_cases(self, temp_workspace):
        """Test edge cases in filename handling."""
        create_tool = CreateRFCTool()
        move_tool = MoveRFCTool()
        
        # Test 1: RFC with dots in name
        create_tool.execute({
            'title': 'API v2.0 Update',
            'summary': 'Testing dots in name',
            'short_name': 'api-v2.0'
        })
        
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        dot_files = list(rfc_path.glob("api-v2-0-*.md"))  # Dots get converted to dashes
        if dot_files:
            result = move_tool.execute({
                'rfc_id': dot_files[0].name,
                'target_status': 'archived'
            })
            assert "moved successfully" in result.lower()
        
        # Test 2: Very long filename
        create_tool.execute({
            'title': 'Very Long Title',
            'summary': 'Testing long names',
            'short_name': 'this-is-a-very-long-short-name-that-should-still-work'
        })
        
        long_files = list(rfc_path.glob("this-is-a-very-long-*.md"))
        if long_files:
            result = move_tool.execute({
                'rfc_id': long_files[0].name,
                'target_status': 'archived'
            })
            assert "moved successfully" in result.lower()
        
        # Verify no extension issues in archived
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        for f in archived_path.iterdir():
            assert not f.name.endswith('.md.md')
            assert not f.name.endswith('.md.json')