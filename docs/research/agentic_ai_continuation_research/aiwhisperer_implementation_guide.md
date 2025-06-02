# AIWhisperer Continuation Implementation Guide

This guide provides concrete implementation recommendations for adding automatic continuation capabilities to AIWhisperer, based on patterns observed in leading AI systems.

## JSON Schema for Continuation Control

Since AIWhisperer uses JSON for plans and subtasks, here's a recommended schema for implementing continuation:

```json
{
  "response": "The content of the AI's response",
  "continuation": {
    "status": "CONTINUE",  // or "TERMINATE"
    "reason": "Need to perform additional research",  // Optional explanation
    "confidence": 0.95,  // Optional confidence score
    "next_action": {
      "type": "tool_call",  // or "reasoning", "planning", etc.
      "tool": "search_web",  // If type is tool_call
      "parameters": {
        "query": "example search query"
      }
    }
  },
  "completion_percentage": 75  // Optional progress indicator
}
```

## System Prompt Instructions

Add these instructions to your system prompt to encourage the model to signal continuation:

```
When responding, you must include a "continuation" field in your JSON response with a "status" of either "CONTINUE" or "TERMINATE".

- Use "CONTINUE" when:
  - You need to use additional tools to complete the task
  - You need more information to provide a complete answer
  - The task requires multiple steps and you haven't finished all steps
  - You're uncertain and need to verify information

- Use "TERMINATE" when:
  - The task is fully complete
  - You've provided a comprehensive answer
  - No further actions are needed
  - The user's request has been fully addressed

When using "CONTINUE", include a "next_action" field specifying what tool or action should be taken next.
```

## Implementation Approach

### 1. Execution Loop

Implement a main execution loop that continues until termination is signaled:

```python
def run_aiwhisperer_task(task, context=None):
    context = context or {}
    
    while True:
        # Get response from model
        response_json = get_model_response(task, context)
        
        # Extract continuation status
        continuation = response_json.get("continuation", {})
        status = continuation.get("status", "TERMINATE")
        
        # Add response to context
        context["previous_responses"] = context.get("previous_responses", []) + [response_json]
        
        # Check if we should continue
        if status == "TERMINATE":
            return response_json
        
        # Handle continuation
        next_action = continuation.get("next_action", {})
        action_type = next_action.get("type")
        
        if action_type == "tool_call":
            # Execute tool and add result to context
            tool_name = next_action.get("tool")
            parameters = next_action.get("parameters", {})
            tool_result = execute_tool(tool_name, parameters)
            context["tool_results"] = context.get("tool_results", []) + [{
                "tool": tool_name,
                "parameters": parameters,
                "result": tool_result
            }]
        
        # Continue loop with updated context
```

### 2. Response Parsing

Implement robust parsing of the continuation signals:

```python
def extract_continuation_status(response_text):
    """Extract continuation status from unstructured text if JSON parsing fails"""
    # Default to TERMINATE if unclear
    status = "TERMINATE"
    
    # Check for explicit continuation signals
    if re.search(r'\b(CONTINUE|continue|need\s+more|next\s+step|not\s+finished)\b', response_text):
        status = "CONTINUE"
    
    # Check for explicit termination signals
    if re.search(r'\b(TERMINATE|terminate|complete|finished|done|task\s+completed)\b', response_text):
        status = "TERMINATE"
        
    return status
```

### 3. Fallback Mechanism

Implement a fallback for when the model doesn't follow the JSON structure:

```python
def get_model_response(task, context):
    """Get response from model with fallback for non-JSON responses"""
    response = call_model(task, context)
    
    try:
        # Try to parse as JSON
        response_json = json.loads(response)
        
        # Ensure continuation field exists
        if "continuation" not in response_json:
            status = extract_continuation_status(response)
            response_json["continuation"] = {"status": status}
            
        return response_json
    except json.JSONDecodeError:
        # Fallback for non-JSON responses
        status = extract_continuation_status(response)
        return {
            "response": response,
            "continuation": {"status": status}
        }
```

## Best Practices

1. **Clear Instructions**: Provide explicit instructions in the system prompt about continuation signaling
2. **Structured Output**: Enforce JSON structure with continuation fields
3. **Fallback Mechanisms**: Handle cases where the model doesn't follow the structure
4. **Context Management**: Maintain comprehensive context across iterations
5. **Tool Result Incorporation**: Clearly include tool results in the context for the next iteration
6. **Timeout Mechanism**: Implement a maximum iteration count to prevent infinite loops
7. **Progress Tracking**: Track and report progress through the continuation chain

## Example Implementation

Here's a complete example showing how to implement continuation in AIWhisperer:

```python
def run_aiwhisperer_task(task, max_iterations=10):
    """Run an AIWhisperer task with automatic continuation"""
    context = {
        "task_history": [],
        "tool_results": []
    }
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        
        # Prepare prompt with continuation instructions
        prompt = {
            "task": task,
            "context": context,
            "instructions": "Respond in JSON format with a 'continuation' field indicating 'CONTINUE' or 'TERMINATE'."
        }
        
        # Get model response
        response = call_model(prompt)
        response_json = parse_response(response)
        
        # Add to task history
        context["task_history"].append(response_json)
        
        # Check continuation status
        continuation = response_json.get("continuation", {})
        status = continuation.get("status", "TERMINATE")
        
        if status == "TERMINATE":
            return {
                "final_response": response_json,
                "iterations": iteration,
                "context": context
            }
        
        # Handle continuation
        next_action = continuation.get("next_action", {})
        if next_action.get("type") == "tool_call":
            tool_result = execute_tool(
                next_action.get("tool"),
                next_action.get("parameters", {})
            )
            context["tool_results"].append({
                "tool": next_action.get("tool"),
                "parameters": next_action.get("parameters", {}),
                "result": tool_result
            })
    
    # Reached max iterations
    return {
        "final_response": response_json,
        "iterations": iteration,
        "context": context,
        "status": "MAX_ITERATIONS_REACHED"
    }
```

This implementation provides a robust framework for handling continuation in AIWhisperer, following patterns observed in leading AI systems while maintaining compatibility with JSON-based workflows.
