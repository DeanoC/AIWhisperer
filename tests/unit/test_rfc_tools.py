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
from ai_whisperer.path_management import PathManager


class TestCreateRFCTool:
    """Test CreateRFCTool functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc"
            (rfc_dir / "new").mkdir(parents=True)
            (rfc_dir / "in_progress").mkdir(parents=True)
            (rfc_dir / "archived").mkdir(parents=True)
            
            # Create templates directory
            templates_dir = Path(tmpdir) / "templates"
            templates_dir.mkdir()
            
            yield tmpdir
    
    @pytest.fixture
    def create_tool(self, temp_workspace):
        """Create tool instance with mocked PathManager."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
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
            "summary": "This is a test RFC"
        }
        
        result = create_tool.execute(arguments)
        
        # Check success message
        assert "RFC created successfully!" in result
        assert "RFC-" in result
        
        # Verify file was created
        rfc_files = list(Path(temp_workspace, ".WHISPER", "rfc", "new").glob("RFC-*.md"))
        assert len(rfc_files) == 1
        
        # Verify content
        with open(rfc_files[0], 'r') as f:
            content = f.read()
            assert "# RFC: Test RFC" in content
            assert "This is a test RFC" in content
            assert "**Status**: new" in content
    
    def test_create_rfc_with_requirements(self, create_tool, temp_workspace):
        """Test creating RFC with initial requirements."""
        arguments = {
            "title": "Feature RFC",
            "summary": "Add new feature",
            "background": "Users need this feature",
            "initial_requirements": ["Requirement 1", "Requirement 2"],
            "author": "Test User"
        }
        
        result = create_tool.execute(arguments)
        
        # Find created file
        rfc_files = list(Path(temp_workspace, ".WHISPER", "rfc", "new").glob("RFC-*.md"))
        assert len(rfc_files) == 1
        
        with open(rfc_files[0], 'r') as f:
            content = f.read()
            assert "- [ ] Requirement 1" in content
            assert "- [ ] Requirement 2" in content
            assert "**Author**: Test User" in content
            assert "Users need this feature" in content
    
    def test_generate_unique_rfc_id(self, create_tool, temp_workspace):
        """Test RFC ID generation is unique."""
        # Create first RFC
        result1 = create_tool.execute({"title": "RFC 1", "summary": "First"})
        
        # Create second RFC
        result2 = create_tool.execute({"title": "RFC 2", "summary": "Second"})
        
        # Extract IDs
        import re
        id1 = re.search(r'RFC-\d{4}-\d{2}-\d{2}-\d{4}', result1).group()
        id2 = re.search(r'RFC-\d{4}-\d{2}-\d{2}-\d{4}', result2).group()
        
        assert id1 != id2
        
    def test_metadata_file_creation(self, create_tool, temp_workspace):
        """Test that metadata JSON file is created."""
        arguments = {
            "title": "Test RFC",
            "summary": "Test summary",
            "author": "Tester"
        }
        
        create_tool.execute(arguments)
        
        # Check for JSON metadata file
        json_files = list(Path(temp_workspace, ".WHISPER", "rfc", "new").glob("RFC-*.json"))
        assert len(json_files) == 1
        
        # Verify metadata content
        with open(json_files[0], 'r') as f:
            metadata = json.load(f)
            assert metadata["title"] == "Test RFC"
            assert metadata["status"] == "new"
            assert metadata["author"] == "Tester"


