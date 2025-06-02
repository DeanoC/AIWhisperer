"""Complete unit tests for all RFC management tools."""
import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile

from ai_whisperer.tools.update_rfc_tool import UpdateRFCTool
from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
from ai_whisperer.utils.path import PathManager


class TestUpdateRFCTool:
    """Test UpdateRFCTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_rfc(self):
        """Create workspace with sample RFC."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc"
            (rfc_dir / "in_progress").mkdir(parents=True)
            
            # Create sample RFC
            rfc_content = """# RFC: Test Feature

**RFC ID**: RFC-2025-05-29-0001
**Status**: in_progress
**Created**: 2025-05-29 10:00:00
**Last Updated**: 2025-05-29 10:00:00
**Author**: Test User

## Summary
This is a test summary.

## Background
*To be defined during refinement*

## Requirements
- [ ] Requirement 1

## Technical Considerations
*To be defined during refinement*

## Open Questions
- [ ] Question 1

## Refinement History
- 2025-05-29 10:00:00: RFC created with initial idea

---
*This RFC was created by AIWhisperer's Agent P (Patricia)*"""
            
            rfc_path = rfc_dir / "in_progress" / "RFC-2025-05-29-0001.md"
            rfc_path.write_text(rfc_content)
            
            # Create metadata file
            metadata = {
                "rfc_id": "RFC-2025-05-29-0001",
                "title": "Test Feature",
                "status": "in_progress",
                "created": "2025-05-29 10:00:00",
                "updated": "2025-05-29 10:00:00",
                "author": "Test User"
            }
            
            metadata_path = rfc_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            yield tmpdir
    
    @pytest.fixture
    def update_tool(self, temp_workspace_with_rfc):
        """Create tool instance."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_rfc
            mock_pm.return_value = mock_instance
            
            tool = UpdateRFCTool()
            yield tool
    
    def test_tool_properties(self, update_tool):
        """Test tool properties."""
        assert update_tool.name == "update_rfc"
        assert "Update an existing RFC" in update_tool.description
        assert update_tool.category == "RFC Management"
        assert "rfc" in update_tool.tags
    
    def test_update_existing_section(self, update_tool, temp_workspace_with_rfc):
        """Test updating an existing section."""
        result = update_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "background",
            "content": "Users need a caching mechanism to improve performance."
        })
        
        assert "RFC updated successfully!" in result
        assert "Background" in result
        
        # Verify file was updated
        rfc_path = Path(temp_workspace_with_rfc) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.md"
        content = rfc_path.read_text()
        assert "Users need a caching mechanism" in content
        # Check that the background section specifically was updated
        assert "## Background\nUsers need a caching mechanism" in content
    
    def test_append_to_section(self, update_tool, temp_workspace_with_rfc):
        """Test appending to a section."""
        result = update_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "requirements",
            "content": "- [ ] Requirement 2\n- [ ] Requirement 3",
            "append": True
        })
        
        assert "RFC updated successfully!" in result
        assert "Appended to" in result
        
        # Verify content was appended
        rfc_path = Path(temp_workspace_with_rfc) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.md"
        content = rfc_path.read_text()
        assert "- [ ] Requirement 1" in content  # Original
        assert "- [ ] Requirement 2" in content  # Appended
        assert "- [ ] Requirement 3" in content  # Appended
    
    def test_update_title(self, update_tool, temp_workspace_with_rfc):
        """Test updating RFC title."""
        result = update_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "title",
            "content": "Enhanced Caching Feature"
        })
        
        assert "RFC updated successfully!" in result
        
        # Verify title was updated
        rfc_path = Path(temp_workspace_with_rfc) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.md"
        content = rfc_path.read_text()
        assert "# RFC: Enhanced Caching Feature" in content
    
    def test_add_new_section(self, update_tool, temp_workspace_with_rfc):
        """Test adding a new section that doesn't exist."""
        result = update_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "implementation_approach",
            "content": "Use Redis for distributed caching."
        })
        
        assert "RFC updated successfully!" in result
        
        # Verify section was added
        rfc_path = Path(temp_workspace_with_rfc) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.md"
        content = rfc_path.read_text()
        assert "## Implementation Approach" in content
        assert "Use Redis for distributed caching" in content
    
    def test_history_tracking(self, update_tool, temp_workspace_with_rfc):
        """Test that updates are tracked in history."""
        update_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "requirements",
            "content": "- [ ] New requirement",
            "history_note": "Added performance requirements"
        })
        
        # Check history
        rfc_path = Path(temp_workspace_with_rfc) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.md"
        content = rfc_path.read_text()
        assert "Added performance requirements" in content
        assert "## Refinement History" in content
    
    def test_metadata_update(self, update_tool, temp_workspace_with_rfc):
        """Test that metadata is updated."""
        update_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "summary",
            "content": "Updated summary"
        })
        
        # Check metadata
        metadata_path = Path(temp_workspace_with_rfc) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['updated'] != "2025-05-29 10:00:00"  # Should be updated
        assert metadata['last_updated_section'] == "summary"
        assert metadata['last_updated_by'] == "Agent P"
    
    def test_rfc_not_found(self, update_tool):
        """Test updating non-existent RFC."""
        result = update_tool.execute({
            "rfc_id": "RFC-9999-99-99-9999",
            "section": "summary",
            "content": "New content"
        })
        
        assert "Error: RFC 'RFC-9999-99-99-9999' not found" in result


