# Graceful Exit Analysis for Interactive Session

This document outlines the analysis for implementing graceful exit for the interactive Textual UI session, specifically focusing on the Double Ctrl-C mechanism.

## Requirements:

- Implement a mechanism to detect and handle the Double Ctrl-C signal (or equivalent interrupt) within the Textual application.
- Ensure a clean exit process that prevents resource leaks or orphaned processes.
- Restore the original terminal delegate upon exiting the interactive session.

## Analysis and Implementation Strategy:

Textual applications can handle interrupt signals like `SIGINT` (typically triggered by Ctrl-C) using the `on_key` method or by binding keys to actions. To implement the Double Ctrl-C mechanism, we can:

1.  **Intercept the first Ctrl-C:** Use a key binding or `on_key` to detect the first Ctrl-C.
2.  **Set a flag and timer:** Upon the first Ctrl-C, set a flag indicating that the first interrupt has occurred and start a short timer.
3.  **Prompt the user:** Display a message to the user indicating that they should press Ctrl-C again to exit.
4.  **Intercept the second Ctrl-C:** If a second Ctrl-C is received within the timer duration, trigger the graceful exit process.
5.  **Reset the flag:** If the timer expires before a second Ctrl-C is received, reset the flag.

## Cleanup Steps:

Before the application exits gracefully, the following cleanup steps must be performed:

1.  **Restore Original Delegate:** The original terminal delegate, which was replaced by the interactive delegate, must be restored using the `delegate_manager`. This is crucial to ensure the user's terminal is left in a usable state.
2.  **Stop Background Threads/Processes:** Any background threads or processes initiated by the interactive session (e.g., for running the AI loop) should be gracefully stopped.
3.  **Save Session State (Optional but Recommended):** Depending on future requirements, the current session state (e.g., conversation history) could be saved.

## Current Implementation Status:

- The basic Textual UI scaffolding is in place.
- The `delegate_manager` has a mechanism to set and potentially restore delegates.
- The `ai_loop` is designed to respond to a stop signal.

## Recommendations for Implementation:

- Implement the Ctrl-C handling logic within the `InteractiveUIBase` class using Textual's key binding or event handling mechanisms.
- Utilize a timer to differentiate between a single and double Ctrl-C press.
- Add a method to the `InteractiveUIBase` to perform the necessary cleanup steps, including calling a method in `delegate_manager` to restore the original delegate and signaling the `ai_loop` to stop.
- Ensure that the main application loop in `ai_whisperer/main.py` waits for the Textual application to exit gracefully before terminating.
