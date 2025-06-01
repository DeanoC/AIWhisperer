# Continuation Trigger Mechanisms in AI Systems

This document analyzes how AI systems determine when to continue processing without user input, focusing on the specific signals and mechanisms that trigger continuation.

## Types of Continuation Triggers

Based on the research, continuation in AI systems is typically triggered through three main mechanisms:

### 1. Explicit Tokens/Markers

Many systems use explicit tokens or markers in the model's output to signal continuation:

- **"CONTINUE"/"TERMINATE" Tokens**: Systems like LangGraph and ReAct agents map specific output tokens to continuation decisions
- **State Signals**: Words like "continue", "end", "stop", or "terminate" that indicate the model's intention
- **Completion Markers**: Phrases like "task completed" or "more steps needed" that signal task status

### 2. Response Structure Analysis

Some systems analyze the structure of responses to determine continuation:

- **JSON Schema Validation**: Checking if the response follows a predefined schema
- **Tool Call Detection**: Identifying when a response contains a tool call request
- **Completion Status Fields**: Dedicated fields in structured outputs that indicate completion status

### 3. Internal State Assessment

Advanced systems use internal state assessment:

- **Task Completion Heuristics**: Algorithms that determine if a task is complete based on output and context
- **Confidence Metrics**: Internal confidence scores that determine if more processing is needed
- **Goal Achievement Detection**: Checking if the stated goal has been achieved

## Implementation Examples by Platform

### OpenAI

OpenAI's function calling and tool use implementations rely on:

1. **Tool Call Detection**: The system detects when a model response includes a `tool_calls` field
2. **Response Structure**: The model returns a specific JSON structure for tool calls
3. **Execution Loop**: The system executes tools and continues until no more tool calls are detected

Example from OpenAI documentation:
```python
# Loop until the model doesn't call a function
while True:
    # Get response from model
    response = client.chat.completions.create(...)
    
    # Check if model wants to call a function
    if response.choices[0].finish_reason == "tool_calls":
        # Execute function and continue
        # ...
    else:
        # No more function calls, terminate loop
        break
```

### Claude (Anthropic)

Claude uses:

1. **Explicit Markers**: The model is trained to output "CONTINUE" or "TERMINATE" signals
2. **System Message Directives**: Instructions in the system message that define continuation criteria
3. **Interleaved Thinking**: The model reasons about tool call results before deciding next steps

Example from leaked Claude system prompt:
```
Reply TERMINATE if the task has been solved at full satisfaction. 
Otherwise, reply CONTINUE, or the reason why the task is not solved yet.
```

### GitHub Copilot (Agent Mode)

Copilot's agent mode uses:

1. **Task Completion Assessment**: The agent determines if the coding task is complete
2. **Multi-step Planning**: The agent creates and follows a plan, continuing until completion
3. **User Intent Fulfillment**: The agent checks if the user's stated intent has been fulfilled

### LangGraph/LangChain

LangGraph implements:

1. **State Transitions**: Mapping "continue" signals to tool nodes and "end" signals to termination
2. **Conditional Edges**: Graph structures that determine continuation based on state
3. **Node-based Orchestration**: Explicit flow control through graph structure

Example from LangGraph:
```python
def should_continue(state):
    # Check if the last message contains a continuation signal
    last_message = state["messages"][-1]["content"]
    if "CONTINUE" in last_message:
        return "tool_node"
    else:
        return "END"

graph = (
    StateGraph(MessagesState)
    .add_node("tool_node", call_tool)
    .add_conditional_edges(
        "tool_node",
        should_continue
    )
    .compile()
)
```

## Common Patterns Across Systems

Despite implementation differences, several common patterns emerge:

1. **Explicit Signaling**: Most systems rely on explicit signals in the model output
2. **Loop-based Orchestration**: Continuation is managed through execution loops
3. **State-based Decision Making**: Decisions are based on the current state of the conversation or task
4. **Tool Use as Continuation Driver**: Tool/function calling often drives continuation
5. **Termination Conditions**: Clear conditions for when to stop the continuation loop

## JSON-Compatible Implementation

For a JSON-based system like AIWhisperer, continuation can be implemented through:

1. **Status Field**: Include a dedicated field in the JSON response to indicate continuation status
2. **Next Action Field**: Specify the next action to take if continuation is needed
3. **Completion Assessment**: Logic to determine if the task is complete based on the response

Example JSON structure:
```json
{
  "response": "...",
  "status": "CONTINUE", // or "TERMINATE"
  "next_action": {
    "type": "tool_call",
    "tool": "search_web",
    "parameters": {
      "query": "..."
    }
  },
  "completion_percentage": 75
}
```

## Implementation Recommendations

Based on the analysis, here are recommendations for implementing continuation in AIWhisperer:

1. **Explicit Instruction**: Include instructions in the system prompt for the model to signal continuation
2. **Structured Output**: Require responses in a specific JSON format with continuation signals
3. **Loop-based Execution**: Implement an execution loop that continues until termination is signaled
4. **State Tracking**: Maintain state across iterations to provide context for continuation decisions
5. **Tool Integration**: Use tool calls as a natural driver for continuation
