"""Unit tests for RFC management tools."""
import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile

from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
from ai_whisperer.tools.read_rfc_tool import ReadRFCTool
from ai_whisperer.tools.list_rfcs_tool import ListRFCsTool
from ai_whisperer.utils.path import PathManager


class TestCreateRFCTool:
    """Test CreateRFCTool functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc"
            (rfc_dir / "in_progress").mkdir(parents=True)
            (rfc_dir / "archived").mkdir(parents=True)
            
            # Create templates directory
            templates_dir = Path(tmpdir) / "templates"
            templates_dir.mkdir()
            
            yield tmpdir
    
    @pytest.fixture
    def create_tool(self, temp_workspace):
        """Create tool instance with mocked PathManager."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace
            mock_pm.return_value = mock_instance
            
            tool = CreateRFCTool()
            yield tool
    
    def test_tool_properties(self, create_tool):
        """Test tool properties."""
        assert create_tool.name == "create_rfc"
        assert "Create a new RFC" in create_tool.description
        assert create_tool.category == "RFC Management"
        assert "rfc" in create_tool.tags
        
    def test_create_basic_rfc(self, create_tool, temp_workspace):
        """Test creating a basic RFC."""
        arguments = {
            "title": "Test RFC",
            "summary": "This is a test RFC",
            "short_name": "test-rfc"
        }
        
        result = create_tool.execute(arguments)
        
        assert isinstance(result, dict)
        assert 'rfc_id' in result
        assert result['rfc_id'].startswith("RFC-")
        assert 'path' in result
        
        # Verify file was created - look for files with the short name pattern
        rfc_files = list(Path(temp_workspace, ".WHISPER", "rfc", "in_progress").glob("test-rfc-*.md"))
        assert len(rfc_files) == 1
        
        # Verify content
        with open(rfc_files[0], 'r') as f:
            content = f.read()
            assert "# RFC: Test RFC" in content
            assert "This is a test RFC" in content
            assert "**Status**: in_progress" in content
    
    def test_create_rfc_with_requirements(self, create_tool, temp_workspace):
        """Test creating RFC with initial requirements."""
        arguments = {
            "title": "Feature RFC",
            "summary": "Add new feature",
            "short_name": "feature-rfc",
            "background": "Users need this feature",
            "initial_requirements": ["Requirement 1", "Requirement 2"],
            "author": "Test User"
        }
        
        result = create_tool.execute(arguments)
        
        assert isinstance(result, dict)
        assert 'rfc_id' in result
        
        # Find created file
        rfc_files = list(Path(temp_workspace, ".WHISPER", "rfc", "in_progress").glob("feature-rfc-*.md"))
        assert len(rfc_files) == 1
        
        with open(rfc_files[0], 'r') as f:
            content = f.read()
            assert "- [ ] Requirement 1" in content
            assert "- [ ] Requirement 2" in content
            assert "**Author**: Test User" in content
            assert "Users need this feature" in content
    
    def test_generate_unique_rfc_id(self, create_tool, temp_workspace):
        """Test RFC ID generation is unique."""
        # Create first RFC with same short name to force counter increment
        result1 = create_tool.execute({"title": "RFC 1", "summary": "First", "short_name": "test-rfc"})
        
        # Create second RFC with same short name - should get different ID
        result2 = create_tool.execute({"title": "RFC 2", "summary": "Second", "short_name": "test-rfc"})
        
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        
        # Extract IDs
        id1 = result1['rfc_id']
        id2 = result2['rfc_id']
        
        assert id1 != id2
        
    def test_metadata_file_creation(self, create_tool, temp_workspace):
        """Test that metadata JSON file is created."""
        arguments = {
            "title": "Test RFC",
            "summary": "Test summary",
            "short_name": "test-metadata",
            "author": "Tester"
        }
        
        result = create_tool.execute(arguments)
        assert isinstance(result, dict)
        
        # Check for JSON metadata file
        json_files = list(Path(temp_workspace, ".WHISPER", "rfc", "in_progress").glob("test-metadata-*.json"))
        assert len(json_files) == 1
        
        # Verify metadata content
        with open(json_files[0], 'r') as f:
            metadata = json.load(f)
            assert metadata["title"] == "Test RFC"
            assert metadata["status"] == "in_progress"
            assert metadata["author"] == "Tester"


class TestReadRFCTool:
    """Test ReadRFCTool functionality."""
    
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
This is the background.

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Technical Considerations
Technical details here.

## Open Questions
- [ ] Question 1
- [ ] Question 2

