"""
Agent switching handler for synchronous mailbox communication.
Handles the logic for switching between agents when mail is sent.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox

logger = logging.getLogger(__name__)

class AgentSwitchHandler:
    """Handles agent switching for synchronous mailbox communication."""
    
    def __init__(self, session):
        """
        Initialize the handler.
        
        Args:
            session: The StatelessInteractiveSession instance
        """
        self.session = session
        self.switch_stack = []  # Stack to track nested switches
        self.max_switch_depth = 5  # Maximum depth to prevent infinite loops
        
    async def handle_tool_results(self, tool_calls: list, tool_results: str) -> Tuple[bool, Optional[str]]:
        """
        Check tool results for agent switching requirements.
        
        Args:
            tool_calls: List of tool calls that were executed
            tool_results: The formatted results string
            
        Returns:
            Tuple of (switch_occurred, additional_response)
        """
        if not tool_calls:
            return False, None
            
        # Check each tool call for agent switch metadata
        for tool_call in tool_calls:
            tool_name = tool_call.get('function', {}).get('name')
            
            if tool_name in ['send_mail', 'send_mail_with_switch']:
                # Check if the send_mail was successful by looking at the tool results
                if "Error" in tool_results or "failed" in tool_results.lower():
                    logger.info(f"send_mail failed, not triggering agent switch")
                    continue
                    
                # Parse the tool arguments to check if agent switch is needed
                import json
                try:
                    args_str = tool_call.get('function', {}).get('arguments', '{}')
                    args = json.loads(args_str)
                    to_agent = args.get('to_agent', '').strip()
                    
                    if to_agent and ("sent" in tool_results or "send_mail_with_switch" in tool_results):
                        # This is successful agent-to-agent communication
                        logger.info(f"Detected successful mail sent to agent: {to_agent}")
                        
                        # Perform synchronous agent switch
                        additional_response = await self._perform_agent_switch(
                            to_agent=to_agent,
                            from_agent=self.session.active_agent,
                            mail_context=args
                        )
                        
                        return True, additional_response
                        
                except Exception as e:
                    logger.error(f"Error parsing send_mail arguments: {e}")
                    
        return False, None
        
    async def _perform_agent_switch(self, to_agent: str, from_agent: str, mail_context: dict) -> Optional[str]:
        """
        Perform synchronous agent switch for mail processing.
        
        Args:
            to_agent: Target agent ID
            from_agent: Source agent ID  
            mail_context: Mail context (subject, body, etc.)
            
        Returns:
            Additional response text to append
        """
        try:
            logger.info(f"Starting synchronous agent switch: {from_agent} -> {to_agent}")
            
            # Use the agent registry to resolve the agent name to ID
            try:
                # Get the agent registry from the session
                agent_registry = self.session.agent_registry if hasattr(self.session, 'agent_registry') else None
                
                if agent_registry:
                    # Use the registry's name resolution
                    target_agent_id = agent_registry.resolve_agent_name_to_id(to_agent)
                else:
                    # Fallback to basic mapping if registry not available
                    logger.warning("Agent registry not available, using fallback mapping")
                    agent_name_map = {
                        'alice': 'a',
                        'patricia': 'p',
                        'tessa': 't',
                        'debbie': 'd',
                        'eamonn': 'e'
                    }
                    to_agent_lower = to_agent.lower()
                    first_word = to_agent_lower.split()[0] if ' ' in to_agent_lower else to_agent_lower
                    target_agent_id = agent_name_map.get(first_word, to_agent_lower)
                    
                    if not target_agent_id:
                        raise ValueError(f"Unknown agent: {to_agent}")
                        
            except ValueError as e:
                logger.error(f"Failed to resolve agent name: {e}")
                return f"\n\n[Error: {str(e)}]"
            
            # Check for circular mail (max depth exceeded)
            if len(self.switch_stack) >= self.max_switch_depth:
                logger.error(f"Maximum switch depth ({self.max_switch_depth}) exceeded - possible circular mail")
                return f"\n\n[Error: Maximum agent switch depth exceeded - possible circular mail scenario. Switch stack: {' -> '.join([s['agent'] for s in self.switch_stack])} -> {from_agent}]"
            
            # Check for immediate circular reference (agent sending to itself)
            if target_agent_id == from_agent:
                logger.warning(f"Agent {from_agent} attempting to send mail to itself (target: {to_agent})")
                return f"\n\n[Warning: Agent cannot send mail to itself]"
                
            # Check if target agent ID is already in the switch stack
            agent_ids_in_stack = [s['agent'] for s in self.switch_stack]
            if target_agent_id in agent_ids_in_stack:
                logger.warning(f"Circular mail detected: {target_agent_id} is already in the switch stack")
                return f"\n\n[Warning: Circular mail detected - {to_agent} (ID: {target_agent_id}) is already processing mail in this chain: {' -> '.join(agent_ids_in_stack)} -> {from_agent}]"
            
            # Save current agent state after all checks pass
            self.switch_stack.append({
                'agent': from_agent,
                'context_snapshot': await self._get_context_snapshot(from_agent)
            })
            
            # Switch to target agent
            await self.session.switch_agent(target_agent_id)
            
            # Notify target agent about mail
            mail_notification = f"You have received mail from {from_agent}. Let me check your mailbox."
            logger.info(f"Notifying {to_agent} about new mail")
            
            # Combine notification and response prompt into one message
            combined_prompt = f"{mail_notification} Please check your mailbox and respond to any messages."
            response_result = await self.session.send_user_message(
                combined_prompt,
                is_continuation=True  # This is part of the same flow
            )
            
            # Extract the response
            target_response = None
            if isinstance(response_result, dict):
                target_response = response_result.get('response', '')
                
            # Switch back to original agent
            await self._restore_agent_context()
            
            # Format the response for the original agent
            if target_response:
                return f"\n\n[{to_agent} processed the mail and responded]"
            else:
                return f"\n\n[Mail sent to {to_agent}]"
                
        except Exception as e:
            logger.error(f"Error during agent switch: {e}")
            # Try to restore original agent on error
            try:
                await self._restore_agent_context()
            except:
                pass
            return f"\n\n[Error: Failed to deliver mail to {to_agent}]"
            
    async def _get_context_snapshot(self, agent_id: str) -> dict:
        """Get a snapshot of agent's current context."""
        if agent_id in self.session.agents:
            agent = self.session.agents[agent_id]
            return {
                'messages': agent.context.retrieve_messages().copy() if hasattr(agent.context, 'retrieve_messages') else [],
                'continuation_depth': self.session._continuation_depth
            }
        return {}
        
    async def _restore_agent_context(self) -> None:
        """Restore the previous agent context from the stack."""
        if not self.switch_stack:
            logger.warning("No agent context to restore")
            return
            
        context = self.switch_stack.pop()
        agent_id = context['agent']
        
        # Switch back to original agent
        await self.session.switch_agent(agent_id)
        
        # Restore continuation depth
        snapshot = context.get('context_snapshot', {})
        self.session._continuation_depth = snapshot.get('continuation_depth', 0)
        
        logger.info(f"Restored context for agent {agent_id}")