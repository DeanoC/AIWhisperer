# Plan for Refactoring Terminal Monitor and AI Runner Threading Model

**Date:** 2025-05-13

**Version:** 1.0

## 1. Introduction

### 1.1 Problem Statement

The current terminal monitor implementation in `src/ai_whisperer/monitoring.py` exhibits instability, particularly with input handling and unexpected exits. These issues are believed to stem from architectural limitations in its current threading model. This instability is a significant blocker for implementing and validating crucial features such as command coloring, interactive help, shortcuts, and command aliases.

### 1.2 Goal

The primary goal is to design and plan the implementation of a new, robust threading model for both the terminal monitor and the AI runner. This refactor aims to:

* Ensure stable and correct input handling within the terminal monitor.
* Improve overall monitor stability and prevent unexpected exits.
* Establish a clear separation of concerns between UI rendering, AI execution, and main application control.
* Lay a foundation for future enhancements, such as multiple concurrent AI tasks.

## 2. Current Architecture Analysis

### 2.1 Current Threading Model

* **Main Thread:** Manages the `rich.live.Live` display when `TerminalMonitor.run()` is invoked.
* **Command Input Thread:** A separate `threading.Thread` is spawned for `_command_input_loop()`, handling blocking user input via `self.console.input()`.
* **Logging:** `TerminalMonitor.emit()` processes log messages originating from potentially any thread in the application (e.g., AI execution, main runner). `emit()` then calls `update_display()`, interacting with the `Live` object.

### 2.2 Identified Issues

* **Thread Safety of Rich Library:** `rich.console.Console` and `rich.live.Live` are generally not thread-safe. Calling `console.input()` in one thread while `live.update()` (or other `Console` operations) are called from other threads (main thread via `Live` updates, logging threads via `emit`, command thread itself via `update_display`) is a primary suspect for instability.
* **Input Handling Conflicts:** The blocking nature of `console.input()` in a dedicated thread, concurrent with `Live` display updates from potentially multiple other threads, creates race conditions and makes reliable input difficult.
* **Complexity:** Synchronizing UI updates and state across these threads when interacting with a non-thread-safe UI library is inherently complex and error-prone.

## 3. Proposed New Threading Architecture

### 3.1 Core Principles

* **Dedicated UI Thread:** Consolidate all interactions with the Rich library (both input and display updates) into a single, dedicated thread.
* **Dedicated AI Runner Thread:** Isolate AI execution logic (e.g., `ExecutionEngine`, `AILoop`) into its own thread.
* **Main Thread Orchestration:** The Main thread will be responsible for initializing, starting, and managing the lifecycle of the UI and AI Runner threads.
* **Thread-Safe Communication:** Use `queue.Queue` for communication from the AI Runner Thread (and other future components) to the UI Thread.

### 3.2 Proposed Threads

* **Main Thread:**
  * Handles initial CLI parsing and application setup.
  * Starts the UI Thread (if monitoring is enabled).
  * Starts the AI Runner Thread (for execution tasks).
  * Waits for the UI and AI Runner threads to complete.
  * Manages application exit.
* **UI Thread (Rich Interaction Thread):**
  * Sole owner and manager of the `rich.live.Live` instance and its associated `Console`.
  * Handles all calls to `live.update()` for display refreshes.
  * Manages user input (ideally non-blocking) and processes commands.
  * Listens to a thread-safe queue for messages (e.g., log entries, status updates) from the AI Runner Thread.
* **AI Runner Thread:**
  * Encapsulates the AI execution logic (e.g., running the plan via `ExecutionEngine` and `AILoop`).
  * Sends log messages, status updates, or any data intended for display to the UI Thread via the thread-safe queue.
  * Crucially, this thread will *not* directly call any Rich library functions.

### 3.3 Communication Mechanism

* A `queue.Queue` will be used for one-way communication from the AI Runner Thread (and potentially other future application logic threads) to the UI Thread. This queue will carry log messages, status update requests, etc.

### 3.4 Conceptual Diagram (Mermaid)

```mermaid
graph TD
    MainThread[Main Application Thread] -->|Starts| UIRunner{UI Thread}
    MainThread -->|Starts| AIRunner{AI Runner Thread}

    subgraph AIRunner [AI Runner Thread]
        direction LR
        AI_Execution_Engine[Execution Engine / AI Loop] -->|Log Data, Status Updates| DataQueue[Thread-safe Queue]
    end

    subgraph UIRunner [Dedicated UI Thread]
        direction TB
        DataQueue --> RichEventLoop{Rich Event & Input Loop}
        UserInput[User Keyboard Input] --> RichEventLoop
        RichEventLoop -->|Process Input| CommandHandler[Command Handler]
        RichEventLoop -->|Render Updates| RichLiveDisplay[Rich Live Display]
        CommandHandler -->|Execute Action (e.g., pause/resume AI)| AIControlInterface[Interface to AI Runner Thread (Optional/Future)]
    end

    MainThread -->|Waits for completion| UIRunner
    MainThread -->|Waits for completion| AIRunner
```

### 3.5 Thread Scenarios

* **Monitored Run:** Main Thread, UI Thread, AI Runner Thread (3 threads).
* **Non-Monitored Run:** Main Thread, AI Runner Thread (2 threads). The AI Runner thread would still execute; its logs/status updates sent to the (non-existent or inactive) UI queue would be handled by a simpler console logger or be no-ops.
* **Non-Run Modes (e.g., CLI help):** Main Thread only (1 thread).

## 4. Implementation Plan

### 4.1 Step 1: Introduce Thread-Safe Queue for UI Updates