---
*This RFC was created by AIWhisperer's Agent P (Patricia)*"""
            
            rfc_path = rfc_dir / "in_progress" / "RFC-2025-05-29-0001.md"
            with open(rfc_path, 'w') as f:
                f.write(rfc_content)
            
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
    def read_tool(self, temp_workspace_with_rfc):
        """Create tool instance."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_rfc
            mock_pm.return_value = mock_instance
            
            tool = ReadRFCTool()
            yield tool
    
    def test_read_full_rfc(self, read_tool):
        """Test reading full RFC content."""
        result = read_tool.execute({"rfc_id": "RFC-2025-05-29-0001"})
        
        assert isinstance(result, dict)
        assert result['found'] is True
        assert 'content' in result
        
        # Content is nested
        content_data = result['content']
        assert isinstance(content_data, dict)
        assert 'content' in content_data
        
        # The actual RFC text is in content['content']
        rfc_text = content_data['content']
        assert "RFC-2025-05-29-0001" in rfc_text
        assert "Test Feature" in rfc_text
        assert "in_progress" in rfc_text
        assert "This is a test summary" in rfc_text
        assert "Technical details here" in rfc_text
    
    def test_read_specific_section(self, read_tool):
        """Test reading specific RFC section."""
        result = read_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "requirements"
        })
        
        assert isinstance(result, dict)
        assert 'content' in result
        
        # Get the section content
        content_data = result['content']
        section_text = content_data['content']
        
        assert "Requirement 1" in section_text
        assert "Requirement 2" in section_text
        # When reading specific section, should not include other sections
        assert "Technical details" not in section_text
    
    def test_read_nonexistent_rfc(self, read_tool):
        """Test reading non-existent RFC."""
        result = read_tool.execute({"rfc_id": "RFC-9999-99-99-9999"})
        
        assert isinstance(result, dict)
        assert 'error' in result
        assert "not found" in result['error']


class TestListRFCsTool:
    """Test ListRFCsTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_rfcs(self):
        """Create workspace with multiple RFCs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc"
            (rfc_dir / "in_progress").mkdir(parents=True)
            (rfc_dir / "archived").mkdir(parents=True)
            
            # Create RFCs in different states
            rfcs = [
                ("in_progress", "RFC-2025-05-29-0001", "Feature A", "2025-05-29 10:00:00"),
                ("in_progress", "RFC-2025-05-29-0002", "Feature B", "2025-05-29 11:00:00"),
                ("in_progress", "RFC-2025-05-28-0001", "Feature C", "2025-05-28 10:00:00"),
                ("archived", "RFC-2025-05-27-0001", "Feature D", "2025-05-27 10:00:00"),
            ]
            
            for status, rfc_id, title, created in rfcs:
                # Create RFC file
                content = f"""# RFC: {title}

**RFC ID**: {rfc_id}
**Status**: {status}
**Created**: {created}
**Last Updated**: {created}
**Author**: Test User

## Summary
Summary for {title}"""
                
                rfc_path = rfc_dir / status / f"{rfc_id}.md"
                with open(rfc_path, 'w') as f:
                    f.write(content)
                
                # Create metadata
                metadata = {
                    "rfc_id": rfc_id,
                    "title": title,
                    "status": status,
                    "created": created,
                    "updated": created,
                    "author": "Test User"
                }
                
                metadata_path = rfc_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
            
            yield tmpdir
    
    @pytest.fixture
    def list_tool(self, temp_workspace_with_rfcs):
        """Create tool instance."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_rfcs
            mock_pm.return_value = mock_instance
            
            tool = ListRFCsTool()
            yield tool
    
    def test_list_all_rfcs(self, list_tool):
        """Test listing all RFCs."""
        result = list_tool.execute({"status": "all"})
        
        assert isinstance(result, dict)
        assert 'by_status' in result
        
        # Collect all RFCs from all statuses
        all_rfcs = []
        for status_rfcs in result['by_status'].values():
            all_rfcs.extend(status_rfcs)
        
        assert len(all_rfcs) == 4
        
        rfc_ids = [rfc['rfc_id'] for rfc in all_rfcs]
        assert "RFC-2025-05-29-0001" in rfc_ids
        assert "RFC-2025-05-28-0001" in rfc_ids
        assert "RFC-2025-05-27-0001" in rfc_ids
        
        titles = [rfc['title'] for rfc in all_rfcs]
        assert "Feature A" in titles
        assert "Feature C" in titles
        assert "Feature D" in titles
    
    def test_list_by_status(self, list_tool):
        """Test filtering by status."""
        result = list_tool.execute({"status": "in_progress"})
        
        assert isinstance(result, dict)
        assert 'by_status' in result
        
        # Should only have in_progress RFCs
        in_progress_rfcs = result['by_status'].get('in_progress', [])
        assert len(in_progress_rfcs) == 3
        
        rfc_ids = [rfc['rfc_id'] for rfc in in_progress_rfcs]
        assert "RFC-2025-05-29-0001" in rfc_ids
        assert "RFC-2025-05-29-0002" in rfc_ids
        assert "RFC-2025-05-28-0001" in rfc_ids  # in_progress
        
        # Archived should not be included when filtering by in_progress
        assert 'archived' not in result['by_status'] or len(result['by_status'].get('archived', [])) == 0
    
    def test_sort_by_created(self, list_tool):
        """Test sorting by creation date."""
        result = list_tool.execute({"sort_by": "created", "limit": 2})
        
        assert isinstance(result, dict)
        assert 'by_status' in result
        assert result.get('sort_by') == 'created'
        
        # Collect all RFCs and check total count respects limit
        all_rfcs = []
        for status_rfcs in result['by_status'].values():
            all_rfcs.extend(status_rfcs)
        
        # With limit=2, should have at most 2 RFCs total
        assert len(all_rfcs) <= 2
    
    def test_empty_status(self, list_tool, temp_workspace_with_rfcs):
        """Test listing empty status folder."""
        # Remove all archived RFCs
        archived_dir = Path(temp_workspace_with_rfcs) / ".WHISPER" / "rfc" / "archived"
        for f in archived_dir.glob("*.md"):
            f.unlink()
        for f in archived_dir.glob("*.json"):
            f.unlink()
        
        result = list_tool.execute({"status": "archived"})
        
        assert isinstance(result, dict)
        assert 'by_status' in result
        # When filtering by archived and it's empty, might not have the key or have empty list
        archived_rfcs = result['by_status'].get('archived', [])
        assert len(archived_rfcs) == 0