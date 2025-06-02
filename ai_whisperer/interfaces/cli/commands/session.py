from ai_whisperer.interfaces.cli.commands.base import Command
from ai_whisperer.interfaces.cli.commands.registry import CommandRegistry

class SessionSwitchAgentCommand(Command):
    name = 'session.switch_agent'
    description = 'Switch the current agent for the session.'

    def run(self, args: str, context=None):
        import json
        from interactive_server.main import session_manager
        params = json.loads(args) if args else {}
        session_id = context.get('session_id') if context else None
        agent_id = params.get('agent_id')
        if not session_id or not agent_id:
            return {'error': 'Missing session_id or agent_id'}
        session = session_manager.get_session(session_id)
        if not session:
            return {'error': f'Session not found: {session_id}'}
        session.current_agent_id = agent_id
        return {'success': True, 'current_agent': agent_id}

CommandRegistry.register(SessionSwitchAgentCommand)
