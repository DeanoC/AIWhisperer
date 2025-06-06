"""
Test suite for Documentation Generation Workflow.

Tests multi-agent collaboration for generating comprehensive documentation
including code analysis, doc writing, review, and publishing.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ai_whisperer.services.agents.async_session_manager_v2 import (
    AsyncAgentSessionManager, AgentState
)
from examples.async_agents.documentation_workflow import (
    DocumentationWorkflow, DocumentationResult
)


@pytest.fixture
def documentation_workflow(tmp_path):
    """Create documentation workflow instance."""
    workspace_path = tmp_path / "workspace"
    output_path = tmp_path / "output"
    workspace_path.mkdir(exist_ok=True)
    output_path.mkdir(exist_ok=True)
    
    return DocumentationWorkflow(
        workspace_path=workspace_path,
        output_path=output_path
    )


@pytest.fixture
def session_manager():
    """Create mock session manager."""
    manager = Mock(spec=AsyncAgentSessionManager)
    
    # Mock agent session creation
    async def create_agent_session(agent_id, auto_start=True):
        session = Mock()
        session.agent_id = agent_id
        session.state = AgentState.ACTIVE if auto_start else AgentState.IDLE
        return session
    
    manager.create_agent_session = AsyncMock(side_effect=create_agent_session)
    manager.sleep_agent = AsyncMock()
    manager.wake_agent = AsyncMock()
    manager.broadcast_event = AsyncMock()
    
    return manager


class TestDocumentationWorkflow:
    """Test documentation generation workflow functionality."""
    
    # === BASIC DOCUMENTATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_documentation_basic(self, documentation_workflow, session_manager):
        """Test basic documentation generation with Alice and Patricia."""
        target_config = {
            "target": {
                "type": "module",
                "path": "ai_whisperer/tools",
                "name": "Tool System"
            },
            "agents": ["a", "p"],  # Alice analyzes, Patricia writes
            "doc_type": "api"
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify basic results
        assert result["status"] == "completed"
        assert result["target_name"] == "Tool System"
        assert result["doc_type"] == "api"
        assert len(result["agent_contributions"]) == 2
        
        # Check agent contributions
        assert "a" in result["agent_contributions"]
        assert "p" in result["agent_contributions"]
        
        # Verify documentation sections
        assert "sections_generated" in result
        assert len(result["sections_generated"]) > 0
        assert "api_reference" in result["sections_generated"]
    
    @pytest.mark.asyncio
    async def test_documentation_comprehensive(self, documentation_workflow, session_manager):
        """Test comprehensive documentation with all agents."""
        target_config = {
            "target": {
                "type": "project",
                "path": ".",
                "name": "AIWhisperer"
            },
            "agents": ["a", "p", "d", "e", "t"],  # All agents contribute
            "doc_type": "comprehensive",
            "include_examples": True,
            "include_tests": True,
            "review_enabled": True
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify comprehensive documentation
        assert result["status"] == "completed"
        assert result["doc_type"] == "comprehensive"
        assert len(result["agent_contributions"]) == 5
        
        # Check all sections
        expected_sections = [
            "overview", "architecture", "api_reference",
            "examples", "testing_guide", "troubleshooting"
        ]
        for section in expected_sections:
            assert section in result["sections_generated"]
        
        # Verify review was performed
        assert result["review_performed"] is True
        assert "review_feedback" in result
        assert len(result["review_feedback"]) > 0
    
    # === SPECIALIZED DOCUMENTATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_documentation_tutorial_generation(self, documentation_workflow, session_manager):
        """Test tutorial documentation generation."""
        target_config = {
            "target": {
                "type": "feature",
                "path": "ai_whisperer/tools/send_mail_tool.py",
                "name": "Mail System"
            },
            "agents": ["a", "p", "e"],  # Alice, Patricia, Eamonn
            "doc_type": "tutorial",
            "tutorial_config": {
                "difficulty": "beginner",
                "include_exercises": True,
                "step_by_step": True
            }
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify tutorial generation
        assert result["status"] == "completed"
        assert result["doc_type"] == "tutorial"
        assert result["tutorial_metadata"]["difficulty"] == "beginner"
        
        # Check tutorial structure
        assert "tutorial_sections" in result
        tutorial = result["tutorial_sections"]
        assert "introduction" in tutorial
        assert "prerequisites" in tutorial
        assert "steps" in tutorial
        assert len(tutorial["steps"]) >= 3
        assert "exercises" in tutorial
        assert "summary" in tutorial
    
    @pytest.mark.asyncio
    async def test_documentation_migration_guide(self, documentation_workflow, session_manager):
        """Test migration guide generation between versions."""
        target_config = {
            "target": {
                "type": "migration",
                "from_version": "1.0",
                "to_version": "2.0",
                "name": "AIWhisperer Migration Guide"
            },
            "agents": ["a", "p", "d"],  # Need debugging expertise
            "doc_type": "migration",
            "analyze_breaking_changes": True,
            "generate_migration_scripts": True
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify migration guide
        assert result["status"] == "completed"
        assert result["doc_type"] == "migration"
        assert result["from_version"] == "1.0"
        assert result["to_version"] == "2.0"
        
        # Check migration content
        assert "breaking_changes" in result
        assert len(result["breaking_changes"]) > 0
        assert "migration_steps" in result
        assert "migration_scripts" in result
        assert result["scripts_generated"] is True
    
    # === COLLABORATIVE DOCUMENTATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_documentation_collaborative_review(self, documentation_workflow, session_manager):
        """Test collaborative documentation review process."""
        target_config = {
            "target": {
                "type": "module",
                "path": "ai_whisperer/services",
                "name": "Services Layer"
            },
            "agents": ["a", "p", "t"],  # Tessa reviews
            "doc_type": "technical",
            "review_enabled": True,
            "review_iterations": 2,
            "incorporate_feedback": True
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify review iterations
        assert result["status"] == "completed"
        assert result["review_iterations_completed"] == 2
        assert result["feedback_incorporated"] is True
        
        # Check review history
        assert "review_history" in result
        assert len(result["review_history"]) == 2
        for review in result["review_history"]:
            assert "reviewer" in review
            assert "feedback" in review
            assert "improvements" in review
            assert review["reviewer"] == "t"  # Tessa
    
    @pytest.mark.asyncio
    async def test_documentation_multi_format_output(self, documentation_workflow, session_manager):
        """Test generating documentation in multiple formats."""
        target_config = {
            "target": {
                "type": "module",
                "path": "ai_whisperer/tools",
                "name": "Tools"
            },
            "agents": ["a", "p", "e"],
            "doc_type": "api",
            "output_formats": ["markdown", "html", "pdf", "docstring"],
            "style_guide": "google"
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify multi-format output
        assert result["status"] == "completed"
        assert "output_files" in result
        assert len(result["output_files"]) == 4
        
        # Check each format
        formats_found = {fmt: False for fmt in ["markdown", "html", "pdf", "docstring"]}
        for file_info in result["output_files"]:
            assert "format" in file_info
            assert "path" in file_info
            assert "size" in file_info
            formats_found[file_info["format"]] = True
        
        assert all(formats_found.values())
        assert result["style_guide_applied"] == "google"
    
    # === ADVANCED FEATURES TESTS ===
    
    @pytest.mark.asyncio
    async def test_documentation_auto_update_detection(self, documentation_workflow, session_manager):
        """Test automatic detection of outdated documentation."""
        target_config = {
            "target": {
                "type": "module",
                "path": "ai_whisperer/core",
                "name": "Core Module"
            },
            "agents": ["a", "d"],  # Alice and Debbie analyze
            "doc_type": "api",
            "check_existing": True,
            "update_mode": "auto",
            "compare_with_code": True
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify update detection
        assert result["status"] == "completed"
        assert "outdated_sections" in result
        assert len(result["outdated_sections"]) > 0
        assert "update_recommendations" in result
        
        # Check specific updates
        for section in result["outdated_sections"]:
            assert "name" in section
            assert "reason" in section
            assert "last_updated" in section
            assert "changes_detected" in section
    
    @pytest.mark.asyncio
    async def test_documentation_batch_generation(self, documentation_workflow, session_manager):
        """Test batch documentation generation for multiple targets."""
        target_config = {
            "targets": [
                {"type": "module", "path": "ai_whisperer/tools", "name": "Tools"},
                {"type": "module", "path": "ai_whisperer/services", "name": "Services"},
                {"type": "module", "path": "ai_whisperer/core", "name": "Core"}
            ],
            "agents": ["a", "p"],
            "doc_type": "api",
            "parallel_generation": True,
            "consistent_style": True
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify batch results
        assert result["status"] == "completed"
        assert result["targets_processed"] == 3
        assert "documentation_results" in result
        assert len(result["documentation_results"]) == 3
        
        # Check consistency
        assert result["style_consistency_score"] > 0.8
        assert "cross_references_generated" in result
        assert result["cross_references_generated"] is True
    
    # === ERROR HANDLING TESTS ===
    
    @pytest.mark.asyncio
    async def test_documentation_error_recovery(self, documentation_workflow, session_manager):
        """Test documentation generation with errors and recovery."""
        target_config = {
            "target": {
                "type": "module",
                "path": "non_existent_module",
                "name": "Missing Module"
            },
            "agents": ["a", "p"],
            "doc_type": "api",
            "fallback_to_partial": True,
            "simulate_failures": {
                "a": "timeout"  # Alice fails
            }
        }
        
        # Run workflow
        result = await documentation_workflow.run(
            config=target_config,
            session_manager=session_manager
        )
        
        # Verify partial completion
        assert result["status"] == "completed_with_limitations"
        assert len(result["errors"]) > 0
        assert result["partial_documentation"] is True
        
        # Check fallback behavior
        assert "p" in result["agent_contributions"]  # Patricia still contributed
        assert result["confidence_level"] == "low"
        assert "missing_analysis" in result["limitations"]