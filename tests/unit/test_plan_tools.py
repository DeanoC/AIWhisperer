"""Unit tests for Plan management tools."""
import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import hashlib

from ai_whisperer.tools.create_plan_from_rfc_tool import CreatePlanFromRFCTool
from ai_whisperer.tools.list_plans_tool import ListPlansTool
from ai_whisperer.tools.read_plan_tool import ReadPlanTool
from ai_whisperer.tools.update_plan_from_rfc_tool import UpdatePlanFromRFCTool
from ai_whisperer.tools.move_plan_tool import MovePlanTool
from ai_whisperer.path_management import PathManager


class TestCreatePlanFromRFCTool:
    """Test CreatePlanFromRFCTool functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC structure with sample RFC
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc" / "in_progress"
            rfc_dir.mkdir(parents=True)
            
            # Create plan directories
            plan_dir = Path(tmpdir) / ".WHISPER" / "plans"
            (plan_dir / "in_progress").mkdir(parents=True)
            (plan_dir / "archived").mkdir(parents=True)
            
            # Create sample RFC
            rfc_content = """# RFC: Add Caching Feature

**RFC ID**: RFC-2025-05-31-0001
**Status**: in_progress
**Created**: 2025-05-31 10:00:00
**Last Updated**: 2025-05-31 10:00:00
**Author**: Test User
**Short Name**: add-caching

## Summary
Add a caching layer to improve application performance.

## Background
Users are experiencing slow response times. A caching layer would help.

## Requirements
- [ ] Implement in-memory cache
- [ ] Add Redis support
- [ ] Create cache invalidation strategy
- [ ] Add cache metrics

## Technical Considerations
- Use decorator pattern for cache integration
- Consider TTL for cache entries
- Handle cache misses gracefully

## Implementation Approach
Start with in-memory implementation, then add Redis support.

## Open Questions
- [ ] What cache eviction policy to use?
- [ ] Should we support multiple cache backends?

