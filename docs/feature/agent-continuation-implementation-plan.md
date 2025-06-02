# Agent Continuation System Implementation Plan

## Overview

This document outlines the implementation plan for adding automatic continuation capabilities to AIWhisperer, allowing agents to perform multi-step operations without user nudging. Based on research of leading AI systems (Claude, GitHub Copilot, Manus.im), we'll implement a hybrid approach leveraging both API-level capabilities and system-level orchestration.

The implementation will integrate with the existing PromptSystem to add shared system prompt components that can be injected into all agents at runtime.

## Goals

1. **Eliminate User Nudging**: Agents should complete multi-step tasks autonomously
2. **Maintain Transparency**: Users should see progress during long operations
3. **Preserve Agent Autonomy**: Let AI decide when to continue vs system-forcing continuation
4. **Support All Models**: Work with both single-tool (Gemini) and multi-tool (GPT-4) models
5. **Integrate Seamlessly**: Build on existing stateless architecture and PromptSystem
6. **Shared System Capabilities**: Extend PromptSystem to support shared prompt injection

## Architecture Design

### Core Components

1. **Enhanced PromptSystem** (`ai_whisperer/prompt_system.py`)
   - Add shared prompt component management
   - Support runtime injection of system-wide features
   - Maintain backward compatibility

2. **Continuation Strategy Module** (`ai_whisperer/agents/continuation_strategy.py`)
   - Handles continuation detection and execution
   - Manages iteration limits and safety checks
   - Tracks progress and state across iterations

3. **Enhanced Stateless Session Manager**
   - Already has basic continuation for tool calls
   - Extend with sophisticated continuation patterns
   - Add progress tracking and user notifications

4. **Shared Prompt Components** (`prompts/shared/`)
   - Continuation protocol instructions
   - Mailbox communication protocol
   - Core system instructions
   - Tool usage guidelines

5. **Progress Notification System**
   - WebSocket notifications for continuation progress
   - Status updates during long operations
   - Iteration count and completion percentage

### Prompt System Architecture

```
Final Agent Prompt = Agent Base Prompt + Shared System Components

Shared System Components:
├── Core Instructions (always included)
├── Continuation Protocol (if enabled)
├── Mailbox Protocol (if enabled) 
├── Tool Usage Guidelines (if tools available)
└── Output Format Requirements (JSON schema, etc.)
```

### Continuation Flow

```
User Message → Agent Processing → Response with Continuation Signal
                                         ↓
                                  Check Continuation Status
                                         ↓
                        CONTINUE ←───────┴───────→ TERMINATE
                           ↓                           ↓
                    Execute Next Action          Return Final Response
                           ↓
                    Update Context/State
                           ↓
                    Send Progress Update
                           ↓
                    Loop (with limits)
```

## Implementation Phases

### Phase 1: Enhance PromptSystem for Shared Components (Week 1, Days 1-2)

1. Extend PromptSystem class with shared component support
2. Create shared prompt loading mechanism
3. Implement prompt composition with injection points
4. Add configuration for enabling/disabling features
5. Create shared prompt files structure
6. Write tests for enhanced prompt system

### Phase 2: Core Continuation Infrastructure (Week 1, Days 3-5)

1. Create continuation strategy module
2. Define continuation JSON schema
3. Implement continuation detection logic
4. Add iteration limits and safety checks
5. Create unit tests for continuation logic

### Phase 3: Agent Integration (Week 1-2)

1. Update agent initialization to use enhanced prompts
2. Modify stateless session manager for continuation
3. Implement progress tracking
4. Add WebSocket notifications for continuation status
5. Create integration tests

### Phase 4: Model-Specific Optimizations (Week 2)

1. Optimize for single-tool vs multi-tool models
2. Add model-specific continuation patterns
3. Implement intelligent batching for multi-tool models
4. Add performance monitoring

### Phase 5: Advanced Features (Week 2-3)

1. Implement continuation persistence across sessions
2. Add continuation analytics and monitoring
3. Create continuation templates for common patterns
4. Add user controls for continuation behavior

## Technical Implementation Details

### Enhanced PromptSystem