* **Location:** `TerminalMonitor` class in `src/ai_whisperer/monitoring.py`.
* **Action:** Add an instance of `queue.Queue`.
* **Modification:** Refactor `TerminalMonitor.emit()`, `set_active_step()`, `set_runner_status_info()`, and `set_plan_name()` to put formatted messages or update requests onto this queue instead of directly calling `update_display()`.
* **Status:** Completed

### 4.2 Step 2: Establish the UI Thread in `TerminalMonitor`

* **Location:** `TerminalMonitor.run()` method.
* **Action:** Refactor `run()` to initialize and start the new UI thread.
* **UI Thread Loop:** This loop will:
  * Initialize and manage the `rich.live.Live` object and its `Console`.
  * Continuously check the queue for new messages (non-blocking or with a short timeout).
  * Process these messages, update internal state for display.
  * Call `update_display()` (now exclusively from this thread).
  * Handle user input (see Step 4.3).
* **Status:** Completed

### 4.3 Step 3: Refactor Input Handling within UI Thread

* **Action:** Integrate the logic from the current `_command_input_loop()` into the UI thread's main loop.
* **Input Strategy:**
  * **Preferred:** Investigate Rich library for non-blocking input mechanisms or event hooks suitable for a full-screen application that can be integrated into the UI thread's loop.
  * **Fallback:** If non-blocking input is not feasible, use `console.input()` within the UI thread's loop, potentially with timeouts or by carefully alternating input checks with queue checks. The critical aspect is that `console.input()` and `live.update()` are invoked from the *same thread*.
* **Status:** Completed

### 4.4 Step 4: Isolate AI Execution into an AI Runner Thread

* **Location:** Likely in `src/ai_whisperer/main.py` or `src/ai_whisperer/cli.py` (wherever plan execution is currently initiated).
* **Action:**
  * Wrap the core logic of plan execution (e.g., `ExecutionEngine.run_plan()`) in a function. This function will become the target for a new `threading.Thread` (the AI Runner Thread).
  * The AI Runner thread will need access to the UI update queue (passed during its initialization if monitoring is enabled) to send updates.
  * The Main thread will start this AI Runner thread and can wait for its completion using `thread.join()`.
* **Status:** Completed

### 4.5 Step 5: Implement Graceful Shutdown for All Threads

* **UI Thread:**
  * Design a mechanism to signal the UI thread to terminate cleanly (e.g., a special "shutdown" message on its queue, or using a `threading.Event`).
  * `TerminalMonitor.run()` (or a new `stop()` method) will initiate this shutdown.
  * Ensure `set_active_monitor_handler(None)` is called upon UI thread termination.
* **AI Runner Thread:**
  * Implement a mechanism for graceful interruption (e.g., `threading.Event`), especially for long-running AI tasks.
  * The Main thread should signal this if the application needs to exit prematurely.
* **Main Thread:**
  * Responsible for coordinating the shutdown sequence.
  * Signal shutdown to both UI and AI Runner threads.
  * Wait for both threads to join before exiting the application.
* **Status:** Completed

### 4.6 Anticipated Code Changes

* **`src/ai_whisperer/monitoring.py`:** Significant refactoring for the UI thread, queue integration, and input handling.
* **`src/ai_whisperer/main.py` or `src/ai_whisperer/cli.py`:** Modifications to spawn the AI execution logic in the new AI Runner Thread. This includes passing the UI update queue to the AI runner if monitoring is active.

### 4.7 New Files

* No new Python files are anticipated for this refactoring. This plan document itself is a new file.

## 5. Validation Plan

### 5.1 Monitor-Specific Validation

* **Basic Logging:** Confirm log messages from various components are received and displayed correctly and promptly by the monitor, including JSON highlighting.
* **Input Handling & Command Reliability:** Thoroughly test user command input (e.g., `exit`, `debug`, `ask`). Commands should be accepted reliably without loss, especially under high logging load. Test responsiveness with rapid/continuous input.
* **Stability Under Stress:** Simulate high volumes of log messages to check for freezes, crashes, display artifacts, or excessive CPU usage.
* **Dynamic Status Updates:** Verify that changes to runner status, plan name, and active subtask ID are reflected accurately and immediately.
* **Graceful UI Shutdown:** Confirm "exit" or "quit" commands lead to a clean shutdown of the monitor and `set_active_monitor_handler(None)` is called.
* **`monitor_enabled = False` Behavior:** Ensure correct application operation without the monitor UI when disabled.

### 5.2 AI Runner Thread Validation

* **Correct Execution:** Confirm AI execution (e.g., a simple plan) runs correctly in its own thread.
* **UI Updates:** Verify logs and status updates from the AI Runner Thread are correctly passed to and displayed by the UI Thread (when monitoring is active).
* **Graceful Shutdown/Interruption:** Test graceful shutdown/interruption of the AI Runner Thread.
* **Status:** Completed

### 5.3 Non-Monitored Run Validation

* Ensure the application (with the AI Runner Thread) runs correctly and produces expected output (e.g., to standard console/log files) when terminal monitoring is disabled.

### 5.4 Post-Refactor Feature Validation

* Once the new threading model is stable, re-test features previously blocked or problematic (command coloring, help, shortcuts, aliases) to confirm the refactor has enabled their correct implementation and function.

## 6. Output

* This plan document: `project_dev/in_dev/terminal_monitor_threading_refactor/overview_terminal_monitor_refactor.md`

## 7. Future Considerations (Out of Scope for this Refactor)

* Direct control interface from UI Thread to AI Runner Thread (e.g., for pause/resume).
* Support for multiple concurrent AI Runner Threads.
