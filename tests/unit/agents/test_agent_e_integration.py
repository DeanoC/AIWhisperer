"""
Test Agent E integration with the system.
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.tools.tool_registry import get_tool_registry, ToolRegistry



pytestmark = pytest.mark.xfail(reason="Agent E feature in development")
# Mark all tests as xfail - Agent E feature in development

class TestAgentEIntegration:
    """Test Agent E integration into AIWhisperer."""
    
    def setup_method(self):
        """Set up test environment."""
        # Reset tool registry singleton
        ToolRegistry.reset_instance()
        self.tool_registry = get_tool_registry()
    
    def test_agent_e_in_registry(self):
        """Test that Agent E is registered in the agent registry."""
        # Use the actual prompts directory
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        registry = AgentRegistry(prompts_dir=prompts_dir)
        
        # Get Agent E
        agent_e = registry.get_agent("E")
        
        # Verify Agent E exists and has correct properties
        assert agent_e is not None
        assert agent_e.agent_id == "E"
        assert agent_e.name == "Eamonn the Executioner"
        assert agent_e.role == "task_decomposer"
        assert "task_decomposition" in agent_e.tool_tags
        assert "external_agents" in agent_e.tool_tags
        assert "mailbox" in agent_e.tool_tags
        assert agent_e.prompt_file == "agent_eamonn.prompt.md"
        assert agent_e.color == "#7C3AED"
        assert agent_e.icon == "⚔️"
    
    def test_agent_e_prompt_exists(self):
        """Test that Agent E's prompt file exists."""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "agents" / "agent_eamonn.prompt.md"
        assert prompt_path.exists()
        
        # Verify it contains expected content
        content = prompt_path.read_text()
        assert "Eamonn The Executioner" in content
        assert "task decomposition specialist" in content
        assert "decompose_plan" in content
        assert "external_agent" in content
    
    def test_agent_e_tool_sets_defined(self):
        """Test that Agent E's tool sets are defined in tool_sets.yaml."""
        tool_sets_path = Path(__file__).parent.parent.parent / "ai_whisperer" / "tools" / "tool_sets.yaml"
        assert tool_sets_path.exists()
        
        import yaml
        with open(tool_sets_path) as f:
            tool_sets = yaml.safe_load(f)
        
        # Check specialized_sets contains Agent E's tool sets
        specialized = tool_sets.get("specialized_sets", {})
        assert "task_decomposition" in specialized
        assert "mailbox_tools" in specialized
        assert "external_agent_tools" in specialized
        
        # Verify task decomposition tools
        task_decomp = specialized["task_decomposition"]
        assert "decompose_plan" in task_decomp["tools"]
        assert "analyze_dependencies" in task_decomp["tools"]
        assert "format_for_external_agent" in task_decomp["tools"]
        assert "update_task_status" in task_decomp["tools"]
    
    def test_agent_e_tools_can_be_registered(self):
        """Test that Agent E's tools can be registered."""
        from ai_whisperer.tools.tool_registration import register_tool_category
        
        # Register Agent E tools
        register_tool_category('agent_e')
        
        # Verify tools are registered
        all_tools = self.tool_registry.get_all_tools()
        tool_names = [tool.name for tool in all_tools]
        
        # Check task decomposition tools
        assert "decompose_plan" in tool_names
        assert "analyze_dependencies" in tool_names
        assert "format_for_external_agent" in tool_names
        assert "update_task_status" in tool_names
        
        # Check external agent tools
        assert "validate_external_agent" in tool_names
        assert "recommend_external_agent" in tool_names
        assert "parse_external_result" in tool_names
    
    @pytest.mark.asyncio
    async def test_agent_e_can_be_created(self):
        """Test that Agent E can be created as a StatelessAgent."""
        # Mock the AI loop and service
        mock_ai_loop = Mock(spec=StatelessAILoop)
        mock_ai_loop.process_message = Mock(return_value={
            'response': 'Hello, I am Eamonn the Executioner',
            'tool_calls': []
        })
        
        # Create agent config
        config = AgentConfig(
            name="Eamonn the Executioner",
            description="Task decomposition specialist",
            system_prompt="You are Eamonn the Executioner",
            model_name="openai/gpt-4",
            provider="openrouter",
            api_settings={"api_key": "test-key"},
            generation_params={},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
        
        # Create agent context
        context = AgentContext(agent_id="e", system_prompt="You are Eamonn")
        
        # Create the agent
        agent = StatelessAgent(config, context, mock_ai_loop)
        
        # Verify agent is created
        assert agent is not None
        assert agent.config.name == "Eamonn the Executioner"
        assert agent.context.agent_id == "e"
    
    def test_mailbox_tools_available(self):
        """Test that mailbox tools are available for Agent E."""
        from ai_whisperer.tools.tool_registration import register_tool_category
        
        # Register mailbox tools
        register_tool_category('mailbox')
        
        # Get tools by set
        mailbox_tools = self.tool_registry.get_tools_by_set('mailbox_tools')
        tool_names = [tool.name for tool in mailbox_tools]
        
        # Verify mailbox tools
        assert "send_mail" in tool_names
        assert "check_mail" in tool_names
        assert "reply_mail" in tool_names
    
    def test_agent_e_capabilities_in_config(self):
        """Test that Agent E's capabilities are defined in agents.yaml."""
        agents_yaml_path = Path(__file__).parent.parent.parent / "ai_whisperer" / "agents" / "config" / "agents.yaml"
        assert agents_yaml_path.exists()
        
        import yaml
        with open(agents_yaml_path) as f:
            agents_config = yaml.safe_load(f)
        
        # Get Agent E config
        agent_e_config = agents_config["agents"]["e"]
        
        # Verify capabilities
        capabilities = agent_e_config.get("capabilities", [])
        assert "plan_decomposition" in capabilities
        assert "dependency_resolution" in capabilities
        assert "technology_detection" in capabilities
        assert "external_agent_formatting" in capabilities
        assert "task_complexity_estimation" in capabilities
        assert "clarification_requests" in capabilities
        assert "progress_tracking" in capabilities
        
        # Verify configuration
        config = agent_e_config.get("configuration", {})
        assert "decomposition" in config
        assert "external_agents" in config
        assert "communication" in config
        
        # Check external agents configuration
        external_config = config["external_agents"]
        assert "claude_code" in external_config["supported"]
        assert "roocode" in external_config["supported"]
        assert "github_copilot" in external_config["supported"]