## Acceptance Criteria
- Response times improved by 50%
- Cache hit rate > 80%
- No stale data issues
"""
            
            rfc_path = rfc_dir / "add-caching-2025-05-31.md"
            with open(rfc_path, 'w') as f:
                f.write(rfc_content)
            
            # Create RFC metadata
            metadata = {
                "rfc_id": "RFC-2025-05-31-0001",
                "filename": "add-caching-2025-05-31.md",
                "short_name": "add-caching",
                "title": "Add Caching Feature",
                "status": "in_progress",
                "created": "2025-05-31 10:00:00",
                "updated": "2025-05-31 10:00:00",
                "author": "Test User"
            }
            
            metadata_path = rfc_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            yield tmpdir
    
    @pytest.fixture
    def create_tool(self, temp_workspace):
        """Create tool instance with mocked PathManager."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace
            mock_pm.return_value = mock_instance
            
            tool = CreatePlanFromRFCTool()
            yield tool
    
    def test_tool_properties(self, create_tool):
        """Test tool properties."""
        assert create_tool.name == "create_plan_from_rfc"
        assert "RFC into a structured execution plan" in create_tool.description
        assert create_tool.category == "Plan Management"
        assert "rfc" in create_tool.tags
        assert "plan" in create_tool.tags
    
    def test_create_plan_from_rfc_basic(self, create_tool, temp_workspace):
        """Test creating a plan from an RFC."""
        # Mock AI service for structured output
        with patch('ai_whisperer.tools.create_plan_from_rfc_tool.OpenRouterAIService') as mock_ai_class:
            mock_service = Mock()
            mock_response = {
                "plan_type": "initial",
                "title": "Implement Caching Feature",
                "description": "Add caching layer as specified in RFC",
                "agent_type": "code_generation",
                "tasks": [
                    {
                        "name": "Write cache interface tests",
                        "description": "TDD: Create tests for cache interface",
                        "agent_type": "test_generation",
                        "dependencies": []
                    },
                    {
                        "name": "Implement cache interface",
                        "description": "Create abstract cache interface",
                        "agent_type": "code_generation",
                        "dependencies": ["Write cache interface tests"]
                    },
                    {
                        "name": "Write in-memory cache tests",
                        "description": "TDD: Create tests for in-memory implementation",
                        "agent_type": "test_generation",
                        "dependencies": ["Implement cache interface"]
                    },
                    {
                        "name": "Implement in-memory cache",
                        "description": "Create in-memory cache implementation",
                        "agent_type": "code_generation",
                        "dependencies": ["Write in-memory cache tests"]
                    }
                ],
                "validation_criteria": [
                    "All tests pass",
                    "Cache interface is abstract",
                    "In-memory implementation works"
                ]
            }
            
            # Mock the async stream_chat_completion method
            async def mock_stream():
                from ai_whisperer.ai_service.ai_service import AIStreamChunk
                yield AIStreamChunk(delta_content=json.dumps(mock_response))
            
            mock_service.stream_chat_completion = Mock(return_value=mock_stream())
            mock_ai_class.return_value = mock_service
            
            arguments = {
                "rfc_id": "RFC-2025-05-31-0001"
            }
            
            result = create_tool.execute(arguments)
            
            # Check success message
            assert "Plan created successfully!" in result
            assert "add-caching-plan-2025-05-31" in result
            
            # Verify plan directory was created
            plan_dirs = list(Path(temp_workspace, ".WHISPER", "plans", "in_progress").iterdir())
            assert len(plan_dirs) == 1
            plan_dir = plan_dirs[0]
            assert plan_dir.name.startswith("add-caching-plan-")
            
            # Verify plan.json was created
            plan_file = plan_dir / "plan.json"
            assert plan_file.exists()
            
            with open(plan_file, 'r') as f:
                plan_data = json.load(f)
                assert plan_data["source_rfc"]["rfc_id"] == "RFC-2025-05-31-0001"
                assert plan_data["plan_type"] == "initial"
                assert len(plan_data["tasks"]) == 4
                assert plan_data["tasks"][0]["name"] == "Write cache interface tests"
            
            # Verify rfc_reference.json was created
            ref_file = plan_dir / "rfc_reference.json"
            assert ref_file.exists()
            
            # Verify RFC metadata was updated
            rfc_metadata_path = Path(temp_workspace, ".WHISPER", "rfc", "in_progress", "add-caching-2025-05-31.json")
            with open(rfc_metadata_path, 'r') as f:
                rfc_metadata = json.load(f)
                assert "derived_plans" in rfc_metadata
                assert len(rfc_metadata["derived_plans"]) == 1
                assert rfc_metadata["derived_plans"][0]["plan_name"] == plan_dir.name
    
    def test_create_plan_with_short_name(self, create_tool, temp_workspace):
        """Test creating plan using RFC short name."""
        with patch('ai_whisperer.tools.create_plan_from_rfc_tool.OpenRouterAIService') as mock_ai_class:
            mock_service = Mock()
            mock_response = {
                "plan_type": "initial",
                "title": "Implement Caching Feature",
                "tasks": [],
                "validation_criteria": ["Basic validation"]
            }
            
            async def mock_stream():
                from ai_whisperer.ai_service.ai_service import AIStreamChunk
                yield AIStreamChunk(delta_content=json.dumps(mock_response))
            
            mock_service.stream_chat_completion = Mock(return_value=mock_stream())
            mock_ai_class.return_value = mock_service
            
            arguments = {
                "rfc_id": "add-caching"  # Using short name
            }
            
            result = create_tool.execute(arguments)
            assert "Plan created successfully!" in result
    
    def test_create_plan_nonexistent_rfc(self, create_tool):
        """Test creating plan from non-existent RFC."""
        arguments = {
            "rfc_id": "RFC-9999-99-99-9999"
        }
        
        result = create_tool.execute(arguments)
        assert "Error: RFC 'RFC-9999-99-99-9999' not found" in result
    
    def test_create_plan_with_model_override(self, create_tool, temp_workspace):
        """Test creating plan with specific model."""
        with patch('ai_whisperer.tools.create_plan_from_rfc_tool.OpenRouterAIService') as mock_ai_class:
            mock_service = Mock()
            mock_response = {"plan_type": "initial", "title": "Test", "tasks": [], "validation_criteria": ["Test passes"]}
            
            async def mock_stream():
                from ai_whisperer.ai_service.ai_service import AIStreamChunk
                yield AIStreamChunk(delta_content=json.dumps(mock_response))
            
            mock_service.stream_chat_completion = Mock(return_value=mock_stream())
            mock_ai_class.return_value = mock_service
            
            arguments = {
                "rfc_id": "RFC-2025-05-31-0001",
                "model": "gpt-4"
            }
            
            result = create_tool.execute(arguments)
            assert "Plan created successfully!" in result
            
            # Verify model was passed to AI service constructor
            # Now using config parameter instead of positional dict
            assert mock_ai_class.call_args.kwargs['config'].model_id == "gpt-4"


