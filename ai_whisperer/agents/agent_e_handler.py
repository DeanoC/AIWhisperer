"""
Agent E Handler - manages communication and task decomposition for external agent execution.
"""
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

from .task_decomposer import TaskDecomposer
from .decomposed_task import DecomposedTask
from .agent_communication import (
    AgentMessage,
    MessageType,
    ClarificationRequest,
    ClarificationResponse,
    PlanRefinementRequest,
    PlanRefinementResponse
)
from .agent_e_exceptions import AgentEException, CommunicationError


logger = logging.getLogger(__name__)


class AgentEHandler:
    """Handles Agent E operations including decomposition and communication."""
    
    def __init__(self, agent_registry, session_manager=None):
        """Initialize Agent E handler.
        
        Args:
            agent_registry: Registry containing other agents for communication
            session_manager: Optional session manager for interactive mode
        """
        self.agent_registry = agent_registry
        self.session_manager = session_manager
        self.task_decomposer = TaskDecomposer()
        self.pending_clarifications = {}
        self.message_history = []
        self.current_tasks = {}
        
    async def process_plan(self, plan: Dict[str, Any]) -> List[DecomposedTask]:
        """Process a plan and decompose it into tasks.
        
        Args:
            plan: The plan to decompose
            
        Returns:
            List of decomposed tasks
        """
        try:
            # Decompose the plan
            decomposed_tasks = self.task_decomposer.decompose_plan(plan)
            
            # Store tasks for tracking
            for task in decomposed_tasks:
                self.current_tasks[task.task_id] = task
                
            return decomposed_tasks
            
        except Exception as e:
            logger.error(f"Error processing plan: {e}")
            raise AgentEException(f"Failed to process plan: {e}")
    
    async def request_clarification(self, task: Dict[str, Any], questions: List[str]) -> str:
        """Request clarification from Agent P using the mailbox.
        
        Args:
            task: The task dictionary needing clarification
            questions: List of clarification questions
            
        Returns:
            Message ID of the clarification request
        """
        from ..agents.mailbox import Mail, MessagePriority, get_mailbox
        
        task_name = task.get('name', 'Unknown Task')
        
        # Format questions as a numbered list
        questions_body = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
        
        # Create mail body with context
        body = f"""I need clarification on the task: {task_name}

Original Description: {task.get('description', 'No description provided')}

Questions:
{questions_body}

Validation Criteria:
{chr(10).join('- ' + vc for vc in task.get('validation_criteria', ['None specified']))}

Please provide guidance on these questions to help me decompose this task effectively.
"""
        
        # Create mail
        mail = Mail(
            from_agent="agent_e",
            to_agent="agent_p",
            subject=f"Clarification needed: {task_name}",
            body=body,
            priority=MessagePriority.HIGH,
            metadata={
                'task_name': task_name,
                'questions': questions,
                'original_task': task
            }
        )
        
        # Send via mailbox
        mailbox = get_mailbox()
        message_id = mailbox.send_mail(mail)
        
        # Store for tracking
        self.pending_clarifications[message_id] = {
            'task': task,
            'questions': questions,
            'timestamp': datetime.now(timezone.utc)
        }
        
        return message_id
    
    async def handle_clarification_response(self, response: ClarificationResponse):
        """Handle clarification response from Agent P.
        
        Args:
            response: The clarification response
        """
        # Find the original request
        request = self.pending_clarifications.pop(response.request_id, None)
        if not request:
            logger.warning(f"Received response for unknown request: {response.request_id}")
            return
            
        # Update task context with clarification
        task_dict = request['task']  # request is a dict from pending_clarifications
        task_id = task_dict.get('id') or task_dict.get('task_id')
        task = self.current_tasks.get(task_id) if task_id else None
        if task:
            if 'clarifications' not in task.context:
                task.context['clarifications'] = []
            
            task.context['clarifications'].append({
                'question': request['questions'],
                'answer': response.answer,
                'confidence': response.confidence,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    async def suggest_plan_refinement(self, task_id: str, issue: str,
                                    suggestions: List[Dict[str, Any]]) -> str:
        """Suggest plan refinement based on decomposition insights.
        
        Args:
            task_id: ID of the problematic task
            issue: Description of the issue
            suggestions: List of suggested refinements
            
        Returns:
            Refinement request ID
        """
        task = self.current_tasks.get(task_id)
        if not task:
            raise ValueError(f"Unknown task ID: {task_id}")
            
        # Gather decomposition insights
        insights = {
            'complexity': task.estimated_complexity,
            'dependencies': task.get_dependencies(),
            'technology_stack': task.context.get('technology_stack', {}),
            'execution_strategy': task.execution_strategy
        }
        
        # Create refinement request
        request = PlanRefinementRequest(
            task_id=task_id,
            task_name=task.parent_task_name,
            issue_description=issue,
            suggested_refinements=suggestions,
            decomposition_insights=insights
        )
        
        # Generate message
        message_id = str(uuid.uuid4())
        message = request.to_message(
            sender="agent_e",
            recipient="agent_p",
            message_id=message_id
        )
        
        # Send to Agent P
        await self._send_message(message)
        
        return message_id
    
    async def handle_plan_refinement_response(self, response: PlanRefinementResponse):
        """Handle plan refinement response from Agent P.
        
        Args:
            response: The refinement response
        """
        if response.approved and response.refined_plan:
            # Re-decompose the refined plan
            try:
                refined_tasks = await self.process_plan(response.refined_plan)
                logger.info(f"Successfully processed refined plan with {len(refined_tasks)} tasks")
            except Exception as e:
                logger.error(f"Failed to process refined plan: {e}")
    
    async def _send_message(self, message: AgentMessage):
        """Send message to another agent.
        
        Args:
            message: The message to send
        """
        # Store in history
        self.message_history.append(message)
        
        # Get recipient agent
        recipient = self.agent_registry.get_agent(message.recipient)
        if not recipient:
            raise CommunicationError(f"Agent not found: {message.recipient}")
            
        # Send message
        await recipient.receive_message(message)
    
    async def receive_message(self, message: AgentMessage):
        """Receive message from another agent.
        
        Args:
            message: The received message
        """
        # Store in history
        self.message_history.append(message)
        
        # Route based on message type
        if message.message_type == MessageType.CLARIFICATION_RESPONSE:
            response = ClarificationResponse(
                request_id=message.content['request_id'],
                answer=message.content['answer'],
                additional_context=message.content.get('additional_context', {}),
                confidence=message.content.get('confidence', 1.0)
            )
            await self.handle_clarification_response(response)
            
        elif message.message_type == MessageType.PLAN_REFINEMENT_RESPONSE:
            response = PlanRefinementResponse(
                request_id=message.content['request_id'],
                approved=message.content['approved'],
                refined_plan=message.content.get('refined_plan'),
                reasoning=message.content.get('reasoning', '')
            )
            await self.handle_plan_refinement_response(response)
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task status or None if not found
        """
        task = self.current_tasks.get(task_id)
        return task.status if task else None
    
    def get_message_history(self, message_type: Optional[MessageType] = None) -> List[AgentMessage]:
        """Get message history, optionally filtered by type.
        
        Args:
            message_type: Optional message type filter
            
        Returns:
            List of messages
        """
        if message_type:
            return [m for m in self.message_history if m.message_type == message_type]
        return self.message_history.copy()