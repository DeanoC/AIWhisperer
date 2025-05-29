from .base import Command
from .registry import CommandRegistry

# Command class for agent.inspect

# Synchronous wrapper for async inspect_agent_context
def inspect_agent_context(agent_id: str, info_type: str = "context", context_manager=None, session_id: str = None):
    """
    Inspect agent info (context, state, etc.) for debugging. Synchronous version for command system.
    """
    result = {"agent_id": agent_id, "info_type": info_type}
    if context_manager is None:
        context_manager = get_context_manager_for_agent(agent_id, session_id=session_id)
    if context_manager is None:
        result["context"] = []
        result["error"] = f"No context manager found for agent_id: {agent_id}"
        return result
    if info_type == "context":
        # Use agent-specific context if possible
        result["context"] = context_manager.get_history(agent_id=agent_id)
    else:
        result["context"] = []
        result["error"] = f"Unknown info_type: {info_type}"
    return result

class AgentInspectCommand(Command):
    name = 'agent.inspect'
    description = 'Inspect agent context or state for debugging.'

    def run(self, args: str, context=None):
        import json
        try:
            params = json.loads(args) if args else {}
        except Exception:
            params = {}
        agent_id = params.get('agent_id') or (context and context.get('agent_id'))
        info_type = params.get('info_type', 'context')
        session_id = params.get('session_id') or (context and context.get('session_id'))
        return inspect_agent_context(agent_id=agent_id, info_type=info_type, session_id=session_id)

# Register the command
CommandRegistry.register(AgentInspectCommand)
"""
Agent inspection commands for development/debugging.
"""
from typing import Any, Dict

# This would be replaced with actual agent/session/context lookup in the real system
AGENT_CONTEXT_MANAGERS = {}


# Real implementation: look up context manager from session manager
def get_context_manager_for_agent(agent_id: str, session_id: str = None):
    import logging
    try:
        from interactive_server.main import session_manager
        logging.error(f"[get_context_manager_for_agent] Called with agent_id={agent_id}, session_id={session_id}")
        # If session_id is provided, use it to get the session
        if session_id:
            session = session_manager.get_session(session_id)
            logging.error(f"[get_context_manager_for_agent] session_manager.get_session({session_id}) returned: {session}")
            if session and hasattr(session, 'context_manager'):
                logging.error(f"[get_context_manager_for_agent] session.context_manager exists: {session.context_manager}")
                return session.context_manager
            else:
                logging.error(f"[get_context_manager_for_agent] session or context_manager not found for session_id={session_id}")
        # Fallback: try by agent_id if your system supports it
        # (You may want to map agent_id to session or context manager here)
    except Exception as e:
        logging.error(f"[get_context_manager_for_agent] Exception: {e}")
    return None


