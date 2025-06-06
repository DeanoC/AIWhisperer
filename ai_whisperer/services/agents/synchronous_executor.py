"""
Synchronous agent executor for mailbox-based task execution.

This module enables synchronous execution of agent tasks via mailbox,
allowing agents like Claude to delegate work to other agents like Debbie
and wait for results.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.execution.ai_loop import AILoop
from ai_whisperer.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class TaskRequest:
    """Represents a task request sent via mailbox."""
    request_id: str
    from_agent: str
    to_agent: str
    task: str
    parameters: Dict[str, Any]
    timeout: float = 30.0


@dataclass 
class TaskResponse:
    """Represents a task response sent via mailbox."""
    request_id: str
    status: str  # 'completed', 'error', 'timeout'
    result: Optional[Any] = None
    error: Optional[str] = None


class SynchronousAgentExecutor:
    """Handles synchronous agent task execution via mailbox."""
    
    def __init__(self):
        self.mailbox = get_mailbox()
        self.pending_requests: Dict[str, TaskRequest] = {}
        
    async def send_task_request(
        self, 
        from_agent: str,
        to_agent: str, 
        task: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> str:
        """Send a task request to another agent and return request ID."""
        request_id = f"req_{datetime.now().timestamp()}"
        
        task_request = TaskRequest(
            request_id=request_id,
            from_agent=from_agent,
            to_agent=to_agent,
            task=task,
            parameters=parameters or {},
            timeout=timeout
        )
        
        # Store pending request
        self.pending_requests[request_id] = task_request
        
        # Send mail
        mail = Mail(
            from_agent=from_agent,
            to_agent=to_agent,
            subject=f"Task Request: {task}",
            body=json.dumps({
                "request_id": request_id,
                "task": task,
                "parameters": parameters or {},
                "timeout": timeout
            }),
            priority=MessagePriority.HIGH
        )
        
        self.mailbox.send_mail(mail)
        logger.info(f"Sent task request {request_id} from {from_agent} to {to_agent}")
        
        return request_id
        
    async def wait_for_response(
        self, 
        agent_name: str,
        request_id: str,
        timeout: Optional[float] = None
    ) -> TaskResponse:
        """Wait for a response to a task request."""
        task_request = self.pending_requests.get(request_id)
        if not task_request:
            return TaskResponse(
                request_id=request_id,
                status="error",
                error="Unknown request ID"
            )
            
        timeout = timeout or task_request.timeout
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            messages = self.mailbox.get_mail(agent_name)
            
            for msg in messages:
                if msg.subject.startswith("Re: Task Request"):
                    try:
                        body = json.loads(msg.body)
                        if body.get("request_id") == request_id:
                            # Mark as read and remove from pending
                            self.mailbox.mark_as_read(agent_name, msg.id)
                            del self.pending_requests[request_id]
                            
                            return TaskResponse(
                                request_id=request_id,
                                status=body.get("status", "completed"),
                                result=body.get("result"),
                                error=body.get("error")
                            )
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse response: {msg.body}")
                        
            await asyncio.sleep(0.1)
            
        # Timeout
        del self.pending_requests[request_id]
        return TaskResponse(
            request_id=request_id,
            status="timeout",
            error=f"Request timed out after {timeout} seconds"
        )
        
    async def execute_task_request(
        self,
        agent_name: str,
        request: Dict[str, Any],
        context: Any
    ) -> None:
        """Execute a task request received via mailbox."""
        request_id = request.get("request_id")
        task = request.get("task")
        parameters = request.get("parameters", {})
        
        logger.info(f"Agent {agent_name} executing task: {task}")
        
        try:
            # Parse task to determine what to do
            if task.startswith("execute tool:"):
                tool_name = task.replace("execute tool:", "").strip()
                result = await self._execute_tool(tool_name, parameters, context)
                status = "completed"
                error = None
            else:
                # For more complex tasks, would invoke AI loop here
                result = f"Task '{task}' acknowledged but not implemented"
                status = "completed"
                error = None
                
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            result = None
            status = "error"
            error = str(e)
            
        # Send response
        response_mail = Mail(
            from_agent=agent_name,
            to_agent=request.get("from_agent", "Unknown"),
            subject=f"Re: Task Request: {task}",
            body=json.dumps({
                "request_id": request_id,
                "status": status,
                "result": result,
                "error": error
            }),
            priority=MessagePriority.HIGH
        )
        
        self.mailbox.send_mail(response_mail)
        logger.info(f"Sent response for request {request_id}")
        
    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Any
    ) -> Any:
        """Execute a tool with given parameters."""
        tool_registry = ToolRegistry()
        
        try:
            tool = tool_registry.get_tool(tool_name)
            parameters["_context"] = context
            
            # Handle both sync and async tools
            import inspect
            if inspect.iscoroutinefunction(tool.execute):
                result = await tool.execute(**parameters)
            else:
                result = tool.execute(**parameters)
                
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise


# Global executor instance
_executor = None

def get_synchronous_executor() -> SynchronousAgentExecutor:
    """Get the global synchronous executor instance."""
    global _executor
    if _executor is None:
        _executor = SynchronousAgentExecutor()
    return _executor