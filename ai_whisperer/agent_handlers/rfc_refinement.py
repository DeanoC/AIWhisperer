"""
RFC Refinement Handler for Agent Patricia
"""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json

from ai_whisperer.ai_service.ai_service import AIService

logger = logging.getLogger(__name__)


class RFCRefinementHandler:
    """Handler for RFC refinement conversations with Agent Patricia."""
    
    def __init__(self, ai_service: AIService):
        """Initialize RFC refinement handler.
        
        Args:
            ai_service: AI service for processing
        """
        self.ai_service = ai_service
        self.conversation_state: Dict[str, Any] = {}
        self.active_rfcs: Dict[str, Dict[str, Any]] = {}  # Track RFCs being refined
    
    def can_handle(self, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if this handler can process the message.
        
        RFC handler can handle:
        - Messages about creating RFCs
        - Messages about features/ideas
        - Messages referencing existing RFCs
        """
        message_lower = message.lower()
        
        # RFC-specific keywords
        rfc_keywords = [
            'rfc', 'feature', 'idea', 'requirement', 'implement', 
            'add', 'create', 'build', 'develop', 'enhancement',
            'improvement', 'change', 'modify', 'update'
        ]
        
        # Check for RFC references
        if re.search(r'RFC-\d{4}-\d{2}-\d{2}-\d{4}', message):
            return True
        
        # Check for feature/idea keywords
        for keyword in rfc_keywords:
            if keyword in message_lower:
                return True
        
        # Check if we're in an active RFC refinement
        if context and context.get('active_rfc_id'):
            return True
        
        return False
    
    async def handle(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle RFC refinement conversation.
        
        Args:
            message: User message
            context: Conversation context
            
        Returns:
            Response with refined requirements
        """
        try:
            # Extract or create session context
            session_id = context.get('session_id', 'default')
            agent_id = context.get('agent_id', 'p')
            
            # Initialize session state if needed
            if session_id not in self.conversation_state:
                self.conversation_state[session_id] = {
                    'active_rfc_id': None,
                    'refinement_stage': 'initial',
                    'questions_asked': [],
                    'context_gathered': {}
                }
            
            state = self.conversation_state[session_id]
            
            # Check for RFC reference in message
            rfc_match = re.search(r'RFC-\d{4}-\d{2}-\d{2}-\d{4}', message)
            if rfc_match:
                state['active_rfc_id'] = rfc_match.group()
            
            # Determine refinement action
            action = self._determine_action(message, state)
            
            # Build prompt based on action
            if action == 'create_new':
                prompt = self._build_new_rfc_prompt(message, state)
            elif action == 'refine_existing':
                prompt = self._build_refinement_prompt(message, state)
            elif action == 'answer_question':
                prompt = self._build_answer_processing_prompt(message, state)
            else:
                prompt = self._build_general_prompt(message, state)
            
            # Get AI response
            response = await self.ai_service.process(prompt, context)
            
            # Extract any tool calls from response
            tool_calls = self._extract_tool_calls(response.get('content', ''))
            
            # Update state based on response
            self._update_state(state, response, tool_calls)
            
            # Format response
            result = {
                'content': response.get('content', ''),
                'rfc_id': state.get('active_rfc_id'),
                'refinement_stage': state.get('refinement_stage'),
                'tool_calls': tool_calls,
                'next_steps': self._get_next_steps(state)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RFC refinement handler: {e}")
            return {
                'content': f"I encountered an error while processing your request: {str(e)}",
                'error': True
            }
    
    def _determine_action(self, message: str, state: Dict[str, Any]) -> str:
        """Determine what action to take based on message and state."""
        message_lower = message.lower()
        
        # Check if answering a question
        if state.get('pending_question'):
            return 'answer_question'
        
        # Check for new RFC creation
        if any(phrase in message_lower for phrase in ['create rfc', 'new rfc', 'start rfc']):
            return 'create_new'
        
        # Check if we have an active RFC
        if state.get('active_rfc_id'):
            return 'refine_existing'
        
        # Check if this is a new feature idea
        feature_indicators = ['i want to', 'we need', 'can you add', 'feature request', 
                            'it would be nice', 'implement', 'build']
        if any(phrase in message_lower for phrase in feature_indicators):
            return 'create_new'
        
        return 'general'
    
    def _build_new_rfc_prompt(self, message: str, state: Dict[str, Any]) -> str:
        """Build prompt for creating a new RFC."""
        return f"""You are helping create a new RFC from the user's idea.

User's idea: {message}

Your task:
1. First, use the analyze_languages tool to understand the project context
2. Create a new RFC using the create_rfc tool with a clear title and initial summary
3. Ask 2-3 clarifying questions to better understand the requirements
4. Be specific and focused in your questions

Remember:
- Keep the initial RFC simple - we'll refine it through conversation
- Focus on understanding the core problem/need first
- Technical details can come later"""
    
    def _build_refinement_prompt(self, message: str, state: Dict[str, Any]) -> str:
        """Build prompt for refining an existing RFC."""
        rfc_id = state.get('active_rfc_id')
        stage = state.get('refinement_stage', 'initial')
        
        return f"""You are refining RFC {rfc_id}. Current stage: {stage}

User's input: {message}

Your task:
1. First, use read_rfc to review the current RFC state
2. Based on the user's input, determine what section needs updating
3. Use update_rfc to add or modify the relevant section
4. Ask 1-2 follow-up questions to gather more details
5. If you think the RFC is ready, suggest moving it to 'in_progress' status

Focus on:
- Understanding requirements clearly
- Identifying technical considerations
- Defining acceptance criteria
- Uncovering edge cases"""
    
    def _build_answer_processing_prompt(self, message: str, state: Dict[str, Any]) -> str:
        """Build prompt for processing user's answer to a question."""
        pending_question = state.get('pending_question', '')
        rfc_id = state.get('active_rfc_id')
        
        return f"""The user is answering your question about RFC {rfc_id}.

Your question was: {pending_question}
User's answer: {message}

Your task:
1. Process the answer and update the appropriate RFC section
2. Use find_similar_code to check if similar functionality exists
3. If needed, use web_search to find best practices
4. Ask a follow-up question if more clarity is needed
5. Otherwise, move to the next aspect of refinement

Keep the refinement moving forward productively."""
    
    def _build_general_prompt(self, message: str, state: Dict[str, Any]) -> str:
        """Build prompt for general RFC-related queries."""
        return f"""The user has a request related to RFC or feature development.

User's message: {message}

Your task:
1. Determine if this is a new feature idea that needs an RFC
2. Check if they're asking about existing RFCs (use list_rfcs)
3. Guide them on the RFC process if needed
4. Help them articulate their requirements clearly

Be helpful and guide them toward creating or refining an RFC if appropriate."""
    
    def _extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool calls from AI response."""
        tool_calls = []
        
        # Pattern to match tool calls in the response
        # Looking for patterns like: tool_name(param1=value1, param2=value2)
        tool_pattern = r'(\w+)\((.*?)\)'
        
        # Find all potential tool calls
        for match in re.finditer(tool_pattern, content):
            tool_name = match.group(1)
            params_str = match.group(2)
            
            # Check if this is a known RFC tool
            rfc_tools = ['create_rfc', 'read_rfc', 'update_rfc', 'move_rfc', 'list_rfcs',
                        'analyze_languages', 'find_similar_code', 'get_project_structure',
                        'web_search', 'fetch_url']
            
            if tool_name in rfc_tools:
                # Parse parameters (simplified - in production use proper parsing)
                params = {}
                if params_str:
                    # This is a simplified parser - in production, use a proper parser
                    param_pairs = params_str.split(',')
                    for pair in param_pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            params[key.strip()] = value.strip().strip('"\'')
                
                tool_calls.append({
                    'tool': tool_name,
                    'parameters': params
                })
        
        return tool_calls
    
    def _update_state(self, state: Dict[str, Any], response: Dict[str, Any], 
                     tool_calls: List[Dict[str, Any]]):
        """Update conversation state based on response."""
        # Check if an RFC was created
        for tool_call in tool_calls:
            if tool_call['tool'] == 'create_rfc':
                # Extract RFC ID from response
                rfc_match = re.search(r'RFC-\d{4}-\d{2}-\d{2}-\d{4}', response.get('content', ''))
                if rfc_match:
                    state['active_rfc_id'] = rfc_match.group()
                    state['refinement_stage'] = 'gathering_requirements'
            
            elif tool_call['tool'] == 'move_rfc':
                # Update refinement stage based on status
                target_status = tool_call['parameters'].get('target_status')
                if target_status == 'in_progress':
                    state['refinement_stage'] = 'active_refinement'
                elif target_status == 'archived':
                    state['refinement_stage'] = 'completed'
        
        # Check for questions in response
        question_match = re.search(r'\?(?:\s|$)', response.get('content', ''))
        if question_match:
            # Extract the last question as pending
            questions = re.findall(r'([^.!]+\?)', response.get('content', ''))
            if questions:
                state['pending_question'] = questions[-1].strip()
        else:
            state['pending_question'] = None
    
    def _get_next_steps(self, state: Dict[str, Any]) -> List[str]:
        """Get suggested next steps based on current state."""
        stage = state.get('refinement_stage', 'initial')
        
        if stage == 'initial':
            return ["Share your feature idea or requirement"]
        elif stage == 'gathering_requirements':
            return ["Answer the questions to refine requirements",
                   "Provide specific use cases or examples"]
        elif stage == 'active_refinement':
            return ["Review the RFC with 'read_rfc'",
                   "Continue refining specific sections",
                   "Move to implementation planning when ready"]
        elif stage == 'completed':
            return ["RFC is ready for implementation planning",
                   "Create a new RFC for other features"]
        
        return []
    
    def get_state_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of current refinement state."""
        if session_id not in self.conversation_state:
            return {'status': 'no_active_session'}
        
        state = self.conversation_state[session_id]
        return {
            'active_rfc_id': state.get('active_rfc_id'),
            'refinement_stage': state.get('refinement_stage'),
            'pending_question': state.get('pending_question'),
            'questions_asked': len(state.get('questions_asked', [])),
            'context_gathered': list(state.get('context_gathered', {}).keys())
        }