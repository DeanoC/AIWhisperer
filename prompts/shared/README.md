# Shared Prompt Components

This directory contains shared prompt components that are automatically injected into all agent prompts by the enhanced PromptSystem.

## Overview

The shared prompt system allows system-wide capabilities to be maintained in one place and automatically included in all agent prompts. This ensures consistency across agents and makes it easy to add new system-wide features.

## Available Components

### core.md
Core system instructions that apply to all agents. This is always enabled and cannot be disabled.

### continuation_protocol.md
Defines the protocol for multi-step task continuation. Enables agents to autonomously complete complex tasks without user intervention.

### mailbox_protocol.md
Defines the inter-agent communication protocol using the mailbox system. Enables agents to collaborate on tasks.

### tool_guidelines.md
Best practices and guidelines for using tools effectively. Helps agents make better decisions about tool usage.

### output_format.md
Standards for generating structured outputs (JSON, Markdown, etc.). Ensures consistent formatting across all agents.

## How It Works

1. When an agent is initialized, the PromptSystem loads all shared components from this directory
2. Components are injected into the agent's prompt in a consistent order
3. Features can be enabled/disabled at runtime using the PromptSystem API
4. The final agent prompt = base agent prompt + enabled shared components + tool instructions

## Adding New Shared Components

To add a new shared component:

1. Create a new `.md` file in this directory
2. Name it descriptively (e.g., `feature_name.md`)
3. Write clear instructions that can be understood by any agent
4. The component will be automatically discovered and loadable
5. Enable it using `prompt_system.enable_feature('feature_name')`

## Component Guidelines

When writing shared components:

- Be clear and unambiguous
- Use examples to illustrate concepts
- Define any special formats or structures
- Explain when and why to use the feature
- Include error handling guidance
- Keep components focused on a single capability

## Feature Management

```python
# Enable a feature for all agents
prompt_system.enable_feature('continuation_protocol')

# Disable a feature (except 'core')
prompt_system.disable_feature('mailbox_protocol')

# Check enabled features
enabled = prompt_system.get_enabled_features()
```

## Integration with Agents

Agents automatically receive shared components when their prompts are formatted:

```python
# This includes shared components by default
prompt = prompt_system.get_formatted_prompt(
    category='agents',
    name='alice_assistant',
    include_tools=True,
    include_shared=True  # Default is True
)
```

## Notes

- The 'core' component is always included and cannot be disabled
- Components are loaded once at PromptSystem initialization
- Changes to component files require restarting the application
- Components are injected in alphabetical order for consistency
- Special handling exists for 'continuation_protocol' and 'mailbox_protocol'