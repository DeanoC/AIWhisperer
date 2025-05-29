from typing import List, Dict, Any
from pathlib import Path
from ai_whisperer.context_management import ContextManager
from .registry import Agent


from ai_whisperer.prompt_system import PromptSystem, PromptNotFoundError

class AgentContextManager(ContextManager):
    """Context manager specialized for agent-specific needs"""
    def __init__(self, agent: Agent, workspace_path: Path, prompt_system: PromptSystem = None):
        super().__init__()
        self.agent = agent
        self.workspace_path = workspace_path
        self.context = []
        self.prompt_system = prompt_system
        self._initialize_agent_context()

    def _initialize_agent_context(self):
        """Load system prompt and context based on agent's context_sources"""
        # 1. Load and prepend the agent's system prompt using PromptSystem
        prompt_text = None
        if self.prompt_system:
            # Remove extension and 'agent_' prefix for prompt name
            prompt_name = self.agent.prompt_file
            if prompt_name.startswith("agent_"):
                prompt_name = prompt_name[len("agent_"):]
            if prompt_name.endswith(".md"):
                prompt_name = prompt_name[:-3]
            try:
                prompt = self.prompt_system.get_prompt("agents", prompt_name)
                prompt_text = prompt.content.strip()
            except PromptNotFoundError as e:
                prompt_text = f"[ERROR: Could not load system prompt for agent {self.agent.agent_id}: {e}]"
        if not prompt_text:
            prompt_text = f"[ERROR: No prompt system or prompt not found for agent {self.agent.agent_id}]"
        self.context.append({
            "role": "system",
            "content": prompt_text
        })

        # 2. Load additional context sources
        for source in self.agent.context_sources:
            if source == "workspace_structure":
                self._add_workspace_structure()
            elif source == "existing_schemas":
                self._add_existing_schemas()
            elif source == "recent_changes":
                self._add_recent_changes()
            # Add more context sources as needed

    def _add_workspace_structure(self):
        # Placeholder for actual implementation
        pass

    def _add_existing_schemas(self):
        # Placeholder for actual implementation
        pass

    def _add_recent_changes(self):
        # Placeholder for actual implementation
        pass
