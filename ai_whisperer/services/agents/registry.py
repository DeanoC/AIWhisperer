"""
Module: ai_whisperer/agents/registry.py
Purpose: AI agent implementation for specialized task handling

This module implements an AI agent that processes user messages
and executes specialized tasks. It integrates with the tool system
and manages conversation context.

Key Components:
- Agent: Represents a specialized AI agent with specific capabilities
- AgentRegistry: Manages available agents and their configurations

Usage:
    agent = Agent()
    result = agent.shortcut()

Dependencies:
- dataclasses
- yaml

Related:
- See docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
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
    continuation_config: Optional[Dict[str, Any]] = None  # Configuration for continuation behavior
    ai_config: Optional[Dict[str, Any]] = None  # AI model configuration (model, temperature, etc.)

    @property
    def shortcut(self) -> str:
        """Returns the keyboard shortcut for this agent"""
        return f"[{self.agent_id}]"

class AgentRegistry:
    """Manages available agents and their configurations"""
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._agents: Dict[str, Agent] = {}
        self._agent_name_to_id_map: Dict[str, str] = {}  # Maps various names/aliases to agent IDs
        self._load_default_agents()

    def _load_default_agents(self):
        """Load the default agent configurations, overridable from config."""
        # Try to load from YAML config, fallback to hardcoded
        import yaml
        import os
        # Look for config in the project's config directory
        from ai_whisperer.utils.path import PathManager
        path_manager = PathManager.get_instance()
        config_path = path_manager.project_path / 'config' / 'agents' / 'agents.yaml'
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
                        deny_tools=agent_cfg.get('deny_tools'),
                        continuation_config=agent_cfg.get('continuation_config'),
                        ai_config=agent_cfg.get('ai_config')
                    )
        else:
            # Only use hardcoded fallback if no config file exists
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
        # Build name to ID mapping after loading agents
        self._build_name_mapping()

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self._agents.get(agent_id.upper())

    def list_agents(self) -> List[Agent]:
        """List all available agents"""
        return list(self._agents.values())
    
    def _build_name_mapping(self):
        """Build mapping from various agent names/aliases to agent IDs"""
        self._agent_name_to_id_map.clear()
        
        for agent_id, agent in self._agents.items():
            # Map the agent ID itself (both upper and lower case)
            self._agent_name_to_id_map[agent_id.lower()] = agent_id.lower()
            self._agent_name_to_id_map[agent_id.upper()] = agent_id.lower()
            
            # Map the full agent name
            full_name_lower = agent.name.lower()
            self._agent_name_to_id_map[full_name_lower] = agent_id.lower()
            
            # Map just the first name (e.g., "patricia" from "Patricia the Planner")
            first_name = full_name_lower.split()[0]
            self._agent_name_to_id_map[first_name] = agent_id.lower()
            
            # Map the role (e.g., "planner")
            if agent.role:
                self._agent_name_to_id_map[agent.role.lower()] = agent_id.lower()
            
            # Map common variations
            self._agent_name_to_id_map[f"agent {agent_id.lower()}"] = agent_id.lower()
            self._agent_name_to_id_map[f"agent {first_name}"] = agent_id.lower()
    
    def resolve_agent_name_to_id(self, name: str) -> str:
        """
        Resolve an agent name/alias to its canonical agent ID.
        
        Args:
            name: Agent name, alias, or ID
            
        Returns:
            Canonical agent ID (lowercase single letter)
            
        Raises:
            ValueError: If the agent name cannot be resolved
        """
        if not name:
            raise ValueError("Agent name cannot be empty")
        
        # Normalize the name
        name_lower = name.lower().strip()
        
        # Check if it's already in our mapping
        if name_lower in self._agent_name_to_id_map:
            return self._agent_name_to_id_map[name_lower]
        
        # Try without "the" (e.g., "debbie the debugger" -> "debbie debugger")
        name_without_the = name_lower.replace(" the ", " ")
        if name_without_the in self._agent_name_to_id_map:
            return self._agent_name_to_id_map[name_without_the]
        
        # Try just the first word
        first_word = name_lower.split()[0] if ' ' in name_lower else name_lower
        if first_word in self._agent_name_to_id_map:
            return self._agent_name_to_id_map[first_word]
        
        # If no match found, raise an error
        available_agents = ", ".join(sorted(set(self._agent_name_to_id_map.values())))
        raise ValueError(f"Unknown agent: '{name}'. Available agents: {available_agents}")
    
    def get_canonical_to_id_map(self) -> Dict[str, str]:
        """
        Get a mapping from canonical agent names to agent IDs.
        This is useful for compatibility with mailbox system.
        
        Returns:
            Dict mapping canonical names (e.g., 'alice', 'patricia') to agent IDs ('a', 'p')
        """
        canonical_map = {}
        for agent_id, agent in self._agents.items():
            # Use the first name as the canonical name
            first_name = agent.name.lower().split()[0]
            canonical_map[first_name] = agent_id.lower()
        return canonical_map
