# ContextManager Design

## Purpose

The `ContextManager` class will be responsible for managing the conversation history between the AI and the user/system within the AI Whisperer application. This will centralize the handling of message storage and retrieval, making the AI loop more reusable and maintainable.

## Current Approach (in `code_generation.py`)

Currently, message history is managed within the `_run_ai_interaction_loop` function in `src/ai_whisperer/agent_handlers/code_generation.py`. A simple Python list (`conversation_history`) is used to store message dictionaries. Each turn of the conversation is also stored using the `StateManager`.

## ContextManager Class Design

### Structure

The `ContextManager` class will hold the conversation history internally. A list of message objects or dictionaries is suitable for this purpose.

```python
class ContextManager:
    def __init__(self):
        self._history = [] # Internal storage for messages
```

### Methods

- `add_message(message: dict)`:
  - Adds a new message to the conversation history.
  - `message`: A dictionary representing the message (e.g., `{"role": "user", "content": "..."}`).
  - This method will append the new message to the internal `_history` list.

- `get_history(limit: int = None) -> list[dict]`:
  - Retrieves the conversation history.
  - `limit`: An optional integer to limit the number of recent messages returned. If `None`, the entire history is returned.
  - Returns a list of message dictionaries, ordered from oldest to newest. If a limit is provided, it returns the last `limit` messages.

- `clear_history()`:
  - Clears the entire conversation history.
  - This method will reset the internal `_history` list to empty.

## Interaction with StateManager

The `StateManager` currently stores individual conversation turns. With the introduction of `ContextManager`, the `StateManager` could potentially hold an instance of the `ContextManager` for each active task. Alternatively, the `ContextManager` instance could be created and managed within the execution engine or agent handler and passed to the `StateManager` for persistence if needed.

A likely interaction pattern is that the `ExecutionEngine` or the specific agent handler (like `code_generation`) will instantiate a `ContextManager` for each task. Messages will be added to this `ContextManager` instance. When persistence is required, the `StateManager` could be updated with the current state of the `ContextManager`'s history.

Further refinement of the interaction between `StateManager` and `ContextManager` will be detailed in subsequent design or implementation steps.

## Constraints Adhered To

- The design is documented in Markdown format.
- The design document is placed in the `docs` directory.
- The design focuses solely on managing message history for AI interactions.
