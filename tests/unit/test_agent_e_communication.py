"""
Tests for Agent E communication with Agent P.
Testing the bidirectional communication system for clarification and hierarchical planning.
"""
import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# These imports will fail until implementation
from ai_whisperer.agents.agent_e_handler import AgentEHandler
from ai_whisperer.agents.agent_communication import (
    AgentMessage,
    MessageType,
    ClarificationRequest,
    ClarificationResponse,
    PlanRefinementRequest,
    PlanRefinementResponse
)



pytestmark = pytest.mark.xfail(reason="Agent E feature in development")
# Mark all tests as xfail - Agent E feature in development

class TestAgentCommunication:
    """Test Agent E's communication capabilities with Agent P."""
    
    @pytest.fixture
    def mock_agent_registry(self):
        """Mock agent registry with Agent P."""
        registry = Mock()
        agent_p = Mock()
        agent_p.agent_id = "P"
        agent_p.name = "Patricia the Planner"
        registry.get_agent.return_value = agent_p
        return registry
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager for agent switching."""
        session_manager = Mock()
        session_manager.switch_agent = AsyncMock()
        session_manager.send_message = AsyncMock()
        return session_manager
    
    @pytest.fixture
    def agent_e_handler(self, mock_agent_registry, mock_session_manager):
        """Create Agent E handler with mocked dependencies."""
        handler = AgentEHandler(
            agent_registry=mock_agent_registry,
            session_manager=mock_session_manager
        )
        return handler
    
    @pytest.mark.asyncio
    async def test_send_clarification_request(self, agent_e_handler):
        """Test sending a clarification request to Agent P."""
        unclear_task = {
            "name": "Implement authentication",
            "description": "Add authentication to the system",
            "validation_criteria": ["Authentication works"]  # Too vague
        }
        
        clarification = await agent_e_handler.request_clarification(
            task=unclear_task,
            questions=[
                "What type of authentication is required? (JWT, OAuth, Basic Auth)",
                "Should we support multiple authentication methods?",
                "Are there specific security requirements?"
            ]
        )
        
        assert isinstance(clarification, ClarificationRequest)
        assert clarification.task_name == "Implement authentication"
        assert len(clarification.questions) == 3
        assert clarification.context["original_description"] == unclear_task["description"]
    
    @pytest.mark.asyncio
    async def test_receive_clarification_response(self, agent_e_handler):
        """Test receiving and processing clarification response from Agent P."""
        response_data = {
            "message_type": "clarification_response",
            "task_name": "Implement authentication",
            "clarifications": {
                "authentication_type": "JWT with refresh tokens",
                "multiple_methods": False,
                "security_requirements": [
                    "Tokens expire after 15 minutes",
                    "Refresh tokens valid for 7 days",
                    "Rate limiting on auth endpoints"
                ]
            },
            "updated_description": "Implement JWT authentication with refresh tokens, 15-min access token expiry, 7-day refresh token validity, and rate limiting on auth endpoints"
        }
        
        response = ClarificationResponse.from_dict(response_data)
        updated_task = agent_e_handler.apply_clarifications(
            original_task={"name": "Implement authentication", "description": "Add authentication"},
            response=response
        )
        
        assert updated_task["description"] == response.updated_description
        assert "constraints" in updated_task
        assert "JWT" in updated_task["constraints"][0]
    
    @pytest.mark.asyncio
    async def test_request_hierarchical_planning(self, agent_e_handler):
        """Test requesting Agent P to create sub-plans for complex tasks."""
        complex_task = {
            "name": "Migrate monolith to microservices",
            "description": "Break down monolithic application into microservices",
            "estimated_complexity": "very_complex"
        }
        
        refinement_request = await agent_e_handler.request_plan_refinement(
            task=complex_task,
            reason="Task too complex for single execution",
            suggested_subtasks=[
                "Identify service boundaries",
                "Create service extraction plan",
                "Implement service communication",
                "Migrate data layer",
                "Deploy and cutover"
            ]
        )
        
        assert isinstance(refinement_request, PlanRefinementRequest)
        assert refinement_request.task_name == complex_task["name"]
        assert len(refinement_request.suggested_subtasks) == 5
        assert refinement_request.refinement_type == "decompose_complex"
    
    @pytest.mark.asyncio
    async def test_agent_p_creates_sub_rfc(self, agent_e_handler, mock_session_manager):
        """Test Agent P creating a sub-RFC for complex task."""
        # Simulate Agent P's response with new RFC
        refinement_response = {
            "message_type": "plan_refinement_response",
            "original_task_name": "Migrate monolith to microservices",
            "action_taken": "created_sub_rfc",
            "sub_rfc_id": "RFC-2024-01-01-0001",
            "sub_plan_id": "migration-plan-2024-01-01",
            "new_tasks": [
                {
                    "name": "Execute service extraction plan",
                    "description": "Follow the detailed migration RFC",
                    "sub_plan_reference": "migration-plan-2024-01-01"
                }
            ]
        }
        
        response = PlanRefinementResponse.from_dict(refinement_response)
        hierarchy_update = agent_e_handler.process_refinement_response(response)
        
        assert hierarchy_update["created_sub_rfc"] is True
        assert hierarchy_update["sub_rfc_id"] == "RFC-2024-01-01-0001"
        assert len(hierarchy_update["replacement_tasks"]) == 1
        assert "sub_plan_reference" in hierarchy_update["replacement_tasks"][0]
    
    @pytest.mark.asyncio
    async def test_bidirectional_context_sharing(self, agent_e_handler):
        """Test sharing context between Agent E and Agent P."""
        execution_context = {
            "session_id": "test-session",
            "plan_id": "test-plan",
            "completed_tasks": ["Setup environment", "Write initial tests"],
            "discovered_requirements": [
                "Need Redis for session storage",
                "Database needs specific indexes"
            ],
            "technical_constraints": [
                "Python 3.8 compatibility required",
                "Must work with existing API"
            ]
        }
        
        message = agent_e_handler.create_context_message(
            to_agent="P",
            context_type="execution_update",
            context_data=execution_context
        )
        
        assert message.from_agent == "E"
        assert message.to_agent == "P"
        assert message.message_type == MessageType.STATUS_UPDATE
        assert message.context["session_id"] == "test-session"
        assert len(message.payload["discovered_requirements"]) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_in_communication(self, agent_e_handler, mock_session_manager):
        """Test error handling when Agent P is unavailable or errors occur."""
        # Simulate communication failure
        mock_session_manager.send_message.side_effect = Exception("Agent P unavailable")
        
        with pytest.raises(Exception) as exc_info:
            await agent_e_handler.request_clarification(
                task={"name": "Test task"},
                questions=["Test question?"]
            )
        
        assert "unavailable" in str(exc_info.value)
        
        # Verify retry logic was attempted
        assert mock_session_manager.send_message.call_count >= 1
    
    @pytest.mark.asyncio 
    async def test_message_correlation(self, agent_e_handler):
        """Test that responses are correctly correlated with requests."""
        # Send multiple requests
        request1 = await agent_e_handler.request_clarification(
            task={"name": "Task 1"},
            questions=["Question 1?"]
        )
        
        request2 = await agent_e_handler.request_clarification(
            task={"name": "Task 2"},
            questions=["Question 2?"]
        )
        
        # Verify each has unique message ID
        assert request1.message_id != request2.message_id
        
        # Simulate responses
        response1 = Mock(parent_message_id=request1.message_id)
        response2 = Mock(parent_message_id=request2.message_id)
        
        # Verify correct correlation
        assert agent_e_handler.correlate_response(response1) == request1
        assert agent_e_handler.correlate_response(response2) == request2


class TestAgentMessage:
    """Test the AgentMessage data structure."""
    
    def test_message_creation(self):
        """Test creating agent messages."""
        msg = AgentMessage(
            from_agent="E",
            to_agent="P",
            message_type=MessageType.CLARIFICATION_REQUEST,
            payload={"questions": ["What framework?"]},
            context={"session_id": "test"}
        )
        
        assert msg.message_id  # Auto-generated
        assert msg.timestamp  # Auto-generated
        assert msg.from_agent == "E"
        assert msg.to_agent == "P"
    
    def test_message_serialization(self):
        """Test message serialization for transmission."""
        msg = AgentMessage(
            from_agent="E",
            to_agent="P", 
            message_type=MessageType.CLARIFICATION_REQUEST,
            payload={"questions": ["Test?"]},
            context={"session_id": "test"}
        )
        
        serialized = msg.to_json()
        assert isinstance(serialized, str)
        
        # Can deserialize
        deserialized = AgentMessage.from_json(serialized)
        assert deserialized.message_id == msg.message_id
        assert deserialized.from_agent == msg.from_agent


class TestCollaborativeRefinement:
    """Test collaborative refinement between Agent E and Agent P."""
    
    @pytest.fixture
    def collaborative_session(self, agent_e_handler):
        """Create a collaborative session."""
        return agent_e_handler.start_collaborative_session(
            plan_id="test-plan",
            rfc_id="RFC-2024-01-01-0001"
        )
    
    @pytest.mark.asyncio
    async def test_iterative_refinement(self, collaborative_session):
        """Test iterative refinement process."""
        initial_task = {
            "name": "Build API gateway",
            "description": "Create API gateway for microservices",
            "validation_criteria": ["Gateway routes requests correctly"]
        }
        
        # First refinement - needs more detail
        refinement1 = await collaborative_session.refine_task(initial_task)
        assert "authentication" in refinement1.questions  # Should ask about auth
        
        # Apply clarifications
        refined_task = collaborative_session.apply_refinement(
            initial_task,
            clarifications={"auth_required": True, "auth_type": "OAuth2"}
        )
        
        # Second refinement - might need sub-tasks
        refinement2 = await collaborative_session.refine_task(refined_task)
        assert refinement2.suggests_decomposition  # Complex enough to decompose
    
    @pytest.mark.asyncio
    async def test_automatic_rfc_update_trigger(self, collaborative_session):
        """Test automatic RFC update when significant changes discovered."""
        discoveries = [
            "Existing API uses GraphQL not REST",
            "Performance requirements changed from 100ms to 50ms",
            "New compliance requirements for data encryption"
        ]
        
        for discovery in discoveries:
            collaborative_session.report_discovery(discovery)
        
        # Should trigger RFC update request
        update_triggered = collaborative_session.should_update_rfc()
        assert update_triggered is True
        
        update_request = await collaborative_session.request_rfc_update()
        assert update_request.message_type == MessageType.PLAN_REFINEMENT_REQUEST
        assert len(update_request.payload["discoveries"]) == 3