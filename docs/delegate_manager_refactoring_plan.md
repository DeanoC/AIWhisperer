# DelegateManager Refactoring Plan

## 1. Introduction and Goals

This document outlines a refactoring plan for the `DelegateManager` class within the AIWhisperer project. The primary goal is to enhance its structure and usage patterns to facilitate easier, more robust, and type-safe integration across multiple modules, including future CLI commands and other components.

This plan is based on the findings documented in the [`delegate_manager_analysis.md`](delegate_manager_analysis.md).

The key objectives of this refactoring are:

* **Centralized Management:** Establish a clear pattern for instantiating and accessing a shared `DelegateManager` instance.
* **Standardization:** Introduce standardized, discoverable types for events and controls, moving away from raw strings.
* **Type Safety:** Implement typed payloads for event data to improve clarity, reduce errors, and enhance developer experience.
* **Clear Integration Patterns:** Define how new modules, CLI commands, and other components should interact with the `DelegateManager`.
* **Improved Discoverability:** Make it easier to identify available events and controls.

## 2. Background

The `DelegateManager` currently provides a thread-safe publish/subscribe mechanism for notification and control events, primarily used by `ExecutionEngine` and `AILoop`. The existing implementation, while functional, presents challenges for broader integration due to:

* Decentralized instantiation (e.g., `ExecutionEngine` creates its own instance).
* Use of raw strings for `event_type` and `control_type`, which can lead to typos and makes discovery difficult.
* `event_data` being `typing.Any`, lacking a clear contract for data structures.

The aforementioned [`delegate_manager_analysis.md`](delegate_manager_analysis.md) provides a detailed review of these aspects.

## 3. Proposed Refactoring

To address these points and achieve the stated goals, the following changes are proposed:

### 3.1. Centralized `DelegateManager` Instantiation and Access

Instead of components creating their own `DelegateManager` instances, a single, shared instance will be created at a higher level in the application (e.g., within [`src/ai_whisperer/cli.py`](../src/ai_whisperer/cli.py) or [`src/ai_whisperer/main.py`](../src/ai_whisperer/main.py) during application startup). This instance will then be passed via **dependency injection** to components that require it, such as `ExecutionEngine`, `AILoop`, and any new modules or CLI command handlers.

**Benefits:**

* Ensures all parts of the system interact with the same event bus.
* Improves testability by allowing mock `DelegateManager` instances to be injected during tests.
* Simplifies the lifecycle management of the `DelegateManager`.

### 3.2. Standardization of Event and Control Types

To replace raw string identifiers for events and controls, we will introduce Python `Enum` classes.

* **Location:** These Enums can be defined in a new file, e.g., [`src/ai_whisperer/events.py`](../src/ai_whisperer/events.py), or within [`src/ai_whisperer/delegate_manager.py`](../src/ai_whisperer/delegate_manager.py) if preferred for co-location.
* **Structure:** Separate Enums for different categories of events/controls:
  * `EngineNotificationType(Enum)`
  * `EngineControlType(Enum)`
  * `AILoopNotificationType(Enum)`
  * `AILoopControlType(Enum)`
  * `CLINotificationType(Enum)` (for new CLI-specific events)
  * Generic or shared event/control types can also be defined.
* **Usage:** Methods like `register_notification`, `invoke_notification`, `register_control`, and `invoke_control` in `DelegateManager` will be updated to accept these Enum members as arguments for `event_type` and `control_type`. Their string values (e.g., `EngineNotificationType.TASK_STARTED.value`) will be used internally as dictionary keys if needed, maintaining compatibility with the existing storage mechanism while providing type safety at the API level.

**Example:**

```python
# In events.py or delegate_manager.py
from enum import Enum

class EngineNotificationType(Enum):
    ENGINE_STARTED = "engine_started"
    TASK_EXECUTION_STARTED = "task_execution_started"
    # ... other engine notifications

class AILoopControlType(Enum):
    REQUEST_PAUSE = "ai_loop_request_pause"
    REQUEST_STOP = "ai_loop_request_stop"
    # ... other AI loop controls
```

