# Plan for Implementing the 'run' CLI Command

## 1. Introduction

This document outlines the plan to implement a new `run` command in the AI Whisperer CLI. This command will allow users to execute a project plan defined in an overview JSON file, manage the execution state, and interact with the orchestrator.

The primary goals are:
- Integrate a `run` command into the existing CLI structure in [`src/ai_whisperer/main.py`](../../../../src/ai_whisperer/main.py:0).
- Parse a plan from a user-provided overview JSON file.
- Manage execution state (loading and saving) using [`src/ai_whisperer/state_management.py`](../../../../src/ai_whisperer/state_management.py:0).
- Trigger plan execution via the [`src/ai_whisperer/orchestrator.py`](../../../../src/ai_whisperer/orchestrator.py:0).
- Implement robust error handling.

## 2. CLI Command Definition (`src/ai_whisperer/main.py`)

A new subparser for the `run` command will be added to the `ArgumentParser` in [`src/ai_whisperer/main.py`](../../../../src/ai_whisperer/main.py:0).

```python
# In src/ai_whisperer/main.py

# ... existing subparsers ...

# --- Run Command ---
run_parser = subparsers.add_parser("run", help="Execute a project plan from an overview JSON file.")
run_parser.add_argument(
    "--plan-file",
    required=True,
    help="Path to the input overview JSON file containing the task plan."
)
run_parser.add_argument(
    "--state-file",
    required=True,
    help="Path to the state file. Used for loading previous state and saving current state."
)
run_parser.add_argument(
    "--config",
    required=True,
    help="Path to the configuration YAML file. Required for orchestrator and AI interactions."
)
```

## 3. Plan File Loading and Parsing

The `run` command handler in [`src/ai_whisperer/main.py`](../../../../src/ai_whisperer/main.py:0) will be responsible for loading and parsing the overview JSON plan file specified by the `--plan-file` argument.

