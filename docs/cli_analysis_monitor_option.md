# CLI Analysis for Terminal Monitor Option

This document outlines the analysis for adding a new CLI option to enable a terminal monitor during plan execution.

## 1. Identified CLI Command for Modification

The relevant CLI command to modify is the `run` command. This command is responsible for executing a project plan.

- **File:** `src/ai_whisperer/cli.py`
- **Parser:** The `run_parser` subparser, added using `subparsers.add_parser("run", ...)` (around line 97).

## 2. Proposed CLI Option

- **Option Name:** `--monitor`
- **Type:** Boolean (flag)
- **Action:** `store_true`
- **Help Text:** "Enable the terminal monitor during plan execution."
- **Default:** `False` (monitor is off by default)

## 3. Proposed Location in CLI Definition

The new option should be added to the `run_parser` in [`src/ai_whisperer/cli.py`](src/ai_whisperer/cli.py:1), similar to other arguments for the `run` command.

Example addition:

```python
# In src/ai_whisperer/cli.py, within the main function, after existing run_parser arguments:
run_parser.add_argument(
    "--monitor",
    action="store_true",
    help="Enable the terminal monitor during plan execution."
)
```

## 4. Propagation of the Option's Value

The value of the `--monitor` option will be propagated as follows:

1. **Argument Parsing (`src/ai_whisperer/cli.py`):**
    - `argparse` will parse the `--monitor` flag. If present, `parsed_args.monitor` will be `True`; otherwise, it will be `False` (due to `action="store_true"`).

2. **Command Instantiation (`src/ai_whisperer/cli.py`):**
    - When instantiating `RunCliCommand`, the value of `parsed_args.monitor` will be passed to its constructor.

    ```python
    # Around line 182 in src/ai_whisperer/cli.py
    elif parsed_args.command == "run":
        commands = [RunCliCommand(
            config_path=parsed_args.config,
            plan_file=parsed_args.plan_file,
            state_file=parsed_args.state_file,
            monitor=parsed_args.monitor  # New argument
        )]
    ```

3. **`RunCliCommand` Class (`src/ai_whisperer/commands.py`):**
    - The `__init__` method of `RunCliCommand` will be updated to accept and store the `monitor` boolean value.

    ```python
    # Around line 139 in src/ai_whisperer/commands.py
    class RunCliCommand(BaseCliCommand):
        def __init__(self, config_path: str, plan_file: str, state_file: str, monitor: bool = False): # Added monitor parameter
            super().__init__(config_path)
            self.plan_file = plan_file
            self.state_file = state_file
            self.monitor = monitor # Store the monitor flag
    ```

4. **Passing to `PlanRunner` (`src/ai_whisperer/commands.py`):**
    - In the `execute` method of `RunCliCommand`, the `self.monitor` value will be passed to the `PlanRunner`. This could be during `PlanRunner` instantiation or when calling a method like `run_plan`. Assuming it's passed during instantiation for now:

    ```python
    # Around line 156 in src/ai_whisperer/commands.py
    # plan_runner = PlanRunner(self.config) # Old
    plan_runner = PlanRunner(self.config, monitor=self.monitor) # New, assuming PlanRunner constructor is updated
    ```

    - Alternatively, if `PlanRunner.run_plan` is modified:

    ```python
    # Around line 159 in src/ai_whisperer/commands.py
    # plan_successful = plan_runner.run_plan(plan_parser=plan_parser, state_file_path=self.state_file) # Old
    plan_successful = plan_runner.run_plan(plan_parser=plan_parser, state_file_path=self.state_file, monitor=self.monitor) # New
    ```

    The exact method of passing to `PlanRunner` will depend on its design, but the `RunCliCommand` will hold the `monitor` flag and be responsible for passing it.

5. **`PlanRunner` and Execution Engine/AI Loop:**
    - The `PlanRunner` will then receive this `monitor` flag. It will be responsible for using this flag to enable/disable the terminal monitoring functionality, likely by passing it further to the `ExecutionEngine` or `AILoop` where the actual monitoring display logic is implemented or controlled.

This propagation path ensures that the user's choice via the CLI option is available to the components responsible for the terminal monitor.