**Benefits:**

* Reduces risk of typos in event/control names.
* Improves code readability and maintainability.
* Enables auto-completion and static analysis for event/control types.
* Provides a centralized registry of all known events and controls.

### 3.3. Typed Event Data Payloads

For `event_data` passed during `invoke_notification`, we will define specific Pydantic models or Python `dataclasses` for each standardized `event_type`.

* **Location:** These data models can also reside in [`src/ai_whisperer/events.py`](../src/ai_whisperer/events.py) alongside the Enum definitions.
* **Structure:** Each event type that carries data will have a corresponding data model.

**Example:**

```python
# In events.py
from pydantic import BaseModel
from typing import Dict, Any

class TaskExecutionStartedPayload(BaseModel):
    task_id: str
    task_details: Dict[str, Any] # Or a more specific model if task_details has a known structure

class AIRequestPreparedPayload(BaseModel):
    request_payload: Dict[str, Any]
    # Potentially add model_name, timestamp, etc.
```

* **Usage:**
  * When calling `invoke_notification`, the `sender` will construct and pass an instance of the appropriate Pydantic model/dataclass.
  * Delegate functions registered for these events will expect to receive an instance of that specific model, allowing for type hinting and clear data contracts.

**Benefits:**

* Provides clear contracts for the data associated with each event.
* Improves type checking and editor support for delegate implementers.
* Makes it easier to understand and use the data passed with events.

### 3.4. Discoverability of Events

To enhance the ability to understand what events and controls are available or active, the `DelegateManager` will be augmented with methods to list registered types:

* `get_registered_notification_types() -> List[Enum]` (or `List[str]` if returning the string values)
* `get_registered_control_types() -> List[Enum]` (or `List[str]`)
* Optionally, methods to get the number of delegates per type: `get_delegate_counts() -> Dict[Enum, int]`

**Benefits:**

* Useful for debugging and monitoring.
* Can support dynamic UI or plugin systems that need to know available events.

## 4. Implementation Details

### 4.1. `DelegateManager` Modifications ([`src/ai_whisperer/delegate_manager.py`](../src/ai_whisperer/delegate_manager.py))

* Update signatures of `register_notification`, `invoke_notification`, `register_control`, `invoke_control` to accept Enum types for `event_type` and `control_type`.
* Internally, the string value of the Enum can be used as the key for the `_notification_delegates` and `_control_delegates` dictionaries to minimize changes to the storage logic.
* Update type hints for delegate callables in registration methods to reflect that they might receive specific Pydantic models/dataclasses as `event_data`.
* Add the new discoverability methods (e.g., `get_registered_notification_types`).

### 4.2. Impact on `ExecutionEngine` ([`src/ai_whisperer/execution_engine.py`](../src/ai_whisperer/execution_engine.py))

* The `ExecutionEngine` constructor will be modified to accept a `DelegateManager` instance as a parameter, instead of creating its own.
* All calls to `invoke_notification` and `invoke_control` will be updated:
  * Use the new Enum types (e.g., `EngineNotificationType.ENGINE_STARTED`).
  * Pass instances of the corresponding Pydantic models/dataclasses for `event_data` (e.g., `TaskExecutionStartedPayload(...)`).

### 4.3. Impact on `AILoop` ([`src/ai_whisperer/ai_loop.py`](../src/ai_whisperer/ai_loop.py))

* The `run_ai_loop` function (or `AILoop` class if it becomes one) will continue to receive the `DelegateManager` instance.
* All calls to `invoke_notification` and `invoke_control` will be updated similarly to `ExecutionEngine`:
  * Use Enum types (e.g., `AILoopNotificationType.AI_REQUEST_PREPARED`).
  * Pass typed Pydantic models/dataclasses for `event_data`.

### 4.4. Integration with CLI Commands ([`src/ai_whisperer/cli.py`](../src/ai_whisperer/cli.py), [`src/ai_whisperer/commands.py`](../src/ai_whisperer/commands.py))

