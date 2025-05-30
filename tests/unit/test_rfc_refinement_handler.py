"""Unit tests for RFC Refinement Handler."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import re
from datetime import datetime

from ai_whisperer.agent_handlers.rfc_refinement import RFCRefinementHandler
from ai_whisperer.ai_service.ai_service import AIService


class TestRFCRefinementHandler:
    """Test RFC refinement handler functionality."""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service."""
        service = Mock(spec=AIService)
        service.process = AsyncMock()
        return service
    
    @pytest.fixture
    def handler(self, mock_ai_service):
        """Create handler instance."""
        return RFCRefinementHandler(mock_ai_service)
    
    def test_can_handle_rfc_keywords(self, handler):
        """Test that handler recognizes RFC-related messages."""
        # Should handle RFC references
        assert handler.can_handle("Let's work on RFC-2025-05-29-0001")
        
        # Should handle feature keywords
        assert handler.can_handle("I want to add a new feature")
        assert handler.can_handle("Create an RFC for caching")
        assert handler.can_handle("I have an idea for improvement")
        assert handler.can_handle("Let's implement user authentication")
        
        # Should handle context with active RFC
        assert handler.can_handle("Sure, let me explain", {'active_rfc_id': 'RFC-2025-05-29-0001'})
        
        # Should not handle unrelated messages
        assert not handler.can_handle("What's the weather today?")
        assert not handler.can_handle("Tell me a joke")
    
    @pytest.mark.asyncio
    async def test_handle_new_rfc_creation(self, handler, mock_ai_service):
        """Test creating a new RFC."""
        # Mock AI response with tool call
        mock_ai_service.process.return_value = {
            'content': """I'll help you create an RFC for the caching feature.

First, let me analyze the project structure:
analyze_languages()

Now I'll create the RFC:
create_rfc(title="Caching System", summary="Implement a distributed caching system")

I've created RFC-2025-05-29-0001. Let me ask some questions:
1. What type of data will you be caching?
2. Do you need distributed caching or local caching?
3. What are your performance requirements?"""
        }
        
        result = await handler.handle(
            "I want to create an RFC for a caching feature",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        # Verify response
        assert "RFC-2025-05-29-0001" in result['content']
        assert result['rfc_id'] == 'RFC-2025-05-29-0001'
        assert result['refinement_stage'] == 'gathering_requirements'
        
        # Verify tool calls were extracted
        assert len(result['tool_calls']) == 2
        assert result['tool_calls'][0]['tool'] == 'analyze_languages'
        assert result['tool_calls'][1]['tool'] == 'create_rfc'
        assert result['tool_calls'][1]['parameters']['title'] == 'Caching System'
        
        # Verify state was updated
        state = handler.conversation_state['test123']
        assert state['active_rfc_id'] == 'RFC-2025-05-29-0001'
        assert state['pending_question'] is not None
    
    @pytest.mark.asyncio
    async def test_handle_question_answer(self, handler, mock_ai_service):
        """Test processing user's answer to a question."""
        # Set up existing state
        handler.conversation_state['test123'] = {
            'active_rfc_id': 'RFC-2025-05-29-0001',
            'refinement_stage': 'gathering_requirements',
            'pending_question': 'What type of data will you be caching?',
            'questions_asked': [],
            'context_gathered': {}
        }
        
        # Mock AI response
        mock_ai_service.process.return_value = {
            'content': """Thank you for clarifying. I'll update the RFC with this information.

update_rfc(rfc_id="RFC-2025-05-29-0001", section="requirements", content="- Cache user session data\\n- Cache API responses", append=True)

I see you need to cache user sessions and API responses. Let me check for similar implementations:
find_similar_code(pattern="cache", file_pattern="*.py")

One more question: What's the expected cache size and TTL requirements?"""
        }
        
        result = await handler.handle(
            "We need to cache user session data and API responses",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        # Verify tool calls
        assert len(result['tool_calls']) == 2
        assert result['tool_calls'][0]['tool'] == 'update_rfc'
        assert result['tool_calls'][1]['tool'] == 'find_similar_code'
        
        # Verify state update
        state = handler.conversation_state['test123']
        assert "cache size and TTL" in state['pending_question']
    
    @pytest.mark.asyncio
    async def test_handle_rfc_refinement(self, handler, mock_ai_service):
        """Test refining an existing RFC."""
        # Mock AI response
        mock_ai_service.process.return_value = {
            'content': """Let me read the current state of this RFC.

read_rfc(rfc_id="RFC-2025-05-29-0001")

Based on our discussion, I'll update the technical considerations:
update_rfc(rfc_id="RFC-2025-05-29-0001", section="technical_considerations", content="- Use Redis for distributed caching\\n- Implement cache warming strategies")

The RFC is looking comprehensive. Would you like me to move it to 'in_progress' status?"""
        }
        
        result = await handler.handle(
            "Let's refine RFC-2025-05-29-0001 with the technical details we discussed",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        # Verify RFC was recognized
        assert result['rfc_id'] == 'RFC-2025-05-29-0001'
        
        # Verify tool calls
        assert len(result['tool_calls']) == 2
        assert result['tool_calls'][0]['tool'] == 'read_rfc'
        assert result['tool_calls'][1]['tool'] == 'update_rfc'
    
    @pytest.mark.asyncio
    async def test_handle_status_transition(self, handler, mock_ai_service):
        """Test moving RFC to different status."""
        # Set up state
        handler.conversation_state['test123'] = {
            'active_rfc_id': 'RFC-2025-05-29-0001',
            'refinement_stage': 'gathering_requirements',
            'questions_asked': [],
            'context_gathered': {}
        }
        
        # Mock AI response
        mock_ai_service.process.return_value = {
            'content': """Great! The RFC has sufficient detail now. Let me move it to active development.

move_rfc(rfc_id="RFC-2025-05-29-0001", target_status="in_progress", reason="Requirements gathered and technical approach defined")

RFC-2025-05-29-0001 is now in active refinement. You can continue to refine it or start implementation planning."""
        }
        
        result = await handler.handle(
            "Yes, please move it to in_progress",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        # Verify tool call
        assert len(result['tool_calls']) == 1
        assert result['tool_calls'][0]['tool'] == 'move_rfc'
        assert result['tool_calls'][0]['parameters']['target_status'] == 'in_progress'
        
        # Verify state update
        assert result['refinement_stage'] == 'active_refinement'
    
    @pytest.mark.asyncio
    async def test_handle_web_research(self, handler, mock_ai_service):
        """Test using web search for research."""
        # Mock AI response
        mock_ai_service.process.return_value = {
            'content': """Let me search for best practices on caching strategies.

web_search(query="distributed caching best practices Redis")

Based on the search results, I'll also fetch a specific article:
fetch_url(url="https://example.com/caching-guide")

The research shows several important patterns we should consider. Should we include cache invalidation strategies in the RFC?"""
        }
        
        result = await handler.handle(
            "Can you research best practices for distributed caching?",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        # Verify tool calls
        assert len(result['tool_calls']) == 2
        assert result['tool_calls'][0]['tool'] == 'web_search'
        assert result['tool_calls'][1]['tool'] == 'fetch_url'
    
    def test_extract_tool_calls(self, handler):
        """Test tool call extraction from AI response."""
        content = """Let me help with that.
        
First, I'll check the project structure:
get_project_structure(max_depth=2)

Then create an RFC:
create_rfc(title="New Feature", summary="Add authentication system")

I'll also search for similar code:
find_similar_code(pattern="auth", file_pattern="*.py")
"""
        
        tool_calls = handler._extract_tool_calls(content)
        
        assert len(tool_calls) == 3
        assert tool_calls[0]['tool'] == 'get_project_structure'
        assert tool_calls[0]['parameters']['max_depth'] == '2'
        assert tool_calls[1]['tool'] == 'create_rfc'
        assert tool_calls[1]['parameters']['title'] == 'New Feature'
        assert tool_calls[2]['tool'] == 'find_similar_code'
    
    def test_determine_action(self, handler):
        """Test action determination logic."""
        # Test with pending question
        state = {'pending_question': 'What is the cache size?'}
        assert handler._determine_action("About 1GB", state) == 'answer_question'
        
        # Test new RFC creation
        state = {'pending_question': None}
        assert handler._determine_action("Create RFC for logging", state) == 'create_new'
        assert handler._determine_action("I want to add user profiles", state) == 'create_new'
        
        # Test existing RFC refinement
        state = {'active_rfc_id': 'RFC-2025-05-29-0001', 'pending_question': None}
        assert handler._determine_action("Let's add more details", state) == 'refine_existing'
        
        # Test general query
        state = {'pending_question': None}
        assert handler._determine_action("Hello there", state) == 'general'
    
    def test_get_next_steps(self, handler):
        """Test next steps suggestions."""
        # Initial stage
        state = {'refinement_stage': 'initial'}
        steps = handler._get_next_steps(state)
        assert "Share your feature idea" in steps[0]
        
        # Gathering requirements
        state = {'refinement_stage': 'gathering_requirements'}
        steps = handler._get_next_steps(state)
        assert "Answer the questions" in steps[0]
        
        # Active refinement
        state = {'refinement_stage': 'active_refinement'}
        steps = handler._get_next_steps(state)
        assert "Review the RFC" in steps[0]
        
        # Completed
        state = {'refinement_stage': 'completed'}
        steps = handler._get_next_steps(state)
        assert "ready for implementation" in steps[0]
    
    def test_get_state_summary(self, handler):
        """Test state summary generation."""
        # No session
        summary = handler.get_state_summary('unknown')
        assert summary['status'] == 'no_active_session'
        
        # Active session
        handler.conversation_state['test123'] = {
            'active_rfc_id': 'RFC-2025-05-29-0001',
            'refinement_stage': 'gathering_requirements',
            'pending_question': 'What is the use case?',
            'questions_asked': ['q1', 'q2'],
            'context_gathered': {'user_type': 'enterprise', 'scale': 'large'}
        }
        
        summary = handler.get_state_summary('test123')
        assert summary['active_rfc_id'] == 'RFC-2025-05-29-0001'
        assert summary['refinement_stage'] == 'gathering_requirements'
        assert summary['pending_question'] == 'What is the use case?'
        assert summary['questions_asked'] == 2
        assert 'user_type' in summary['context_gathered']
    
    @pytest.mark.asyncio
    async def test_error_handling(self, handler, mock_ai_service):
        """Test error handling in handler."""
        # Mock AI service to raise error
        mock_ai_service.process.side_effect = Exception("AI service error")
        
        result = await handler.handle(
            "Create an RFC",
            {'session_id': 'test123', 'agent_id': 'p'}
        )
        
        assert result['error'] is True
        assert "encountered an error" in result['content']
        assert "AI service error" in result['content']