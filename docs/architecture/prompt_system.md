# Prompt System Architecture

## Overview

The AIWhisperer prompt system provides a centralized, structured approach to managing AI prompts, with special integration for the agent system. Each agent has its own dedicated prompt that defines its personality, capabilities, and behavior.

## Core Components

### 1. PromptSystem

The central service for accessing prompts throughout the application.

**Key Features:**
- Lazy loading of prompt content
- Hierarchical prompt resolution
- Support for prompt overrides
- Integration with agent registry

**Usage Example:**
```python
prompt_system = PromptSystem(config)
# Get agent prompt
agent_prompt = prompt_system.get_formatted_prompt("agents", "alice_assistant")
# Get core system prompt
plan_prompt = prompt_system.get_formatted_prompt("core", "initial_plan")
```

### 2. Agent Prompt Integration

Each agent in the system has a corresponding prompt file that defines its behavior:

```text
prompts/
├── agents/                          # Agent-specific prompts
│   ├── alice_assistant.prompt.md    # Alice the Assistant
│   ├── agent_planner.prompt.md      # Patricia the Planner
│   ├── agent_tester.prompt.md       # Tessa the Tester
│   ├── code_generation.prompt.md    # Generic code generation
│   └── default.md                   # Default agent behavior
└── core/                           # Core system prompts
    ├── initial_plan.prompt.md
    ├── refine_requirements.prompt.md
    └── subtask_generator.prompt.md
```

### 3. Agent Configuration

Agents are configured in `ai_whisperer/agents/config/agents.yaml`:

```yaml
agents:
  - id: "A"
    name: "Alice the Assistant"
    prompt_file: "alice_assistant.prompt.md"
    color: "#9b59b6"  # Purple
    icon: "👩‍💻"
    # ... other config
```

When an agent is loaded, the system:
1. Reads the agent configuration
2. Uses PromptSystem to load the corresponding prompt file
3. Creates the agent with the loaded system prompt

## Prompt Resolution Hierarchy

The PromptResolver uses this order to find prompts:

1. **Project-specific overrides**: `{project_path}/prompts/agents/`
2. **Application defaults**: `{app_path}/prompts/agents/`
3. **Built-in fallbacks**: Hardcoded defaults if no file found

This allows projects to customize agent behavior by providing their own prompt files.

## Agent Prompt Structure

Agent prompts follow a consistent structure:

```markdown
You are [Agent Name], [role description].

## Core Capabilities
- [Capability 1]
- [Capability 2]

## Personality Traits
- [Trait 1]
- [Trait 2]

## Communication Style
[Description of how the agent should communicate]

## Constraints
- [Constraint 1]
- [Constraint 2]
```

Example from `alice_assistant.prompt.md`:
```markdown
You are Alice, an AI assistant specialized in software development...

## Core Capabilities
- Writing clean, maintainable code
- Debugging and troubleshooting
- Explaining technical concepts clearly
...
```

## Integration with Stateless Sessions

In the interactive server, prompts are loaded when agents are created:

```python
# In StatelessInteractiveSession
async def switch_agent(self, agent_id: str):
    agent_info = self.agent_registry.get_agent(agent_id)
    
    # Load agent prompt
    prompt_name = agent_info.prompt_file.replace('.md', '')
    system_prompt = self.prompt_system.get_formatted_prompt(
        "agents", prompt_name
    )
    
    # Create agent with loaded prompt
    await self._create_agent_internal(
        agent_id, 
        system_prompt
    )
```

## Prompt Customization

### Project-Level Overrides

Projects can customize agent behavior by creating override prompts:

```text
my_project/
└── prompts/
    └── agents/
        └── alice_assistant.prompt.md  # Overrides default Alice
```

### Dynamic Agent Creation

New agents can be added by:
1. Creating a prompt file in `prompts/agents/`
2. Adding an entry to `agents.yaml`
3. The agent becomes available in the UI

## Best Practices

### 1. Prompt Design
- Keep agent personalities consistent and distinct
- Include clear capabilities and constraints
- Use conversational, friendly language
- Avoid overly complex instructions

### 2. File Organization
- One prompt file per agent
- Use descriptive filenames
- Keep related prompts in the same category

### 3. Version Control
- Track prompt changes in git
- Document significant prompt updates
- Test prompt changes thoroughly

## Future Enhancements

### Planned Features
- **Prompt Templates**: Reusable prompt components
- **Dynamic Parameters**: Runtime prompt customization
- **Prompt Versioning**: Track and rollback prompt changes
- **A/B Testing**: Compare different prompt versions

### Under Consideration
- Multi-language prompt support
- Context-aware prompt selection
- Prompt performance metrics
- User-defined custom agents

## API Reference

### PromptSystem Methods

```python
class PromptSystem:
    def get_prompt(self, category: str, name: str) -> Prompt:
        """Get a Prompt object (lazy-loaded)"""
        
    def get_formatted_prompt(self, category: str, name: str, **kwargs) -> str:
        """Get formatted prompt content with parameter substitution"""
        
    def list_prompts(self, category: Optional[str] = None) -> List[Tuple[str, str]]:
        """List available prompts, optionally filtered by category"""
```

### Integration Points

- **Agent Creation**: `StatelessInteractiveSession._create_agent_internal()`
- **Agent Registry**: `AgentRegistry` loads agent configs
- **Prompt Loading**: `PromptSystem.get_formatted_prompt()`

## Summary

The prompt system is a critical component that defines agent behavior in AIWhisperer. By providing a structured, hierarchical system with easy customization options, it enables both consistent default behavior and flexible project-specific modifications. The tight integration with the agent system ensures that each AI agent has a well-defined personality and capabilities.