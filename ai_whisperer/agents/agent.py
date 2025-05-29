from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext

class Agent:
    def __init__(self, config: AgentConfig, context: AgentContext, ai_loop):
        if config is None:
            raise ValueError("AgentConfig must not be None")
        if context is None:
            raise ValueError("AgentContext must not be None")
        if ai_loop is None:
            raise ValueError("AILoop instance must not be None")
        self.config = config
        self.context = context
        self.ai_loop = ai_loop

    async def process_message(self, message):
        try:
            # Ensure session is started
            if not hasattr(self.ai_loop, "_session_task") or self.ai_loop._session_task is None or self.ai_loop._session_task.done():
                # Use system prompt from config or context if available
                system_prompt = getattr(self.config, "system_prompt", None)
                if not system_prompt and hasattr(self.context, "system_prompt"):
                    system_prompt = self.context.system_prompt
                if not system_prompt:
                    system_prompt = "You are an AI assistant."
                await self.ai_loop.start_session(system_prompt)
            return await self.ai_loop.send_user_message(message)
        except Exception as e:
            # Let exceptions propagate for testability and error handling
            raise