```python
# prompt_system.py additions
class PromptSystem:
    def __init__(self, prompt_config: PromptConfiguration, tool_registry: Optional['ToolRegistry'] = None):
        # ... existing init code ...
        self._shared_components = {}
        self._enabled_features = set(['core'])  # Core is always enabled
        self._load_shared_components()
    
    def _load_shared_components(self):
        """Load shared prompt components from prompts/shared/"""
        shared_dir = self._resolver._get_shared_prompts_dir()
        if shared_dir.exists():
            for component_file in shared_dir.glob("*.md"):
                component_name = component_file.stem
                try:
                    with open(component_file, 'r', encoding='utf-8') as f:
                        self._shared_components[component_name] = f.read()
                    logger.info(f"Loaded shared component: {component_name}")
                except Exception as e:
                    logger.error(f"Failed to load shared component {component_name}: {e}")
    
    def enable_feature(self, feature: str):
        """Enable a shared feature for all agents"""
        if feature in self._shared_components:
            self._enabled_features.add(feature)
            logger.info(f"Enabled feature: {feature}")
        else:
            logger.warning(f"Feature {feature} not found in shared components")
    
    def disable_feature(self, feature: str):
        """Disable a shared feature"""
        if feature != 'core':  # Can't disable core
            self._enabled_features.discard(feature)
            logger.info(f"Disabled feature: {feature}")
    
    def get_formatted_prompt(self, category: str, name: str, include_tools: bool = False, 
                           include_shared: bool = True, **kwargs) -> str:
        """
        Retrieves the processed and formatted content of a prompt, 
        including shared components and optionally tool instructions.
        """
        # Get base prompt content
        prompt = self.get_prompt(category, name)
        content_parts = [prompt.content]
        
        # Add shared components if requested (default: True)
        if include_shared:
            # Add enabled shared components
            for feature in sorted(self._enabled_features):  # Sort for consistent ordering
                if feature in self._shared_components:
                    content_parts.append(f"\n\n## {feature.upper()} INSTRUCTIONS\n{self._shared_components[feature]}")
            
            # Add continuation if enabled
            if 'continuation' in self._enabled_features:
                content_parts.append(f"\n\n## CONTINUATION PROTOCOL\n{self._shared_components.get('continuation_protocol', '')}")
            
            # Add mailbox if enabled
            if 'mailbox' in self._enabled_features:
                content_parts.append(f"\n\n## MAILBOX PROTOCOL\n{self._shared_components.get('mailbox_protocol', '')}")
        
        # Include tool instructions if requested and tool registry is available
        if include_tools and self._tool_registry:
            tool_instructions = self._tool_registry.get_all_ai_prompt_instructions()
            if tool_instructions:
                content_parts.append("\n\n## AVAILABLE TOOLS\n" + tool_instructions)
        
        # Combine all parts
        content = "\n".join(content_parts)
        
        # Handle template parameters
        if kwargs:
            import re
            for key, value in kwargs.items():
                pattern = r"{{{" + re.escape(key) + r"}}}"
                content = re.sub(pattern, lambda m: str(value), content)
        
        return content
```

### Shared Prompt Files Structure

```
prompts/
├── agents/                          # Agent-specific prompts
│   ├── alice_assistant.prompt.md
│   ├── agent_patricia.prompt.md
│   └── ...
└── shared/                          # Shared system components
    ├── core.md                      # Core instructions
    ├── continuation_protocol.md     # Continuation protocol
    ├── mailbox_protocol.md         # Mailbox communication
    ├── tool_guidelines.md          # Tool usage guidelines
    └── output_format.md            # Output format requirements
```

### Continuation Protocol Prompt

```markdown
# prompts/shared/continuation_protocol.md

When responding, you MUST include a "continuation" field in your response to indicate whether you need to perform additional actions.

### Continuation Decision Criteria

Use "CONTINUE" when:
- You need to use additional tools to complete the task
- The task requires multiple steps and you haven't finished all steps
- You need to verify or refine your work
- You're following a multi-step plan
- Tool execution results require further processing
- You're in the middle of a complex operation

Use "TERMINATE" when:
- The task is fully complete
- You've provided a comprehensive answer
- No further actions would improve the response
- You've reached a natural stopping point
- An error prevents further progress

### Response Format

Include the following in your response:
```json
{
  "response": "Your response text",
  "continuation": {
    "status": "CONTINUE" or "TERMINATE",
    "reason": "Brief explanation of why continuing or terminating",
    "next_action": {
      "type": "tool_call",
      "tool": "tool_name",
      "parameters": {}
    },
    "progress": {
      "current_step": 3,
      "total_steps": 5,
      "completion_percentage": 60
    }
  }
}
```

### Important Notes
- Always be explicit about continuation status
- Provide clear reasons for your decision
- Include progress information when possible
- Consider user experience - avoid unnecessary continuations
```

### Continuation Strategy Module