class TestListPlansTool:
    """Test ListPlansTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_plans(self):
        """Create workspace with multiple plans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create plan structure
            plan_dir = Path(tmpdir) / ".WHISPER" / "plans"
            (plan_dir / "in_progress").mkdir(parents=True)
            (plan_dir / "archived").mkdir(parents=True)
            
            # Create plans in different states
            plans = [
                ("in_progress", "feature-a-plan-2025-05-31", "Feature A Implementation", "RFC-2025-05-31-0001"),
                ("in_progress", "feature-b-plan-2025-05-30", "Feature B Implementation", "RFC-2025-05-30-0001"),
                ("archived", "feature-c-plan-2025-05-29", "Feature C Implementation", "RFC-2025-05-29-0001"),
            ]
            
            for status, plan_name, title, rfc_id in plans:
                # Create plan directory
                dir_path = plan_dir / status / plan_name
                dir_path.mkdir()
                
                # Create plan.json
                plan_data = {
                    "plan_type": "initial",
                    "title": title,
                    "status": status,
                    "created": f"{plan_name[-10:]} 10:00:00",
                    "updated": f"{plan_name[-10:]} 10:00:00",
                    "source_rfc": {
                        "rfc_id": rfc_id,
                        "title": title.replace("Implementation", "RFC")
                    },
                    "tasks": []
                }
                
                with open(dir_path / "plan.json", 'w') as f:
                    json.dump(plan_data, f)
            
            yield tmpdir
    
    @pytest.fixture
    def list_tool(self, temp_workspace_with_plans):
        """Create tool instance."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_plans
            mock_pm.return_value = mock_instance
            
            tool = ListPlansTool()
            yield tool
    
    def test_list_all_plans(self, list_tool):
        """Test listing all plans."""
        result = list_tool.execute({})
        
        assert "Found 3 plan(s)" in result
        assert "feature-a-plan-2025-05-31" in result
        assert "feature-b-plan-2025-05-30" in result
        assert "feature-c-plan-2025-05-29" in result
        assert "Feature A Implementation" in result
        assert "RFC-2025-05-31-0001" in result
    
    def test_list_by_status(self, list_tool):
        """Test filtering by status."""
        result = list_tool.execute({"status": "in_progress"})
        
        assert "Found 2 plan(s)" in result
        assert "feature-a-plan-2025-05-31" in result
        assert "feature-b-plan-2025-05-30" in result
        assert "feature-c-plan-2025-05-29" not in result
    
    def test_list_with_limit(self, list_tool):
        """Test limiting results."""
        result = list_tool.execute({"limit": 1})
        
        assert "feature-a-plan-2025-05-31" in result
        assert "feature-b-plan-2025-05-30" not in result


class TestReadPlanTool:
    """Test ReadPlanTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_plan(self):
        """Create workspace with a sample plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create plan structure
            plan_dir = Path(tmpdir) / ".WHISPER" / "plans" / "in_progress" / "test-feature-plan-2025-05-31"
            plan_dir.mkdir(parents=True)
            
            # Create plan.json
            plan_data = {
                "plan_type": "initial",
                "title": "Test Feature Implementation",
                "description": "Implement test feature as per RFC",
                "status": "in_progress",
                "created": "2025-05-31 10:00:00",
                "updated": "2025-05-31 10:00:00",
                "source_rfc": {
                    "rfc_id": "RFC-2025-05-31-0001",
                    "title": "Test Feature RFC",
                    "filename": "test-feature-2025-05-31.md"
                },
                "tasks": [
                    {
                        "name": "Write tests",
                        "description": "TDD: Write failing tests first",
                        "agent_type": "test_generation",
                        "dependencies": []
                    },
                    {
                        "name": "Implement feature",
                        "description": "Make tests pass",
                        "agent_type": "code_generation",
                        "dependencies": ["Write tests"]
                    }
                ],
                "validation_criteria": ["All tests pass", "Code review approved"]
            }
            
            with open(plan_dir / "plan.json", 'w') as f:
                json.dump(plan_data, f, indent=2)
            
            # Create rfc_reference.json
            ref_data = {
                "rfc_id": "RFC-2025-05-31-0001",
                "rfc_path": ".WHISPER/rfc/in_progress/test-feature-2025-05-31.md",
                "rfc_content_hash": "abc123",
                "last_sync": "2025-05-31 10:00:00"
            }
            
            with open(plan_dir / "rfc_reference.json", 'w') as f:
                json.dump(ref_data, f, indent=2)
            
            yield tmpdir
    
    @pytest.fixture
    def read_tool(self, temp_workspace_with_plan):
        """Create tool instance."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_plan
            mock_pm.return_value = mock_instance
            
            tool = ReadPlanTool()
            yield tool
    
    def test_read_plan(self, read_tool):
        """Test reading a plan."""
        result = read_tool.execute({"plan_name": "test-feature-plan-2025-05-31"})
        
        assert "**Plan Found**: test-feature-plan-2025-05-31" in result
        assert "**Title**: Test Feature Implementation" in result
        assert "**Source RFC**: RFC-2025-05-31-0001" in result
        assert "Write tests" in result
        assert "TDD: Write failing tests first" in result
        assert "All tests pass" in result
    
    def test_read_nonexistent_plan(self, read_tool):
        """Test reading non-existent plan."""
        result = read_tool.execute({"plan_name": "nonexistent-plan"})
        
        assert "Error: Plan 'nonexistent-plan' not found" in result