* The main `DelegateManager` instance, created at application startup (likely in `cli.py` or `main.py`), will be made available to CLI command handlers.
  * This can be achieved by passing it as an argument to command functions, or if using a framework like Click, by storing it in the `Context` object (`ctx.obj`) and accessing it via `@click.pass_context`.
* CLI commands can then:
  * Register delegates for existing system events (e.g., to log specific `ExecutionEngine` progress to the console in a CLI-specific format).
  * Define and invoke new CLI-specific notifications (e.g., `CLINotificationType.COMMAND_STARTED`, `CLINotificationType.ARGUMENT_PARSED`) using their own Enums and payload types.
  * Register control delegates if CLI operations need to be pausable/stoppable via the delegate mechanism.

### 4.5. Pattern for New Modules

New modules or classes that need to interact with the `DelegateManager` will:

1. Accept the shared `DelegateManager` instance via dependency injection (typically in their constructor).
2. Import necessary Enum types and Pydantic payload models from the central definitions (e.g., [`src/ai_whisperer/events.py`](../src/ai_whisperer/events.py)).
3. Use these types when registering delegates or invoking notifications/controls.

**Example:**

```python
# In a new_module.py
from .delegate_manager import DelegateManager # Assuming relative import
from .events import CustomNotificationType, CustomDataPayload # Assuming events.py

class MyNewService:
    def __init__(self, delegate_manager: DelegateManager):
        self._delegate_manager = delegate_manager
        self._delegate_manager.register_notification(
            EngineNotificationType.TASK_EXECUTION_COMPLETED, 
            self._handle_task_completion
        )

    def _handle_task_completion(self, sender, event_type, event_data: TaskExecutionCompletedPayload):
        print(f"Task {event_data.task_id} completed with status: {event_data.status}")

    def perform_action(self, data: str):
        # ... perform some action ...
        payload = CustomDataPayload(info=data, timestamp=datetime.utcnow())
        self._delegate_manager.invoke_notification(
            self, 
            CustomNotificationType.ACTION_PERFORMED, 
            payload
        )
```

## 5. Visual Overview

The following diagram illustrates the proposed centralized `DelegateManager` flow:

```mermaid
graph TD
    subgraph AppEntryPoint [Application Entry Point (e.g., cli.py/main.py)]
        DM_Instance[("DelegateManager Instance")]
    end

    AppEntryPoint -- Creates & Passes --> DM_Instance

    DM_Instance -- Injected Into --> EE([ExecutionEngine])
    DM_Instance -- Injected Into --> AL([AILoop])
    DM_Instance -- Injected Into --> CLI_Cmds([CLI Commands])
    DM_Instance -- Injected Into --> NewMod([New Modules/Components])

    EE -- Uses (Invoke/Register) --> DM_Instance
    AL -- Uses (Invoke/Register) --> DM_Instance
    CLI_Cmds -- Uses (Invoke/Register) --> DM_Instance
    NewMod -- Uses (Invoke/Register) --> DM_Instance
```

## 6. Future Considerations

While the following enhancements from the [`delegate_manager_analysis.md`](delegate_manager_analysis.md) are not part of this immediate refactoring scope, they are worth noting for future improvements:

* **Asynchronous Delegate Support:** Adding support for `async def` delegates.
* **Advanced Error Handling for Delegates:** More sophisticated mechanisms for reporting and handling errors occurring within delegate functions.
* **Flexibility in Control Delegate Aggregation:** Allowing different logic (e.g., "AND") for `invoke_control`.

These can be addressed in subsequent development phases once the foundational refactoring described here is complete.

## 7. Conclusion

Refactoring the `DelegateManager` as proposed will significantly improve its usability, maintainability, and type safety. By centralizing its instance, standardizing event/control types with Enums, and introducing typed payloads, we create a more robust and developer-friendly event system. This will make it easier to integrate the `DelegateManager` into various parts of the AIWhisperer application, including CLI commands and new modules, fostering a more decoupled and extensible architecture.
