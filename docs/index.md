# Welcome to AI Whisperer Documentation

The AI Whisperer is a system designed to automate and streamline the process of implementing features and tasks based on natural language requirements. It leverages AI models to generate detailed plans and subtasks, and a runner to execute these plans.

## State Management

The AI Whisperer runner includes a robust State Management feature. This feature is crucial for maintaining the overall state of the feature implementation process across multiple steps and tasks. It stores intermediate results, file paths, and any context necessary for subsequent steps. This enables the runner to support checkpointing and resuming of plan execution, allowing developers to pick up where they left off if a run is interrupted.

## Logging and Monitoring

AIWhisperer incorporates a comprehensive logging system and a real-time terminal monitoring interface. These features are designed to provide clear visibility into the execution of plans, aid in debugging, and allow for user interaction with running tasks. Key aspects include detailed action logging, status tracking of plan steps, and interactive commands like pause, resume, and cancel.

For an in-depth understanding, please see the [Logging and Monitoring Documentation](logging_monitoring.md).
