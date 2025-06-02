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
        
        assert "RFC created successfully!" in result
        assert "dark-mode-" in result  # Should contain the short name
        assert "RFC-" in result  # Should still have RFC ID
        
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
        assert "RFC created successfully!" in result
        
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
        filename_match = re.search(r'api-auth-[\d-]+\.md', create_result)
        assert filename_match
        filename = filename_match.group()
        
        # Test reading by filename
        read_tool = ReadRFCTool()
        
        # Should work with full filename
        result = read_tool.execute({'rfc_id': filename})
        assert "API Authentication" in result
        assert "not found" not in result.lower()
        
        # Should work without .md extension
        result = read_tool.execute({'rfc_id': filename[:-3]})
        assert "API Authentication" in result
        assert "not found" not in result.lower()
    
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
        import re
        rfc_id_match = re.search(r'RFC-\d{4}-\d{2}-\d{2}-\d{4}', create_result)
        assert rfc_id_match
        rfc_id = rfc_id_match.group()
        
        # Test reading by RFC ID
        read_tool = ReadRFCTool()
        result = read_tool.execute({'rfc_id': rfc_id})
        assert "User Profiles" in result
        assert "not found" not in result.lower()
    
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
        filename_match = re.search(r'batch-processing-[\d-]+\.md', create_result)
        assert filename_match
        filename = filename_match.group()
        
        # Move to archived
        move_tool = MoveRFCTool()
        move_result = move_tool.execute({
            'rfc_id': filename,
            'target_status': 'archived',
            'reason': 'Testing move'
        })
        
        assert "moved successfully" in move_result.lower()
        
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
        filename_match = re.search(r'test-delete-[\d-]+\.md', create_result)
        assert filename_match
        filename = filename_match.group()
        
        # Delete with confirmation
        delete_tool = DeleteRFCTool()
        result = delete_tool.execute({
            'rfc_id': filename,
            'confirm_delete': True,
            'reason': 'Testing deletion'
        })
        
        assert "deleted successfully" in result.lower()
        assert filename in result
        
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
        
        assert "feature-one-" in result
        assert "feature-two-" in result
        assert ".md" in result  # Should show full filename
        assert "RFC-" in result  # Should still show RFC IDs
    
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
        filename_match = re.search(r'ext-test-[\d-]+\.md', create_result)
        assert filename_match
        filename = filename_match.group()
        
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
            
            assert "RFC created successfully!" in result
            
            # Check cleaned filename
            rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
            matching_files = list(rfc_path.glob(f"{expected_prefix}-*.md"))
            assert len(matching_files) >= 1, f"No files matching {expected_prefix}-*.md found"