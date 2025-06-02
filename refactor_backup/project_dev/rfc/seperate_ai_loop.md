# Separate AI Loop

Currently our ai_loop.py depends on ExecutionEngine and StateManager, which makes it hard to use in other contexts. We want to refactor the AI loop to be a more of standalone component that can be used outside of the ExecutionEngine.

## Goal

1. Refactor the AI loop to not depend on ExecutionEngine and StateManager.
2. Make it work during an interacive session (list-models interactive is the first example).
3. Use streaming API where possible, with delegate calls so interactive sessions can provide updates/progress bars to the user.
4. Make it flexible enough that it can be used a general purpose AI loop, not just for code generation.

