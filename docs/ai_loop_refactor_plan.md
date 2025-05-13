# AI Loop Refactor Plan

## Purpose

This document outlines the plan to refactor the core AI interaction loop currently residing in `src/ai_whisperer/agent_handlers/code_generation.py` into a separate, reusable component and integrate it with the new `ContextManager`.

## Identified AI Loop Logic

The core AI interaction loop logic is primarily contained within the `_run_ai_interaction_loop` function in `src/ai_whisperer/agent_handlers/code_generation.py` (approximately lines 178-396). This includes:

- Initial AI call with the prompt.
- Processing AI responses, including tool calls and content.
- Executing tools via the `ToolRegistry`.
- Managing the conversation history (`conversation_history` list).
- Handling consecutive tool calls and potential infinite loops.
- Storing conversation turns using the `StateManager`.
- Determining the loop termination condition (receiving content or stop signal).

## Encapsulation Approach

The AI loop logic will be extracted into a new module, `src/ai_whisperer/ai_loop.py`. Within this module, a function or class will encapsulate the loop. A class, potentially named `AILoop`, is preferred as it can manage state related to the interaction if needed in the future (though the initial refactor might use a function). For this plan, we will assume a function-based approach within the new module for simplicity, named `run_ai_loop`.

## Integration with ContextManager

The refactored AI loop component (`run_ai_loop` function) will receive an instance of the `ContextManager` as a parameter. It will use this instance to:

- Add new messages (user prompts, AI responses, tool outputs) to the conversation history using the `add_message` method.
- Retrieve the conversation history to pass to the AI model using the `get_history` method.

The `ContextManager` will be instantiated in the calling code (e.g., within the `handle_code_generation` function) and passed to `run_ai_loop`.

## Necessary Code Modifications in `code_generation.py`

The following modifications will be made to `src/ai_whisperer/agent_handlers/code_generation.py`:

1. **Import the new AI loop component:**

    ```python
    from src.ai_whisperer.ai_loop import run_ai_loop
    from src.ai_whisperer.context_management import ContextManager # Import ContextManager
    ```

2. **Instantiate `ContextManager`:**
    - Within the `handle_code_generation` function, create an instance of `ContextManager`.
    - Initialize the `ContextManager` with the initial prompt.

3. **Replace `_run_ai_interaction_loop` content:**
    - Remove the existing logic within `_run_ai_interaction_loop`.
    - Call the new `run_ai_loop` function, passing the necessary parameters, including the `ContextManager` instance, the `ExecutionEngine` instance (or relevant parts like the AI service and tool registry), and the task definition.

4. **Update StateManager interaction:**
    - The `run_ai_loop` function will be responsible for adding messages to the `ContextManager`.
    - The interaction with the `StateManager` for persistence will need to be reviewed. It might be handled within `run_ai_loop` or remain in `handle_code_generation`, potentially serializing the `ContextManager`'s history to the StateManager. For the initial refactor, the `run_ai_loop` function will handle adding messages to the `ContextManager`, and the calling code (`handle_code_generation`) will be responsible for persisting the `ContextManager`'s state via the `StateManager` if necessary after the loop completes.

## Constraints Adhered To

- The plan is documented in Markdown format.
- The plan document is placed in the `docs` directory.