```python
# continuation_strategy.py
from typing import Optional, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

class ContinuationStrategy:
    """Manages continuation detection and execution for agents"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.max_iterations = config.get('max_iterations', 10)
        self.timeout = config.get('timeout', 300)  # 5 minutes
        self.require_explicit_signal = config.get('require_explicit_signal', True)
        self.continuation_patterns = config.get('patterns', [
            r'\bCONTINUE\b',
            r'"status":\s*"CONTINUE"',
            r'need.*more.*steps',
            r'not.*finished'
        ])
        self.termination_patterns = config.get('termination_patterns', [
            r'\bTERMINATE\b',
            r'"status":\s*"TERMINATE"',
            r'task.*completed',
            r'finished.*successfully'
        ])
    
    def should_continue(self, response: Dict[str, Any]) -> bool:
        """Determine if continuation is needed based on response"""
        # First check for explicit continuation field
        if 'continuation' in response:
            continuation = response['continuation']
            if isinstance(continuation, dict) and 'status' in continuation:
                should_continue = continuation['status'] == 'CONTINUE'
                reason = continuation.get('reason', 'No reason provided')
                logger.info(f"Explicit continuation signal: {should_continue}, reason: {reason}")
                return should_continue
        
        # If no explicit signal and we require it, default to terminate
        if self.require_explicit_signal:
            logger.info("No explicit continuation signal found, defaulting to TERMINATE")
            return False
        
        # Fallback to pattern matching
        response_text = str(response.get('response', ''))
        
        # Check termination patterns first (they take precedence)
        for pattern in self.termination_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                logger.info(f"Found termination pattern: {pattern}")
                return False
        
        # Check continuation patterns
        for pattern in self.continuation_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                logger.info(f"Found continuation pattern: {pattern}")
                return True
        
        # Default to terminate if no patterns match
        logger.info("No continuation patterns found, defaulting to TERMINATE")
        return False
    
    def extract_next_action(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract the next action from response"""
        if 'continuation' in response:
            continuation = response['continuation']
            if isinstance(continuation, dict) and 'next_action' in continuation:
                return continuation['next_action']
        
        # Check if there are pending tool calls
        if 'tool_calls' in response and response['tool_calls']:
            # Convert tool calls to next action format
            first_tool = response['tool_calls'][0]
            return {
                'type': 'tool_call',
                'tool': first_tool.get('function', {}).get('name'),
                'parameters': first_tool.get('function', {}).get('arguments', {})
            }
        
        return None
    
    def update_context(self, context: Dict[str, Any], response: Dict[str, Any], 
                      tool_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update context with new information from response and tool results"""
        # Initialize continuation history if not present
        if 'continuation_history' not in context:
            context['continuation_history'] = []
        
        # Add current iteration
        iteration_info = {
            'timestamp': time.time(),
            'response_summary': response.get('response', '')[:200] + '...' if len(response.get('response', '')) > 200 else response.get('response', ''),
            'continuation_status': response.get('continuation', {}).get('status', 'UNKNOWN'),
            'tool_calls': len(response.get('tool_calls', [])),
        }
        
        if tool_results:
            iteration_info['tool_results'] = tool_results
        
        context['continuation_history'].append(iteration_info)
        
        # Update progress information
        if 'continuation' in response and 'progress' in response['continuation']:
            context['progress'] = response['continuation']['progress']
        
        return context
    
    def get_progress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get current progress information"""
        return context.get('progress', {
            'current_step': len(context.get('continuation_history', [])),
            'total_steps': None,
            'completion_percentage': None
        })
```

### Integration with StatelessSessionManager

```python
# Modifications to stateless_session_manager.py

async def _should_continue_after_tools(self, result: dict, original_message: str) -> bool:
    """
    Enhanced continuation detection using ContinuationStrategy
    """
    # Check if agent has continuation strategy
    if self.active_agent and self.active_agent in self.agents:
        agent = self.agents[self.active_agent]
        if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
            return agent.continuation_strategy.should_continue(result)
    
    # Fallback to existing logic
    return await self._existing_continuation_logic(result, original_message)

async def send_user_message(self, message: str, is_continuation: bool = False) -> dict:
    """Enhanced with continuation progress tracking"""
    # ... existing code ...
    
    # If continuing, send progress notification
    if is_continuation and self.active_agent in self.agents:
        agent = self.agents[self.active_agent]
        if hasattr(agent, 'continuation_strategy'):
            progress = agent.continuation_strategy.get_progress(agent.context._context)
            await self._send_progress_notification(progress)
    
    # ... rest of existing code ...
```

