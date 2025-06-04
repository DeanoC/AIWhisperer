"""
Tests for RFC naming functionality and extension handling
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
from ai_whisperer.tools.read_rfc_tool import ReadRFCTool
from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
from ai_whisperer.tools.delete_rfc_tool import DeleteRFCTool
from ai_whisperer.tools.list_rfcs_tool import ListRFCsTool
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


class TestRFCNaming:
    """Test RFC naming with descriptive filenames."""
    
    def test_create_rfc_with_short_name(self, temp_workspace):
        """Test creating RFC with descriptive short name."""
        tool = CreateRFCTool()
        
        result = tool.execute({
            'title': 'Dark Mode Feature',
            'summary': 'Add dark mode support to the application',
            'short_name': 'dark-mode'
        })
        
        assert result.get("rfc_id") is not None
        assert "dark-mode-" in result.get("filename", "")  # Should contain the short name
        assert "RFC-" in result.get("rfc_id", "")  # Should still have RFC ID
        
        # Check file was created with correct name
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        md_files = list(rfc_path.glob("dark-mode-*.md"))
        assert len(md_files) == 1
        
        # Check metadata file
        json_files = list(rfc_path.glob("dark-mode-*.json"))
        assert len(json_files) == 1
        
        # Verify no double extensions
        assert not any(f.name.endswith('.md.md') for f in rfc_path.iterdir())
        assert not any(f.name.endswith('.md.json') for f in rfc_path.iterdir())
    
    def test_create_rfc_validates_short_name(self, temp_workspace):
        """Test that short_name validation works."""
        tool = CreateRFCTool()
        
        # Test with invalid characters
        result = tool.execute({
            'title': 'Test RFC',
            'summary': 'Test summary',
            'short_name': 'Invalid Name!'  # Has space and special char
        })
        
        # Should still work but clean the name
        assert result.get("rfc_id") is not None
        
        # Check the cleaned filename
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        md_files = list(rfc_path.glob("invalid-name-*.md"))
        assert len(md_files) == 1
    
    def test_read_rfc_by_filename(self, temp_workspace):
        """Test reading RFC by filename."""
        # First create an RFC
        create_tool = CreateRFCTool()
        create_result = create_tool.execute({
            'title': 'API Authentication',
            'summary': 'Add JWT authentication to API',
            'short_name': 'api-auth'
        })
        
        # Extract filename from result
        import re
        assert isinstance(create_result, dict) and "filename" in create_result
        filename = create_result["filename"]
        
        
        # Test reading by filename
        read_tool = ReadRFCTool()
        
        # Should work with full filename
        result = read_tool.execute({'rfc_id': filename})
        assert result.get("found") is True
        assert "API Authentication" in result.get("content", {}).get("content", "")
        
        # Should work without .md extension
        result = read_tool.execute({'rfc_id': filename[:-3]})
        assert result.get("found") is True
        assert "API Authentication" in result.get("content", {}).get("content", "")
    
    def test_read_rfc_by_rfc_id(self, temp_workspace):
        """Test reading RFC by RFC ID from metadata."""
        # Create an RFC
        create_tool = CreateRFCTool()
        create_result = create_tool.execute({
            'title': 'User Profiles',
            'summary': 'Add user profile management',
            'short_name': 'user-profiles'
        })
        
        # Extract RFC ID from result
        assert isinstance(create_result, dict) and "rfc_id" in create_result
        rfc_id = create_result["rfc_id"]
        
        # Test reading by RFC ID
        read_tool = ReadRFCTool()
        result = read_tool.execute({'rfc_id': rfc_id})
        assert result.get("found") is True
        assert "User Profiles" in result.get("content", {}).get("content", "")
    
    def test_move_rfc_preserves_filename(self, temp_workspace):
        """Test that moving RFC doesn't create double extensions."""
        # Create an RFC
        create_tool = CreateRFCTool()
        create_result = create_tool.execute({
            'title': 'Batch Processing',
            'summary': 'Add batch processing support',
            'short_name': 'batch-processing'
        })
        
        # Extract filename
        import re
        assert isinstance(create_result, dict) and "filename" in create_result
        filename = create_result["filename"]
        
        
        # Move to archived
        move_tool = MoveRFCTool()
        move_result = move_tool.execute({
            'rfc_id': filename,
            'target_status': 'archived',
            'reason': 'Testing move'
        })
        
        assert move_result.get("moved")
        
        # Check no double extensions in archived
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        assert not any(f.name.endswith('.md.md') for f in archived_path.iterdir())
        assert not any(f.name.endswith('.md.json') for f in archived_path.iterdir())
        
        # Verify correct files exist
        assert (archived_path / filename).exists()
        assert (archived_path / filename.replace('.md', '.json')).exists()
    
    def test_delete_rfc_by_filename(self, temp_workspace):
        """Test deleting RFC by filename."""
        # Create an RFC
        create_tool = CreateRFCTool()
        create_result = create_tool.execute({
            'title': 'Test Delete',
            'summary': 'RFC to test deletion',
            'short_name': 'test-delete'
        })
        
        # Extract filename
        import re
        assert isinstance(create_result, dict) and "filename" in create_result
        filename = create_result["filename"]
        
        
        # Delete with confirmation
        delete_tool = DeleteRFCTool()
        result = delete_tool.execute({
            'rfc_id': filename,
            'confirm_delete': True,
            'reason': 'Testing deletion'
        })
        
        assert result.get("deleted")
        # Check that the filename appears in at least one of the deleted files
        files_deleted = result.get("files_deleted", [])
        assert any(filename in f for f in files_deleted)
        
        # Verify files are gone
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        assert not (rfc_path / filename).exists()
        assert not (rfc_path / filename.replace('.md', '.json')).exists()
    
    def test_list_rfcs_shows_filenames(self, temp_workspace):
        """Test that list RFCs shows user-friendly filenames."""
        # Create multiple RFCs
        create_tool = CreateRFCTool()
        
        create_tool.execute({
            'title': 'Feature One',
            'summary': 'First feature',
            'short_name': 'feature-one'
        })
        
        create_tool.execute({
            'title': 'Feature Two',
            'summary': 'Second feature',
            'short_name': 'feature-two'
        })
        
        # List RFCs
        list_tool = ListRFCsTool()
        result = list_tool.execute({})
        
        assert isinstance(result, dict) and "rfcs" in result
        rfcs = result["rfcs"]
        assert len(rfcs) >= 2
        
        # Check that filenames are included
        filenames = [rfc.get("filename", "") for rfc in rfcs]
        assert any("feature-one-" in fn for fn in filenames)
        assert any("feature-two-" in fn for fn in filenames)
        
        # Check RFC IDs are included
        rfc_ids = [rfc.get("rfc_id", "") for rfc in rfcs]
        assert any("RFC-" in id for id in rfc_ids)
    
    def test_no_extension_accumulation(self, temp_workspace):
        """Test that operations don't accumulate extensions."""
        # Create RFC
        create_tool = CreateRFCTool()
        create_result = create_tool.execute({
            'title': 'Extension Test',
            'summary': 'Test extension handling',
            'short_name': 'ext-test'
        })
        
        # Extract filename
        import re
        assert isinstance(create_result, dict) and "filename" in create_result
        filename = create_result["filename"]
        
        
        # Multiple operations that could cause extension issues
        move_tool = MoveRFCTool()
        
        # Move to archived
        move_tool.execute({
            'rfc_id': filename,
            'target_status': 'archived'
        })
        
        # Move back to in_progress
        move_tool.execute({
            'rfc_id': filename,
            'target_status': 'in_progress'
        })
        
        # Check no accumulated extensions
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        all_files = list(rfc_path.iterdir())
        
        for f in all_files:
            # No double .md extensions
            assert not f.name.endswith('.md.md')
            # No .md.json extensions
            assert not f.name.endswith('.md.json')
            # JSON files should end with just .json
            if f.suffix == '.json':
                assert not '.md.json' in f.name
    
    def test_special_characters_in_filename(self, temp_workspace):
        """Test handling of special characters in short names."""
        create_tool = CreateRFCTool()
        
        # Test various problematic names
        test_cases = [
            ('api_v2', 'api-v2'),  # Underscores
            ('User Profile!', 'user-profile'),  # Spaces and special chars
            ('feature---test', 'feature-test'),  # Multiple dashes
            ('-leading-dash', 'leading-dash'),  # Leading dash
            ('trailing-dash-', 'trailing-dash'),  # Trailing dash
        ]
        
        for input_name, expected_prefix in test_cases:
            result = create_tool.execute({
                'title': f'Test {input_name}',
                'summary': f'Testing {input_name}',
                'short_name': input_name
            })
            
            assert result.get("rfc_id") is not None
            
            # Check cleaned filename
            rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
            matching_files = list(rfc_path.glob(f"{expected_prefix}-*.md"))
            assert len(matching_files) >= 1, f"No files matching {expected_prefix}-*.md found"