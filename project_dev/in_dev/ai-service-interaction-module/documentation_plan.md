# Documentation Plan: AI Service Interaction Module

**Overall Goal:** Create comprehensive documentation for the AI Service Interaction Module, update existing relevant documentation, and ensure all documentation is consistent and discoverable.

**I. Create New Documentation Page: `docs/ai_service_interaction.md`**

This new page will be the primary source of information for the AI Service Interaction Module.

*   **1.1. Introduction & Purpose:**
    *   Describe the module's role: facilitating communication with AI services (specifically OpenRouter).
    *   Highlight key capabilities: prompt sending, handling standard and streaming responses, API authentication.
    *   Identify the core class: [`OpenRouterAPI`](src/ai_whisperer/ai_service_interaction.py:20) in [`src/ai_whisperer/ai_service_interaction.py`](src/ai_whisperer/ai_service_interaction.py).
*   **1.2. Configuration:**
    *   Explain that configuration relies on `config.yaml` and the `OPENROUTER_API_KEY` environment variable.
    *   Detail the `openrouter` section from `config.yaml` (referencing [`docs/configuration.md`](docs/configuration.md:40)):
        *   `api_key`: Sourced from `OPENROUTER_API_KEY`.
        *   `model`: Default OpenRouter model.
        *   `params`: Default API parameters (e.g., `temperature`, `max_tokens`).
        *   `site_url`, `app_name`: For API request headers.
        *   `cache`: Boolean for enabling/disabling API response caching.
        *   `timeout_seconds`: API request timeout.
    *   Explain `task_models` in `config.yaml` for task-specific overrides (referencing [`docs/configuration.md`](docs/configuration.md:67)).
    *   Include a `config.yaml` example snippet for the `openrouter` section.
*   **1.3. Programmatic Usage (via `OpenRouterAPI` class):**
    *   **1.3.1. Non-Streaming Interactions (`call_chat_completion` method):**
        *   Explain the purpose of [`call_chat_completion()`](src/ai_whisperer/ai_service_interaction.py:172).
        *   List and describe key parameters: `prompt_text`, `model`, `params`, `system_prompt`, `tools`, `response_format`, `images`, `pdfs`, `messages_history`.
        *   Provide Python code examples for:
            *   A basic API call.
            *   Using `tools` (function calling).
            *   Requesting `response_format` (e.g., JSON output).
            *   Sending multimodal input (e.g., `images`).
    *   **1.3.2. Streaming Interactions (`stream_chat_completion` method):**
        *   Explain the purpose of [`stream_chat_completion()`](src/ai_whisperer/ai_service_interaction.py:384).
        *   List and describe key parameters.
        *   Clarify that it returns a generator yielding Server-Sent Event (SSE) data chunks.
        *   Provide a Python code example showing how to iterate through the stream and process data chunks.
*   **1.4. Error Handling:**
    *   Summarize common exceptions raised by the module (e.g., [`OpenRouterAuthError`](src/ai_whisperer/exceptions.py:9), [`OpenRouterRateLimitError`](src/ai_whisperer/exceptions.py:10), [`OpenRouterConnectionError`](src/ai_whisperer/exceptions.py:11), [`OpenRouterAPIError`](src/ai_whisperer/exceptions.py:8), [`ConfigError`](src/ai_whisperer/exceptions.py:10)).
    *   Briefly explain potential causes for these errors.

**II. Update Existing Usage Guide: `docs/usage.md`**

*   **2.1. Review and Refine:** Check if current content in [`docs/usage.md`](docs/usage.md:1) needs updates or removal due to the new module.
*   **2.2. New Section: "Programmatic AI Service Interaction"**
    *   Add a new major section detailing how to use the `OpenRouterAPI` class programmatically.
    *   Include a concise example of instantiating `OpenRouterAPI` (using `load_config` from [`src/ai_whisperer/config.py`](src/ai_whisperer/config.py:64)).
    *   Provide practical, use-case-driven Python examples for:
        *   `call_chat_completion` (e.g., simple Q&A).
        *   `stream_chat_completion` (e.g., accumulating streamed text).
    *   Cross-reference the new [`docs/ai_service_interaction.md`](docs/ai_service_interaction.md) for detailed API information.
*   **2.3. Integrate with Other Sections:** If other parts of [`docs/usage.md`](docs/usage.md:1) (like "Running JSON Plans") involve AI interactions now handled by this module, update them to reflect this.

**III. Update Main Index Page: `docs/index.md`**

*   **3.1. Add New "AI Service Interaction" Section:**
    *   Include a brief (1-2 sentences) overview of the module's purpose.
    *   Add a direct link to the new [`docs/ai_service_interaction.md`](docs/ai_service_interaction.md) page.

**IV. General Requirements**

*   **4.1. Consistency:** Ensure all new and modified documentation matches the style, formatting, and tone of existing `docs/` files.
*   **4.2. Markdown Usage:** Utilize Markdown best practices for headings, code blocks (with language specification), lists, and links.

**Visual Plan (Documentation Structure Update):**

```mermaid
graph TD
    subgraph "Documentation Root"
        A([`docs/index.md`](docs/index.md))
    end

    subgraph "Core Module Documentation"
        B([`docs/ai_service_interaction.md`](docs/ai_service_interaction.md) - New)
    end

    subgraph "Usage & Configuration Guides"
        C([`docs/usage.md`](docs/usage.md) - Updated)
        D([`docs/configuration.md`](docs/configuration.md) - Referenced)
        E([`docs/logging_monitoring.md`](docs/logging_monitoring.md) - Existing)
    end

    subgraph "Source Code & Design (References)"
        F([`src/ai_whisperer/ai_service_interaction.py`](src/ai_whisperer/ai_service_interaction.py))
        G([`src/ai_whisperer/config.py`](src/ai_whisperer/config.py))
        H([`ai_service_interaction_design.md`](project_dev/in_dev/ai-service-interaction-module/ai_service_interaction_design.md))
    end

    A -->|Links to / Introduces| B
    A -->|Links to| C
    A -->|Links to| D
    A -->|Links to| E

    C -->|References for detailed examples| B
    C -->|References for config details| D

    B -->|Documents| F
    B -->|Explains configuration based on| G
    B -->|References for config structure| D
    B -->|Based on design from| H