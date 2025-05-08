# AI Service Interaction Module

## Description
The AI Service Interaction Module interfaces with AI services, primarily OpenRouter, to send prompts and receive responses. It supports streaming responses from AI models to provide real-time feedback or allow for iterative processing. It handles API authentication, request formatting, and response parsing, and allows configuration of different models for different types of tasks (leveraging AIWhisperer's existing task-specific model configuration).

## User Stories

- As a developer, I want the runner to interact with AI services (like OpenRouter) so that I can leverage AI capabilities in my plans.
- As a developer, I want the runner to handle streaming responses from AI models so that I can process responses in real-time.

## Acceptance Criteria

- The runner can send prompts to an AI service (OpenRouter) and receive responses.
- The runner can handle streaming responses from the AI service.
- The runner can authenticate with the AI service using API keys from the configuration.