## Testing Strategy

### Unit Tests
- PromptSystem shared component loading
- Continuation strategy detection logic
- Context update mechanisms
- Progress calculation
- Safety limits (iteration count, timeout)

### Integration Tests
- End-to-end continuation flows
- Shared prompt injection across agents
- WebSocket notification delivery
- Multi-agent continuation scenarios
- Error recovery during continuation

### Performance Tests
- Prompt composition overhead
- Continuation with large contexts
- Multiple concurrent continuations
- Memory usage during long operations

## Implementation Checklist

### Phase 1: Enhanced PromptSystem
- [ ] Add `_shared_components` dictionary to PromptSystem
- [ ] Implement `_load_shared_components()` method
- [ ] Add `enable_feature()` and `disable_feature()` methods
- [ ] Extend `get_formatted_prompt()` with shared component injection
- [ ] Create `prompts/shared/` directory structure
- [ ] Write shared prompt files (core.md, continuation_protocol.md, etc.)
- [ ] Add unit tests for shared component loading
- [ ] Add integration tests for prompt composition
- [ ] Update documentation for shared prompts

### Phase 2: Continuation Infrastructure
- [ ] Create `continuation_strategy.py` module
- [ ] Implement `ContinuationStrategy` class
- [ ] Add continuation detection logic
- [ ] Implement context update mechanism
- [ ] Add progress tracking
- [ ] Create continuation JSON schema
- [ ] Write unit tests for continuation logic
- [ ] Add safety limits (iteration, timeout)

### Phase 3: Agent Integration
- [ ] Update `StatelessAgent` to support continuation strategy
- [ ] Modify agent initialization in session manager
- [ ] Enable continuation in PromptSystem by default
- [ ] Update `_should_continue_after_tools()` method
- [ ] Add progress notification support
- [ ] Create integration tests
- [ ] Test with multiple agents

### Phase 4: Model Optimizations
- [ ] Add model-specific continuation configurations
- [ ] Optimize for single-tool models (Gemini)
- [ ] Optimize for multi-tool models (GPT-4)
- [ ] Add performance monitoring
- [ ] Create model-specific tests

### Phase 5: Advanced Features
- [ ] Add continuation persistence
- [ ] Implement analytics/monitoring
- [ ] Create continuation templates
- [ ] Add user preference controls
- [ ] Write comprehensive documentation
- [ ] Create example use cases

## Success Metrics

1. **User Experience**
   - 90% reduction in user nudging for multi-step tasks
   - Clear progress visibility during operations
   - Smooth handling of long-running tasks

2. **Technical Metrics**
   - <100ms overhead per continuation decision
   - Successful completion of 95% of continuation chains
   - Proper termination within iteration limits
   - <10ms overhead for shared prompt composition

3. **Agent Effectiveness**
   - Agents complete complex tasks autonomously
   - Natural conversation flow maintained
   - Appropriate use of continuation vs termination
   - Consistent behavior across all agents

## Risk Mitigation

1. **Infinite Loops**: Hard limits on iterations and timeouts
2. **Context Explosion**: Smart context pruning between iterations
3. **User Confusion**: Clear progress indicators and status updates
4. **Model Failures**: Fallback to termination on errors
5. **Resource Usage**: Monitor and limit resource consumption
6. **Prompt Conflicts**: Careful ordering of shared components

## Benefits

1. **Maintainability**: System-wide features updated in one place
2. **Consistency**: All agents behave consistently for shared features
3. **Flexibility**: Easy to add new system-wide capabilities
4. **Testing**: Shared components tested independently
5. **Configuration**: Feature toggles without code changes
6. **Extensibility**: New features added without touching agent prompts

## Timeline

- Week 1, Days 1-2: Enhanced PromptSystem implementation
- Week 1, Days 3-5: Core continuation infrastructure
- Week 2: Integration and model optimizations
- Week 3: Testing, refinement, and documentation
- Week 4: Deployment and monitoring

## Dependencies

- Existing PromptSystem and configuration
- Stateless session manager and agent system
- WebSocket infrastructure for notifications
- JSON schema validation
- Agent registry and factory

## Success Criteria

The implementation will be considered successful when:
1. Shared prompts are seamlessly injected into all agents
2. Agents can complete multi-step tasks without user intervention
3. Users have visibility into continuation progress
4. The system gracefully handles edge cases and errors
5. Performance remains acceptable under load
6. New system-wide features can be added without updating individual agents
7. The feature integrates seamlessly with existing architecture