# API vs System-Level Continuation in AI Frameworks

This document analyzes whether continuation (handling multiple tools/actions without user interaction) is implemented at the API level or system level in major AI frameworks and products.

## OpenAI API

### Chat Completions API

The Chat Completions API provides some native support for continuation through:

1. **Function Calling**: The API allows models to determine when and how to call functions, but requires the system to:
   - Define the functions/tools
   - Execute the function when called
   - Return the results back to the API
   - Continue the conversation

2. **Tool Choice Parameter**: The API provides a `tool_choice` parameter that can be set to:
   - `"auto"`: Let the model decide when to use tools
   - `"required"`: Force the model to use a specific tool
   - `"none"`: Prevent tool usage

However, the actual orchestration of multi-step flows requires system-level implementation:
- The system must handle the execution loop
- The system must maintain conversation state
- The system must decide when to continue or terminate the flow

### Assistants API

The Assistants API provides more native support for continuation:

1. **Stateful Conversations**: The API maintains conversation threads
2. **Built-in Tool Execution**: For certain tools (like code interpreter)
3. **Multi-Assistant Orchestration**: Ability to use multiple assistants in one thread

From documentation: "The Assistants API is a stateful evolution of our Chat Completions API meant to simplify the creation of assistant-like experiences."

However, complex multi-agent orchestration still requires system-level implementation:
- The system must coordinate between multiple assistants
- The system must handle complex workflows beyond simple tool usage

## Gemini API

Gemini API (especially 2.5 series) provides native support for continuation through:

1. **Internal "Thinking Process"**: Models use an internal reasoning process that improves multi-step planning
2. **Reasoning Toggle**: Some models support a reasoning toggle via system prompt
3. **Flash Thinking Mode**: Provides advanced reasoning capabilities

From documentation: "Gemini 2.5 models are now thinking models, capable of reasoning before responding, resulting in dramatically improved performance."

However, complex orchestration still requires system-level implementation:
- Multi-step agents with Gemini often use frameworks like LangGraph
- The system must handle the execution loop and state management

## OpenRouter

OpenRouter provides a unified API gateway to access multiple models but doesn't add continuation capabilities beyond what the underlying models provide:

1. **Model-Dependent**: Continuation capabilities depend on the specific model being accessed
2. **Standardized Interface**: Provides a consistent interface across models, simplifying system-level orchestration

## System-Level Implementation in Products

### GitHub Copilot

GitHub Copilot implements continuation at the system level:

1. **Agentic Coding Flow**: "Copilot autonomously invokes multiple tools to plan and implement the code"
2. **Context Management**: The system maintains context across multiple interactions
3. **Integration with Claude**: When using Claude models, the system handles the orchestration

### Claude

Claude implements continuation primarily at the system level:

1. **Stateful Conversations**: The system maintains conversation state
2. **Tool Usage Orchestration**: The system handles tool execution and result incorporation
3. **Multi-Step Reasoning**: While the model has reasoning capabilities, the system orchestrates complex workflows

### Manus.im

Manus.im implements continuation at the system level:

1. **Sandbox Environment**: "Manus Sandbox is a container-based environment that provides a secure, isolated space for AI agents to interact"
2. **Tool Orchestration**: The system handles tool execution and result incorporation
3. **State Management**: The system maintains state across multiple interactions

## Conclusion

While modern AI APIs provide some native support for continuation through features like function calling, internal thinking processes, and stateful conversations, complex multi-step flows and tool orchestration typically require system-level implementation.

The distinction can be summarized as:

**API Level**:
- Function/tool calling capabilities
- Internal reasoning processes
- Basic stateful conversation (Assistants API)
- Simple tool execution (for built-in tools)

**System Level**:
- Complex workflow orchestration
- Multi-agent coordination
- Advanced state management
- Error handling and recovery
- Tool execution and result incorporation
- Decision logic for continuation

Products like GitHub Copilot, Claude, and Manus.im build upon the API-level capabilities but implement significant system-level orchestration to achieve seamless multi-step flows without requiring user intervention at each step.
