# Requirements for model_per_task Configuration

This document outlines the requirements for a based model per task selection system.
We currently store a single model configuration in the `config.yaml` file, but we need to extend this to support multiple models for different tasks.
So far we have two AI tasks:
1. **Subtask Generation**: This task generates detailed subtask YAML definitions from high-level task steps.
2. **Orchestrator**: This task orchestrates the execution of subtasks, managing dependencies and execution order.

By implementing a model per task system, we can optimize the performance and cost of our AI interactions by selecting the most suitable model for each task.

## Goal

The primary goal is to create a module that allows selecting different AI models for different tasks, optimizing performance and cost based on task requirements.

## Scope

The scope of this task includes:
- Implementing a configuration system that allows specifying different models for different tasks.
- Ensuring that the chosen model is used correctly in the respective task.
- Updating the existing code to support this new configuration system.

### Initial Implementation
Whilst we only currently have two tasks, we will implement a system that allows for easy addition of new tasks and models in the future.