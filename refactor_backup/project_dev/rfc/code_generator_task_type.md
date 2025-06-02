# Code Generator Task Type

initial_plan_default.md defines a number of task types, we are implementing the code_generator task types.

This task should parse subtask with type `code_generation` and provide enough information for a LLM AI call to perform the task.

The actual task is defined by subtask_schema.json

## Goal

1. That we implement a execution engine handler for type `code_generation`
2. That handler is capable of instruction an agentic AI using a specialisation prompt that with the subtask and tools provided can implement the code genertion task.
3. The prompt should be very precise about following the plan, including examining files in projects, focussing on resuse of exsting code where possible.
4. If there are tests involved, it should run them checking they are not faked and they pass before completion

## Notes

This is a complex key part of this project, its likely to need extensive research. This should be included in the instructions to the AI making planning this rfc
