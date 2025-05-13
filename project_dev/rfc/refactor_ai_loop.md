# Refactor several code_generation.py function to be reusable

This is a refactor task, we currently have some functionality in code_generation.py that will be useful to be usable in future by other handlers.

## Goal

1. The ai loop should become a seperate thing as it will be useful, for many handlers
2. Make this usable from AIwhisperer directly, not only when run via an overview plan (tho this must also work)
3. Create a ContextManager that StateManager will use to handle message history
4. Move all message history and message funcitonality to ContextManager
5. Initial ContextManager will have the same identity transform as now (just storing and providing all AI messages and reponses)

## Details

1. Use test_run_plan_script.py to ensure nothing the refactor hasn't broken anything
2. Just do the refactor (including unit tests), your task isn't to use the refactored functionality outside of code_generation.py
3. Ensure all applicable tests pass (don't try to fix any fails that happen before the refactor)
4. The AI loop calls to the AI should get there context from the ContentManager
