from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class Agent:
    """Represents a specialized AI agent with specific capabilities"""
    agent_id: str  # Single letter ID (P, T, C, etc.)
    name: str  # Full name (Pat the Planner)
    role: str  # Role identifier (planner, tester, coder)
    description: str  # User-facing description
    tool_tags: List[str]  # Tags to filter tools from registry
    prompt_file: str  # Filename in prompts directory
    context_sources: List[str]  # Types of context to include
    color: str  # UI color for agent identification
    icon: str = "🤖"  # Icon for UI display
    tool_sets: Optional[List[str]] = None  # Tool sets from tool_sets.yaml
    allow_tools: Optional[List[str]] = None  # Explicitly allowed tool names
    deny_tools: Optional[List[str]] = None  # Explicitly denied tool names

    @property
    def shortcut(self) -> str:
        """Returns the keyboard shortcut for this agent"""
        return f"[{self.agent_id}]"

class AgentRegistry:
    """Manages available agents and their configurations"""
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._agents: Dict[str, Agent] = {}
        self._load_default_agents()

    def _load_default_agents(self):
        """Load the default agent configurations, overridable from config."""
        # Try to load from YAML config, fallback to hardcoded
        import yaml
        import os
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'agents.yaml')
        agents = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                for agent_id, agent_cfg in data.get('agents', {}).items():
                    agents[agent_id.upper()] = Agent(
                        agent_id=agent_id.upper(),
                        name=agent_cfg['name'],
                        role=agent_cfg['role'],
                        description=agent_cfg['description'],
                        tool_tags=agent_cfg.get('tool_tags', []),
                        prompt_file=agent_cfg['prompt_file'],
                        context_sources=agent_cfg.get('context_sources', []),
                        color=agent_cfg.get('color', '#888888'),
                        icon=agent_cfg.get('icon', '🤖'),
                        tool_sets=agent_cfg.get('tool_sets'),
                        allow_tools=agent_cfg.get('allow_tools'),
                        deny_tools=agent_cfg.get('deny_tools')
                    )
        else:
            # Hardcoded fallback
            agents = {
                "P": Agent(
                    agent_id="P",
                    name="Patricia the Planner",
                    role="planner",
                    description="Creates structured implementation plans from feature requests",
                    tool_tags=["filesystem", "analysis", "planning"],
                    prompt_file="agent_planner.md",
                    context_sources=["workspace_structure", "existing_schemas", "recent_changes"],
                    color="#4CAF50"
                ),
                "T": Agent(
                    agent_id="T",
                    name="Tessa the Tester",
                    role="tester",
                    description="Generates comprehensive test suites and test plans",
                    tool_tags=["filesystem", "testing", "analysis"],
                    prompt_file="agent_tester.md",
                    context_sources=["existing_tests", "code_coverage", "test_patterns"],
                    color="#2196F3"
                )
            }
        self._agents = agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self._agents.get(agent_id.upper())

    def list_agents(self) -> List[Agent]:
        """List all available agents"""
        return list(self._agents.values())
