"""
Regression tests for RFC extension handling bugs
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
from ai_whisperer.tools.delete_rfc_tool import DeleteRFCTool
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


class TestRFCExtensionRegression:
    """Regression tests to prevent extension handling bugs."""
    
    def test_no_double_md_extension_on_move(self, temp_workspace):
        """Regression test: Moving RFC with .md in input shouldn't create .md.md file."""
        # This test catches the exact bug we found where moving "chat-icons-2025-05-31.md"
        # created "chat-icons-2025-05-31.md.md" in the destination
        
        # Create an RFC
        create_tool = CreateRFCTool()
        result = create_tool.execute({
            'title': 'Chat Icons Feature',
            'summary': 'Add chat icons',
            'short_name': 'chat-icons'
        })
        
        # Get the filename from result
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
        assert 'filename' in result, f"No filename in result: {result}"
        filename = result['filename']
        
        # Move using the FULL filename (including .md)
        move_tool = MoveRFCTool()
        move_result = move_tool.execute({
            'rfc_id': filename,  # This includes .md extension
            'target_status': 'archived'
        })
        
        assert isinstance(move_result, dict), f"Expected dict result, got {type(move_result)}"
        assert move_result.get('moved'), f"Move failed: {move_result}"
        
        # Check archived folder - should NOT have .md.md file
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        files = list(archived_path.iterdir())
        
        # Debug output
        print(f"Files in archived: {[f.name for f in files]}")
        
        # Critical assertions
        assert not any(f.name.endswith('.md.md') for f in files), \
            f"Found .md.md file! Files: {[f.name for f in files]}"
        assert any(f.name == filename for f in files), \
            f"Original filename {filename} not found in archived"
        
        # Also check JSON file
        json_filename = filename.replace('.md', '.json')
        assert any(f.name == json_filename for f in files), \
            f"JSON file {json_filename} not found"
        assert not any(f.name.endswith('.md.json') for f in files), \
            f"Found .md.json file! Files: {[f.name for f in files]}"
    
    def test_delete_after_move_with_extension_issue(self, temp_workspace):
        """Test that delete can handle files even if they have extension issues."""
        # Simulate the bug by creating files with double extensions
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        
        # Create a file with double extension (simulating the bug)
        bad_md_file = archived_path / "test-rfc-2025-05-31.md.md"
        bad_json_file = archived_path / "test-rfc-2025-05-31.md.json"
        
        bad_md_file.write_text("# RFC: Test\n**RFC ID**: RFC-2025-05-31-0001")
        bad_json_file.write_text(json.dumps({
            "rfc_id": "RFC-2025-05-31-0001",
            "filename": "test-rfc-2025-05-31.md",  # Original intended name
            "title": "Test RFC"
        }))
        
        # Try to delete using various inputs
        delete_tool = DeleteRFCTool()
        
        # Should find by RFC ID even with messed up filename
        result = delete_tool.execute({
            'rfc_id': 'RFC-2025-05-31-0001',
            'confirm_delete': True
        })
        
        # Should successfully delete despite extension issues
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
        assert result.get('deleted') or 'error' not in result
    
    def test_create_move_delete_workflow(self, temp_workspace):
        """Full workflow test to ensure no extension issues."""
        create_tool = CreateRFCTool()
        move_tool = MoveRFCTool()
        delete_tool = DeleteRFCTool()
        
        # Step 1: Create
        create_result = create_tool.execute({
            'title': 'Workflow Test',
            'summary': 'Testing full workflow',
            'short_name': 'workflow-test'
        })
        
        # Extract filename
        assert isinstance(create_result, dict), f"Expected dict result, got {type(create_result)}"
        assert 'filename' in create_result, f"No filename in result: {create_result}"
        filename = create_result['filename']
        
        # Step 2: Move to archived (using full filename)
        move_result = move_tool.execute({
            'rfc_id': filename,
            'target_status': 'archived'
        })
        assert move_result.get('moved')
        
        # Verify no double extensions
        archived_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "archived"
        assert (archived_path / filename).exists()
        assert not (archived_path / f"{filename}.md").exists()  # No .md.md
        
        # Step 3: Delete (using full filename)
        delete_result = delete_tool.execute({
            'rfc_id': filename,
            'confirm_delete': True,
            'reason': 'Workflow test cleanup'
        })
        assert delete_result.get('deleted')
        
        # Verify deletion
        assert not (archived_path / filename).exists()
        assert not any(f.name.startswith('workflow-test') for f in archived_path.iterdir())
    
    def test_metadata_filename_field_consistency(self, temp_workspace):
        """Ensure metadata filename field matches actual filename."""
        create_tool = CreateRFCTool()
        
        # Create RFC
        create_tool.execute({
            'title': 'Metadata Test',
            'summary': 'Testing metadata',
            'short_name': 'meta-check'
        })
        
        # Find created files
        rfc_path = Path(temp_workspace) / ".WHISPER" / "rfc" / "in_progress"
        md_files = list(rfc_path.glob("meta-check-*.md"))
        json_files = list(rfc_path.glob("meta-check-*.json"))
        
        assert len(md_files) == 1 and len(json_files) == 1
        
        md_filename = md_files[0].name
        json_filename = json_files[0].name
        
        # Read metadata
        with open(rfc_path / json_filename, 'r') as f:
            metadata = json.load(f)
        
        # Metadata filename should match actual MD filename
        assert metadata['filename'] == md_filename, \
            f"Metadata filename '{metadata['filename']}' doesn't match actual '{md_filename}'"
        
        # JSON filename should be MD filename with .json instead of .md
        expected_json = md_filename.replace('.md', '.json')
        assert json_filename == expected_json, \
            f"JSON filename '{json_filename}' doesn't match expected '{expected_json}'"