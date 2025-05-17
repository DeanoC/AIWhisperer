# Add Delegate Manager to all ai using parts

We currently have delegate manager attached to execution_engine, getting ready for a proper monitor implementation.
We should also add it into initial_plan, overview_plan and list_models cli commands.

This is so we can have a consistent interface for all ai using parts of the code for user facing non logging messages.

## Goal

- Add delegate manager to all command execution using parts of the code.
- Ensure all command execution using parts of the code are using the delegate manager for user facing non logging messages
- Provide for automatic ending of a command execution or pausing at the end of a command execution.
- Have one place to setup the delegate manager for all command execution using parts of the code.

## Notes

Each of the 5 commands returned from the cli should have a delegate manager, this will allow us to have a consistent interface in future that doesn't rely on the loggin system (which will be used for non user facing messages).

src/aiwhisperer/execution_engine.py is an example of how to use the delegate manager.
src/aiwhisperer/cli.py is where the commands are used.
src/aiwhisperer/plan_runner.py will need the delegate manager.
src/aiwhisperer/initial_plan_generator.py will need the delegate manager.
src/aiwhisperer/overview_plan_generator.py will need the delegate manager.
src/aiwhisperer/list_models.py will need the delegate manager.

The current delegate managers may need moving from execution_engine and ai_loop to provide a consistent interface for all command execution using parts of the code.
