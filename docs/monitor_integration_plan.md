# Monitor Integration Plan

This document outlines the plan for conditionally starting the terminal monitor thread based on a new CLI option.

## 1. Overview

The terminal monitor functionality is primarily managed by the `TerminalMonitor` class in [`src/ai_whisperer/monitoring.py`](src/ai_whisperer/monitoring.py). The conditional start of the monitor is controlled by a boolean flag passed during its initialization. The CLI option's value will be propagated through various components to this flag.

## 2. Code Locations and Mechanism

### 2.1. CLI Option Propagation

As detailed in [`docs/cli_analysis_monitor_option.md`](docs/cli_analysis_monitor_option.md), the `--monitor` CLI flag (boolean, default `False`) will be propagated as follows:

1. **`src/ai_whisperer/cli.py`**:
    * `argparse` parses the `--monitor` flag. `parsed_args.monitor` will hold the boolean value.
    * This value is passed to the `RunCommand` constructor: `RunCommand(..., monitor=parsed_args.monitor)`.

2. **`src/ai_whisperer/commands.py`**:
    * `RunCommand.__init__` accepts and stores the `monitor` flag: `self.monitor = monitor`.
    * `RunCommand.execute` passes this flag to the `PlanRunner` constructor: `PlanRunner(self.config, monitor=self.monitor)`.

3. **`src/ai_whisperer/plan_runner.py`**:
    * `PlanRunner.__init__` (around line 34) accepts and stores the `monitor` flag: `self.monitor_enabled = monitor`.
    * In `PlanRunner.run_plan` (around line 140), this `self.monitor_enabled` flag is passed to the `TerminalMonitor` constructor: `TerminalMonitor(state_manager, monitor_enabled=self.monitor_enabled)`.

### 2.2. Conditional Monitor Start Location

The actual conditional starting logic for the terminal monitor's display (the Rich `Live` object) resides within the `TerminalMonitor` class.

* **File:** [`src/ai_whisperer/monitoring.py`](src/ai_whisperer/monitoring.py)
* **Class:** `TerminalMonitor`
* **Constructor (`__init__`)**: (around line 20)
  * Accepts `monitor_enabled: bool`.
  * Stores this as `self.monitor_enabled`.
* **Method (`run`)**: (around line 153)
  * This method is responsible for starting the Rich `Live` display.
  * It explicitly checks `if self.monitor_enabled:` before creating and running the `Live` object.

    ```python
    # In src/ai_whisperer/monitoring.py
    class TerminalMonitor:
        def __init__(self, state_manager: StateManager, monitor_enabled: bool = True):
            # ...
            self.monitor_enabled = monitor_enabled # Store the flag
            # ...

        def run(self):
            """Starts the terminal monitoring interface."""
            if self.monitor_enabled: # <<< CONDITIONAL LOGIC HERE
                with Live(self._layout, console=self.console, screen=True, refresh_per_second=4) as live:
                    self._live = live
                    self.update_display()
                    # ...
            else:
                # If monitoring is disabled, just log that the monitor is "running" without display
                print("Terminal monitoring is disabled.") # Or use a logger if appropriate
    ```

### 2.3. Accessing and Using the CLI Option Value

* The `PlanRunner` receives the boolean value from the `RunCommand` (which originated from the CLI parser).
* It then passes this boolean value directly to the `TerminalMonitor` constructor as the `monitor_enabled` argument.
* The `TerminalMonitor` stores this value in `self.monitor_enabled`.
* The `TerminalMonitor.run()` method uses `self.monitor_enabled` in an `if` condition to decide whether to initialize and start the Rich `Live` display.

## 3. Detailed Logic for Conditional Starting

The logic is straightforward:

1. The `PlanRunner` instantiates `TerminalMonitor`, passing the `monitor_enabled` boolean (derived from the CLI `--monitor` option).

    ```python
    # In src/ai_whisperer/plan_runner.py, method run_plan (around line 140)
    monitor = TerminalMonitor(state_manager, monitor_enabled=self.monitor_enabled)
    ```

2. If the `TerminalMonitor` is to be run (e.g., in a separate thread by the application's main entry point or a higher-level orchestrator after `PlanRunner` setup), its `run()` method will be called.
3. Inside `TerminalMonitor.run()`:
    * An `if self.monitor_enabled:` check is performed.
    * If `True`, the Rich `Live` instance is created and started, enabling the terminal UI.
    * If `False`, the Rich `Live` instance is not created, and a message indicating that monitoring is disabled can be printed or logged. The UI will not appear.

The `ExecutionEngine` receives the `monitor` instance (which might be a "no-op" version or one that doesn't display if `monitor_enabled` was false) and calls its methods like `add_log_message` and `set_active_step`. The `TerminalMonitor`'s methods (e.g., `update_display`, `add_log_message`) also internally check `self.monitor_enabled` (or rely on `self._live` being `None`) before attempting to interact with the Rich `Live` object, preventing errors if it wasn't started.

## 4. Summary of Implementation Steps

No direct code changes are required in `ExecutionEngine` or `PlanRunner` for the *conditional starting logic itself*, as this is already correctly handled by the `TerminalMonitor` based on the `monitor_enabled` flag it receives. The primary work involves ensuring the CLI flag is correctly defined and its value propagated to the `PlanRunner` and subsequently to the `TerminalMonitor`, as outlined in [`docs/cli_analysis_monitor_option.md`](docs/cli_analysis_monitor_option.md) and recapped above.

The implementation subtasks will focus on:

1. Adding the `--monitor` argument to `run_parser` in [`src/ai_whisperer/cli.py`](src/ai_whisperer/cli.py).
2. Updating `RunCommand.__init__` in [`src/ai_whisperer/commands.py`](src/ai_whisperer/commands.py) to accept and store the `monitor` argument.
3. Updating `RunCommand.execute` in [`src/ai_whisperer/commands.py`](src/ai_whisperer/commands.py) to pass `self.monitor` to the `PlanRunner` constructor.
4. Ensuring `PlanRunner.__init__` in [`src/ai_whisperer/plan_runner.py`](src/ai_whisperer/plan_runner.py) correctly receives and uses this argument to set `self.monitor_enabled`.
5. Verifying that `PlanRunner.run_plan` passes `self.monitor_enabled` to `TerminalMonitor`.

The core conditional logic within `TerminalMonitor.run()` is already in place.
