"""
Integration tests for RFC-to-Plan bidirectional updates.
Tests the synchronization between RFCs and their derived plans.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
from unittest.mock import Mock, patch

from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
from ai_whisperer.tools.update_rfc_tool import UpdateRFCTool
from ai_whisperer.tools.prepare_plan_from_rfc_tool import PreparePlanFromRFCTool
from ai_whisperer.tools.save_generated_plan_tool import SaveGeneratedPlanTool
from ai_whisperer.tools.update_plan_from_rfc_tool import UpdatePlanFromRFCTool
from ai_whisperer.tools.read_plan_tool import ReadPlanTool
from ai_whisperer.tools.move_plan_tool import MovePlanTool
from ai_whisperer.tools.delete_plan_tool import DeletePlanTool
from ai_whisperer.utils.path import PathManager


class TestRFCPlanBidirectional:
    """Test bidirectional updates between RFCs and Plans."""
    
    def _extract_rfc_id(self, result):
        """Extract RFC ID from create result."""
        rfc_id = result.get('rfc_id')
        assert rfc_id, f"Could not extract RFC ID from result: {result}"
        return rfc_id
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize PathManager with temp directory
            PathManager().initialize(config_values={
                'workspace_path': temp_dir,
                'output_path': temp_dir
            })
            
            # Create .WHISPER structure
            whisper_dir = Path(temp_dir) / ".WHISPER"
            (whisper_dir / "rfc" / "in_progress").mkdir(parents=True)
            (whisper_dir / "rfc" / "archived").mkdir(parents=True)
            (whisper_dir / "plans" / "in_progress").mkdir(parents=True)
            (whisper_dir / "plans" / "archived").mkdir(parents=True)
            
            yield temp_dir
    
    def test_rfc_to_plan_creation_and_linkage(self, temp_workspace):
        """Test creating a plan from an RFC maintains proper linkage."""
        # Create an RFC
        create_tool = CreateRFCTool()
        result = create_tool.execute({
            "title": "Add Authentication System",
            "short_name": "auth-system",
            "summary": "Implement user authentication with JWT"
        })
        assert result.get('rfc_id') is not None
        
        # Extract the RFC ID from the result
        rfc_id = self._extract_rfc_id(result)
        
        # Simulate plan creation (prepare + save)
        prepare_tool = PreparePlanFromRFCTool()
        prepare_result = prepare_tool.execute({
            "rfc_id": rfc_id,
            "plan_type": "initial"
        })
        assert prepare_result.get('prepared') is True
        
        # Extract RFC metadata from prepare result
        rfc_hash = prepare_result.get('rfc_hash')
        
        # Create a sample plan
        sample_plan = {
            "plan_type": "initial",
            "title": "Implement Authentication System",
            "description": "Plan for adding JWT authentication",
            "agent_type": "planning",
            "tdd_phases": {
                "red": ["Write auth tests"],
                "green": ["Implement auth logic"],
                "refactor": ["Clean up auth code"]
            },
            "tasks": [{
                "name": "Write auth tests",
                "description": "Create test suite for authentication",
                "agent_type": "test_generation",
                "dependencies": [],
                "tdd_phase": "red"
            }],
            "validation_criteria": ["All tests pass"]
        }
        
        # Save the plan (use the actual RFC ID, not the short name)
        save_tool = SaveGeneratedPlanTool()
        save_result = save_tool.execute({
            "plan_name": "auth-system-plan-2024-01-01",
            "plan_content": sample_plan,
            "rfc_id": rfc_id,  # Use the actual RFC ID
            "rfc_hash": rfc_hash
        })
        assert save_result.get('saved') is True
        
        # Verify RFC metadata was updated
        path_manager = PathManager.get_instance()
        rfc_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc" / "in_progress"
        # CreateRFCTool creates files with date suffix - use glob to find it
        import glob
        metadata_files = glob.glob(str(rfc_path / "auth-system-*.json"))
        assert len(metadata_files) == 1, f"Expected 1 metadata file, found {len(metadata_files)}"
        rfc_metadata_path = metadata_files[0]
        
        with open(rfc_metadata_path) as f:
            rfc_metadata = json.load(f)
        
        assert "derived_plans" in rfc_metadata
        assert len(rfc_metadata["derived_plans"]) == 1
        assert rfc_metadata["derived_plans"][0]["plan_name"] == "auth-system-plan-2024-01-01"
    
    def test_rfc_update_triggers_plan_sync(self, temp_workspace):
        """Test that RFC updates can trigger plan updates."""
        # Create RFC and plan first
        create_tool = CreateRFCTool()
        rfc_result = create_tool.execute({
            "title": "Add Caching Layer",
            "short_name": "caching",
            "summary": "Implement Redis caching"
        })
        
        # Extract RFC ID from the result
        rfc_id = rfc_result.get('rfc_id')
        assert rfc_id, f"Could not extract RFC ID from result: {rfc_result}"
        
        # Prepare and save a plan
        prepare_tool = PreparePlanFromRFCTool()
        prepare_result = prepare_tool.execute({
            "rfc_id": rfc_id,
            "plan_type": "initial"
        })
        
        rfc_hash = prepare_result.get('rfc_hash')
        
        save_tool = SaveGeneratedPlanTool()
        save_tool.execute({
            "plan_name": "caching-plan-2024-01-01",
            "plan_content": {
                "plan_type": "initial",
                "title": "Implement Caching Layer",
                "description": "Plan for Redis caching",
                "agent_type": "planning",
                "tdd_phases": {"red": [], "green": [], "refactor": []},
                "tasks": [],
                "validation_criteria": []
            },
            "rfc_id": rfc_id,
            "rfc_hash": rfc_hash
        })
        
        # Update the RFC
        update_tool = UpdateRFCTool()
        update_result = update_tool.execute({
            "rfc_id": rfc_id,
            "section": "requirements",
            "content": "- Use Redis for caching\n- Support TTL configuration\n- Add cache invalidation"
        })
        assert update_result.get('updated') is True
        
        # Check if plan needs update - mock the AI service
        with patch('ai_whisperer.tools.update_plan_from_rfc_tool.OpenRouterAIService') as mock_service:
            mock_ai = Mock()
            mock_service.return_value = mock_ai
            
            # Mock streaming response with updated plan
            async def mock_stream(*args, **kwargs):
                mock_chunk = Mock()
                # Return an updated plan with new tasks based on the RFC changes
                updated_plan = {
                    "plan_type": "initial",
                    "title": "Implement Caching Layer - Updated",
                    "description": "Plan for Redis caching with TTL and invalidation",
                    "agent_type": "planning",
                    "tasks": [
                        {
                            "name": "Configure Redis with TTL",
                            "description": "Set up Redis with configurable TTL",
                            "agent_type": "code_generation",
                            "tdd_phase": "green"
                        }
                    ],
                    "validation_criteria": ["Redis caching works", "TTL is configurable"]
                }
                mock_chunk.delta_content = json.dumps(updated_plan)
                yield mock_chunk
            
            mock_ai.stream_chat_completion = mock_stream
            
            update_plan_tool = UpdatePlanFromRFCTool()
            sync_result = update_plan_tool.execute({
                "plan_name": "caching-plan-2024-01-01"
            })
            
            # Should detect RFC changes
            assert sync_result.get('updated') is not None or sync_result.get('up_to_date') is True
    
    def test_plan_archival_workflow(self, temp_workspace):
        """Test moving plans between in_progress and archived."""
        # Create RFC and plan
        create_tool = CreateRFCTool()
        rfc_result = create_tool.execute({
            "title": "Add Logging System",
            "short_name": "logging",
            "summary": "Centralized logging"
        })
        
        # Extract RFC ID from the result
        rfc_id = self._extract_rfc_id(rfc_result)
        
        prepare_tool = PreparePlanFromRFCTool()
        prepare_result = prepare_tool.execute({
            "rfc_id": rfc_id,
            "plan_type": "initial"
        })
        
        rfc_hash = prepare_result.get('rfc_hash')
        
        save_tool = SaveGeneratedPlanTool()
        save_tool.execute({
            "plan_name": "logging-plan-2024-01-01",
            "plan_content": {
                "plan_type": "initial",
                "title": "Implement Logging",
                "description": "Logging system plan",
                "agent_type": "planning",
                "tdd_phases": {"red": [], "green": [], "refactor": []},
                "tasks": [],
                "validation_criteria": []
            },
            "rfc_id": rfc_id,
            "rfc_hash": rfc_hash
        })
        
        # Archive the plan
        move_tool = MovePlanTool()
        archive_result = move_tool.execute({
            "plan_name": "logging-plan-2024-01-01",
            "to_status": "archived"
        })
        assert archive_result.get('moved') is True
        
        # Verify plan is in archived folder
        path_manager = PathManager.get_instance()
        archived_path = Path(path_manager.workspace_path) / ".WHISPER" / "plans" / "archived" / "logging-plan-2024-01-01"
        assert archived_path.exists()
        
        # Verify RFC metadata was updated
        rfc_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc" / "in_progress"
        # Use glob to find the metadata file since date is dynamic
        import glob
        metadata_files = glob.glob(str(rfc_path / "logging-*.json"))
        assert len(metadata_files) == 1, f"Expected 1 metadata file, found {len(metadata_files)}"
        rfc_metadata_path = metadata_files[0]
        
        with open(rfc_metadata_path) as f:
            rfc_metadata = json.load(f)
        
        # Check that plan reference shows archived status
        assert rfc_metadata["derived_plans"][0]["status"] == "archived"
    
    def test_plan_deletion_updates_rfc(self, temp_workspace):
        """Test that deleting a plan removes its reference from the RFC."""
        # Create RFC and plan
        create_tool = CreateRFCTool()
        rfc_result = create_tool.execute({
            "title": "Add Metrics Collection",
            "short_name": "metrics",
            "summary": "Application metrics"
        })
        
        # Extract RFC ID from the result
        rfc_id = self._extract_rfc_id(rfc_result)
        
        prepare_tool = PreparePlanFromRFCTool()
        prepare_result = prepare_tool.execute({
            "rfc_id": rfc_id,
            "plan_type": "initial"
        })
        
        rfc_hash = prepare_result.get('rfc_hash')
        
        save_tool = SaveGeneratedPlanTool()
        save_tool.execute({
            "plan_name": "metrics-plan-2024-01-01",
            "plan_content": {
                "plan_type": "initial",
                "title": "Implement Metrics",
                "description": "Metrics collection plan",
                "agent_type": "planning",
                "tdd_phases": {"red": [], "green": [], "refactor": []},
                "tasks": [],
                "validation_criteria": []
            },
            "rfc_id": rfc_id,
            "rfc_hash": rfc_hash
        })
        
        # Delete the plan
        delete_tool = DeletePlanTool()
        delete_result = delete_tool.execute({
            "plan_name": "metrics-plan-2024-01-01",
            "confirm_delete": True,
            "reason": "Test deletion"
        })
        assert delete_result.get('deleted') is True
        
        # Verify RFC metadata was updated
        path_manager = PathManager.get_instance()
        rfc_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc" / "in_progress"
        # Use glob to find the metadata file since date is dynamic
        import glob
        metadata_files = glob.glob(str(rfc_path / "metrics-*.json"))
        assert len(metadata_files) == 1, f"Expected 1 metadata file, found {len(metadata_files)}"
        rfc_metadata_path = metadata_files[0]
        
        with open(rfc_metadata_path) as f:
            rfc_metadata = json.load(f)
        
        # Plan reference should be removed
        assert len(rfc_metadata.get("derived_plans", [])) == 0
    
    def test_error_handling_missing_rfc(self, temp_workspace):
        """Test error handling when RFC doesn't exist."""
        prepare_tool = PreparePlanFromRFCTool()
        result = prepare_tool.execute({
            "rfc_id": "non-existent-rfc",
            "plan_type": "initial"
        })
        assert "error" in result
        assert "not found" in result.get('error', '')
    
    def test_error_handling_invalid_plan_content(self, temp_workspace):
        """Test error handling for invalid plan content."""
        # Create an RFC first
        create_tool = CreateRFCTool()
        rfc_result = create_tool.execute({
            "title": "Test RFC",
            "short_name": "test",
            "summary": "Test"
        })
        
        # Extract RFC ID from the result
        rfc_id = self._extract_rfc_id(rfc_result)
        
        save_tool = SaveGeneratedPlanTool()
        result = save_tool.execute({
            "plan_name": "test-plan",
            "plan_content": {"invalid": "structure"},  # Missing required fields
            "rfc_id": rfc_id
        })
        assert "error" in result or "validation" in result.get('error', '').lower()
    
    def test_multiple_plans_from_single_rfc(self, temp_workspace):
        """Test creating multiple plans from a single RFC."""
        # Create RFC
        create_tool = CreateRFCTool()
        rfc_result = create_tool.execute({
            "title": "Complex Feature",
            "short_name": "complex",
            "summary": "Multi-phase implementation"
        })
        
        # Extract RFC ID from the result
        rfc_id = self._extract_rfc_id(rfc_result)
        
        prepare_tool = PreparePlanFromRFCTool()
        save_tool = SaveGeneratedPlanTool()
        
        # Create first plan (initial)
        prepare_result = prepare_tool.execute({
            "rfc_id": rfc_id,
            "plan_type": "initial"
        })
        rfc_hash = prepare_result.get('rfc_hash')
        
        save_tool.execute({
            "plan_name": "complex-plan-phase1",
            "plan_content": {
                "plan_type": "initial",
                "title": "Phase 1",
                "description": "First phase",
                "agent_type": "planning",
                "tdd_phases": {"red": [], "green": [], "refactor": []},
                "tasks": [],
                "validation_criteria": []
            },
            "rfc_id": rfc_id,
            "rfc_hash": rfc_hash
        })
        
        # Create second plan (overview)
        save_tool.execute({
            "plan_name": "complex-plan-phase2",
            "plan_content": {
                "plan_type": "overview",
                "title": "Phase 2",
                "description": "Second phase",
                "agent_type": "planning",
                "tdd_phases": {"red": [], "green": [], "refactor": []},
                "tasks": [],
                "validation_criteria": []
            },
            "rfc_id": rfc_id,
            "rfc_hash": rfc_hash
        })
        
        # Verify RFC has both plans
        path_manager = PathManager.get_instance()
        rfc_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc" / "in_progress"
        # Use glob to find the metadata file since date is dynamic
        import glob
        metadata_files = glob.glob(str(rfc_path / "complex-*.json"))
        assert len(metadata_files) == 1, f"Expected 1 metadata file, found {len(metadata_files)}"
        rfc_metadata_path = metadata_files[0]
        
        with open(rfc_metadata_path) as f:
            rfc_metadata = json.load(f)
        
        assert len(rfc_metadata["derived_plans"]) == 2
        plan_names = [p["plan_name"] for p in rfc_metadata["derived_plans"]]
        assert "complex-plan-phase1" in plan_names
        assert "complex-plan-phase2" in plan_names