"""Continuation strategy module for managing multi-step agent operations."""

import re
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ContinuationProgress:
    """Tracks progress information for continuation operations."""
    current_step: int = 0
    total_steps: Optional[int] = None
    completion_percentage: Optional[float] = None
    steps_completed: List[str] = field(default_factory=list)
    steps_remaining: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'completion_percentage': self.completion_percentage,
            'steps_completed': self.steps_completed,
            'steps_remaining': self.steps_remaining
        }


@dataclass
class ContinuationState:
    """Represents the continuation state from an AI response."""
    status: str  # CONTINUE or TERMINATE
    reason: Optional[str] = None
    next_action: Optional[Dict[str, Any]] = None
    progress: Optional[ContinuationProgress] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContinuationState':
        """Create from dictionary data."""
        progress = None
        if 'progress' in data and data['progress']:
            progress_data = data['progress']
            progress = ContinuationProgress(
                current_step=progress_data.get('current_step', 0),
                total_steps=progress_data.get('total_steps'),
                completion_percentage=progress_data.get('completion_percentage'),
                steps_completed=progress_data.get('steps_completed', []),
                steps_remaining=progress_data.get('steps_remaining', [])
            )
        
        return cls(
            status=data.get('status', 'TERMINATE'),
            reason=data.get('reason'),
            next_action=data.get('next_action'),
            progress=progress
        )


class ContinuationStrategy:
    """Manages continuation detection and execution for agents."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize continuation strategy with configuration."""
        config = config or {}
        self.max_iterations = config.get('max_iterations', 10)
        self.timeout = config.get('timeout', 300)  # 5 minutes
        self.require_explicit_signal = config.get('require_explicit_signal', True)
        self.continuation_patterns = config.get('patterns', [
            r'\bCONTINUE\b',
            r'"status":\s*"CONTINUE"',
            r'need.*more.*steps',
            r'not.*finished'
        ])
        self.termination_patterns = config.get('termination_patterns', [
            r'\bTERMINATE\b',
            r'"status":\s*"TERMINATE"',
            r'task.*completed',
            r'finished.*successfully'
        ])
        self._start_time = None
        self._iteration_count = 0
        self._continuation_history = []
    
    def reset(self):
        """Reset the strategy for a new operation."""
        self._start_time = time.time()
        self._iteration_count = 0
        self._continuation_history = []
    
    def should_continue(self, response: Dict[str, Any], original_message: str = None) -> bool:
        """
        Determine if continuation is needed based on response.
        
        Args:
            response: The AI response containing potential continuation signals
            original_message: Optional original message (kept for compatibility)
            
        Returns:
            True if continuation is needed, False otherwise
        """
        # Check safety limits first
        if not self._check_safety_limits():
            logger.warning("Safety limits reached, forcing termination")
            return False
        
        # First check for explicit continuation field
        if 'continuation' in response:
            continuation = response['continuation']
            if isinstance(continuation, dict) and 'status' in continuation:
                should_continue = continuation['status'] == 'CONTINUE'
                reason = continuation.get('reason', 'No reason provided')
                logger.info(f"Explicit continuation signal: {should_continue}, reason: {reason}")
                return should_continue
        
        # If no explicit signal and we require it, default to terminate
        if self.require_explicit_signal:
            logger.info("No explicit continuation signal found, defaulting to TERMINATE")
            return False
        
        # Fallback to pattern matching
        response_text = str(response.get('response', ''))
        
        # Check termination patterns first (they take precedence)
        for pattern in self.termination_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                logger.info(f"Found termination pattern: {pattern}")
                return False
        
        # Check continuation patterns
        for pattern in self.continuation_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                logger.info(f"Found continuation pattern: {pattern}")
                return True
        
        # Default to terminate if no patterns match
        logger.info("No continuation patterns found, defaulting to TERMINATE")
        return False
    
    def extract_continuation_state(self, response: Dict[str, Any]) -> Optional[ContinuationState]:
        """Extract structured continuation state from response."""
        if 'continuation' in response and isinstance(response['continuation'], dict):
            return ContinuationState.from_dict(response['continuation'])
        return None
    
    def extract_next_action(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract the next action from response."""
        # First check continuation field
        state = self.extract_continuation_state(response)
        if state and state.next_action:
            return state.next_action
        
        # Check if there are pending tool calls
        if 'tool_calls' in response and response['tool_calls']:
            # Convert tool calls to next action format
            first_tool = response['tool_calls'][0]
            return {
                'type': 'tool_call',
                'tool': first_tool.get('function', {}).get('name'),
                'parameters': first_tool.get('function', {}).get('arguments', {})
            }
        
        return None
    
    def update_context(self, context: Dict[str, Any], response: Dict[str, Any], 
                      tool_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update context with new information from response and tool results."""
        # Initialize continuation history if not present
        if 'continuation_history' not in context:
            context['continuation_history'] = []
        
        # Increment iteration count
        self._iteration_count += 1
        
        # Add current iteration
        iteration_info = {
            'iteration': self._iteration_count,
            'timestamp': time.time(),
            'response_summary': self._summarize_response(response),
            'continuation_status': 'UNKNOWN',
            'tool_calls': len(response.get('tool_calls', [])),
        }
        
        # Extract continuation state
        state = self.extract_continuation_state(response)
        if state:
            iteration_info['continuation_status'] = state.status
            iteration_info['continuation_reason'] = state.reason
            if state.progress:
                iteration_info['progress'] = state.progress.to_dict()
        
        if tool_results:
            iteration_info['tool_results'] = tool_results
        
        context['continuation_history'].append(iteration_info)
        self._continuation_history.append(iteration_info)
        
        # Update progress information
        if state and state.progress:
            context['progress'] = state.progress.to_dict()
        
        return context
    
    def get_progress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get current progress information."""
        # First check if we have explicit progress
        if 'progress' in context:
            return context['progress']
        
        # Calculate from history
        history = context.get('continuation_history', [])
        return {
            'current_step': len(history),
            'total_steps': None,
            'completion_percentage': None,
            'iteration_count': self._iteration_count,
            'elapsed_time': time.time() - self._start_time if self._start_time else 0
        }
    
    def get_continuation_message(self, tool_names: List[str], original_message: str) -> str:
        """
        Get continuation message (kept for backward compatibility).
        
        With the new continuation protocol, agents generate their own continuation
        context, so this just returns a generic message.
        """
        return "Please continue with the next step based on the continuation protocol."
    
    def _check_safety_limits(self) -> bool:
        """Check if we're within safety limits."""
        # Check iteration limit
        if self._iteration_count >= self.max_iterations:
            logger.warning(f"Reached maximum iterations ({self.max_iterations})")
            return False
        
        # Check timeout
        if self._start_time:
            elapsed = time.time() - self._start_time
            if elapsed > self.timeout:
                logger.warning(f"Reached timeout ({self.timeout}s)")
                return False
        
        return True
    
    def _summarize_response(self, response: Dict[str, Any]) -> str:
        """Create a brief summary of the response."""
        text = response.get('response', '')
        max_length = 200
        if len(text) > max_length:
            return text[:max_length] + '...'
        return text
    
    def get_iteration_count(self) -> int:
        """Get the current iteration count."""
        return self._iteration_count
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since start."""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the continuation history."""
        return self._continuation_history.copy()