- The file path will be resolved.
- The file will be opened and read.
- The content will be parsed using `json.load()` (if reading from a file object) or `json.loads()` (if reading the content into a string first).
- Basic validation (e.g., ensuring it's a dictionary) can be performed.

```python
# In src/ai_whisperer/main.py, within the 'run' command handler

try:
    with open(args.plan_file, 'r', encoding='utf-8') as f:
        plan_data = json.load(f)
except FileNotFoundError:
    console.print(f"[bold red]Error:[/bold red] Plan file not found: {args.plan_file}")
    sys.exit(1)
except json.JSONDecodeError as e:
    console.print(f"[bold red]Error:[/bold red] Invalid JSON in plan file {args.plan_file}: {e}")
    sys.exit(1)
except Exception as e:
    console.print(f"[bold red]Error:[/bold red] Failed to load plan file {args.plan_file}: {e}")
    sys.exit(1)

if not isinstance(plan_data, dict):
    console.print(f"[bold red]Error:[/bold red] Plan file content must be a JSON object.")
    sys.exit(1)
```

## 4. State Management (`src/ai_whisperer/state_management.py`)

State management will be primarily handled by the `Orchestrator`'s `run_plan` method, which internally uses the `StateManager` class from [`src/ai_whisperer/state_management.py`](../../../../src/ai_whisperer/state_management.py:0).

-   **Loading State**: The `Orchestrator.run_plan()` method, when called with the `state_file_path` (from `--state-file`), will instantiate a `StateManager`. The `StateManager`'s `load_state()` method is called if the state file exists. If it doesn't exist, `StateManager.initialize_state(plan_data)` is called to create an initial state based on the loaded plan.
-   **Saving State**: After the `ExecutionEngine` completes or is interrupted, the `Orchestrator.run_plan()` method ensures the `StateManager.save_state()` method is called to persist the current execution state to the specified `--state-file` path. This includes creating the file if it doesn't exist or overwriting it. The `save_state` function in `state_management.py` already handles atomic writes using a temporary file.

No direct calls to `StateManager` are needed from `main.py` for the `run` command itself, as the `Orchestrator` encapsulates this logic.

## 5. Orchestrator Interaction (`src/ai_whisperer/orchestrator.py`)

The `run` command handler in [`src/ai_whisperer/main.py`](../../../../src/ai_whisperer/main.py:0) will interact with the `Orchestrator` as follows:

1.  Load the application configuration using `load_config(args.config)`.
2.  Instantiate the `Orchestrator`: `orchestrator = Orchestrator(config, args.output)` (Note: `args.output` might need to be re-evaluated for the `run` command, or a default/derived path used if not directly applicable. For now, we assume the existing constructor is sufficient, or it might be adapted if `output_dir` is not relevant for `run`). The `output_dir` in `Orchestrator` is mainly used for `generate_initial_json` and `generate_full_project_plan`. For `run_plan`, it's less critical but might be used for logging or temporary files by the execution engine.
3.  Call the `run_plan` method: `orchestrator.run_plan(plan_data=plan_data, state_file_path=args.state_file)`.

The [`Orchestrator.run_plan()`](../../../../src/ai_whisperer/orchestrator.py:634) method will:
    - Initialize or load state using `StateManager`.
    - Initialize the `ExecutionEngine`.
    - Iterate through tasks in the plan, executing them via `ExecutionEngine.run_step()`.
    - Update and save state after each step or at the end.

## 6. Execution Flow

```mermaid
graph TD
    A[CLI: ai-whisperer run --plan-file plan.json --state-file state.json --config config.yaml] --> B{main.py: Parse Args};
    B --> C{main.py: Load Config};
    C --> D{main.py: Load Plan JSON from --plan-file};
    D --> E{main.py: Instantiate Orchestrator};
    E --> F[main.py: Call orchestrator.run_plan(plan_data, state_file_path)];
    F --> G{Orchestrator.run_plan};
    G --> H{StateManager: Initialize or Load State from state_file_path};
    H --> I{ExecutionEngine: Initialize};
    I --> J{ExecutionEngine: Loop through plan steps};
    J -- Execute Step --> K[ExecutionEngine: run_step(step_data)];
    K -- Step Result/Error --> J;
    J -- Update State --> L{StateManager: Update Task Status/Result};
    L -- Save State --> M[StateManager: Save State to state_file_path];
    J -- Plan Complete/Error --> G;
    G -- Final Save State --> M;
    M --> N[Output/Log to Console];
```

## 7. Error Handling

The `run` command handler in [`src/ai_whisperer/main.py`](../../../../src/ai_whisperer/main.py:0) will include `try-except` blocks to catch and report errors gracefully.

-   **File Not Found**: For `--plan-file` or `--config` file.
-   **JSON Parsing Errors**: For `--plan-file`.
-   **Configuration Errors**: From `load_config()`.
-   **State Management Errors**: Errors during state loading or saving, though these are largely handled within `Orchestrator` and `StateManager`, they might propagate. `Orchestrator.run_plan` should catch and log these, or `main.py` can catch `OrchestratorError` or `StateManagerError` (if defined and raised).
-   **Orchestrator Errors**: Any exceptions raised by `Orchestrator.run_plan()` (e.g., `OrchestratorError`, `ExecutionEngineError`).
-   **General Exceptions**: A catch-all for unexpected errors.

Error messages will be printed to the console using `rich.console` for better formatting, and the application will exit with a non-zero status code.

```python
# In src/ai_whisperer/main.py, within the 'run' command handler

try:
    # ... (load config, load plan_data) ...

    orchestrator = Orchestrator(config, output_dir=".") # Adjust output_dir as needed
    orchestrator.run_plan(plan_data=plan_data, state_file_path=args.state_file)

    console.print("[green]Plan execution completed successfully.[/green]")
    sys.exit(0)

except FileNotFoundError as e:
    console.print(f"[bold red]Error:[/bold red] File not found: {e}")
    sys.exit(1)
except json.JSONDecodeError as e:
    # This might be caught earlier during plan loading
    console.print(f"[bold red]Error:[/bold red] Invalid JSON: {e}")
    sys.exit(1)
except ConfigError as e:
    console.print(f"[bold red]Configuration Error:[/bold red] {e}")
    sys.exit(1)
except OrchestratorError as e: # Assuming OrchestratorError can be raised by run_plan
    console.print(f"[bold red]Orchestration Error:[/bold red] {e}")
    sys.exit(1)
# Add more specific exceptions like StateManagerError, ExecutionEngineError if they are distinct
except AIWhispererError as e: # Catch base custom error
    console.print(f"[bold red]Application Error:[/bold red] {e}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"An unexpected error occurred during 'run' command: {e}", exc_info=True)
    console.print(f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details.")
    sys.exit(1)
```

## 8. Output

-   The primary output will be the side effects of the plan execution (e.g., file modifications, API calls made by tasks).
-   The state file (`--state-file`) will be created or updated.
-   Console output will indicate the progress of the execution (handled by `Orchestrator` and `ExecutionEngine` logging/printing) and the final status (success or error).

This plan provides a comprehensive approach to implementing the `run` CLI command, ensuring it integrates well with existing components and handles state and errors effectively.