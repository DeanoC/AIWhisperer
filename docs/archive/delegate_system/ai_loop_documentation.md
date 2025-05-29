# AI Loop Documentation

This document provides an overview and usage guide for the refactored AI loop implementation in AIWhisperer.

## Overview

The AI loop, implemented in [`ai_whisperer/ai_loop/ai_loopy.py`](ai_whisperer/ai_loop/ai_loopy.py), is the core component responsible for managing the interaction between the user, the AI service, and the system's tools and delegates. Its refactored design focuses on modularity, testability, and clear separation of concerns, allowing for easier integration with different AI services and configurations.

The loop operates by maintaining a session state, processing user messages, interacting with the AI service to generate responses and tool calls, and executing tool calls through the `DelegateManager`.

## Instantiation and Usage

The `AILoop` class is designed to be instantiated with concrete implementations of its dependencies, specifically an `AIService` and an `AIConfig`. In the main application entry point, [`ai_whisperer/interactive_ai.py`](ai_whisperer/interactive_ai.py), the `AILoop` is instantiated with a real `OpenRouterAIService` and an `AIConfig` derived from the main application `Config`.

```python
# Example instantiation (from interactive_ai.py)
from ai_whisperer.ai_loop.ai_loopy import AILoop
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.config import Config
from ai_whisperer.context_manager import ContextManager
from ai_whisperer.delegates.delegate_manager import DelegateManager
from ai_whisperer.tools.tool_registry import ToolRegistry

# Assuming config, context_manager, and delegate_manager are initialized
config: Config = ...
context_manager: ContextManager = ...
delegate_manager: DelegateManager = ...
tool_registry: ToolRegistry = ...

# Create AIService instance
ai_service = OpenRouterAIService(config.ai_service_config)

# Create AIConfig from main Config
ai_loop_config = config.ai_loop_config

# Instantiate AILoop
ai_loop = AILoop(
    ai_service=ai_service,
    context_manager=context_manager,
    delegate_manager=delegate_manager,
    tool_registry=tool_registry,
    config=ai_loop_config
)
```

Once instantiated, the AI loop can be controlled using its key methods.

## Key Methods

The `AILoop` class provides the following key methods for managing the AI session:

* `start_session()`: Initializes a new AI session. This typically involves setting up the initial context and preparing the loop to receive user input.
* `stop_session()`: Terminates the current AI session gracefully.
* `pause_session()`: Pauses the processing of the current AI session. This might be used to temporarily halt interaction.
* `resume_session()`: Resumes a previously paused AI session.
* `send_user_message(message: str)`: Sends a user message to the AI loop for processing. This is the primary method for user interaction. The loop will then interact with the `AIService` and potentially execute tool calls based on the message.

## Interaction with Dependencies

The `AILoop` interacts with several key dependencies:

* **`AIService` (specifically `OpenRouterAIService`)**: The loop uses the provided `AIService` instance to send prompts and receive responses from the AI model. The `OpenRouterAIService` is a concrete implementation that interfaces with the OpenRouter API.
* **`ContextManager`**: The loop utilizes the `ContextManager` to manage the conversation history and other contextual information relevant to the AI session.
* **`DelegateManager`**: When the AI service returns tool calls, the `AILoop` uses the `DelegateManager` to execute these calls. The `DelegateManager` is responsible for routing the tool calls to the appropriate handlers.
* **`ToolRegistry`**: The `AILoop` uses the `ToolRegistry` to access information about available tools, which is necessary for processing tool calls from the AI.

## Handling Tool Calls and Results

A crucial part of the AI loop's functionality is the handling of tool calls. When the `AIService` response includes tool calls, the `AILoop` identifies these calls and passes them to the `DelegateManager` for execution. The results of the tool calls are then incorporated back into the conversation context, allowing the AI to use the tool output in subsequent responses.

## `AIConfig`

The `AIConfig` is a configuration object that holds settings specific to the AI loop's behavior. This configuration is typically created from the main application `Config` object, ensuring that the AI loop's settings are consistent with the overall application configuration. It may include settings related to session management, logging, or other loop-specific parameters.

## Integration Considerations

When integrating the AI loop into different parts of the application, it's important to:

* Ensure that valid instances of `AIService`, `ContextManager`, `DelegateManager`, and `ToolRegistry` are provided during `AILoop` instantiation.
* Properly handle the state transitions of the AI loop using the `start_session`, `stop_session`, `pause_session`, and `resume_session` methods.
* Utilize the `send_user_message` method to interact with the AI loop and process user input.
* Consider how the output from the AI loop (responses, tool call results) will be handled and presented to the user or other parts of the system.
