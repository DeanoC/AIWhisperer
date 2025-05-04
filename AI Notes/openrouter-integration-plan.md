# OpenRouter API Integration Plan

**Date:** May 4, 2025

**Goal:** Implement the foundational `ai_whisperer.openrouter_api` module to handle basic interactions with the OpenRouter API, including authentication, sending requests, and basic response/error handling. Integrate this module into the existing CLI shell (`main.py`) for a simple end-to-end test.

**Scope:**

* **In Scope:**
  * Creating/refining the `ai_whisperer.openrouter_api` module.
  * Implementing a function/method to send a request to OpenRouter using configuration details (API key, model, parameters).
  * Handling API key retrieval securely (preferring environment variables).
  * Basic error handling for API responses (authentication, rate limits, server errors) and network issues.
  * Defining custom exceptions for OpenRouter API errors in `exceptions.py`.
  * Writing unit tests (`tests/test_openrouter_api.py`) covering success and various error scenarios using mocking.
  * Minimal integration into `main.py`: calling the API function with a placeholder prompt and printing the raw response or error.
* **Out of Scope:**
  * Complex prompt construction logic (combining markdown, config prompts, etc.). This will be handled by the `processing` module in a later task.
  * Detailed parsing or validation of the LLM response content.
  * Transforming the response into the target YAML format.
  * Implementation of the full iterative refinement loop described in the design report.

**Implementation Details:**

1. **Configuration (`config.py`):**
   * Ensure `AppConfig` can load the OpenRouter API key, preferably from an environment variable (`OPENROUTER_API_KEY`) with a fallback to the `config.yaml` (clearly documented as less secure).
   * Ensure `AppConfig` loads the selected model ID and relevant parameters (temperature, max_tokens).
2. **Exceptions (`exceptions.py`):**
   * Define specific exception classes for API errors (e.g., `OpenRouterAPIError`, `OpenRouterAuthError`, `OpenRouterRateLimitError`).
3. **OpenRouter API Module (`openrouter_api.py`):**
   * Use a suitable HTTP client library (e.g., `requests` or `httpx`). Add it to `requirements.txt`.
   * Implement a primary function/method, e.g., `call_openrouter(prompt: str, config: AppConfig) -> str`:
     * Retrieve API key securely from `config`.
     * Construct the request payload (model, messages/prompt, parameters) according to OpenRouter API documentation (OpenAI-compatible format).
     * Set appropriate headers (Authorization, HTTP-Referer, X-Title).
     * Send the POST request to the OpenRouter chat completions endpoint (`https://openrouter.ai/api/v1/chat/completions`).
     * Handle successful responses: extract the content from the first choice's message.
     * Handle error responses: check status codes (401, 402, 429, 500, etc.) and raise corresponding custom exceptions defined in `exceptions.py`.
     * Handle network errors (e.g., connection timeout) and raise an appropriate exception.
4. **Testing (`tests/test_openrouter_api.py`):**
   * Use `pytest` and a mocking library (like `unittest.mock` or `pytest-mock`).
   * Mock the HTTP client library (`requests.post` or `httpx.post`).
   * Test successful API call and response parsing.
   * Test handling of 401 Unauthorized error -> `OpenRouterAuthError`.
   * Test handling of 429 Rate Limit error -> `OpenRouterRateLimitError`.
   * Test handling of other relevant HTTP error codes -> `OpenRouterAPIError`.
   * Test handling of network/request exceptions.
   * Test correct construction of request payload and headers.
5. **Main Integration (`main.py`):**
   * In the main execution flow (after loading config and requirements):
     * Create a simple placeholder prompt (e.g., "Explain the concept of Test Driven Development in one sentence.").
     * Call `openrouter_api.call_openrouter` with the placeholder prompt and loaded config.
     * Wrap the call in a try/except block to catch potential `OpenRouterAPIError` exceptions and print user-friendly messages.
     * Print the raw response content or the error message to the console. (Actual YAML generation/saving is out of scope for this task).

**Checklist:**

* [x] Update `config.py` for API key handling (prefer environment variable).

* [x] Add HTTP client library (`requests` or `httpx`) to `requirements.txt`.

* [x] Define custom exceptions in `exceptions.py`.

* [x] Implement `call_openrouter` function in `openrouter_api.py` with request logic and error handling.

* [x] Implement unit tests in `test_openrouter_api.py` covering success and error cases.

* [x] Add minimal integration call in `main.py` with basic error catching and output.

* [x] Ensure all tests pass (`pytest`).

* [x] Document the new functions/exceptions with docstrings.

* [x] Update `Openrouter Task.md` to reflect this refined scope and link to this plan.