class TestUpdatePlanFromRFCTool:
    """Test UpdatePlanFromRFCTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_modified_rfc(self):
        """Create workspace with RFC and plan where RFC has been modified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RFC
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc" / "in_progress"
            rfc_dir.mkdir(parents=True)
            
            rfc_content = """# RFC: Updated Feature

## Requirements
- [ ] New requirement added
- [ ] Original requirement
"""
            
            rfc_path = rfc_dir / "test-feature-2025-05-31.md"
            with open(rfc_path, 'w') as f:
                f.write(rfc_content)
            
            # Create plan with old RFC hash
            plan_dir = Path(tmpdir) / ".WHISPER" / "plans" / "in_progress" / "test-feature-plan-2025-05-31"
            plan_dir.mkdir(parents=True)
            
            plan_data = {
                "plan_type": "initial",
                "title": "Test Feature Implementation",
                "source_rfc": {
                    "rfc_id": "RFC-2025-05-31-0001",
                    "title": "Test Feature",
                    "filename": "test-feature-2025-05-31.md",
                    "version_hash": "old_hash_value"
                },
                "tasks": [],
                "validation_criteria": ["Basic validation"],
                "created": "2025-05-31 09:00:00",
                "updated": "2025-05-31 09:00:00"
            }
            
            with open(plan_dir / "plan.json", 'w') as f:
                json.dump(plan_data, f)
            
            # Create reference with old hash
            ref_data = {
                "rfc_id": "RFC-2025-05-31-0001",
                "rfc_path": ".WHISPER/rfc/in_progress/test-feature-2025-05-31.md",
                "rfc_content_hash": "old_hash_value",
                "last_sync": "2025-05-31 10:00:00"
            }
            
            with open(plan_dir / "rfc_reference.json", 'w') as f:
                json.dump(ref_data, f)
            
            yield tmpdir
    
    @pytest.fixture
    def update_tool(self, temp_workspace_with_modified_rfc):
        """Create tool instance."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_modified_rfc
            mock_pm.return_value = mock_instance
            
            tool = UpdatePlanFromRFCTool()
            yield tool
    
    def test_update_plan_from_changed_rfc(self, update_tool):
        """Test updating plan when RFC has changed."""
        with patch('ai_whisperer.tools.update_plan_from_rfc_tool.OpenRouterAIService') as mock_ai_class:
            mock_service = Mock()
            mock_response = {
                "tasks": [
                    {"name": "Write tests for new requirement", "agent_type": "test_generation", "description": "TDD for new req", "dependencies": []},
                    {"name": "Implement new requirement", "agent_type": "code_generation", "description": "Implement new req", "dependencies": ["Write tests for new requirement"]}
                ],
                "validation_criteria": ["New requirement works", "All tests pass"]
            }
            
            async def mock_stream():
                from ai_whisperer.ai_service.ai_service import AIStreamChunk
                yield AIStreamChunk(delta_content=json.dumps(mock_response))
            
            mock_service.stream_chat_completion = Mock(return_value=mock_stream())
            mock_ai_class.return_value = mock_service
            
            result = update_tool.execute({"plan_name": "test-feature-plan-2025-05-31"})
            
            assert "Plan updated successfully!" in result
            assert "RFC has changed since last sync" in result
    
    def test_update_plan_no_changes(self, update_tool, temp_workspace_with_modified_rfc):
        """Test updating plan when RFC hasn't changed."""
        # Update the hash to match current content
        plan_dir = Path(temp_workspace_with_modified_rfc) / ".WHISPER" / "plans" / "in_progress" / "test-feature-plan-2025-05-31"
        rfc_path = Path(temp_workspace_with_modified_rfc) / ".WHISPER" / "rfc" / "in_progress" / "test-feature-2025-05-31.md"
        
        with open(rfc_path, 'r') as f:
            content = f.read()
            current_hash = hashlib.sha256(content.encode()).hexdigest()
        
        ref_path = plan_dir / "rfc_reference.json"
        with open(ref_path, 'r') as f:
            ref_data = json.load(f)
        
        ref_data["rfc_content_hash"] = current_hash
        
        with open(ref_path, 'w') as f:
            json.dump(ref_data, f)
        
        result = update_tool.execute({"plan_name": "test-feature-plan-2025-05-31"})
        
        assert "Plan is already up to date" in result