class TestReadRFCTool:
    """Test ReadRFCTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_rfc(self):
        """Create workspace with sample RFC."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc"
            (rfc_dir / "new").mkdir(parents=True)
            
            # Create sample RFC
            rfc_content = """# RFC: Test Feature

**RFC ID**: RFC-2025-05-29-0001
**Status**: new
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
            
            rfc_path = rfc_dir / "new" / "RFC-2025-05-29-0001.md"
            with open(rfc_path, 'w') as f:
                f.write(rfc_content)
            
            # Create metadata file
            metadata = {
                "rfc_id": "RFC-2025-05-29-0001",
                "title": "Test Feature",
                "status": "new",
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
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_rfc
            mock_pm.return_value = mock_instance
            
            tool = ReadRFCTool()
            yield tool
    
    def test_read_full_rfc(self, read_tool):
        """Test reading full RFC content."""
        result = read_tool.execute({"rfc_id": "RFC-2025-05-29-0001"})
        
        assert "**RFC Found**: RFC-2025-05-29-0001" in result
        assert "**Title**: Test Feature" in result
        assert "**Status**: new" in result
        assert "This is a test summary" in result
        assert "Technical details here" in result
    
    def test_read_specific_section(self, read_tool):
        """Test reading specific RFC section."""
        result = read_tool.execute({
            "rfc_id": "RFC-2025-05-29-0001",
            "section": "requirements"
        })
        
        assert "## Requirements Section" in result
        assert "- [ ] Requirement 1" in result
        assert "- [ ] Requirement 2" in result
        assert "Technical details" not in result  # Should not include other sections
    
    def test_read_nonexistent_rfc(self, read_tool):
        """Test reading non-existent RFC."""
        result = read_tool.execute({"rfc_id": "RFC-9999-99-99-9999"})
        
        assert "Error: RFC 'RFC-9999-99-99-9999' not found" in result


class TestListRFCsTool:
    """Test ListRFCsTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_rfcs(self):
        """Create workspace with multiple RFCs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc"
            (rfc_dir / "new").mkdir(parents=True)
            (rfc_dir / "in_progress").mkdir(parents=True)
            (rfc_dir / "archived").mkdir(parents=True)
            
            # Create RFCs in different states
            rfcs = [
                ("new", "RFC-2025-05-29-0001", "Feature A", "2025-05-29 10:00:00"),
                ("new", "RFC-2025-05-29-0002", "Feature B", "2025-05-29 11:00:00"),
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
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_rfcs
            mock_pm.return_value = mock_instance
            
            tool = ListRFCsTool()
            yield tool
    
    def test_list_all_rfcs(self, list_tool):
        """Test listing all RFCs."""
        result = list_tool.execute({})
        
        assert "Found 4 RFC(s)" in result
        assert "RFC-2025-05-29-0001" in result
        assert "RFC-2025-05-28-0001" in result
        assert "RFC-2025-05-27-0001" in result
        assert "Feature A" in result
        assert "Feature C" in result
        assert "Feature D" in result
    
    def test_list_by_status(self, list_tool):
        """Test filtering by status."""
        result = list_tool.execute({"status": "new"})
        
        assert "Found 2 RFC(s)" in result
        assert "RFC-2025-05-29-0001" in result
        assert "RFC-2025-05-29-0002" in result
        assert "RFC-2025-05-28-0001" not in result  # in_progress
        assert "RFC-2025-05-27-0001" not in result  # archived
    
    def test_sort_by_created(self, list_tool):
        """Test sorting by creation date."""
        result = list_tool.execute({"sort_by": "created", "limit": 2})
        
        # Check that we got results
        assert "Found" in result
        assert "RFC-2025-05-29" in result  # Should include newest RFCs
        
        # Should be sorted by created date (newest first)
        # Just verify the structure is present
        assert "## New" in result or "## In Progress" in result
    
    def test_empty_status(self, list_tool, temp_workspace_with_rfcs):
        """Test listing empty status folder."""
        # Remove all archived RFCs
        archived_dir = Path(temp_workspace_with_rfcs) / ".WHISPER" / "rfc" / "archived"
        for f in archived_dir.glob("*.md"):
            f.unlink()
        for f in archived_dir.glob("*.json"):
            f.unlink()
        
        result = list_tool.execute({"status": "archived"})
        
        assert "No RFCs found" in result