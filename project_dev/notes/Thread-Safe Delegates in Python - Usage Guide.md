# Thread-Safe Delegates in Python - Usage Guide

This guide explains how to use the thread-safe delegates implementation for debugging execution loops.

## Overview

The implementation provides a thread-safe way for objects running on different threads to:
1. Receive notifications from an execution loop
2. Control the execution loop (e.g., pause/resume) without tight coupling

## Key Components

### DelegateManager

The central class that manages registration and invocation of delegates:
- Maintains thread-safe collections of delegates
- Handles registration/unregistration
- Provides methods to invoke delegates

### ExecutionLoop

An example class that demonstrates how to use delegates in an execution loop:
- Checks for pause requests at the beginning of each iteration
- Sends notifications about execution progress
- Runs in a separate thread

### Observer

An example class that shows how to hook into an execution loop:
- Registers for notifications and control
- Can request the execution loop to pause/resume
- Can be connected/disconnected at runtime

## How to Use

### 1. Create an Execution Loop

```python
# Create and start an execution loop
loop = ExecutionLoop()
loop.start()
```

### 2. Create and Connect Observers

```python
# Create an observer
observer = Observer("MyObserver")

# Connect to the execution loop
observer.connect_to_loop(loop)
```

### 3. Control Execution

```python
# Pause the execution
observer.request_pause(True)

# Resume execution
observer.request_pause(False)
```

### 4. Disconnect Observers

```python
# Disconnect when no longer needed
observer.disconnect_from_loop(loop)
```

### 5. Stop the Execution Loop

```python
# Stop the execution loop
loop.stop()
```

## Creating Your Own Implementation

To adapt this pattern for your own use case:

1. Create a delegate manager in your execution loop class
2. Add appropriate control checks in your loop
3. Send notifications at key points
4. Create observer classes that register for notifications and controls

## Thread Safety Considerations

- All delegate collections are protected by locks
- Delegate invocation is done on copies to avoid holding locks during execution
- Observers should be designed to be thread-safe if they access shared state

## Example

Run the provided example to see the delegates in action:

```
python thread_safe_delegates.py
```

The example demonstrates:
- Multiple observers receiving notifications
- Pausing and resuming execution
- Safely connecting and disconnecting observers at runtime