class TestMovePlanTool:
    """Test MovePlanTool functionality."""
    
    @pytest.fixture
    def temp_workspace_with_plan_to_move(self):
        """Create workspace with a plan to move."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create plan in in_progress
            plan_dir = Path(tmpdir) / ".WHISPER" / "plans"
            in_progress_dir = plan_dir / "in_progress" / "test-plan-2025-05-31"
            in_progress_dir.mkdir(parents=True)
            (plan_dir / "archived").mkdir(parents=True)
            
            # Create plan files
            plan_data = {
                "plan_type": "initial",
                "title": "Test Plan",
                "status": "in_progress",
                "source_rfc": {"rfc_id": "RFC-2025-05-31-0001"}
            }
            
            with open(in_progress_dir / "plan.json", 'w') as f:
                json.dump(plan_data, f)
            
            # Create RFC with plan reference
            rfc_dir = Path(tmpdir) / ".WHISPER" / "rfc" / "in_progress"
            rfc_dir.mkdir(parents=True)
            
            rfc_metadata = {
                "rfc_id": "RFC-2025-05-31-0001",
                "derived_plans": [{
                    "plan_name": "test-plan-2025-05-31",
                    "status": "in_progress",
                    "location": ".WHISPER/plans/in_progress/test-plan-2025-05-31"
                }]
            }
            
            with open(rfc_dir / "test-rfc.json", 'w') as f:
                json.dump(rfc_metadata, f)
            
            yield tmpdir
    
    @pytest.fixture
    def move_tool(self, temp_workspace_with_plan_to_move):
        """Create tool instance."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_instance = Mock()
            mock_instance.workspace_path = temp_workspace_with_plan_to_move
            mock_pm.return_value = mock_instance
            
            tool = MovePlanTool()
            yield tool
    
    def test_move_plan_to_archived(self, move_tool, temp_workspace_with_plan_to_move):
        """Test moving plan to archived."""
        result = move_tool.execute({
            "plan_name": "test-plan-2025-05-31",
            "to_status": "archived"
        })
        
        assert "Plan moved successfully!" in result
        assert "**From**: in_progress" in result
        assert "**To**: archived" in result
        
        # Verify plan was moved
        workspace = Path(temp_workspace_with_plan_to_move)
        assert not (workspace / ".WHISPER" / "plans" / "in_progress" / "test-plan-2025-05-31").exists()
        assert (workspace / ".WHISPER" / "plans" / "archived" / "test-plan-2025-05-31").exists()
    
    def test_move_nonexistent_plan(self, move_tool):
        """Test moving non-existent plan."""
        result = move_tool.execute({
            "plan_name": "nonexistent-plan",
            "to_status": "archived"
        })
        
        assert "Error: Plan 'nonexistent-plan' not found" in result