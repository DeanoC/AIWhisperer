# Documentation Update Plan: Cost and Token Tracking Feature

**Overall Goal:** Update documentation to reflect the new cost and token tracking feature for OpenRouter models.

**Affected Files:**
1.  [`docs/ai_service_interaction.md`](docs/ai_service_interaction.md:1)
2.  [`docs/usage.md`](docs/usage.md:1)
3.  [`docs/index.md`](docs/index.md:1)

---

**Plan Details:**

**1. Update [`docs/ai_service_interaction.md`](docs/ai_service_interaction.md:1)**

*   **Location:** A new subsection titled "Cost and Token Tracking" will be added after the "Error Handling" section.
*   **Content Rationale:** This file is the primary source of truth for the `OpenRouterAPI` client, so it needs the most detailed explanation.
*   **Proposed Text:**
    ```markdown
    ## Cost and Token Tracking

    The `OpenRouterAPI` client now automatically tracks estimated cost and token usage for interactions with OpenRouter models. This provides insights into API consumption.

    ### What is Tracked?

    For each call made through `call_chat_completion()` or `stream_chat_completion()` to an OpenRouter model, the following information is tracked:

    *   **Prompt Tokens:** The number of tokens in the input prompt.
    *   **Completion Tokens:** The number of tokens in the generated response.
    *   **Total Tokens:** The sum of prompt and completion tokens.
    *   **Estimated Cost:** The estimated cost of the API call, calculated based on the model's pricing and the token counts.

    This information is typically extracted from the response headers or body provided by the OpenRouter API.

    ### How is it Handled?

    After each successful API call, the cost and token information for that specific call is stored as attributes within the `OpenRouterAPI` instance. Developers using the library programmatically can access these values directly from the client object after a call completes.

    For example:

    ```python
    # Assuming openrouter_client is an instantiated OpenRouterAPI object
    # and a call has just been made:
    # response = openrouter_client.call_chat_completion(...)

    # Access the tracked information for the last call:
    last_cost = openrouter_client.last_call_cost 
    last_prompt_tokens = openrouter_client.last_call_prompt_tokens
    last_completion_tokens = openrouter_client.last_call_completion_tokens
    last_total_tokens = openrouter_client.last_call_total_tokens

    if last_cost is not None:
        print(f"Last call cost: ${last_cost:.6f}")
        print(f"Prompt tokens: {last_prompt_tokens}, Completion tokens: {last_completion_tokens}, Total: {last_total_tokens}")
    else:
        print("Cost and token information for the last call is not available (e.g., call failed or model doesn't provide it).")
    ```

    This information is primarily for internal tracking and can be leveraged for future features such as detailed usage analysis, reporting, or budget management within applications built on AIWhisperer. Currently, this data is not aggregated across calls or exposed through a dedicated CLI command for end-users but is available programmatically.
    ```

---

**2. Update [`docs/usage.md`](docs/usage.md:1)**

*   **Location:** A new subsection "6. Cost and Token Tracking" will be added under the "Advanced OpenRouter API Usage (via AI Whisperer Library)" section. This will follow the "5. Caching" subsection.
*   **Content Rationale:** This file describes general usage, so a brief mention and a link to the detailed documentation is appropriate.
*   **Proposed Text:**
    ```markdown
    ### 6. Cost and Token Tracking

    When using the `OpenRouterAPI` client programmatically, AIWhisperer now tracks the estimated cost and token usage (prompt and completion) for each interaction with OpenRouter models. This information is stored within the `OpenRouterAPI` object after each call.

    This is useful for developers who want to monitor their API consumption. For detailed information on what is tracked, how it's handled, and how to access this data programmatically, please refer to the "Cost and Token Tracking" section in the [AI Service Interaction Module Documentation](ai_service_interaction.md).
    ```

---

**3. Update [`docs/index.md`](docs/index.md:1)**

*   **Location:** An additional sentence will be added to the existing "AI Service Interaction Module" section.
*   **Content Rationale:** The index provides a high-level overview, so a brief mention of this new capability within the relevant module description is suitable.
*   **Proposed Text (showing the modified section):**
    ```markdown
    ## AI Service Interaction Module

    The AI Service Interaction Module handles communication with external AI services, including sending prompts and processing streaming responses from providers like OpenRouter. It also includes capabilities for tracking the cost and token usage associated with these API calls.

    For detailed information, please see the [AI Service Interaction Module Documentation](ai_service_interaction.md).
    ```

---

**Diagram Review:**
Based on the file listing of the `docs` directory and the nature of this feature (data tracking), it is unlikely that any existing diagrams require updates. The changes are primarily textual.