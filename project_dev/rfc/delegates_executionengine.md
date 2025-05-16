# Delegates in the Execution Engine

To allows us to build a monitor and debugger for the execution engine, we need to add observers and delegates to the execution engine. This will allow us to monitor the execution of the code and provide feedback to the user.
It will also allow us to pause, resume, and stop the execution of the code. This is crucial for debugging and monitoring the execution of the code.

We will also need to add a similar system to ai_loop. This will involve adding delegates and observers to the AI loop to monitor its execution and provide feedback.

## Examples and notes

project_dev/notes/Thread-Safe Delegates Design Document.md
project_dev/notes/Thread-Safe Delegates in Python - Usage Guide.md

are both some notes on how to implement thread-safe delegates in Python. They provide a design document and usage guide for implementing delegates in a thread-safe manner. However they are specific to this project, so are just guides for the implementation.

project_dev/notes/thread_safe_delegates.py is an example of how to implement thread-safe delegates in Python. This can be used to implement the delegates in the execution engine and AI loop.

## Goals

1. Provide observability to all AI prompts and returns.
2. Provide the ability to pause, resume, and stop the execution of the code.
3. Do this with coupling the monitoring and debugging system to the execution engine or AI loop.
4. Allow for easy addition of new delegates and observers in the future.