class TestMoveRFCTool:
    """Test MoveRFCTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_rfcs(self):
        """Create workspace with RFCs in different states."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc"
            (rfc_dir / "in_progress").mkdir(parents=True)
            (rfc_dir / "archived").mkdir(parents=True)
            
            # Create RFC in in_progress status
            rfc_content = """# RFC: Test Feature

**RFC ID**: RFC-2025-05-29-0001
**Status**: in_progress
**Created**: 2025-05-29 10:00:00
**Last Updated**: 2025-05-29 10:00:00
**Author**: Test User

## Summary
Test summary.

## Refinement History
- 2025-05-29 10:00:00: RFC created"""
            
            rfc_path = rfc_dir / "in_progress" / "RFC-2025-05-29-0001.md"
            rfc_path.write_text(rfc_content)
            
            # Create metadata
            metadata = {
                "rfc_id": "RFC-2025-05-29-0001",
                "title": "Test Feature",
                "status": "in_progress",
                "created": "2025-05-29 10:00:00",
                "updated": "2025-05-29 10:00:00"
            }
            
            with open(rfc_path.with_suffix('.json'), 'w') as f:
                json.dump(metadata, f)
            
            yield tmpdir
    
    @pytest.fixture
    def move_tool(self, temp_workspace_with_rfcs):
        """Create tool instance."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_rfcs
            mock_pm.return_value = mock_instance
            
            tool = MoveRFCTool()
            yield tool
    
    def test_tool_properties(self, move_tool):
        """Test tool properties."""
        assert move_tool.name == "move_rfc"
        assert "Move an RFC document" in move_tool.description
        assert move_tool.category == "RFC Management"
        assert "workflow" in move_tool.tags
    
    def test_move_in_progress_to_archived(self, move_tool, temp_workspace_with_rfcs):
        """Test moving RFC from in_progress to archived."""
        result = move_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "target_status": "archived",
            "reason": "Refinement complete"
        })
        
        assert "RFC moved successfully!" in result
        assert "in_progress" in result
        assert "archived" in result
        assert "Refinement complete" in result
        
        # Verify file was moved
        old_path = Path(temp_workspace_with_rfcs) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.md"
        new_path = Path(temp_workspace_with_rfcs) / ".WHISPER" / "rfc" / "archived" / "RFC-2025-05-29-0001.md"
        
        assert not old_path.exists()
        assert new_path.exists()
        
        # Verify status was updated in content
        content = new_path.read_text()
        assert "**Status**: archived" in content
    
    def test_move_with_metadata(self, move_tool, temp_workspace_with_rfcs):
        """Test that metadata is moved and updated."""
        move_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "target_status": "archived"
        })
        
        # Check metadata was moved
        old_meta = Path(temp_workspace_with_rfcs) / ".WHISPER" / "rfc" / "in_progress" / "RFC-2025-05-29-0001.json"
        new_meta = Path(temp_workspace_with_rfcs) / ".WHISPER" / "rfc" / "archived" / "RFC-2025-05-29-0001.json"
        
        assert not old_meta.exists()
        assert new_meta.exists()
        
        # Check metadata content
        with open(new_meta, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['status'] == "archived"
        assert 'status_history' in metadata
        assert len(metadata['status_history']) == 1
        assert metadata['status_history'][0]['from'] == "in_progress"
        assert metadata['status_history'][0]['to'] == "archived"
    
    def test_history_tracking(self, move_tool, temp_workspace_with_rfcs):
        """Test that moves are tracked in refinement history."""
        move_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "target_status": "archived",
            "reason": "Requirements gathered"
        })
        
        # Check history
        rfc_path = Path(temp_workspace_with_rfcs) / ".WHISPER" / "rfc" / "archived" / "RFC-2025-05-29-0001.md"
        content = rfc_path.read_text()
        
        assert "Status changed from 'in_progress' to 'archived'" in content
        assert "Requirements gathered" in content
    
    def test_already_in_target_status(self, move_tool, temp_workspace_with_rfcs):
        """Test moving to same status."""
        result = move_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "target_status": "in_progress"
        })
        
        assert "already in 'in_progress' status" in result
    
    def test_rfc_not_found(self, move_tool):
        """Test moving non-existent RFC."""
        result = move_tool.execute({
            "rfc_id": "RFC-9999-99-99-9999",
            "target_status": "in_progress"
        })
        
        assert "Error: RFC 'RFC-9999-99-99-9999' not found" in result
    
    def test_transition_messages(self, move_tool, temp_workspace_with_rfcs):
        """Test appropriate messages for different transitions."""
        # In_progress to archived
        result = move_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "target_status": "archived"
        })
        assert "refinement is complete" in result